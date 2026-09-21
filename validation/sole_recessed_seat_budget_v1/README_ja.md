# 座面増厚案の寸法予算

以前の境界位置誤差±0.2mmを変更せずに比較。実測公差ではない。
座面残厚1.2mm、ヨーク残厚1.6mm、溝半径方向隙間0.19mm。
溝端壁は公称0.2mm、最悪−0.2mmとなるため、製造可能な閉じた壁とは判定しない。
これは寸法評価で、強度許容値・材料適合を証明しない。
再現: `python3 software/sim/structural/check_recessed_seat_budget.py --out /tmp/seat-budget`
