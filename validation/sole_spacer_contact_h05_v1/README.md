# 片側接触モデルの0.7→0.5 mm診断

同じCAD・材料仮定・20 N荷重・接触ペナルティ・アンカー目標座標で細分化。座面三角形は両側421個で一致し、接触面積誤差0.4456%は事前の1%以内。

変形の比較は各部品の節点変位から最小二乗の微小剛体運動を除去した指標。変形ピーク変化はボス4.071%、スペーサー0.234%で5%以内。一方、接触圧ピーク3.98515→4.77354 MPa（19.783%）は10%基準外。全積分点の最大絶対主応力はボス2.21568→2.56419 MPa（15.729%）で10%基準外、スペーサー16.4061→15.8129 MPa（3.616%）は基準内。応力のピーク除外・節点平均化はしていない。材料許容応力の認定ではない。

個別反力・モーメントの比はそれぞれ1.50814e-4、1.48344e-4で、以前からの1e-4基準を超える。

## 切り分け上の問題

アンカーは最近傍節点で選ぶため、目標座標を固定しても実座標が変化した。例: スペーサー最初の拘束点は(32.075,6,−19.85)から(32.025,6,−19.8)、3番目は(35,8.925,−19.85)から(35.12414,8.92236,−19.85)。各analysis/assembly.jsonに実座標を保存。したがってこれは純粋なメッシュだけの感度ではない。加えて非剛体変位指標の最小二乗は節点数による重みで、メッシュ密度の影響がある。収束証明として使わない。

次に幾何学的に固定したアンカー点をメッシュへ刻印し、同じ位置・自由度を維持した比較を行う。失敗基準を緩和したり、ピークを除外して合格としない。片側接触モデルと接合強度の認定は未完了。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --mesh-mm 0.5 --out outputs/sole_h05_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_spacer_contact.py --mesh-mm 0.5 --boss-mesh-dir outputs/sole_h05_mesh/boss --spacer-mesh-dir outputs/sole_h05_mesh/spacer --out outputs/sole_h05_analysis
cp validation/sole_spacer_anchor_audit_v1/anchor_plan.json outputs/sole_h05_analysis/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sole_spacer_anchors.py --source outputs/sole_h05_analysis
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/evaluate_sole_spacer_contact.py --source outputs/sole_h05_analysis
mkdir -p outputs/sole_h05_compare
cp validation/sole_spacer_contact_h05_v1/comparison_plan.json outputs/sole_h05_compare/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_anchor_positions.py --baseline validation/sole_spacer_anchor_audit_v1 --variant outputs/sole_h05_analysis --out outputs/sole_h05_compare
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_contact_stress.py --baseline validation/sole_spacer_anchor_audit_v1 --variant outputs/sole_h05_analysis --out outputs/sole_h05_compare
```

比較JSONの`opposite`は流用した比較器のキー名で、今回は反対側アンカーではなく0.5 mmケースを指す。入力引数と本記録で区別する。DATは可逆gzip。
