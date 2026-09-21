# 回生スイッチ固着オンの試験

公称5.1 Ωの感度下限4.42714 Ωで、起動時から主枝または両枝のMOSを0.1 Ωに置換。完全短絡とは区別する。サーボ負荷ゼロ、電池80 ms切離し、300 msから1 A・20 ms回生注入の条件。通電中50〜79 msと切離し後を内部時間点で測定。

|固着|通電バス V|1枝の電流 A|1枝の抵抗電力 W|
|---|---:|---:|---:|
|主枝のみ|5.084241|1.123058|5.583773|
|両枝|5.028070|1.110650|5.461073|

通電時4.75〜5.25 Vと切離し後最大6 Vの電圧基準は達成。しかし両枝で約10.92 Wを消費してもバスは正常範囲に残る。電圧合格を故障検出・保護合格と同一視できない。枝電流の監視、要求していない通電の検出、上流遮断、再投入ラッチを具体化する必要がある。

通電の測定窓は29 msで、長時間の発熱成立を示さない。変換器の電流制限、全12軸駆動との同時負荷、MOS完全短絡、抵抗短絡、遮断遅延/エネルギー、復帰条件は未検証。固着枝のmos_*は仮の0.1 Ωでの損失であり実故障素子の保証値ではない。

再現（faultをprimary_stuck_on/both_stuck_onに変更）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --brake-ohms 4.42714 --brake-fault primary_stuck_on --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/brake_stuck_on
```

各report.jsonのpowered_measurementsとbus_after_disconnect_max_Vを事前plan.jsonへ照合した集計がルートreport.json。ngspice42。生ログ/表示波形は可逆gzip、ハッシュはmanifest.json。Issue #24は未完了。
