# 足部取付面へのEPIC4荷重変換

38系列・266000サンプルを保持。足首ロールの子ボディ座標軸のまま、原点を取付面中心へ移した。取付穴x=-34,+36 mm、左y=-14.5,+26.5 mm、右y=-26.5,+14.5 mmの中心は(1,±6,-16) mm。CAD部品はankle_rollボディに対応する（software/sim/mujoco/build_fast_turn_feet.py）。

親から子への力の符号を保持し、M_center=M_joint−center×Fを使用。N·mからN·mmへ変換。逆変換残差は1e-9 N·mm以内。各成分の最大・最小を記録する際も、他成分は同時刻の値を保持する。

全系列の力ノルム最大10.44293 N、取付面中心モーメントノルム最大226.37208 N·mm。両者は同時発生とは限らず、合成荷重にはしない。npzは全時系列、report.jsonは出典ハッシュ・治具条件・時刻・極値を記録。

これは合力の座標変換であり、ねじ別荷重の計算ではない。ヨークとブーツの慣性、床からの接触力、足裏からの荷重経路を含む自由物体図・構造モデルが必要。最新CADの質量変更も反映していない。Issue #17/#18の完了証跡にはまだ不足。

再現（リポジトリルート、新規出力先）:

```sh
.venv-engineering/bin/python software/sim/structural/map_ankle_mount_loads.py --out outputs/ankle_mount_loads_repro
```
