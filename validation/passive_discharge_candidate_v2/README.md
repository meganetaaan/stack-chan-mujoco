# 放電抵抗360 Ω案

前版390 Ω案のRC単独・1本断線時未達を受け、360 Ωを2本とした。判定条件は前版から変更しない。事前plan.json、回路、全ケースのログと結果を保存。

仮条件: 抵抗の総変動±5%、出力容量上限960 µF、初期電圧上限5.25 V、切離し920 ms後0.5 V以下。回路モデルは電池7.4 V、サーボ無負荷、回生なし。他の消費経路を除いたRC計算も併記する。

|状態|結合回路の残留rail V|RC単独の残留 V|仮目標（結合/RC）|
|---|---:|---:|---|
|2本正常|0.000860|0.032965|達成/達成|
|1本断線|0.018056|0.416010|達成/達成|
|2本断線|0.740727|5.250000|未達/未達|

通常5.25 V・抵抗−5%時は1本80.59 mW、合計161.18 mW。1本断線しても健全側の通常電力は増えないが、出力容量に蓄えた電荷の放電が遅くなる。短絡故障は別で、今回の断線解析で保護されたとは言えない。

Vishay D/CRCW1206 e3を部品候補とした。メーカー資料20035（14-Apr-2026）p1〜3から、P70=0.25 W、許容膜温度155℃、1%・100 ppm/K品の型番規則を確認。CRCW1206360RFKEAはその規則から構成した候補番号で、調達可否未確認。定格は基板放熱と膜温度の条件に依存するため、80.59 mWが0.25 Wより低いことだけで温度合格とはしない。

一次資料: https://www.vishay.com/docs/20035/dcrcwe3.pdf
候補カード: schematics/power/passive_discharge_candidate.json

±5%は初期公差だけでなく温度・経時変化を含めて満たすべき仮の総包絡で、部品選定によって保証済みではない。960 µFも12軸内部容量等を含む実総容量の保証ではない。回生・外部給電があればRC放電式は適用できず、今回の0.5 Vは安全・脱力を保証する閾値ではない。停止/復帰仕様、短絡保護、実総容量、温度、公差を確定するまでIssue #24は完了扱いにしない。

再現（リポジトリルート、新規出力先）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --open-bleeds 0 --out outputs/passive_discharge_v2/both_working
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --open-bleeds 1 --out outputs/passive_discharge_v2/one_open
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --open-bleeds 2 --out outputs/passive_discharge_v2/both_open
cp validation/passive_discharge_candidate_v2/plan.json outputs/passive_discharge_v2/plan.json
.venv-engineering/bin/python software/sim/circuits/summarize_passive_discharge.py --source outputs/passive_discharge_v2
```

ngspice42。生ログ・表示波形は可逆gzip、manifest.jsonに圧縮前後のSHA-256を保存。前版の未達記録は変更しない。
