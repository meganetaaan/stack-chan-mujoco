# スペーサー内部メッシュの切り分け

3段階の全体細分化ではspacerの弾性エネルギーも未収束だったため、粗い基準の接触/荷重面設定を保ち、spacer内部だけ目標0.125 mmにする比較を準備。GmshのMathEvalをRestrictでspacer体積へ限定し、IncludeBoundary/IncludeEmbeddedを無効化。従来の既定メッシュ設定は変更しない。

Gmsh一次資料: https://gmsh.info/doc/texinfo/ （Mesh size fields / Restrict）

比較結果: bossはSHA-256まで同一。spacerの四面体数50,496→81,674、節点18,874→24,021。出力している全ての接触/荷重面の三角形座標は小数10桁丸めで一致する。未タグ外面全てを照合したものではない。面積誤差は従来同様1%以内。

analysis/report.jsonの出力前は解析未完了。comparison_plan.jsonは事前判定基準。内部細分化による変化を調べる診断で、最終の3段階収束や実材料強度の承認ではない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --spacer-interior-mm .125 --curvature-points 16 --circle-points 64 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm .5 --out outputs/spacer_interior_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_mesh_boundaries.py --baseline validation/sole_rounded_local_mesh_v1 --variant outputs/spacer_interior_mesh --out outputs/spacer_boundary_comparison.json
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/spacer_interior_mesh --mesh-mm 0.5 --out outputs/spacer_interior_analysis
```

保存結果の比較: `.venv-engineering/bin/python software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_spacer_interior_probe_v1`。再生成した解析には比較planのvariantを別フォルダで変更する。
