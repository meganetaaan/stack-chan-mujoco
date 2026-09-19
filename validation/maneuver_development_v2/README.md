# 後退・旋回の開発診断 v2

受入試験ではない。試した全条件を保存し、失敗を除外していない。予約済みの217xxx/218xxx seedは未使用。モデル、衝突判定、関節制限、モータ特性、保護停止条件は既存の搭載バッテリーモデルのまま。

後退参照は周期0.32秒、重心前方オフセット−1.5 mmで改善した。固定条件96歩・31.72秒を完走し、−1.4695 m移動した。2秒以降の実測X速度は−0.04814 m/s、終了時yaw変化は約0.0513度（積分状態のルート四元数から計算）。開発用ランダムseed310101〜310105の24歩試験も全5件異常なく完走した。ただし正式な205秒の全動作切替・20/20と18/20の証拠ではない。

旋回は参照速度0、周期0.32秒で定数関節補正を試した。股関節ピッチ左右差と足首ピッチ左右差では両足の着地を伴う左右約0.087 rad/sのyaw応答が出た。目標の約0.157 rad/sは未達。膝を含めた複合補正では片足の有効着地が不足し、股関節＋足首の複合補正はwalking_interruptedで停止した。単に回転が観測されたことを旋回合格とは扱わない。

| ケース | 実行時間 s | 実測X速度 m/s | 実測yaw速度 rad/s | 左右有効着地 | 結果 |
|---|---:|---:|---:|---|---|
| backward_0p32_long_v1 | 31.720 | -0.04813724720949324 | None | [47, 48] | 短時間完走 |
| backward_random_development_v1/310101 | 8.680 | -0.047575958893641766 | -6.243374138715717e-05 | [11, 12] | 短時間完走 |
| backward_random_development_v1/310102 | 8.680 | -0.0480425751628267 | 0.00020681783419098672 | [11, 12] | 短時間完走 |
| backward_random_development_v1/310103 | 8.680 | -0.04861227034559252 | -7.287004499002619e-06 | [11, 12] | 短時間完走 |
| backward_random_development_v1/310104 | 8.680 | -0.04807625132806334 | 0.000282885691183388 | [11, 11] | 短時間完走 |
| backward_random_development_v1/310105 | 8.680 | -0.04865678818880258 | -0.0001624480714290621 | [11, 12] | 短時間完走 |
| backward_timing_sweep_v1/p0.22_x-1.5_z0 | 6.280 | -0.01002706019456844 | None | [7, 8] | 短時間完走 |
| backward_timing_sweep_v1/p0.22_x-1.5_z2 | 6.280 | -0.007026219841936997 | None | [7, 9] | 短時間完走 |
| backward_timing_sweep_v1/p0.22_x-3_z0 | 6.280 | -0.010008777650907647 | None | [8, 7] | 短時間完走 |
| backward_timing_sweep_v1/p0.22_x-3_z2 | 3.149 | -0.003919079272540013 | None | [2, 2] | walking_interrupted |
| backward_timing_sweep_v1/p0.32_x-1.5_z0 | 8.680 | -0.04814969244091182 | None | [11, 12] | 短時間完走 |
| backward_timing_sweep_v1/p0.32_x-1.5_z2 | 8.680 | -0.048110135344809984 | None | [11, 12] | 短時間完走 |
| backward_timing_sweep_v1/p0.32_x-3_z0 | 8.680 | -0.048326092890277596 | None | [11, 12] | 短時間完走 |
| backward_timing_sweep_v1/p0.32_x-3_z2 | 0.000 | None | None | None | Analytic IK exceeds configured joint limits |
| backward_timing_sweep_v1/p0.4_x-1.5_z0 | 0.000 | None | None | None | Analytic IK exceeds configured joint limits |
| backward_timing_sweep_v1/p0.4_x-1.5_z2 | 0.000 | None | None | None | Analytic IK exceeds configured joint limits |
| backward_timing_sweep_v1/p0.4_x-3_z0 | 0.000 | None | None | None | Analytic IK exceeds configured joint limits |
| backward_timing_sweep_v1/p0.4_x-3_z2 | 0.000 | None | None | None | Analytic IK exceeds configured joint limits |
| inplace_combined_yaw_v1 | 8.680 | -0.008920219471922574 | 0.08387257178629871 | [11, 0] | 短時間完走 |
| inplace_hip_ankle_yaw_v1 | 2.742 | -0.014236329873129356 | 0.11146864249384836 | [1, 0] | walking_interrupted |
| inplace_yaw_probe_v1/ankle_pitch-1 | 8.680 | -0.0021455384615229767 | -0.08792853620402918 | [10, 12] | 短時間完走 |
| inplace_yaw_probe_v1/ankle_pitch1 | 8.680 | -0.0022633748933043605 | 0.0877380786738103 | [11, 11] | 短時間完走 |
| inplace_yaw_probe_v1/hip_pitch-1 | 8.680 | 0.0014834635874911807 | -0.0871559605759622 | [11, 12] | 短時間完走 |
| inplace_yaw_probe_v1/hip_pitch1 | 8.680 | 0.001426585425898432 | 0.0864517459290003 | [11, 11] | 短時間完走 |
| inplace_yaw_probe_v1/knee-1 | 8.680 | -0.0016899350837453599 | -0.07719723845837266 | [2, 11] | 短時間完走 |
| inplace_yaw_probe_v1/knee1 | 8.680 | -0.0018078906527447382 | 0.07768113413489583 | [11, 2] | 短時間完走 |
| inplace_yaw_probe_v1/zero | 8.680 | 0.001063936866879745 | 8.742087411174272e-06 | [11, 11] | 短時間完走 |

## 再現

RL環境にSciPy 1.18.1を追加し、`docs/REPRODUCE_MOUNTED_ja.md` に沿ってCAD参照元を生成する。新しい出力先で実行する。

```sh
python probe_signed_reference.py --cad-design outputs/design_r6_base_collisions --speed -.05 --step-period .32 --com-forward-offset-mm -1.5 --steps 96 --out outputs/new_backward_long
python probe_signed_reference.py --cad-design outputs/design_r6_base_collisions --speed -.05 --step-period .32 --com-forward-offset-mm -1.5 --randomize --seed 310101 --out outputs/new_backward_random
python probe_signed_reference.py --cad-design outputs/design_r6_base_collisions --speed 0 --step-period .32 --constant-action 0 1 0 0 0 0 -1 0 0 0 --out outputs/new_inplace_hip
```

各reportに歩行周期・高さ・オフセット・定数action・乱数seed・物理ばらつきを保存。実行に使ったスクリプトは各ケースのprobe_source.pyに保存した。時期の異なる診断ではreportの項目が異なる。X速度は世界座標での回帰値であり、旋回中のbody前後速度と同一ではない。

物理実行ケースには完全なMuJoCo積分状態states.npzがある。計画失敗ケースには物理状態がない。保存configの参照軌道パスは実行時パスであり、別checkoutでは上記コマンドで新規出力を生成する。
