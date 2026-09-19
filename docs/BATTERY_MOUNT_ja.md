# 胴体内バッテリートレーのCAD試案

製作リリースではない。胴体128 mm角、大腿50 mm、下腿44 mm、足94×52 mmを維持するため、既存の内部レールに取り付けるトレーを作成した。電池中心は胴体座標(-1, 0, 80) mm。現在の合格歩行モデルの(0, 0, 78) mmから移動するため、その歩行成績を転用しない。

トレーは1個の有効なソリッド。既存レールとトレーの2か所に直径3.4 mmのM3用穴を設けた。静止姿勢でトレーと全機械部品をCAD体積・距離で検査し、体積干渉はなかった。電池底面と取付レールは意図した接触。固定クレードルとの隙間0.80 mm、5 V変換器との隙間0.85 mmは公称形状の値で、公差や動作中の保証ではない。

トレー体積6090.130 mm³、レール穴の除去体積43.580 mm³。材料密度1240 kg/m³の仮定で印刷部の正味増加7.498 g。ベルト1.2 gと締結具2 gを別加算し、総増加10.698 g。旧配線・締結具の予約質量を減らして相殺していない。ベルト・ねじ・ナットはまだCAD化しておらず、この質量は仮定。

再生成（CAD依存環境と既存R6設計の生成は `design/README_ja.md`、追加接触形状は `docs/BASE_COLLISIONS_ja.md`）：

```sh
.venv-cad/bin/python build_battery_mount.py --design outputs/design_r6_base_collisions --out outputs/battery_mount_review_v1
```

出力先は新規ディレクトリを指定する。`validation/battery_mount_review_v1` にトレーSTEP/STL、変更する胴体と電池のSTEP、検査結果・入力ハッシュを保存した。組立STEPは同コマンドで生成できる。

残作業は、動作中の脚との干渉、ベルト経路・締結具の形状と作業空間、電池端子・交換経路、保持強度、公差、衝突モデルと質量・慣性の再生成、最終構成の歩行評価。電気的適合は `docs/POWER_ja.md` の未確定項目を引き継ぐ。

## ベルト・締結具の形状追加と歩行姿勢検査

`validation/battery_mount_review_v2` に保持ベルトとM3締結具2組の形状を追加。全て有効な一体ソリッドで、静止姿勢の既存部品・トレーとの体積干渉はなかった。ねじ・ナットは融合した外形モデルで、ねじ山、締付け力、ベルトの留め部・変形は未モデル化。質量は前記仮定を維持する。現在の生成コマンドはv2を出力する。v1の厳密な再生成にはコミット `0d8e607` の生成スクリプトを使用する。

固定条件の実記録 `validation/r6_steering_seed20260923/fixed/trial_00` から250フレーム間隔、終端、各関節の最大・最小角を選んだ39姿勢で、トレーと移動後の電池を既存機械部品と検査した。体積干渉なし。記録は固定具追加前の歩行であり、固定具込みの動力学成功を示さない。ベルト・締結具はこの39姿勢検査の対象外。全連続姿勢の保証でもない。

```sh
.venv-cad/bin/python check_battery_mount_trajectory.py --design outputs/design_r6_base_collisions --mount validation/battery_mount_review_v1 --trial validation/r6_steering_seed20260923/fixed/trial_00 --out outputs/battery_mount_fixed00_sampled.json
```

## 固定具を反映したMuJoCo候補

`assets/r6_mounted_battery` に固定具込みの別モデルを保存。総質量865.9819 g（従来855.2842 g）、差分10.6977 g。胴体リンク重心は(5.32142, 0.00884, 69.19325) mm。胴体の全慣性テンソルをCAD部品から平行軸の定理で再計算した。これは機体全体重心とは異なる。機体全体重心は姿勢に依存し、各試行の記録で確認する。

トレーは構成箱、ベルトは中空部分を残した6個の凸プリズム、M3締結具は各1個の外接箱で接触を表現。CAD被覆の欠損体積は各0 mm³。トレーのねじ穴と締結具の軸周囲は保守的に埋まる。元の胴体レールの接触簡略化は残る。URDFを今回の候補へ転用せず、MJCFのみを出力する。

```sh
.venv-cad/bin/python integrate_battery_mount.py --design outputs/design_r6_base_collisions --mount validation/battery_mount_review_v2 --out outputs/r6_mounted_battery
/home/sskw/stackchan-mujoco/.venv/bin/python -m unittest discover -s tests -p 'test_mounted_battery.py'
```

新規出力先を指定する。2テストにより、胴体以外の質量特性・関節・アクチュエータ設定の不変性、固定具質量の増分、コンパイル済み接触形状・電池位置・重力を確認した。歩行合格の証拠ではない。新しいモデルでは `train_mounted_residual.py` により既存の学習済み重みを初期値としてPPOを実行し、`configs/r6/mounted_evaluation_seeds.json` の別シードで評価する。
