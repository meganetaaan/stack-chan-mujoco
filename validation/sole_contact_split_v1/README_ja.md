# 購入接地材0.8mmの厚さ分割比較

[3M SJ5832](https://www.3m.com/3M/en_US/p/d/b5005035229/)を接地材の比較候補とする。
[メーカー選定表](https://multimedia.3m.com/mws/media/2231379O/3m-bumpon-protective-products-resilient-rollstock-product-selection-guide.pdf)
の総厚0.8mmを使い、旧足裏の底面Z=-22mmから0.8mmを切り分けた。
接地高さ・足外形を増やさず、保持側／接地側とも左右各1ソリッド。
分割前後の体積差は約2.1e-10mm³。これは材料の貼付け・加工成立ではない。

既存ねじ頭の最低Z=-21.2mmと層境界が一致する。接地面から頭まで公称0.8mmは
維持されるが、接地材の圧縮・摩耗・厚さ公差と組立誤差を引く前の値。
既存の床側残余隙間0.55mm基準に対する総減少予算は公称0.25mmしかない。
この予算を満たす根拠がなければ、ねじ頭の座面位置または保持構造を変更する。
足を厚くして脚長を延ばすことで解決した扱いにはしない。

保持部の旧TPU嵌合形状は残っているため、出力をPETG用完成部品と扱わない。
接地層も一定厚さシートで加工可能な輪郭か、ねじアクセスと接着範囲を確認する必要がある。
資料の接着評価を3Dプリント表面や実床の摩擦係数へ転用しない。
材の調達形態・実厚公差・表面処理・保持・摩擦・圧縮は未確定。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/split_sole_contact_layer.py --out /tmp/sole-contact-recheck
```
