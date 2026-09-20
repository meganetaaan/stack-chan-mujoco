# 独立した二つの回生吸収経路の候補

Issue #24の開放故障対策として、回生吸収用の抵抗・MOSFET・コンパレータ・基準源・ゲート保護を二組設ける回路を評価する。
主経路の分圧上側抵抗は11.8 kΩ、補助経路は12.1 kΩ。補助経路が少し高いバス電圧で作動する構成とした。
両方とも既存解析の「遅い作動側」の定数を用いる。値と判定基準は各実行前に `plan.json` へ保存する。

「独立」は回路モデル上で検出・吸収部品を共有しないという意味。共通バス、配線、接地、実装熱、同一型番の共通原因故障の独立性は検証していない。
別コンパレータICと別基準源の使用を前提とし、同一ICの二回路を使うだけで独立保護と見なさない。

## 事前の評価条件

- 故障なし、主経路開放、補助経路開放、両経路開放に同じ1 A・20 msの規定回生電流を注入する。
- 通常負荷にはEPIC #4の既存12軸合計電流を使用する。
- 通常バス4.75〜5.25 V、故障注入バス4.75〜5.8 V。
- 各経路でゲート絶対値10 V以下、抵抗ピーク10 W以下・1回0.15 J以下、ツェナーピーク0.1 W以下、プルアップピーク0.25 W以下。
- エネルギー収支誤差1%未満。通常時の二経路合計吸収エネルギー0.001 J以下。

ngspiceの開放注入は対象MOSFETスイッチを動作不能にするもの。抵抗断線やスイッチ開放と同じく吸収電流がなくなる状況を調べる。
短絡、常時導通、基準源異常、コンパレータ出力固着、共通原因故障はこの試験に含まれない。

## 再現

```sh
.venv-engineering/bin/python software/sim/circuits/run_dual_brake.py --out outputs/dual_no_fault_new
.venv-engineering/bin/python software/sim/circuits/run_dual_brake.py --out outputs/dual_primary_open_new --fault primary_open
.venv-engineering/bin/python software/sim/circuits/run_dual_brake.py --out outputs/dual_secondary_open_new --fault secondary_open
.venv-engineering/bin/python software/sim/circuits/run_dual_brake.py --out outputs/dual_both_open_new --fault both_open
.venv-engineering/bin/python software/sim/circuits/run_dual_brake.py --out outputs/dual_normal_new --normal-load
```

[回生モデル](BRAKE_DEVELOPMENT_ja.md)と[ゲート保護モデル](GATE_CLAMP_DEVELOPMENT_ja.md)の近似・部品未確定の制約を引き継ぐ。
全公差・全温度の最悪条件、繰返し回生の温度、実際の回生エネルギー、電池の低電圧・短絡保護、故障検出後の停止・復帰は別途必要。
既存モデルの定数を流用した段階であり、全保護設計の成立を意味しない。

## 結果

|条件|最大バス V|吸収した経路|開発基準|
|---|---:|---|---|
|回生・故障なし|5.5926|主|合格|
|回生・主経路開放|5.6719|補助|合格|
|回生・補助経路開放|5.5926|主|合格|
|回生・両経路開放|30.5261|なし|電圧不合格|
|通常12軸負荷|5.1436|モデル上なし|合格|

主経路開放時の補助抵抗は最大6.2133 W、1回0.11223 J。全条件のエネルギー収支誤差は8×10⁻⁶未満。
両経路開放時はMOSFET候補の30 Vドレイン定格も超える。この領域は破壊を再現しておらず、実回路の電圧予測ではない。

**起動時のゲート電圧は約1.81 Vに上がる。** 現在の2.5 Vで切り替わるスイッチモデルではオフだが、実MOSFETはしきい値を超えて部分導通し得る。
したがって「通常負荷で吸収なし」は現モデルの結果に限る。起動保持回路または実MOSFETモデルでの起動・線形領域検証が必要。

最初のv1実行は回路計算後、NumPy真偽値のJSON保存で失敗した。Pythonのboolへ変換してv2を再実行した。回路・判定基準は変更していない。
`validation/dual_brake_development_v1/` にv2の5条件の計画、回路、波形、判定、実行コードを保存した。
