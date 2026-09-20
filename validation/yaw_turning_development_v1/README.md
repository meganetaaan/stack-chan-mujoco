# 股関節ヨーによる左右旋回の開発試験

12軸候補 `assets/r7_yaw_xc_ankles_v1` に、接地中は一定速度で逆向きにヨーを動かし、遊脚中に次の足向きへ戻す参照を追加した。元の足位置を6軸脚の逆運動学で維持する。胴体の位置・向きは初期化後に上書きせず、全関節は有限トルク・速度・遅延・フィルタ・保護を持つ実MuJoCoで積分した。外形・脚長・足形状は変更していない。

**これは独立した旋回の開発試験で、205秒の動作切替、固定20/20、ランダム化18/20の受入試験ではない。** plantのランダム化はまだ適用していない。受入シードは使用していない。

## 結果

全条件11.24秒、冒頭1秒は直立、周期0.32秒、足上げ4 mm、姿勢高さ補正2 mm。ヨーのPDゲインは6 Nm/radと0.13 Nm s/rad。元の直進参照からの静的トルク補償を近似として保持し、ヨーにはフィードフォワードトルクを加えていない。

最初のCOM inset 24 mmでは、足踏み、左右0.08 rad/s、左右π/20 rad/sの5条件すべてで物理異常なく完了した。左右π/20の実回転量は+1.57072、−1.57003 rad。ただし横速度の平滑化RMSEは約0.03295〜0.03297 m/sで、事前閾値0.030 m/sを超えた。

接地側の重心目標を足中心から内側へ25 mmに置き、左右移動を減らした結果：

| 指標 | 左旋回 | 右旋回 | 対応する事前閾値 |
|---|---:|---:|---:|
| 定常平均ヨー速度 rad/s | +0.15161 | −0.15201 | 指令±0.15708 |
| 平均ヨー速度誤差 rad/s | 0.00547 | 0.00507 | 0.04 |
| 平滑化ヨー速度RMSE rad/s | 0.00799 | 0.00796 | 0.06 |
| 平滑化横速度RMSE m/s | 0.02565 | 0.02567 | 0.03 |
| 旋回中最大位置ずれ m | 0.03006 | 0.02810 | 0.15 |
| 有効着地 左/右 | 15/15 | 15/16 | 区間当たり各2以上 |
| 転倒・自己衝突・関節逸脱・保護停止 | なし | なし | なし |

定常値は3.0〜11.24秒、平滑化窓は事前定義の0.5秒。比較した6つの運動指標は左右とも閾値内だが、正式な区間積分誤差・停止・切替評価は含まない。`analyze_yaw_development.py` は常に `formal_acceptance: false` を出力する。25.5 mmの左旋回も物理異常なしで横速度RMSEは0.02253 m/sだったが、25 mmで左右を確認した。

## 再現

MuJoCoとCAD元データの環境は既存再現文書に従う。未使用の出力先を指定する。

```sh
python generate_yaw_zero_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r7_yaw_xc_ankles_v1 --out outputs/new_turn_base --speed 0 --period .32 --height-offset-mm 2 --steps 32 --com-inset-mm 25
python generate_yaw_step_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r7_yaw_xc_ankles_v1 --reference outputs/new_turn_base/reference.json.gz --out outputs/new_left_ref --rate 0.15707963267948966
python probe_yaw_dynamics_candidate.py --design assets/r7_yaw_xc_ankles_v1 --reference outputs/new_left_ref/reference.json.gz --out outputs/new_left_trial --duration 11.24 --static-torque-scale 1 --yaw-kp 6 --yaw-kd .13
python analyze_yaw_development.py --trial outputs/new_left_trial --reference-report outputs/new_left_ref/report.json --out outputs/new_left_metrics.json
MUJOCO_GL=egl python replay_yaw_candidate.py --trial outputs/new_left_trial --design assets/r7_yaw_xc_ankles_v1 --out outputs/new_left.mp4
```

右旋回はrateの符号を反転。`step_screen` はinset24、`com_screen` は25・25.5の比較。参照・実積分状態・停止理由・ソースハッシュを保存し、元のoutputsパスは履歴として残す。生成スクリプトのスナップショットも収録した。

再生は元モデル・全凍結アセット・軌跡のハッシュ、状態サイズ、時刻間隔を検査した後、記録した積分状態を各フレームへ適用する。ロボットの動きを補間・生成しない。カメラのみ胴体へ追従。動画は563フレーム、50 fps、状態の最終時刻11.24秒（動画長11.26秒は初期フレームを含む）。最初の左旋回動画から静止画を抽出し表示を確認した。

次の課題は指令切替に連続な12軸参照、旋回中の前進、停止、ばらつきを含む物理検証。追加支持の実ホーン・締結・軸受・剛性も未検証で、最終製作設計ではない。
