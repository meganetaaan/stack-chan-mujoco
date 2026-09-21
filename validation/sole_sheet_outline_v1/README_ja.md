# 接地シートの切出し輪郭候補

左右の接地層について底面輪郭を0.8mm押し出し、元形状との双方向差集合が0であることを
確認した。従って、この形状は一定厚さシートから作る輪郭として表現できる。
外周1つと内部切抜き1つ、面積4088.1044mm²。CAD座標のXY、単位mmでDXFを出力。
DXF読戻し後の押出しも有効形状で、体積差1e-5mm³未満を確認した。

これは公称輪郭であり、刃幅・加工公差・接着・実厚・圧縮・摩耗を含む加工承認ではない。
内部切抜きを埋めない。接着面の裏表、左右の取付方向、ねじアクセスと保持構造を
確認した加工図を別途完成させる。旧TPU保持部が硬質材に対応したという意味でもない。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/export_sole_sheet_outline.py --out /tmp/sole-outline-recheck
```

初回のDXF読戻し結果はreport.jsonに保存。接地高さは旧形状のまま。
