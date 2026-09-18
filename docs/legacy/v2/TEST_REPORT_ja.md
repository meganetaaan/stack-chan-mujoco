# v2 配布前テスト結果

**96件を検出し、82件を実行して合格。MuJoCo/Gymnasium/SB3を必要とする14件は未実行です。実学習・歩行成功を確認した結果ではありません。**

作成環境：Python 3.13.5、NumPy 2.3.5、PyTorch 2.10.0+cpu。`pip install` を試しましたが、パッケージ取得先の名前解決に失敗してMuJoCo/Gymnasium/SB3を導入できませんでした。ユーザーのWSL2でこれらが動かないという意味ではありません。

## 実行したテスト

| 範囲 | 結果 |
|---|---|
| Python構文コンパイル | 合格 |
| 旧キットのオフライン回帰40件 | 合格 |
| 新しい報酬・接地イベント・選択・互換性・workflow・torch転送の42件 | 合格 |
| 全A案assetのSHA-256 | 旧キットと一致 |
| 旧/新Stage 1〜3の方策I/O契約 | 一致 |
| 速度0、半分の速度、指令一致、後退に対する報酬値 | 人工状態で比較済み |
| 初期落下・滑り・チャタリング・同時跳躍・同一足連打 | 人工接地系列で得点/カウントを検査済み |
| 同じ区間の足の往復、胴体の揺動 | 前進記録を繰り返し得点にしない検査に合格 |
| actorの出力保持、criticの非転送、log_std再設定 | PyTorchのSB3類似構造で検査。実SB3実行とは別 |
| 旧configの補完 | 報酬version 1と旧係数を保持 |
| 時間だけ完走した方策のbest選択 | 人工評価データで、実歩数・前進のある候補を優先 |
| 停止試験と歩行試験が混在する進級判定 | 全指令を検査し、停止成功で歩行失敗を隠さない |

## 未実行

MuJoCoによる新コードのコンパイル・接触・PD駆動、実SB3でのactor転送、PPO更新、並列プロセス・保存・再読込み、GUI/動画、長時間学習、ユーザーの既存policyでの再現、歩行成功率は未確認です。ユーザーの学習済み重みと詳細評価CSVは受け取っていません。

`check_env.py --config configs/walk_step1.json` と `smoke_test.py --subproc` を実行しましたが、依存不足を検出した段階で終了コード2となりました。シミュレーターをスタブ化して「実行済み」にする処理はありません。

## 報酬式だけの検査例

0.02 m/s指令に対し、旧式では静止中も速度項が約1.443/秒（最大2/秒）、新式では0/秒（指令一致時8/秒）です。新式では半分の速度0.01 m/sも正の速度項になります。

この数値は人工的な状態で関数を呼んだ結果で、力学的に到達可能な歩容を観測したものではありません。報酬の順位が改善したことと、PPOの収束・歩行成功は別です。探索や接触条件、機構の制約が原因となる可能性も残ります。

## 再実行

既にMuJoCoが動くWSLの仮想環境で、キットのルートから次を実行します。

```bash
python -m unittest discover -s tests -v
python smoke_test.py --subproc
```

依存がある環境では14件の実行テストも走ります。`OK (skipped=14)` はそれら14件の合格を意味しません。`validation/run_tests.py` で検査記録を更新できます。

詳しい実行ログは `validation/unit_tests.json`, `validation/unit_tests.log`, `validation/preflight.json`, `validation/runtime_v2/`, `validation/reward_audit.json`, `validation/dependency_install_attempt.log`、旧配布版の検査記録は `validation/v1/` に保存しています。
