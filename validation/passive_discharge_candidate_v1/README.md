# 常設放電抵抗2本の候補と断線評価

Issue #24の残留電荷対策として、出力railからGNDへ390 Ωを2本独立に追加する案を評価。部品未選定の要求値案であり、BOM・基板への採用は未確定。事前計画plan.jsonで「切離し920 ms後に0.5 V以下」を仮の電気的設計目標とした。0.5 Vはサーボの脱力保証や安全電圧を意味せず、停止仕様の承認済み基準ではない。

抵抗+5%で409.5 Ω、出力容量+20%で960 µFを仮定し、電池7.4 Vを80 msで理想的に切離し、時刻1 sで評価。サーボ無負荷・回生なし。出力容量には実サーボ等の容量をまだ追加しておらず、960 µFを実機全体の上限として扱わない。

|状態|結合回路の残留rail V|抵抗と容量だけの残留 V|仮目標の判定（結合/RC）|
|---|---:|---:|---|
|2本正常|0.001361|0.048690|達成/達成|
|1本断線|0.022891|0.505593|達成/未達|
|2本断線|0.740727|5.250000|未達/未達|

RC計算は初期5.25 V、V=V0 exp(-t/RC)。結合回路には他の消費経路があり、初期電圧も約5.143 Vなので、両者は同一モデルではない。RC単独の1本断線条件は目標未達。結合回路の合格だけで設計を確定すると、行動モデルで表した他の消費電流に依存する。電源や回生が残ればRC式を上限評価に使えない。

この仮条件で1本のみの放電を成立させる抵抗上限は407.563 Ω。現在の公差上限409.5 Ωはこれを超えるため、抵抗値を下げる案を次に評価する。仮目標を緩めて既存結果を合格にしない。5.25 V・抵抗−5%で1本の通常損失は74.39 mW、2本合計148.79 mW。これは定格の選定結果ではなく必要負担の計算値。最大初期Coutエネルギー13.23 mJも全系のエネルギーではない。実抵抗の温度ディレーティング、パルス耐量、短絡故障時の上流保護、回生中遮断、再投入、実全容量は未評価。

再現（リポジトリルート、出力先は新規ディレクトリ）:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 409.5 --cout-uf 960 --open-bleeds 0 --out outputs/passive_discharge/both_working
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 409.5 --cout-uf 960 --open-bleeds 1 --out outputs/passive_discharge/one_open
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 409.5 --cout-uf 960 --open-bleeds 2 --out outputs/passive_discharge/both_open
cp validation/passive_discharge_candidate_v1/plan.json outputs/passive_discharge/plan.json
.venv-engineering/bin/python software/sim/circuits/summarize_passive_discharge.py --source outputs/passive_discharge
```

ngspice42。保存した生ログと表示波形は可逆gzip圧縮。manifest.jsonに圧縮前後のハッシュを記録。元の放電抵抗なし800 µF結果はdisconnect_residual_v1に保持。Issue #24は未完了。
