# 座面支持ボスのメッシュ感度（応力基準超過）

20 N、ナット名目座面荷重、スペーサー環状面の法線固定。0.7/0.5 mmで最大絶対主応力6.11555/6.00048 MPa、変化1.882%。変位変化0.506%。既存収束基準10%/5%以内だが、応力許容5.6 MPaを超えるため合格ではない。

最大位置はスペーサー外周付近、最細(33.29966,4.93110,-18.97621) mm。支持端を除外せず全積分点で判定した。今の2段階の収束基準内という結果は数学的な特異性不存在の証明ではない。剛体支持・離間なし・切出し形状の仮定を保持する。

20 Nの締付力は未採用。次は座面拡大または実際の接触弾性を取り込む。固定力を下げる場合は滑り・緩み・保持荷重を別途確認する。歩行せん断、クリープ、実部品公差は未評価。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/refine_sole_boss_bearings.py --out outputs/boss_refine_repro
```

メッシュはsole_boss_bearing_mesh_v1を使用し各ハッシュを記録。応力・反力・変位はfields_*.npzに保持。製造リリース前。
