# 切分け積分での0.5→0.35 mm比較

接触領域g<0を切り分け、接触力と剛性を一致させたNewton平衡解で比較。形状・材料仮定・20 N荷重・ペナルティ1e6 N/mm³を固定。事前基準: 圧力/応力変化10%、変位5%。基準解は `sole_clipped_equilibrium_v1`。

最細では3回の補正で平衡残差1.38e-9 N、接触力20.0000000031 N。平均拘束・食込み・分布拘束力の基準も通った。解法部分約160秒。

圧力ピーク4.85760→6.29575 MPa（29.606%）で収束基準外。ボス主応力変化6.773%、スペーサー3.739%、変位変化1.881%/4.630%は基準内。すべてのピークを保持。圧力は固定積分点サンプルの最大ではなく、重なり領域頂点の一次隙間から評価した最大値。

固定3点積分の誤差だけでは、圧力非収束を説明できない。平坦面と45度縁落としの鋭い境界、および局所面形状の再現が次の検討対象。物理的特異性と数値誤差の区別は未完了。実部品に指定可能な丸みを含む候補を検討する場合も、形状・公差・材料の根拠を残し、合格しやすい値だけを選ばない。

Issue #18を再確認し、ブーツ・足首・カプラ薄肉部・胴体・電池トレーの最悪荷重に対する強度、変形、メッシュ・接触条件の証跡が完了条件であることを確認した。今回の仮定締付力による局所検証のみでは満たさず、IssueはOPENのまま。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.35 --out outputs/clipped035_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/clipped035_mesh --mesh-mm 0.35 --out outputs/clipped035_analysis
python3 software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_clipped_refine_v1
```

最後は保存済み比較の再現。新規出力の比較にはcomparison_plan.jsonの入力先を更新する。fieldsのpressure_MPa等は投影点サンプルで、実組立力はcontact_force_N。詳細は基準解README参照。
