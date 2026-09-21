# P30Bセル単体の公称配置

セル仕様と選定範囲は `../direct_cell_p30b_v1/README_ja.md`。
最大外形円柱を旧電池中心へ1配置し、統合v4の52部品をinventoryの順序・体積で照合したうえで各部品と個別に交差判定。Tab5を加えた53対象で重なり0、最小公称距離8.1mm。

保持具・端子・保護回路・取り出し・製造公差・たわみは含まず、製作合格ではない。セル単体の最大47gを完成パック質量へ転用しない。正式CAD・全身質量は変更していない。

再現（未使用出力先）:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_direct_cell_package.py --out /tmp/direct-cell-package
```
