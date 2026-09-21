# 固着オン検出からEN停止への結合

低側シャント0.099 Ω、回生抵抗4.42714 Ωのモデルに、利得19.8/入力オフセット−692 µV/10 µsフィルタ/0.612 V比較/1 ms継続判定と保持を結合。各センサーの補助電源負担0.3 mAを近似追加。ゲート条件はgate−source。ラッチが0.5を超えると理想10 ΩスイッチでENを下げる。

|ケース|20 msラッチ|20 ms EN V|20 ms変換器drive V|
|---|---:|---:|---:|
|正常|0|1.601021|5.15|
|主枝固着オン|0.999987|0.016421|0|
|両枝固着オン|0.999987|0.016421|0|

正常ケースは全1秒でラッチ最大0。固着2ケースは事前20 ms時点の検出/EN停止/drive停止条件を満たす。外部の電池切離しは80 msのため、この20 ms停止は外部切離しによるものではない。ただしバス残留エネルギーや実サーボのトルクが消えた証拠ではない。

比較器、保持回路、ENシンクは行動/理想モデルで実部品未選定。補助電源消失後もラッチ状態を保持する理想要素を使い、実際の保持・再投入・復帰は未検証。センサー動特性、公差全部、ゲート実MOS特性、電池/電力経路の物理遮断、全負荷を検証していない。Issue #24未完了。

再現（faultをnone/primary_stuck_on/both_stuck_onに変更）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --fault-detector --shunt-ohms .099 --brake-ohms 4.42714 --brake-fault primary_stuck_on --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/brake_fault_en
```

ngspice42。内部点測定。各report.jsonのfault_detector_measurementsを事前plan.jsonと照合したものがルートreport.json。ログ/表示波形は可逆gzip、ハッシュはmanifest.json。
