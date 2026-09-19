# v4 配布前検査結果

**212件を検出し、182件を実行して合格。MuJoCo/Gymnasium/SB3を必要とする30件は未実行です。**
物理歩行・PPO本学習・GUI・旧方策の閉ループ再現をこの環境で実行した結果ではありません。

## 実行環境

Python 3.13.5 / NumPy 2.3.5 / PyTorch 2.10.0+cpu。
MuJoCo/Gymnasium/Stable Baselines3は未導入。pipの名前解決に失敗し、別経路での
取得も失敗しました。ユーザーのWSL環境で利用できない、という意味ではありません。
動作中の仮想環境に追加ライブラリーを導入する必要はありません。

## 実行した検査

| 範囲 | 結果 |
|---|---|
| 全Pythonの構文 | compileall成功 |
| 既存v3オフライン回帰 | 134件合格 |
| v4追加オフライン試験 | 48件合格 |
| 元A案の43 asset | SHA-256がすべてv3と一致 |
| フィルター数値 | 凍結した旧bank＋probeと、新制御のトルク・target・遅延状態を照合。40/80 ms、reset、強度係数変更を含め合格 |
| フィルターなし | 元のServoBankとの数値一致、旧interface一致 |
| 指令距離cap | 静止・半速・指令一致・過速で人工状態の報酬を照合 |
| 着地報酬の順序 | 同一脚連打、cooldownで抑制した反対脚、同時着地、停止を検査。生カウントは旧版と一致 |
| 計測・評価・選択 | targetの関節別平均とglobal RMSを分離。静止・過速・連打・欠落データを検査 |
| 保存互換性 | LPF以外のモデル/観測/action差分は拒否。旧設定はtau=0で維持 |
| 実ユーザー重みの転送 | 保存テンソルを一致する純PyTorch構造へ厳密読込み。actor出力差0、新critic非転送、log_std一致 |
| 実preflight / smokeの試行 | 依存不足で終了コード2、物理/PPOに未到達 |

## 実ユーザー重みの試験の意味

提供された `walk_refine_debug.zip` の475,000ステップ時点の `best/model.zip`
（SHA-256 `649edf23c0557e09468bd4c8e6254a4f3fba1250a981228fb09f002d03dd77f4`）
から、`policy.pth`を `torch.load(weights_only=True)` で読み込みました。
SB3と同じ名前・寸法・活性化の層を持つ純PyTorch構造にstrict loadし、実際の
`transfer_policy` 関数を適用しました。100個の同一人工観測に対しactorの生出力の
最大差は0で、log_stdも一致し、新criticの初期値が保持されました。

**SB3のPPO.load、最適化、物理閉ループを試したものではありません。**
モデルZIP内のpickle設定を代替実行して「SB3動作確認」とは扱っていません。
ユーザーの重みそのものは本キットに再配布していません。
記録は `validation/user_checkpoint_transfer.json`。

## 未実行

30件の実行テスト（v3まで22件＋新規8件）、実MuJoCoでのprobe等価性、
SB3への接続、並列学習、真の保存・再開・転送、GUI、動画、本学習、
20試行の改善率、実機動作は未確認です。

ユーザーが既に実行したLPF比較結果は採用判断の根拠ですが、v4のソフトウェアや
新報酬での学習結果ではありません。新しい距離/速度/滑らかさの目標が達成可能と
実証したわけではありません。試験基準を緩めて成功にする変更はしていません。

## 再実行

```bash
python validation/run_tests.py
python check_env.py --config configs/walk_lp40.json
python smoke_test.py --subproc
python audit_lp40.py
```

依存が揃ったWSLでは実行テストも走ります。`skipped=30`は30件の合格ではなく、
未実行を意味します。smokeは短いソフトウェア接続試験で、歩行習得の試験ではありません。

## 検査ファイル

- `validation/unit_tests.json` / `.log`: 212件の内訳・skip理由・環境情報。
- `validation/user_checkpoint_transfer.json`: 実保存重みのテンソル転送。
- `validation/source_hashes.json`: 元ZIP、probe、ユーザー比較結果、43 assetの由来。
- `validation/reward_audit.json`: 人工状態での報酬計算。
- `validation/preflight.*` / `runtime_v4/` / `runtime_smoke.log`: 依存不足で停止した実行記録。
- `validation/dependency_install_attempt.log`: 実際の取得エラー。
- `validation/changes_from_v3.patch`: 実装・設定・文書の差分。
- `validation/v3/`: 過去の検査結果。v4の結果ではありません。
