# 動作に応じた足幅切替の開発検証

同じ `assets/r8_yaw_offset_flange_v1` モデルで、遊脚の足置きを変えて前進時の横揺れと後退時の着地安定性を両立できるか調べる。機構・足形状・脚長・アクチュエータ条件・判定閾値は変更していない。

## 制御変更

`--forward-stance-width-mm 62` を明示した場合のみ、通常の64 mm幅から、前進を開始した最初の2歩を終えた後で62 mmへ移る。正の前進速度を持つ曲線歩行も対象。後退・その場旋回・停止では元の64 mmへ戻す。指令は歩の境界で取り込み、遊脚の水平軌道に滑らかな横方向の足置きを加える。接地中の足を瞬間移動させない。

停止時には足の前後位置・向きだけでなく幅も合わせてから両足支持へ整定する。既定ではこの機能を使わず、変更前の参照先頭8秒のq/q12/base/support/静的トルクと完全一致する。

## 参照とソフトの検証

全205秒・10,251姿勢をMuJoCoモデルの順運動学で再計算し、足中心間隔が62〜64 mm、20 ms当たりの片足横移動が最大0.191 mmであることを確認した。`feet_audit` と `reference_width.png` はこの**関節参照の幾何検査**であり、実際に歩いた証拠とは区別する。実際の歩行は下記の浮遊ベース動力学試験で評価する。

関連18テストが通過。追加テストは全指令スケジュールで足幅の連続性・停止時の復帰と、ヨー角の連続性・制限を確認する。既存の機構・保護・ばらつき・姿勢オブザーバのテストも実行した。

## 開発結果

32秒の開発6シード310611〜310616は全て物理異常なく完了し、先頭5区間の全運動・着地要件を満たした。着地は順に34/33、34/33、34/20、34/34、34/33、34/33回。32秒には旋回が含まれず、全205秒の受入率には読み替えない。

全205秒の固定条件310501は、物理異常なし・全24区間の運動指標・全着地要件を満たし、開発試験として総合通過した。有効着地293/292回、移動区間の各足最少着地14回、最大横速度RMSEは0.0260503 m/s（閾値0.030）。

ランダム3条件も全て物理異常なく205秒を完了し、全24区間の運動指標を満たした。310611（着地293/290回）と310616（293/291回）は全着地要件も通過。310613（275/246回）は14_backwardが16/0回、16_backwardが0/16回となり、総合不合格。**固定の開発1試行とランダム2/3試行の通過であり、正式20/20・18/20の達成ではない。**

全205秒の固定条件とランダム3条件の結果は `summary.json` と各trialのreportを参照。正式受入シード217000〜217019、218000〜218019は未使用。これらの開発シードは調整に再使用しているため、独立な受入標本ではない。

`random32.mp4` は310613の実MuJoCo積分状態を50 fpsで再生したもの。モデルのばらつきも再適用し、運動を合成していない。全試験の状態記録、参照、ソース、失敗を含む判定結果を保存する。

## 再現

各出力先は未使用パスにする。元CAD参照環境は既存の再現手順で作成する。

```sh
python generate_yaw_maneuver_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r8_yaw_offset_flange_v1 --out outputs/new_adaptive_ref --duration 205 --shift-fraction .25 --steady-inset-mm 25.9 --period .32 --forward-period .30 --forward-stance-width-mm 62
python probe_yaw_dynamics_candidate.py --design assets/r8_yaw_offset_flange_v1 --reference outputs/new_adaptive_ref/reference.json.gz --protocol configs/maneuver/acceptance_v1.json --out outputs/new_adaptive_trial --duration 205 --static-torque-scale 1 --yaw-kp 6 --yaw-kd .13
python audit_yaw_reference_feet.py --design assets/r8_yaw_offset_flange_v1 --reference outputs/new_adaptive_ref/reference.json.gz --out outputs/new_feet_audit
MUJOCO_GL=egl python replay_yaw_candidate.py --trial outputs/new_adaptive_trial --design assets/r8_yaw_offset_flange_v1 --out outputs/new_adaptive.mp4
```

32秒比較では生成・実行の両方を `--duration 32` とする。ランダム条件は試験へ `--randomize --seed 310613` などを追加する。全試験で同じ公称参照を使い、真のランダム質量から補償を作り直していない。

report内のoutputsパスは実行時履歴であり、同名ディレクトリへ収録している。モデルは既存assetsの同一物理ファイルを使用。固定側締結・強度・慣性同定などの機構上の未完事項も継続する。実機製作適合や正式受入の達成は主張しない。
