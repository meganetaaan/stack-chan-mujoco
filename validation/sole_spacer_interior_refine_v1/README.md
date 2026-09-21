# スペーサー内部のみの追加細分化

内部目標サイズを0.125 mmから0.08 mmへ変更し、外面固定で内部P1四面体の感度を評価する。comparison_plan.jsonに解析前の比較基準を保存した。圧力・応力10%、変位5%。最終的な全体3段階メッシュ収束を代替しない。

full_boundary_comparison.jsonでboss全9,086面、spacer全34,490面の三角形座標が小数10桁で一致。bossのメッシュSHA-256も一致。spacerは24,021→39,014節点、81,674→169,956四面体。外面・荷重・材料条件を保持した内部細分化として解析する。

analysis/report.jsonが存在しない間は解析未完了。数値収束だけで材料強度・実締結・歩行荷重への適合を主張しない。

再現はリポジトリルートで以下を実行する。出力先は新規ディレクトリを用いる。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --spacer-interior-mm .08 --curvature-points 16 --circle-points 64 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm .5 --out outputs/spacer_interior_refine_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_mesh_boundaries.py --baseline validation/sole_spacer_interior_probe_v1/mesh --variant outputs/spacer_interior_refine_mesh --out outputs/spacer_interior_refine_boundary.json
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/spacer_interior_refine_mesh --mesh-mm 0.5 --out outputs/spacer_interior_refine_analysis
```

保存済み解析の比較は `software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_spacer_interior_refine_v1`。再生成先についてはcomparison_plan.jsonのvariantを対応させる。
