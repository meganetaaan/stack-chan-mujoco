# 立ち幅と横揺れの開発比較

同じ `assets/r8_yaw_offset_flange_v1` モデルで足中心間隔を比較した。胴体・脚長・足形状・アクチュエータ・評価閾値を変更していない。立ち幅は初期の脚関節姿勢で作る。正式受入シードは未使用。

## 結果

| 条件 | 結果 |
|---|---|
| 従来64 mm、固定205秒 | 物理異常なし・全着地要件を満たすが、横速度RMSEが4区間で超過（前回記録） |
| 62 mm、固定32秒 | 物理異常なし、先頭5区間の全運動・着地基準内。着地20/33回 |
| 60 mm、固定32秒予定 | 5秒で歩行中断。有効着地0/0回 |
| **62 mm、固定205秒** | **物理異常なく完走、全24区間の運動指標は基準内。ただし後退2区間で片足の着地不足、総合不合格** |
| 62 mm、ランダム310613 | 5秒で歩行中断。有効着地0/0回 |
| 63 mm、ランダム310613 | 21.05秒で後退中に歩行中断。有効着地19/20回 |
| 62 mm、C2鉛直軌道、ランダム310613 | 5秒で歩行中断。有効着地0/0回。今回の条件では改善なし |

62 mm固定205秒は着地249/274回。`14_backward` は15/1回、`16_backward` は1/15回で、移動区間ごとの各足2回以上という条件を満たさない。転倒・自己衝突・関節逸脱・保護停止はないが、有効歩行の証拠が不足している。全24区間の運動指標通過だけを全体合格とは扱わない。

## 診断

`analyze_yaw_lateral.py` は保存された `[時刻, x, y, yaw]` から身体座標の横速度を再計算し、固定済みスコアとの一致を検査する。従来64 mmの超過4区間では平均横速度の二乗が全RMSE二乗に占める割合は最大0.13%。主因は平均ドリフトではなく左右の振動。

`lateral_plot/lateral_comparison.png` とPDFは同じ固定条件の全移動区間を比較する。62 mmでは横速度RMSEが低下し、全区間で0.030 m/s以下となった。黒印は平均ドリフトの絶対値。評価器の窓幅・サンプル選択・閾値は変更していない。各区間の平滑化に実際に含まれたサンプル数も診断JSONに記録した。

現在の足中心位置は初期状態で左右±32 mm。支持足中心から重心目標までの定常内寄せ25.9 mmを維持し、左右±31 mmへ狭めると、参照上の左右重心振幅が6.1 mmから5.1 mmへ減る。ただし接地確認が短時間途切れる条件が増え、ランダム試験では中断した。狭い幅を全動作へ一律採用する判断はしていない。

追加比較のC2軌道は、遊脚の鉛直高さを `4 mm × 64 f³(1−f)³` としたもの。端点で高さ・速度・加速度がゼロで、中央の最高高さ4 mmを維持する。現行の四次軌道も選択可能で、既定は変更していない。試したC2条件は不合格で、推奨設定ではない。

## 検証と再現

既定の参照先頭8秒は、変更前のq/q12/base/support/静的トルクと完全一致。関連17テストにより軌道端点の滑らかさ、ヨー参照の連続性、機構・保護の既存条件を確認した。

```sh
python generate_yaw_maneuver_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r8_yaw_offset_flange_v1 --out outputs/new_width_ref --duration 205 --shift-fraction .25 --steady-inset-mm 25.9 --period .32 --forward-period .30 --stance-width-mm 62
python probe_yaw_dynamics_candidate.py --design assets/r8_yaw_offset_flange_v1 --reference outputs/new_width_ref/reference.json.gz --protocol configs/maneuver/acceptance_v1.json --out outputs/new_width_trial --duration 205 --static-torque-scale 1 --yaw-kp 6 --yaw-kd .13
python analyze_yaw_lateral.py --trial outputs/new_width_trial --out outputs/new_width_diagnosis.json
MUJOCO_GL=egl python replay_yaw_candidate.py --trial outputs/new_width_trial --design assets/r8_yaw_offset_flange_v1 --out outputs/new_width.mp4
```

短期比較では生成・実行の両方を32秒とする。幅は `--stance-width-mm 60` または63、C2は `--swing-profile c2`、ランダム条件は試験側に `--randomize --seed 310613`。診断図は `plot_yaw_lateral.py` をMatplotlib環境で実行する。

状態記録・失敗例・参照・ソース・ハッシュを保存。reportのoutputsパスは実行時履歴で、同名フォルダへ収録した。ソース変更前のスナップショットは `*_before_c2.py`、最初のC2試験時点のソースはその参照フォルダ内にも保存。既存モデルの固定側締結・強度・慣性同定の未完事項は継続する。

`video205.mp4` は62 mm固定試験の実MuJoCo積分状態を全205秒再生したもの。有限の床表示範囲から外れると背景が黒くなるが、物理上の床は無限平面。動作を合成していない。

次の検討は、狭い前進姿勢と接地が安定した広い後退姿勢を、遊脚の足置きによって連続的に切り替える方法。接地中の足位置を瞬間的に変更せず、歩き始め・停止時の幅合わせも含めて検証する必要がある。これは未実装の検討案で、今回の合格証拠ではない。
