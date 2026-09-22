# 監視・ロジックICの静止電流仕様

2026-09-22の一次資料確認。前段の抵抗小計6.883758 mAに加えるIC負荷について、保証条件の違いを識別した。以下の表は全状態の保証電流収支ではない。

| 種類／回路番号 | 最大値と条件 | 適用上の制限 |
|---|---|---|
| TPS3808／U5,U7,U9,U10,U_MONITOR_START | 3.3 Vで5 µA、6.5 Vで6 µA。RESET非アサート、MR/RESET/CT開放 | 現回路のCT接続、RESETアサート、有効電源幅の全状態へそのまま展開しない |
| TPS3700／LEFT/RIGHT_U12、LEFT/RIGHT_U_WINDOW | 1.8 V無負荷で11 µA、5/12/18 Vで13 µA | 3.207..3.393 Vと出力負荷状態の扱いを分ける。13 µAを全状態の証明としない |
| SN74HCS11／U3 | 6 V、入力0またはVCC、無負荷で2 µA | 中間入力・スイッチングを除外 |
| SN74HCS74／U6 | 同上2 µA | 同上 |
| 74LVC1G17／U4,U8,U11,U15,LEFT/RIGHT_U13 | VCC1.65..5.5 V、入力5.5 VまたはGND、無負荷で4 µA | 追加電流は入力VCC−0.6 Vで最大500 µA/入力。これは全中間電圧での最大保証ではない |
| MAX6816／U1 | 5 V、入力VCC、無負荷で20 µA | ボタン押下時の内部プルアップと3.3 V条件を別に扱う |

[TI TPS3808 RevN §6.5](https://www.ti.com/lit/ds/symlink/tps3808.pdf) はCTの40..200 kΩ抵抗選択が供給電流へ影響しないと説明している。前の直結抵抗小計はCT端子を0 Vと置くため、この箇所は保守的な枠であり実消費予測ではない。

出典: [TPS3700 RevG §6.5](https://www.ti.com/lit/ds/symlink/tps3700.pdf)、[SN74HCS11 RevB §5.5](https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf)、[SN74HCS74 RevD §6.5](https://www.ti.com/lit/ds/symlink/sn74hcs74.pdf)、[74LVC1G17 Rev16.1 Table7](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)、[MAX6816 Rev8 電気特性](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6816-MAX6818.pdf)。

**電源選定への判断:** 各最大値の単純合算を保証されたIC上限として追加しない。一方、仕様の条件差だけを理由に部品を直ちに交換しない。通常の静止状態、ボタン押下・クランプ保持、切替過渡を分け、電源の設計余裕に対する寄与を確認する。特にLVCの中間入力追加電流はµA級静止電流より大きく、入力レベルの成立と滞在時間が重要。

残る一次資料照合はU2 SN74LVC1G04、U14 74AUP1G06、U_MONITOR_RX SN74AUP1T50、候補MCU、供給源自身の電流。SN74AUP1T50の今回の取得はエラーだったため、未取得をゼロと扱わない。これらと過渡負荷の確認後に供給源容量と熱を判定する。#21〜#24は未完了。
