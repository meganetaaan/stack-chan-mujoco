# v6公称接触面

26面を抽出し、STEP再読込みで面積を検査。
板／棚1449.151867 mm²、頭／板7.186393 mm²、棚／座金28.015152 mm²で旧v4と同じ。
座金／ナットはv5からの六角ナット回転包絡なので12.600405 mm²となる。
このナット包絡面積を実際の六角座面・面取りを含む接触面積と扱わない。
公称面の一致は接触圧・摩擦・締付け・引抜き・クリープの証明ではない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/extract_yaw_joint_interfaces.py --candidate validation/yaw_integrated_candidate_v6 --out /tmp/yaw-interfaces-v6
```
