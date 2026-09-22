# 外装固定ドライバーの下側アクセス

候補: Wera 2054 Micro 05118064001。メーカー表の先端二面幅1.3 mm、軸径3 mm、軸長40 mm、柄長97 mmを確認した。NBK SLH-M2の六角穴二面幅1.3 mmと公称で一致する。1.5 mm工具やインチ工具を同等として代用しない。

出典: https://www.wera.de/en/tools/2054-screwdriver-for-hexagon-socket-screws-for-electronic-applications

足部revEの各外装ねじ頭の下面Z=-20.3 mmまで、直径3 mm×長さ40 mmの軸が占める領域を部品と照合した。8箇所とも接地層が装着された状態では5.654867 mm³の交差があり、保持部・接地層を取り外すと交差0。ねじ頭の六角穴は包絡CADにないため、対象ねじ自体は除外し、頭下面までを検査した。

組立順は「外装固定ねじの締結→工具を抜く→足裏保持部と接地層を取り付ける」。整備時は逆順。足部単体を保持して行う局所作業の候補であり、ロボットに取り付いた状態の作業性を証明しない。

柄の径・手・治具、工具の寸法公差、先端の穴への実挿入、トルク制限は未確認。メーカーのねじ最大締付けトルク0.3 N mを樹脂部の組立トルクに転用しない。この工具は現時点で寸法候補であり、締付け管理工具としては未選定。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_boot_driver_access.py
```
