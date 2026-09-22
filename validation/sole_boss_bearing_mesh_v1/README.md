# ナット・スペーサー座面を反映したボスメッシュ

4×4 mmナットと外径4 mmスペーサーの実名目接触域を分割。穴径2.3 mmを除く座面積は11.84524/8.41184 mm²。体積差1e-6 mm³以内、メッシュ面積誤差は0.225%/0.641%で1%基準内。1/.7/.5 mmメッシュを保存。

1 mmメッシュで20 N、スペーサー環状面の法線変位のみ固定した予備解析は変位0.0057135 mm、最大絶対主応力6.53959 MPa。既存仮許容5.6 MPaを超える。全面固定予備解析の合格を実接合へ一般化できない。単一メッシュ、接触離間なし、剛体スペーサー、クリープなしであり最終不合格の定量値としても未収束。

次は応力集中位置と収束を確認し、座面拡大・締付力の適正化を検討する。20 Nは承認締付力ではない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_sole_boss_bearings.py --out outputs/bearing_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_boss_bearings.py --source outputs/bearing_repro
```
