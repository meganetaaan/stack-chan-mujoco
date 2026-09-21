# 丸み候補の3段階目

global .25 mm、曲率32、円周128、境界サイズ延長なし。形状・±20 N荷重・材料・接触法は前2段階と同じ。事前comparison_plan.jsonの基準を維持。メッシュは面積誤差最大0.116287%、接触三角形片側4,376で面積/一致基準を達成。

解析完了。第2→第3段階の圧力変化0.98024%、boss変位1.76709%は基準内。一方boss応力16.2064%、spacer応力18.1093%、spacer変位25.0210%で基準外。3段階の最終収束判定は未達。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --curvature-points 32 --circle-points 128 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.25 --out outputs/sole_rounded_third_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/sole_rounded_third_mesh --mesh-mm 0.25 --out outputs/sole_rounded_third_analysis
```

保存した解析を比較するコマンドは `.venv-engineering/bin/python software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_rounded_third_mesh_v1`。再生成結果はcomparison_plan.jsonを別フォルダにコピーしてvariantを変更する。

## 第3段階の結果

平衡残差2.78e−8 N、接触合力20.000000027 Nで数値ゲートを満たす。最大圧30.00777 MPa、boss最大絶対主応力9.02889 MPa・最大変位0.00440519 mm、spacer最大絶対主応力16.42815 MPa・最大変位0.000227707 mm。ピークは除外しない。第2段階との比較はcomparison.json。圧力だけが基準内でも、応力・変位の未収束を残したまま接合部強度を承認しない。実材料・製造半径公差・予圧・全歩行荷重の課題も残る。
