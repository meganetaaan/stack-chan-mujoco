# 停止・前進・後退の連続切替：開発試験

事前に固定した205秒プロトコルの先頭32秒だけを、固定条件seed310201で実行した。停止→前進→停止→後退→停止の5区間を異常なく完了し、完了区間の全運動指標は基準内だった。旋回以降は未実行なので `complete_schedule=false`、`development_trial_pass=false`、`motion_scoring.motion_pass=false` のまま。正式な合格試験や、全目標の達成ではない。

| 区間 | 平均前後速度誤差 m/s | 平均yaw速度誤差 rad/s | 完了区間の違反 |
|---|---:|---:|---|
| 00_stop | 0.00000 | 0.00000 | なし |
| 01_forward | 0.01276 | 0.00295 | なし |
| 02_stop | 0.00000 | 0.00020 | なし |
| 03_backward | 0.00187 | 0.00008 | なし |
| 04_stop | 0.00000 | 0.00005 | なし |

`maneuver_reference.py` は着地中の足位置を引き継ぎ、停止時に最後の足をそろえて両脚支持へ移行する。停止指令から過渡応答が落ち着くまでの区間も記録されており、評価は既定の2秒整定時間を使用する。ルート位置・向きの強制や補助外力はない。

`stackchan_rl/maneuver_env.py` は既存環境の物理ステップ・衝突・関節制限・転倒・飽和保護の検査をそのまま呼び出す。停止指令だけ着地間隔要件を免除し、動作指令中は従来の1秒以上の着地中断を失敗にする。指令と各区間の有効着地を状態ファイルへ保存する。今回の制御は参照軌道＋静的トルク補償、追加actionはゼロ。

```sh
python probe_maneuvers.py --cad-design outputs/design_r6_base_collisions --duration 32 --out outputs/new_transition_probe
python -m unittest tests.test_maneuver_reference tests.test_maneuver_env tests.test_maneuver_protocol -v
```

実行環境は既存RL環境＋SciPy 1.18.1。状態記録は `states.npz`、実測位置・向きは `motion.npz`、判定値は `report.json`。参考軌道とprotocol/configも保存した。未調整の `--yaw-feedback` はこの試験では使用していない。旋回制御と全区間の受入評価は引き続き必要。
