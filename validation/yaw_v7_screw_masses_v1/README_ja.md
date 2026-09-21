# v7ねじ20本の公称質量照合

取付板8本・仮保持4本はNBK SLH-M2-10、背面8本は優先候補SNS-M3-16。
20項すべてのinventory記録が旧revAから不変であることを照合した。
メーカーの公称質量を2026-09-22に再確認し、各0.23 g×12と1.2 g×8で12.36 g。

出典：
- https://static.nbk1560.com/products/specialscrew/nedzicom/socketheadcapscrew/SLH/SLH-M2/SLH-M2-10/
- https://www.nbk1560.com/products/specialscrew/nedzicom/highintensity/SNS-J/SNS-M3/SNS-M3-16/

これは名目質量の型番・本数照合で、購入品公差・実測質量・重心／慣性の保証ではない。
後者はnullを維持。衝突包絡をカタログ質量で一様に拡大縮小して確定慣性にはしない。
M3候補の12.9級を旧8.8級強度計算へ無条件に転用せず、形状公差・首下丸み・座金・
締付け・ねじ保持の既存残件を維持する。
質量だけの小計として台帳から参照できるが、完全なbody慣性へは未統合。

再現：
```sh
.venv-engineering/bin/python software/sim/structural/reconcile_yaw_v7_screw_masses.py --out /tmp/yaw-v7-screws
```
