# シーケンサーのクリア出力段

目的は実部品でRESET_NをLowへ引く接続を決め、通常時の漏れ・吸込負荷を確認すること。終了条件は接続と静的負荷比較を確定し、時間保証・状態保持の未実装を分けること。未確定の波形を作った過渡解析はしない。

採用候補はNexperia 74AUP1G06GW。入力Highで出力Low、入力Lowで出力開放。100 kΩで入力をLOGIC3V3へ引き上げ、駆動元開放時はクリア側へ寄せる。U14出力をRESET_Nへ接続したrevHは43部品150端子。revGの40部品接続は不変。

125°Cまでの出力OFF漏れ上限0.75 µAを加えたRESET_NのHigh比較下限は2.69695 V。Low時吸込負荷上限38.573 µAは3.0 V給電時2.7 mA／VOL最大0.36 Vの規定点以内。入力開放時のHigh比較下限3.13125 V、解除する駆動元に必要なLow吸込上限35.023 µA。入力は3.0〜3.6 V給電でHigh≥2.0 V／Low≤0.9 V、変化速度≤200 ns/Vを満たす必要がある。Schmitt作用という記述を無制限の入力速度と読み替えない。

比較候補のAO3400Aは55°CでOFF漏れ最大5 µA、74LVC1G06は最大2 µAであり、今回はより小さいAUPを選ぶ。ブレーキMOSFETを変更する判断ではない。

出典：[Nexperia AUP Rev12](https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf) 表6/7、[LVC Rev16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G06.pdf)、[AOS AO3400A Rev3.1](https://www.aosmd.com/sites/default/files/res/datasheets/AO3400A.pdf)。HCS入力・U7漏れの既存比較条件は引き継いでおり、RESET_N受信しきい値の全電源域保証は未完了。

無給電時のU14出力は開放であり、クリア強制ではない。独立電源監視を省略しない。部分給電、入力開放時の遷移時間、CLR保持・解除から次クロックまでの余裕は未確認。実際のシーケンサー出力は未実装で、U14入力をLowへ固定して通電する指示ではない。

再現：`python3 software/sim/circuits/check_sequence_clear_sink.py --out /tmp/sequence-clear-sink-review`（新規出力先）。部品値・接続・入力仕様は`schematics/power/sequence_clear_sink_candidate.json`。#24未完了。
