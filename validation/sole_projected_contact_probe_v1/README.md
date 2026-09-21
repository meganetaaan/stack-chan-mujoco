# 初期隙間付き投影接触の予備計算

`project_sole_contact.py`はスペーサーの平坦部と上面縁落としの各三角形に3点を配置し、ボス底面へ鉛直投影する。両側の変位を面の重心座標で補間し、初期隙間を保持。積分重みは水平投影面積。法線は初期ボス底面の鉛直方向で、有限すべりや回転法線は扱わない。

対応付けデータは `../sole_contact_projection_v1`。1680点、投影面積23.36899 mm²、初期隙間0–0.041667 mm、うち417点に隙間。分配係数和・平面座標の再現誤差は約7e-15、単位力の作用反作用とモーメントも1e-8の事前許容値以内。

平均拘束付き小ひずみソルバーへ接続し、7反復で接触集合が収束。接触点1190、接触力合計20 N、平衡残差5.36e-13 N、平均拘束残差9.91e-18。ボス/スペーサー最大主応力は2.45835/15.79956 MPa。接触圧ピーク3.74808 MPa。従来の節点面積集中モデル2.78231 MPaとは接触面積の積分方法が異なるため、数値一致を期待する比較ではない。部材変形・応力の変化が小さくても圧力近似の妥当性は未確定。

初期隙間を持つ417点は全点非接触、初め平坦な領域の73点は開いた。最小の縁落とし評価点隙間は最終0.008318 mm。この点配置では縁落としの根元直近まで分解できず、狭い接触拡大を見落とす可能性がある。「縁落とし面はどこでも接触しない」と結論しない。点間の隙間を拘束しておらず、連続面の貫通も別途監査が必要。

次は積分点間の隙間監査と接触端の分割を行う。解析コアの単純問題検証は `sole_contact_analytic_v1` にあるが、今回の投影接触の空間収束や実接合強度を証明するものではない。

再現:

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/project_sole_contact.py --mesh-dir validation/sole_extended_contact_mesh_v1 --out outputs/sole_projection
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --projected-contact --mesh-dir validation/sole_extended_contact_mesh_v1 --mesh-mm 0.5 --out outputs/sole_projected_probe
```

既定は従来の一致節点接触。`--projected-contact`を指定した場合だけ初期隙間付き投影を使う。planの一般的なlumpedという説明より、projected_contact=trueと本記録の積分方式がこのケースの詳細を示す。Issueは未完了。
