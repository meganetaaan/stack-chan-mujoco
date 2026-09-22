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

## 全外面の追加照合

四面体の面を列挙し、1要素だけに属する面を外面として抽出して比較した。boss9,086面、spacer34,490面の全三角形座標が小数10桁丸めで一致。全ての四面体面の共有数が2以下であることも確認。full_boundary_comparison.jsonに記録した。先の物理タグ面のみの結果も履歴として保持する。

この確認により、今回の比較で外面の形状近似や分割を変えていないことを示す。内部の四面体分割は非入れ子であり、変位が必ず一方向に収束するとは仮定しない。力学解の収束・要素品質・実CAD精度をこの一致検査で代替しない。

## 解析完了結果

接触合力20.000000002 N、平衡残差2.01e−9 Nで数値ゲートを満たす。元の外面固定基準に対し、圧力7.543%、boss応力8.059%、boss変位0.401%は比較基準内。一方spacer応力39.300%、spacer変位63.537%で未達。spacer最大変位0.000256500 mm、最大絶対主応力18.8793 MPa。

外面が同一でもspacer変位が大きく変わり、内部のP1四面体分割が剛性評価へ強く影響することが分かった。外面曲率の変更だけで未収束を説明することはできない。内部目標0.08 mmの次比較を別フォルダsole_spacer_interior_refine_v1で行う。元の20 N/材料/接触条件の仮定は維持し、強度合格とはしない。
