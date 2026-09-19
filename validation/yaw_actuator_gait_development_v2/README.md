# 12軸候補のアクチュエータ・歩行周期比較

正式受入試験ではない。固定20/20・ランダム化18/20、旋回、全205秒の切替試験の合格を示さない。予約シードは使用していない。ヨーの目標角は両脚ともゼロで、有限トルクで追従させる。

公開モデル `assets/r7_yaw_xc_ankles_v1` は、両足首ピッチをXC330仕様へ変更した候補。重量・慣性・速度・トルク上限を同時に変更し、総質量は0.934558435 kg。外形、脚長、足形状、関節位置、衝突形状は元の12軸候補と同一。0.45 Nmのシミュレーション上限はメーカーの連続定格ではない。ヨーのPDゲインは6 Nm/rad、0.13 Nm s/radを仮定し、実機同定は未実施。

## 開発結果

| 条件 | 完了/停止時刻 s | X変位 m | 有効着地 左/右 | 結果 |
|---|---:|---:|---|---|
| 周期0.32 s、速度指令0.10 m/s、高さ補正2 mm | 6.600 | 0.5576 | 8/8 | 異常なし |
| 周期0.24 s、同速度・高さ | 4.303 | 0.0238 | 3/0 | 歩行中断 |
| 周期0.27 s、高さ補正3 mm | 3.291 | 0.1209 | 2/1 | 歩行中断 |
| 周期0.27 s、速度0.06 m/s、高さ補正2 mm | 3.599 | 0.0912 | 2/3 | 歩行中断 |
| 後退：周期0.32 s、速度指令−0.05 m/s、高さ補正2 mm | 8.680 | −0.3487 | 11/11 | 異常なし |
| 周期0.32 sの延長確認 | 31.720 | 3.1918 | 47/47 | 異常なし |

高さ補正は姿勢の変更で、部品寸法の延長ではない。延長確認は前進1試行であり、姿勢・横ずれ・速度誤差を含む正式な区間評価はまだ適用していない。学習済み方策・姿勢フィードバックは上表では使用していない。接触判定や保護閾値を緩和していない。

膝ケースを既存軸周りに90度、180度回す配置も試したが、初期姿勢でそれぞれ約5.95 mm、約5.27 mmの自己干渉が生じて不採用。両失敗の接触と状態を保存した。これらの配置は公開モデルには反映していない。元モデル同様、追加支持の実ホーン・軸受・締結への適合は未検証。

## 再現

CAD元データは `docs/REPRODUCE_MOUNTED_ja.md` に沿って生成する。MuJoCo実行環境とCadQuery環境を分け、出力は未使用のパスとする。

```sh
.venv-cad/bin/python upgrade_candidate_ankles.py --cad-design outputs/design_r6_base_collisions --out outputs/new_xc_candidate
python generate_yaw_zero_reference.py --cad-design outputs/design_r6_base_collisions --design assets/r7_yaw_xc_ankles_v1 --out outputs/new_period32_ref --period .32 --height-offset-mm 2 --steps 96
python probe_yaw_dynamics_candidate.py --design assets/r7_yaw_xc_ankles_v1 --reference outputs/new_period32_ref/reference.json.gz --static-torque-scale 1 --duration 31.72 --yaw-kp 6 --yaw-kd .13 --out outputs/new_period32_trial
python -m unittest tests.test_candidate_ankle_upgrade tests.test_legacy_policy_view tests.test_yaw_dynamics_candidate tests.test_yaw_kinematics -v
```

ケース回転の再現は生成へ `--knee-case-angle-deg 90` または `180` を追加し、その生成モデルから参照と試験を作る。短期比較は24歩で、全条件を6.6秒で比較。各条件の参照生成reportに速度・周期・高さを記録している。

`states.npz` は実MuJoCo積分状態で、`report.json` は停止理由・接触・モータ仕様・ソースハッシュを含む。生成時のoutputsパスは履歴として保持し、コピー先と同じ相対フォルダ名で収録した。短期比較の物理モデル3ファイル（scene、inertials、robot）は公開モデルとのバイト一致を確認した。ケース回転失敗についてはモデルは生成スクリプトから再生成する。動画および正式受入評価は別途必要。

後退診断は参照生成へ `--speed -.05 --steps 24` を指定し、probeのdurationを8.68秒とする。後退から他動作への切替、長期後退、ランダム化での再検証は未実施。
