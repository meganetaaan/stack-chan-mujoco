# 後退の重心移動22%候補

歩行周期に対する後退の重心移動時間を22%とし、残る遊脚時間68%、整定時間10%とした。前進・旋回の時間配分、r8機構、脚長・足形状、駆動条件、全評価閾値は変更していない。前進足幅62 mm、後退・旋回・停止64 mmの足置きを継続する。

固定開発条件310501と難条件310613は205秒・24区間を総合通過した。開発シード311101〜311120も20/20が全区間の運動・着地要件を通過し、転倒・自己衝突・関節制限逸脱・保護停止なしで完了した。途中のソース変更、失敗の差し替えはない。同じ20条件を25%、20%との比較に使用したため、独立な正式受入標本ではない。

全20条件の実状態から運動指標を再計算し、シード・ハッシュ・着地イベント・集計の一致を確認した結果が `paired20_audit.json`。最大横速度RMSEは0.0297966343 m/s（基準0.030）、移動区間の各足の最少有効着地数は6（基準2）。横速度の余裕は小さく、開発20/20を正式合格の代用にしない。

`actual_motion.png` / `.pdf` は固定条件と310613の実状態軌跡と全24区間の横速度指標。描画スクリプトと入力ハッシュを併記する。各試行は実MuJoCo積分状態、着地イベント、プロトコル、実行ソース、全結果を保存する。実行時の `outputs/` パスは履歴として残す。

再現例（リポジトリルート、出力先は未使用パス）：

```sh
python generate_yaw_maneuver_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r8_yaw_offset_flange_v1 --out outputs/new_phase22_ref --duration 205 --shift-fraction .25 --steady-inset-mm 25.9 --period .32 --forward-period .30 --forward-stance-width-mm 62 --backward-shift-fraction .22
python probe_yaw_dynamics_candidate.py --design assets/r8_yaw_offset_flange_v1 --reference outputs/new_phase22_ref/reference.json.gz --protocol configs/maneuver/acceptance_v1.json --duration 205 --static-torque-scale 1 --yaw-kp 6 --yaw-kd .13 --seed 310613 --randomize --out outputs/new_phase22_trial
python assess_yaw_development_batch.py --batch validation/yaw_backward_phase22_development_v1/paired20 --out outputs/new_phase22_audit.json
```

この候補を正式評価へ進める。正式結果は別ディレクトリに保存し、ここに開発結果と混ぜない。機構の固定側締結・ねじ選定・強度と慣性同定は未確定であり、製造リリース・実機性能は主張しない。

`fixed205.mp4` は固定開発試験の全MuJoCo積分状態を50 fps・10,251フレームで再生したもの。初期時刻のフレームを含むため動画長は205.02秒、最後の実状態時刻は205秒。`fixed205_video.json` にモデル・実状態・動画のハッシュを保存した。24秒の後退、38秒の旋回、198秒の曲線歩行の代表フレームも収録し、目視確認した。後半の黒い背景は有限の描画用床の範囲外であり、物理床は無限平面のまま。動画の見た目を合否判定の代わりには使わない。
