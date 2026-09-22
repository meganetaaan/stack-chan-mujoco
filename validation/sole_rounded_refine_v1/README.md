# 丸み候補の細分化比較：未収束

事前comparison_plan.jsonに従い、global .5→.35 mm、曲率16→24、円周64→96へ細分化。境界サイズ延長は双方無効、形状R0.05、材料、±20 N荷重、平均拘束、切断接触積分、ペナルティは同一。

細分化メッシュの面積誤差最大0.20369%は1%基準内。接触平衡残差5.26e−8 N、合力20.000000676 Nで数値ゲートは達成。

|量|粗|細|変化率|事前許容|判定|
|---|---:|---:|---:|---:|---|
|接触圧 MPa|48.3039|30.3048|37.26%|10%|未達|
|boss最大絶対主応力 MPa|6.37799|7.76970|21.82%|10%|未達|
|boss最大変位 mm|0.00417176|0.00432869|3.76%|5%|達成|
|spacer最大絶対主応力 MPa|13.5530|13.9093|2.63%|10%|達成|
|spacer最大変位 mm|0.000156846|0.000182135|16.12%|5%|未達|

圧力が下がったことは改善や収束を意味しない。ピークは除外していない。3メッシュによる最終収束基準も未完了。現時点で丸み候補の強度を承認できず、接触端形状・局所要素と境界条件の精査が必要。実材料、製造半径公差、予圧、歩行荷重、クリープを検証したものではない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --curvature-points 24 --circle-points 96 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.35 --out outputs/sole_rounded_refine_mesh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir outputs/sole_rounded_refine_mesh --mesh-mm 0.35 --out outputs/sole_rounded_refine_analysis
.venv-engineering/bin/python software/sim/structural/compare_sparse_sole_reports.py --source validation/sole_rounded_refine_v1
```

最後のコマンドは保存済み解析を比較する。再生成結果の比較には新しい比較フォルダへcomparison_plan.jsonをコピーしてvariantを新しい解析先に変更する。fields.npzの投影サンプル圧の加重和は最終合力ではなく、切断積分の最終力を使用する。
