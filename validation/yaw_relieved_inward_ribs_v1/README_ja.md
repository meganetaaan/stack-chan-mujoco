# ねじ逃げ付き内側リブ増厚案

前案で干渉した左右各2本のplate_2/3_screwの軸から半径2.7mmの円柱を、追加する材料だけから除外した。既存支持部を削っていないことを差分体積で確認。半径は3.8mm頭径に対する名目0.8mm余裕の工学的候補で、工具径や実部品公差の保証ではない。

単一有効ソリッド、外形不変、追加部分の干渉0.01mm³以下、コネクタ予約通路1.3mm以上という事前条件を維持。左右とも通過し、各追加体積2026.350687mm³、サーボとの追加部分の隙間1.5mm、通路の最小隙間1.3mm。既存のねじ・座面・脚長を変更していない。

検査は増厚部分を対象とし、既存全体の公差や動的接触、工具挿入、印刷性を証明しない。正式BOM/currentはまだ変更しない。構造比較は `validation/yaw_relieved_inward_ribs_deformation_v1`。

再現（新しい出力ディレクトリ）:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_relieved_inward_ribs.py --out /tmp/stackchan-relieved-ribs
```
