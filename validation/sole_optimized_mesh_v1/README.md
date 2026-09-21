# 四面体品質の影響診断

既存のピーク監査は `../sole_sparse_peak_geometry_v1`。粗・細メッシュのスペーサー応力ピークはいずれも縁落とし近傍で、四面体mean ratioが約0.07、最小高さ0.00356/0.00921 mmだった。要素や応力値は除外していない。

同じCAD・0.5 mmサイズ・固定アンカー点でNetgen最適化を追加。体積保持、接触面一致、面積誤差1%以内の従来チェックを維持。平均拘束の疎行列診断ソルバーで同じ20 N・仮定材料を解いた。

スペーサーの最大絶対主応力は33.6331→15.8062 MPa。ピーク要素のmean ratioは0.07438→0.86608、全体最小値は0.05582→0.16122。ピーク位置は外周底面付近から内周底面付近へ変わった。ボス主応力は2.55614→2.45849 MPa。接触圧ピークは2.80121→2.78231 MPa。釣合い・平均拘束・接触力合計の数値チェックも通った。

これはメッシュ品質への感度を示す比較であり、最適化後の値が真値である証明ではない。小さくなった応力を理由に合格としない。形状品質指標は診断用で、事後に除外閾値を設定していない。最適化済みの複数サイズで収束を調べ、独立接触ベンチマーク・離間・材料等の未検証事項も解消する必要がある。Issue未完了。

再現:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --optimize-tets --fixed-anchor-points --mesh-mm 0.5 --out outputs/sole_opt_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --mesh-dir outputs/sole_opt_mesh --mesh-mm 0.5 --out outputs/sole_opt_analysis
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sparse_sole_elements.py --source outputs/sole_opt_analysis --mesh-dir outputs/sole_opt_mesh --mesh-mm 0.5 --out outputs/sole_opt_quality
```

品質式は12(3V)^(2/3)/Σ辺長²（正四面体で1）。全積分点応力の最大値とメッシュ内の最小品質を記録する。ピーク形状をverticesで保存して再確認可能にした。
