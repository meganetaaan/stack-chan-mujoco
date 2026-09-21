# 拡大座面の収束確認

外径6 mm座面、仮の締付力20 N。最細0.5 mmで最大絶対主応力2.38445 MPa、許容5.6 MPa以内。0.7→0.5 mmの応力変化1.5613%、変位変化0.4331%で既存収束基準以内。変位基準0.2 mmも満たす。

最大応力はナット空洞床の縁付近へ移った。全積分点を評価し、支持端や角部を除外していない。剛体スペーサーの法線拘束・接触離間なし・切出しボスのモデルであり、実接合の強度認定ではない。締付力、歩行横荷重、クリープ、公差、スペーサー製品仕様は未確定。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_sole_boss_bearings.py --seat-radius-mm 3 --mesh-mm 0.7 0.5 --out outputs/wide_mesh_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/refine_sole_boss_bearings.py --mesh-dir outputs/wide_mesh_repro --out outputs/wide_refine_repro
```

次は片側接触とスペーサーの弾性を考慮し、保持部が歩行荷重を伝えられるか検証する。Issueは未完了。
