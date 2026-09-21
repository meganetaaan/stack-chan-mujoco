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

## 最終結果とこの調査の終了

2026-09-21：実行済みケースが完了。平衡残差2.32e-9 N、接触合力20.000000003 N。内部0.125→0.08 mmで圧力0.753%、boss応力0.412%/変位0.0253%、spacer応力1.053%/変位2.760%の変化となり、事前の比較基準は満たした。

この結果は固定された外面・仮定20 N・等方P1モデル内の内部メッシュ感度の確認に限定される。外面も含む全体収束、実材料/予圧/歩行での固定部破損・脱落・干渉の保証ではない。ユーザー指示により本細分化系列をここで終了し、追加の細分化や変形エネルギー診断は自動継続しない。次の判断はdocs/prototype/engineering/prototype_decision/DECISION_ja.mdの故障モード・実寸・保持試験に従う。
