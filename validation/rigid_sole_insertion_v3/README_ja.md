# 増厚座面の組立姿勢検査

sole_recessed_seat_v2の左右保持部とヨークを使用。
下方8mmから挿入、前方8mmからスライド、各0.5mm刻みの計34姿勢／側で
ヨーク・ブーツとの交差0。ねじとワッシャは位置合わせ後に取り付ける。
連続経路・公差・工具アクセス・強度の合格ではない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_rigid_sole_insertion.py --holder-dir validation/sole_recessed_seat_v2 --yoke-dir validation/sole_recessed_seat_v2 --out /tmp/sole-insertion-v3
```
