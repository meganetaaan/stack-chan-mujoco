# 補助起動を接続した191部品候補

[前版](../protected_pack_system_candidate_v1/README_ja.md)の電力経路/部品を維持し、CTRLのLOGIC_START_ALLOWをSYS__LOGIC_START_ALLOWへ接続した。部品追加なし、191参照。既存1 kΩ直列・10 kΩプルダウンを用い、RTNとGNDを短絡しない。

[SHDN静的比較](../../../validation/aux_start_connection_v1/README_ja.md)を根拠にした接続候補で、電源遷移・逆接・漏れの全保証や過渡解析は未完。未駆動/未設計の境界はTab5許可、UV警告、左右レギュレーター許可、シーケンスクリアの5ネット。人の起動操作・Tab5連携・制御順序の未完も継続。

未選定12参照、全負荷/保護協調、全基板/ハーネスと質量割当が残る。動作回路・購入用BOMではなく、製作HOLD。#21〜24未完。旧プローブは今回の追加出力負荷を含まない。

```sh
.venv-engineering/bin/python software/sim/circuits/check_aux_start_connection.py
.venv-engineering/bin/python software/sim/circuits/integrate_protected_pack_system.py --connect-aux
```
