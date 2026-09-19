# v3 配布前検査記録

**156件を検出し、134件を実行して合格、22件は依存ライブラリー不足のため未実行です。MuJoCoの物理歩行、SB3での本学習、v2方策との改善比較は実施していません。**

## 環境と実施範囲

Python 3.13.5、NumPy 2.3.5、PyTorch 2.10.0+cpu。MuJoCo/Gymnasium/Stable Baselines3は未導入です。pipの取得試行が失敗し、追加のpypi.org接続確認でも名前解決失敗を記録しています。ユーザーのWSL2環境でこれらを導入できないという意味ではありません。

| 範囲 | 結果 |
|---|---|
| Python構文コンパイル | 成功 |
| 既存v2のオフライン回帰 | 82件合格 |
| v3の新規オフライン試験 | 52件合格 |
| 全A案assetのSHA-256 | 43ファイル、v2と全一致 |
| 制御・観測契約 | actuation/spec等のハッシュ一致、61次元/10次元のinterface同一 |
| ピッチ/ロール分離、デッドバンド、区間二乗平均 | 人工入力で確認 |
| 初期落下・短い接触チャタリングの除外 | 人工接触系列で確認 |
| 接近速度eventと荷重rateのdt扱い | 人工入力で確認 |
| 歩数差1回の許容、過去の偏りを忘れる4秒窓 | 人工系列で確認 |
| v1/v2の報酬・転送互換性 | オフライン試験で確認 |
| 歩いていない候補を滑らかさだけで選ばないbest選択 | 人工評価データで確認 |
| actorの平均出力とlog_std保持、新criticの非転送 | PyTorchの類似構造の試験で確認。実SB3では未確認 |
| 同一指令/seed/設定による比較、欠けた指標の検出 | 人工JSONで確認 |
| MuJoCo/SB3の旧14件＋v3の新8件 | 計22件skipped、合格ではない |
| `check_env.py --config configs/walk_refine.json` | 依存不足で終了コード2、物理未実行 |
| `smoke_test.py --subproc` | 最初のpreflightで終了コード2、PPOまで到達せず |

モデル質量は元定義どおり 0.8260386996 kgです。実測重量ではありません。model fingerprintは `fd52c6f9a48c468ff049caf0392a1d855c6d3566c5ebf81e93e58a9e5a97f27c`。

## 未確認の項目

実エンジンでのsubstep計測/接触座標、計測ON/OFF時の物理同一性、実SB3のactor転送・保存・再開、並列プロセス、学習時間、GUI/動画、学習による揺れ・着地衝撃・左右偏りの改善率は未確認です。ユーザーの学習済み重みと実評価JSON/CSVも未受領です。報告された約194 mm前進・5対2着地をこの環境で再現していません。

物理テストをスタブに差し替えて通過させていません。人工系列/人工状態のunit testは、力学的に実現可能な歩容や学習の成功を意味しません。新報酬の係数と品質しきい値は最初の試行値で、実測による最適化済みパラメーターではありません。

## 再実行

MuJoCoが動作している仮想環境で、配布フォルダーのルートから実行します。

```bash
python validation/run_tests.py
python check_env.py --config configs/walk_refine.json
python smoke_test.py --subproc
```

依存が揃えば22件のruntime testsも実行対象になります。出力のskippedを合格と解釈せず、失敗時は学習へ進む前に確認してください。smokeは接続試験であり、歩行習得試験ではありません。

## 再現情報

- `validation/unit_tests.json`, `unit_tests.log`：実際の合否とskip理由。
- `validation/source_hashes.json`：source ZIPとassetのハッシュ、方策interface照合。
- `validation/changes_from_v2.patch`：コード/設定/文書のレビュー用差分。自動上書き処理ではありません。
- `validation/preflight.json`, `preflight.log`：実エンジンを呼ぶ前の依存エラー。
- `validation/runtime_v3/`, `runtime_smoke.log`：preflightで停止したsmokeログ。
- `validation/dependency_install_attempt.log`, `network_probe.log`：パッケージ取得試行の失敗。
- `validation/v1/`, `validation/v2/`：旧配布物の検査履歴。現在の版の実行結果とは区別。
