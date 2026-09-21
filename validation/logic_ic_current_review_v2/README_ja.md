# 残るロジックICの電流仕様と集計

2026-09-22確認。前回取得できなかったSN74AUP1T50はTIのgpn URLから取得できた。

| 部品／番号 | 最大静止電流 | 指定点での追加電流最大 |
|---|---|---|
| SN74LVC1G04／U2 | 10 µA、VCC1.65..5.5 V、入力5.5 VまたはGND、無負荷 | VCC3..5.5 V、入力VCC−0.6 Vで500 µA |
| 74AUP1G06／U14 | 0.9 µA、VCC0.8..3.6 V、入力GNDまたはVCC、無負荷、−40..85℃ | VCC3.3 V、入力VCC−0.6 Vで50 µA |
| SN74AUP1T50／U_MONITOR_RX | 0.9 µA、VCC2.3..3.6 V、入力3.6 VまたはGND、無負荷、−40..85℃ | VCC3..3.6 V、入力0.45 Vまたは1.2 Vで12 µA |

出典: [SN74LVC1G04 RevAF §5.5](https://www.ti.com/lit/ds/symlink/sn74lvc1g04.pdf)、[74AUP1G06 Rev12 Table7](https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf)、[SN74AUP1T50 RevA p5](https://www.ti.com/lit/gpn/sn74aup1t50)。追加電流は列挙した入力条件の値であり、全中間電圧での最大保証ではない。74AUP1G06の125℃行は別値であり85℃条件と混ぜない。

前回6種類と合わせ、9種類の公開仕様確認を完了。catalog.jsonは各電源ピンを実アセンブリに照合し、参考計上値（TPS3808は6 µA、TPS3700は13 µAなど）を集計した。LOGIC3V3は93.8 µA、STOP_AUX3V3は48 µA。これらは試験電圧・入力条件の違いを含む**設計見積り**であり、全状態で保証された上限ではない。

前の抵抗小計へ足すと参考値はLOGIC3V3約6.978 mA、STOP_AUX3V3約0.916 mA。MCU本体、MAX6816内部プルアップ、追加・動的電流、供給源自身は未算入。したがって7 mA電源を選んでよいという意味ではない。特にLVCの指定点追加電流500 µA/個は静止電流より大きいため、入力状態を確認せず電源余裕を判断しない。

部品を交換せず次へ進める条件は、起動・通常・押下・クランプ保持の各入力状態を決め、供給源の設計電流枠に動的・MCU分を確保すること。機械的性質や未知の実機値をこの静止電流表で代替しない。

再集計: `.venv-engineering/bin/python software/sim/circuits/catalog_logic_current.py --out /tmp/logic-current-catalog.json`。21個の実部品を電源ピンで分類する。初回の補助集計は個数を誤って19個に固定したassertで停止したため、固定個数を除いて実アセンブリから列挙し直した。電流値・接続の変更はない。
