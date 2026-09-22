# 枝電流検出シャントの挿入影響

各回生MOSのソースとGNDの間に0.101 Ωを挿入。公称0.1 Ωの+1%条件。理想スイッチの制御端子をgate−sourceへ変更し、ソース電位上昇を反映した。従来のシャントなし既定動作を維持。

回生抵抗5.746544 Ω、放電378 Ω×2、Cout960 µF、電池80 ms切離し、300 msから1 A・20 ms注入。事前基準は切離し後バス最大6 V以下。

|条件|最大バス V|最大シャント電力 W|最大の1枝シャントエネルギー J|
|---|---:|---:|---:|
|正常|5.643804|0.0909473|0.00140056|
|主吸収経路開放|5.730872|0.0937751|0.00144724|

両方で電圧基準内。シャント電力/エネルギーは0〜1 s、回生抵抗とMOSの負担は80 ms〜1 sで積分している。シャント挿入前と電流分担が変わるため、以前の素子負担をそのまま転用しない。

INA180は未接続で、入力負荷・電源・信号遅延・ラッチ・遮断は含まない。MOSは理想抵抗性スイッチで、ゲート容量は従来の対GND近似のまま。実ゲート駆動・MOS SOA・比較器無給電特性・寄生・シャント温度公差を保証しない。全負荷や全故障、熱も未完了。

再現（faultはnoneまたはprimary_open）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --shunt-ohms .101 --brake-ohms 5.746544 --brake-fault primary_open --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/brake_shunt_insertion
```

ngspice42、内部点measで評価。各report.jsonの結果を事前plan.jsonの電圧基準と比較したものがルートreport.json。ログと表示波形を可逆gzipで保存、manifest.jsonにハッシュ。Issue #24未完了。
