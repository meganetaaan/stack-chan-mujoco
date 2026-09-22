# 手動復帰回路revHの補助電源監査

結論：電源容量・発熱の適合は未確定。部品の公表試験条件での電流と、実回路の最大消費電流を区別する。本監査だけでTPS70933の採用を確定しない。

## 比較値

|電源ネット|ICの試験条件付き参照値の合計|外付け抵抗を個別に最大電圧で駆動した上界の合計|
|---|---:|---:|
|LOGIC3V3|72.4 µA|1.726144 mA|
|EFUSE_INPUT_5V|16.0 µA|53.030303 µA|

抵抗は既存設計条件の3.393 V／5.25 V、抵抗−1%で比較した。直列経路の二重計上や同時に成立しない状態を含むため、動作時電流の予測値ではない。内部プルアップ、入力電位に依存するIC電流、充放電、未実装の起動監視等を含まない。保証された総電流はreport.jsonでnullとした。

U11の電源は5 V、High入力は3.3 V系である。74LVC1G17の静止電流最大4 µAは入力5.5 VまたはGNDの試験条件なので、そのまま実回路の最大値とできない。追加電流500 µAの規定も入力VCC−0.6 Vであり、実入力条件を保証しない。論理しきい値の照合と電源電流の照合は別である。

## 根拠と限界

- [Nexperia 74LVC1G17](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)：ICC、ΔICCの試験条件。
- [TI SN74LVC1G04](https://www.ti.com/lit/ds/symlink/sn74lvc1g04.pdf)：ICC最大10 µA、入力条件による追加電流。
- [TI SN74HCS11](https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf)、[SN74HCS74](https://www.ti.com/lit/ds/symlink/sn74hcs74.pdf)：6 V、入力が電源/GND、無負荷時のICC最大2 µA。
- [TI TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)：6.5 V、RESET非作動、MR/RESET/CT開放で最大6 µAの参照値。抵抗・内部入力負荷を含む全回路値ではない。
- [TI TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf)、[ADI MAX6816](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6816-MAX6818.pdf)、[Nexperia 74AUP1G06](https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf)：各ICの静止電流参照値。
- [TI TPS709](https://www.ti.com/lit/ds/symlink/tps709.pdf)：150 mA出力定格と電流制限値は別。容量だけでなく入力電圧、ドロップアウト、自己消費、実装熱抵抗を含めて判断する。

## 次に解消する不確実性と終了条件

机上設計では、U11の実入力電圧での電流を保証できる構成を決め、未統合の監視・停止・ボタンを含むネットごとの負荷表を完成する。各状態の電流上限、電源電圧範囲、起動充電、LDO損失・熱条件を部品仕様と照合できた時点で電源選定判断を終える。未知の電流を仮定した波形掃引は追加しない。

実装後の消費電流・温度・電源低下波形の照合は#49。回路選定と机上の容量確認は#21〜#24側に残す。

再現：リポジトリ直下で `python3 software/sim/circuits/audit_manual_rearm_supply.py --out /tmp/manual-rearm-supply-check`（出力先は未作成のディレクトリ）。入力ファイルのSHA-256をreport.jsonへ保存する。
