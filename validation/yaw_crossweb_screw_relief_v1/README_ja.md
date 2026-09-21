# ねじ逃げ付き前端横板

X8..11.6、Z78..88の横板追加分だけから、左右各plate_2/3_screw軸を中心とする半径2.7mmの円柱を除いた。既存支持部の体積を削っていないことを確認。半径は3.8mm頭径に対する名目0.8mm余裕の設計候補で、工具挿入保証ではない。

前案の検査漏れを避け、追加部分を固定アセンブリの各ソリッドと個別に検査した。左右とも単一有効ソリッド、外形変化0、追加干渉なし、メーカーサーボとの隙間3.5mm、予約コネクタ通路1.3mm。追加体積は各856.180365mm³。

さらに `yaw_integrated_candidate_v4` の52部品で変更部品を含む546組を検査し、新規重なりなし。未変更部品同士、全身動作、工具、ケーブル、公差はこの結果に含めない。構造結果は `yaw_crossweb_screw_relief_deformation_v1`。

再現:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_crossweb_screw_relief.py --out /tmp/stackchan-crossweb-relief
```
