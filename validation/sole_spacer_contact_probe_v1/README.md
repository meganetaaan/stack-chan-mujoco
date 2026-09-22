# ボスと独立金属スペーサーの片側接触予備解析

最小外径5.95、最大内径2.35、最小厚さ0.85 mm、45度縁落とし0.05 mmのスペーサーを追加した。形状は `../sole_spacer_contact_geometry_v1`、接触面一致メッシュは `../sole_spacer_contact_mesh_v1`。ボスは従来の切出し形状、スペーサーは独立節点であり、接触面を接着していない。346三角形の接触面座標一致、両部品の体積保持、座面積誤差1%以内を確認した。

CalculiXのsurface-to-surface片側・摩擦なし接触、ペナルティ1e6 N/mm³、C3D4・サイズ0.7 mm。ナット面へ−20 N、ねじ頭面へ+20 Nの分布力を与えた。ボスE1120 MPa・ν0.35、スペーサーE193000 MPa・ν0.3は仮定。金属の値は材料証明書等に基づく確定値ではなく、材料感度と根拠の確認を残す。実ねじ・ナットの弾性と締付力の根拠も未検証。

正常終了、最大食込み3.985e-6 mm、接触圧力評価値0.000131–3.985 MPa。ボス最大変位0.004060 mm、スペーサー最大変位0.000325 mm。事前の数値チェック（終了、合計アンカー反力/20 N≤1e-4、食込み≤0.01 mm）は通った。

**接合強度の合格ではない。** アンカーはスペーサー3-2-1・ボス面内拘束で、合計反力が小さくても個別の拘束力が打ち消す可能性がある。個別アンカー力・モーメント、拘束位置感度、接触力の積分、メッシュ・ペナルティ・材料感度、各部材応力、偏心・歩行荷重、クリープを確認する必要がある。出力に現れる正圧力は接触法の出力であり、以前の両側支持モデルの境界応力積分とは異なる評価量。

再現（出力先はすべて新規ディレクトリ）:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_minimum_sole_spacer.py --out outputs/minimum_spacer_geometry
# mesh生成器は保存済みgeometryのSTEPを入力に使用する。
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --mesh-mm 0.7 --out outputs/sole_contact_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_spacer_contact.py --boss-mesh-dir outputs/sole_contact_mesh/boss --spacer-mesh-dir outputs/sole_contact_mesh/spacer --out outputs/sole_contact_probe
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/evaluate_sole_spacer_contact.py --source outputs/sole_contact_probe
```

大きなDATをgzipで可逆圧縮した。評価スクリプトは圧縮済みDATにも対応する。Issue #17–20は未完了。
