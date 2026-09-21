# 丸み候補の3段階目

global .25 mm、曲率32、円周128、境界サイズ延長なし。形状・±20 N荷重・材料・接触法は前2段階と同じ。事前comparison_plan.jsonの基準を維持。メッシュは面積誤差最大0.116287%、接触三角形片側4,376で面積/一致基準を達成。

解析結果はanalysis/report.jsonが出力されるまで未完了。解析完了後、比較スクリプトで第2段階との差を判定する。3段階の生成だけで収束とみなさない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --curvature-points 32 --circle-points 128 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.25 --out outputs/sole_rounded_third_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/sole_rounded_third_mesh --mesh-mm 0.25 --out outputs/sole_rounded_third_analysis
```

保存した解析を比較するコマンドは `.venv-engineering/bin/python software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_rounded_third_mesh_v1`。再生成結果はcomparison_plan.jsonを別フォルダにコピーしてvariantを変更する。
