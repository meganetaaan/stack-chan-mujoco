# 最小座面の収束と境界トラクション診断

外半径2.925・内半径1.225 mmの剛体座面、締付力20 N、等方PETG E1120 MPa・ν0.35。形状根拠は `../sole_minimum_bearing_v1`。最小スペーサー厚さ・弾性はまだモデル化していない。

0.7→0.5 mmで最大変位変化0.1915%、最大絶対主応力変化5.685%。最細最大絶対主応力2.26478 MPa。既存の変位0.2 mm・主応力5.6 MPa・変位収束5%・応力収束10%という局所スクリーニング基準はすべて満たす。全積分点を評価し、支持端のピークを除外していない。

境界応力から求めた支持圧力の全点は圧縮側。しかし圧力積分と組立反力20 Nとの差は0.7 mmで17.73%、0.5 mmで14.19%。細分化結果を評価する前に `traction_plan.json` で設定した5%診断基準を満たさない。`traction_verdict.json` は明示的に不合格を記録する。これは境界応力回復の精度不足であり、実接触の離間が発生したと断定する結果ではない。

節点反力は二次形状関数による弱形式量であり、負の節点力を直接引張圧力と解釈しない。次の解析では片側接触条件を明示的に扱い、実スペーサーの変形、偏心、最小厚さ、締付力の根拠、歩行横荷重を評価する。今回の結果のみで接合強度やIssue完了を主張しない。

再現:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_sole_boss_bearings.py --seat-radius-mm 2.925 --seat-inner-radius-mm 1.225 --mesh-mm 0.7 0.5 --out outputs/minimum_refine_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/refine_sole_boss_bearings.py --mesh-dir outputs/minimum_refine_mesh --out outputs/minimum_refine_analysis
for h in 0.7 0.5; do
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sole_bearing_traction.py --source outputs --mesh-file outputs/minimum_refine_mesh/boss_${h}.msh --fields-file outputs/minimum_refine_analysis/fields_${h}.npz --out outputs/minimum_traction_${h}
done
python3 validation/sole_minimum_refine_v1/evaluate_traction.py
```

最後のコマンドは保存済み結果の判定再現。新規解析結果を判定する場合は同スクリプト・traction_planと新規traction_0.7/traction_0.5を同じディレクトリ構成で配置する。初回の粗メッシュ診断は `../sole_minimum_traction_v1`。
