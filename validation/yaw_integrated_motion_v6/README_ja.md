# v6ヨー回転部の隙間

ヨー連結部と固定ロールクレードルを一体で±15°回転、1°間隔31点／側を評価。
52部品固定組立v6に対する最小距離は左右とも2.082322 mm。
点間の見落とし上限0.273883 mm、公差各0.2 mm、変形各0.2 mmを差し引き、
連続角度範囲の下限1.008439 mmとなり0.50 mm基準内。
これらの公差・変形は既存の設計割当であり、製造保証値ではない。
全脚運動・配線・工具・最新電池構成・実公差・変形連成は範囲外。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out /tmp/yaw-motion-v6 --step-deg 1 --include-cradle --joint-limits --fixed-assembly validation/yaw_integrated_candidate_v6/yaw_support_candidate.step
```
