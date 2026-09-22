# 嵌合後EH包絡とヨー取付部

JST EH図面2・3ページを目視確認し、基板上のヘッダ高さ6mm、嵌合高さ8.1mm、EHR-3幅9.5mm・厚さ3.8mmを使用。メーカーSTEPのヘッダ端から基板面Z=78.9mmを推定し、嵌合上端Z=87.0mmの参考包絡を配置した。図面値は参考寸法であり、公差付きの実嵌合CADではない。

全4ポートで体積交差0。支持棚まで2.0mm、金属取付板まで1.0mm。既存の公差0.2mm/側、変形0.2mm/側を控除すると支持棚1.2mm、金属板0.2mmで、金属板側が既存残余0.5mm基準に不合格となる。配分値を下げて合格にはしない。

実線材の出口と曲げは未算入。次は金属板の該当位置へ配線の逃げを設計し、ねじ座・有効断面と干渉を確認する。支持棚を全面的に削る根拠はない。ただし電線の通過には棚も関係するため、ハウジングの隙間だけで配線経路の成立を宣言しない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_mated_housing.py --out /tmp/yaw-mated-review
```
