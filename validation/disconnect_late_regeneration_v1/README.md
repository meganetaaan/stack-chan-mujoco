# 補助電源低下後の回生注入

電池切離し80 msに対し、1 A・20 msの注入を100 msから300 msへ遅らせた。その他は前回と同じ378 Ω×2、960 µF、行動モデル。開始時刻はCLIで指定可能にし、既定100 msの動作は維持。

内部時間点での切離し後最大バスは5.588374 Vで、事前の6.0 V以下を満たす。200 ms時点で補助電源は既に0.132929 Vまで低下。今回の結果はモデル化した回生吸収経路がこの条件で動くことを示すが、実比較器や基準電圧の未給電動作を保証しない。実負荷連成、熱、素子故障、任意の回生波形の検証ではなく、Issue #24は未完了。

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/disconnect_late_regeneration
```

ngspice42。判定は内部点meas MAX、表示波形の補間ピークを使わない。生ログと表示波形は可逆gzip。manifest.jsonに圧縮前後ハッシュを保存。
