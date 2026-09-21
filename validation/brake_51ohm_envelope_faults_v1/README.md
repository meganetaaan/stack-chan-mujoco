# 5.1 Ω案の変動包絡・吸収経路断線

事前plan.jsonの感度条件からRmin=4.42714 Ω、Rmax=5.746544 Ω。初期±5%、耐久試験変化±(5%R+0.1 Ω)、基準25℃から抵抗線−55〜200℃、TCR−80 ppm/Kを組み合わせた仮包絡。実寿命や実装温度の保証ではない。

Rmaxで、電池80 ms切離し後、300 msから1 A・20 msを注入。2本の放電抵抗378 ΩとCout960 µFを維持。枝故障は該当MOSスイッチを1 TΩへ置換し、回生吸収経路の開放を模擬する。比較器・ゲート・基準は従来の行動モデル。

|条件|最大バス V|事前6 V基準|
|---|---:|---|
|故障なし|5.624887|達成|
|主経路開放|5.666588|達成|
|副経路開放|5.624887|達成|
|両経路開放|20.324700|未達|

健全な1枝の抵抗最大負担は5.361639 W・0.0829036 J。Rminに6 Vが直接加わるV²/R上限は8.13166 Wで条件付きP70=8.4 W以内。これは抵抗温度と周囲70℃の放熱条件を解析した結果ではなく、定格条件を満たす場合の比較。開放枝のmos_*測定は1 TΩに生じる漏れ損失で、実MOSの損失ではない。

両経路喪失時は保護成立しない。単一故障時の結果を共通原因故障、短絡、全回生条件へ拡張しない。抵抗の寄生、実比較器の無給電挙動、MOS SOA、容量、停止中実モータ回生、全電源熱は未確認。

再現（faultをnone/primary_open/secondary_open/both_openへ変更して4回）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --brake-ohms 5.746544 --brake-fault primary_open --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/brake_envelope_primary_open
.venv-engineering/bin/python software/sim/circuits/summarize_brake_envelope_faults.py
```

集計スクリプトは保存済み4ケースを読み、report.jsonへ再出力する。ngspice42の内部時間点測定を用いる。生ログ・表示波形は可逆圧縮しmanifest.jsonにハッシュを保存。Issue #24は未完了。
