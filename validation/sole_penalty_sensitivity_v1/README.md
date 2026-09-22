# ペナルティ剛性感度

最適化済み0.5 mmメッシュ、20 N、材料・拘束を固定し、法線ペナルティを1e5/1e6/1e7 N/mm³で比較した。基準1e6の結果は `../sole_optimized_mesh_v1/analysis`。事前基準は圧力・主応力変化10%、変位5%。

基準から1/10へ変更すると圧力ピーク2.78231→2.68560 MPa（3.476%）、10倍へ変更すると2.79266 MPa（0.3721%）。部材応力・変位変化も各基準内。最大食込みはlowで2.686e-5 mm、highで2.793e-7 mm。釣合い・拘束残差・接触力合計の数値チェックも通った。

この固定メッシュ・荷重条件では選んだペナルティ範囲の感度は小さい。一方、最適化済み0.5→0.35 mmで圧力が23.289%変化した既存の不合格は解消されない。別メッシュ、異なる荷重や離間条件への外挿はしない。次は接触端付近の空間離散化と荷重パッチの再現を検証する。実接合強度は未認定。

再現:

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --penalty 100000 --mesh-dir validation/sole_optimized_mesh_v1/mesh --mesh-mm 0.5 --out outputs/sole_penalty_low
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --penalty 10000000 --mesh-dir validation/sole_optimized_mesh_v1/mesh --mesh-mm 0.5 --out outputs/sole_penalty_high
python3 validation/sole_penalty_sensitivity_v1/evaluate.py
```

最後は保存済み結果の比較再現。変更は診断用ペナルティ引数の追加のみで、既定値1e6を維持した。評価結果と元フィールドを保存する。
