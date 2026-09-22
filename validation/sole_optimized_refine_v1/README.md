# 最適化済みメッシュ0.5→0.35 mm

同じCAD、Netgen最適化、仮の20 N、材料値、疎行列の平均拘束・節点面積ペナルティ接触を使用。基準は事前のcomparison_plan.json: 応力・圧力変化10%、変位変化5%。0.5 mm基準結果は `../sole_optimized_mesh_v1/analysis`。

0.35 mmでボス最大絶対主応力2.29196 MPa、スペーサー16.39705 MPa。変化はそれぞれ6.774%、3.738%で基準内。変位変化1.881%、4.626%も基準内。接触圧は2.78231→3.43028 MPa（23.289%）で基準外。全積分点・全接触節点を評価し、端部を除外していない。

ピーク要素のmean ratioはボス0.790、スペーサー0.910。スペーサーメッシュ全体最小値0.235。扁平要素による大きな応力変動は今回の比較では抑えられたが、収束の一般的証明にはしない。

pressure_peaks.jsonでは両メッシュの圧力ピークが座面外周r=2.925 mmにある。節点面積は0.08324→0.04304 mm²。端部圧力の離散化依存が残る可能性があり、真の物理的特異性か数値誤差かをこの結果だけで断定しない。接触法・局所形状・ペナルティの検証が必要。小ひずみモデル、材料仮定、離間未検証、歩行荷重未投入という制限も維持する。

全体を合格としない。圧力の不合格を保存し、Issue #17–20は未完了。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --optimize-tets --fixed-anchor-points --mesh-mm 0.35 --out outputs/sole_opt035_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --mesh-dir outputs/sole_opt035_mesh --mesh-mm 0.35 --out outputs/sole_opt035_analysis
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sparse_sole_elements.py --source outputs/sole_opt035_analysis --mesh-dir outputs/sole_opt035_mesh --mesh-mm 0.35 --out outputs/sole_opt035_quality
python3 software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_optimized_refine_v1
```

最後のコマンドは保存済み比較の再現。新規結果の比較ではcomparison_plan.jsonのbaseline/variantを新規出力先へ変更して使用する。解析フィールド、メッシュ、品質・失敗判定を保存。
