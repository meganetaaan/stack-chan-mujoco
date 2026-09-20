# 90度・3秒未満の完了確認

対象はMuJoCo上のr9候補。最終モデルは `assets/r9_fast_turn_v1`、検証記録は `validation/fast_turn_v1`。実機や製造強度の認定ではない。

| 要求 | 確認結果 | 証拠 |
|---|---|---|
| 左右90度を3秒未満で旋回 | 両方向とも停止誤差±1度以内。方位・着地・胴体の揺れの全条件を約2.76秒で満たす | `completion_audit_full_settle.json`、全10試行の状態列 |
| 少ない歩数 | 全試行で左右3回ずつ、計6回の交互の有効着地。空中時間・持上げ・接地確認を1 ms記録から独立再計算 | `contact_trace.npz`、`completion_audit_full_settle.json` |
| 干渉対策を優先 | ヨー軸・股関節間隔・足・連結板・トレー・胴体下面をCADから変更。45部品を左右各63実姿勢で検査し検出干渉なし | `left_cad_audit.json`、`right_cad_audit.json`、モデルCAD |
| 外形を大きく変えない | Tab5顔、128 mm胴体、大腿50 mm、下腿44 mmを維持。足のみ94×52→86×48 mm、股関節間隔44→52 mm | 新旧 `robot.json`、CAD、動画 |
| 現行の駆動・物理・安全判定を維持 | トルク、速度・遅延、摩擦損失、減衰、重力、積分設定、飽和保護を維持。補助力・姿勢拘束・衝突除外なし。全10試行で安全停止なし | `physics_invariants.json`、凍結ソース、試行報告 |
| 実状態から時間と安定性を確認 | 胴体四元数から方位を再計算。角速度・並進速度・傾き・両脚接地を記録から確認し、停止後最低1秒以上維持 | `completion_audit_full_settle.json`、`verify_fast_turn_release.py` |
| 旧正式モデル・結果を保存 | 既存r8の40試行を再評価し固定20/20、ランダム化18/20が一致 | `prior_acceptance_recheck.json` |
| 新候補を分離・再現可能に整理 | モデル、検証結果、開発履歴を分離。新規再生成が公開モデルとバイト一致し、公開配置から実行して同じ結果を確認 | `rebuild_check.json`、`published_model_smoke.json`、`FAST_TURN_RUN_ja.md` |

10条件は左右の名目条件と、重量±5%、摩擦係数0.7／0.9を単独で変えた条件。任意の複合外乱・ランダム条件の成功率を保証するものではない。CAD検査は離散姿勢で、連続掃引やねじ・支持部の強度は保証しない。

再確認：

```sh
python verify_fast_turn_release.py --design assets/r9_fast_turn_v1 \
  --archive validation/fast_turn_v1 --out outputs/r9_release_recheck.json
```
