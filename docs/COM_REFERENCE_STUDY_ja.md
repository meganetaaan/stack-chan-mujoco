# モーター間隙と重心軌道の診断

2026-09-19。外形維持・脚内クリアランス修正候補 `outputs/design_r6_leg_collar_relief` を使用。
固定軌道の改善余地を測る診断であり、実機または10 m歩行の成功を示すものではない。

## CADでのモーター間距離

股ロールモーターと膝モーターの形状は股ロール・股ピッチで相対位置が決まる。
左右各脚について股ロール−0.3〜+0.3 radの7点、股ピッチ0.5〜0.85 radの15点、計210姿勢を調べた。
股ピッチ0.675 radで抽出点全体の最小距離は約1.541 mm、0.700 radで約0.935 mm。
0.750 radには接触する組合せがある。連続角度領域の保証や他部品の隙間の検証ではない。

## 軌道と姿勢補正

`--com-forward-offset-mm` は足の軌道・支持率を保ち、重心の前後参照だけを平行移動する。
その後に逆運動学と静的トルクを再計算する。胴体を物理計算で強制移動するものではない。
`--com-inset-mm` を大きくすると、左右支持足中心へ寄せる重心の振幅が小さくなる。

任意の `--imu-angle-gain` と `--imu-rate-gain` は、理想姿勢角・身体座標の角速度から
足首目標を補正する診断機能。予定支持率を各脚への重みに用いる。
角度制限、速度制限、遅延、LPF、トルク制限は補正後も適用される。
既定値は両方0。今回の補正はすべて失敗し、採用制御器にはしていない。
実機IMUのノイズ・遅延・バイアスや状態推定は実装していない。

## 結果

全条件0.10 m/s参照、静的トルクによる目標角補正あり、slew=6 rad/s、各1試行。
時間・距離は開始前1秒と終了整定を含む。速度参照と実測速度は区別する。

| 周期 / ステップ | 高さ / 前後COM / 横inset (mm) | 実行時間 | 前進量 | 結果 |
|---|---|---:|---:|---|
| 0.30 s / 4 | −5 / −3 / 20 | 0.015 s | −0.035 mm | 膝／足首モーター接触 |
| 0.25 s / 4 | −2 / −3 / 20 | 2.500 s | 45.221 mm | 短時間のモデル接触停止なし |
| 0.25 s / 20 | −2 / −3 / 20 | 6.341 s | −229.579 mm | 接触停止、後退 |
| 0.25 s / 20 | −2 / −3 / 23 | 2.916 s | 93.146 mm | 接触停止 |
| 0.25 s / 20 | −2 / −3 / 25 | 6.500 s | 522.198 mm | モデル接触停止なし、後述のCAD干渉あり |
| 0.25 s / 400 | −2 / −3 / 25 | 12.102 s | 1040.935 mm | 膝／足首モーター接触停止 |

横inset=25 mmの20ステップでは、歩行区間1〜6秒に516.584 mm進み平均約0.1033 m/s。
開始・終了を含む平均は約0.0803 m/s。有効な前進着地は左右10/9回、最大傾斜約8.13°。
足首ピッチのトルク飽和は左右約3.97/4.22%の物理ステップに発生した。
400ステップへの延長では途中で傾斜が増え、約1.04 mで停止。10 m目標を満たしていない。

姿勢角ゲイン0.2/0.5/0.8、角速度ゲイン0.04秒で各60ステップを計画すると、
それぞれ2.831/2.618/2.582秒で接触停止した。単純な足首補正はこの設定では改善にならなかった。
16条件の結果とコマンドは `validation/com_reference/commands_and_results.json`。

## シミュレーションが見落とした干渉

0.52 mのログを5行おきと末尾の66姿勢で全CAD部品検査したところ、終了動作の2姿勢で
左腿／足首ジンバル、左脛／足首ジンバルが干渉した。最大約0.698 mm³。
したがってこの試験を無自己衝突の歩行成功とは扱わない。

モデルを点検すると左右ジンバル・固定クレードルに衝突形状がなく、さらに親子リンクの
接触フィルタが有効だった。電池・電源回路等の4予約部品にも衝突形状がない。
脛・足外装等には簡略形状があるが、存在だけでCAD形状を十分覆うことにはならない。
棚上げせず、次は可動部の衝突形状と親子リンクの接触扱いを修正してから制御評価を続ける。

## 再現

`design/leg_relief/README_ja.md` に従って候補を生成する。

```bash
.venv-cad/bin/python screen_motor_clearance.py \
  --design outputs/design_r6_leg_collar_relief --out outputs/motor_clearance_grid.json
.venv-dynamics/bin/python probe_reference_gait.py \
  --design outputs/design_r6_leg_collar_relief --speed .1 --step-period .25 \
  --height-offset-mm -2 --com-forward-offset-mm -3 --com-inset-mm 25 \
  --static-compensation --slew 6 --steps 20 --out outputs/com_long_inset25
.venv-cad/bin/python check_design_clearance.py \
  --design outputs/design_r6_leg_collar_relief \
  --trajectory-csv validation/com_reference/com_long_inset25/trajectory.csv \
  --stride 5 --out outputs/com_inset25_cad.json
python validation/audit_collision_coverage.py \
  --design outputs/design_r6_leg_collar_relief --out outputs/collision_coverage.json
.venv-dynamics/bin/python -m unittest tests.test_reference_gait
```

CAD検査は既知の干渉により終了コード1となる。診断の終了コード0は記録完了を表す。
比較した前後COM条件・延長試験はコミット `ea67baa`、IMU補正試験は `ff964e9` のコードで実行。
各reportに実行時ソースのSHA-256を収録。現在のコードでもIMUゲイン0が既定値である。
参照軌道は容量を抑えるため `reference.json.gz` に可逆圧縮し、生CSVとreportはそのまま保存した。

## 衝突モデルの追加検証

[ジンバルと軸受外周の衝突形状追加](GIMBAL_COLLISION_ja.md)により、
既知の腿・脛／ジンバル干渉をMuJoCoでも検出できるようになった。
同じ20ステップ試験は6.22秒で接触停止する。全体の衝突形状検証は引き続き未完了。
