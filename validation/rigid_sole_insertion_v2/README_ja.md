# 頭位置変更＋拡大キー穴の挿入比較

左右各34姿勢で、変更後保持部とヨーク・ブーツの公称交差0を確認。
連続経路、公差、強度、ねじや工具、固定後の上下遊びは未認定。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_rigid_sole_insertion.py --holder-dir validation/rigid_sole_heads_v1 --yoke-dir validation/rigid_sole_keyhole_v1 --out /tmp/rigid-sole-insertion-v2-recheck
```
