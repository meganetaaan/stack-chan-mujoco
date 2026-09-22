# 3段階の最大変位位置の照合

各保存fields.npzの節点変位ノルムを全点から再計算し、既存report.jsonの最大値と一致することを確認。ピークの除外や評価位置の変更はしていない。

|メッシュ mm|boss最大位置の半径 mm|spacer最大位置の半径 mm|spacer最大変位 mm|
|---|---:|---:|---:|
|0.5|1.150000|1.177889|0.000156846|
|0.35|1.150000|1.176285|0.000182135|
|0.25|1.150000|1.176962|0.000227707|

boss最大は各段階でナット座面z=−14.2の内径端。spacer最大はz≈−19.81、内径の下側丸み付近。同じ部位で変位が増加し、単に異なる部位が最大になったことでは収束差を説明できない。全変位ベクトルと座標をreport.jsonに保持。

別の応力監査sole_rounded_third_peak_v1ではboss最大9.02889 MPaは半径2.92776、spacer最大16.42815 MPaは半径1.28293付近。bossピーク要素の平均比品質0.24712、spacer0.66075。要素品質だけでピークを無効化せず、外周接触端と内径/荷重面近傍を分けて精査する。これらは原因確定や強度合格ではない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_rounded_displacement_peaks.py
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sparse_sole_elements.py --source validation/sole_rounded_third_mesh_v1/analysis --mesh-dir validation/sole_rounded_third_mesh_v1/mesh --mesh-mm 0.25 --out outputs/sole_rounded_third_peak
```

対象は保存した3ケースのみ。変位は各モデルの平均剛体モード拘束下の量で、実機の固定条件・予圧・歩行荷重ではない。Issue #18/#20未完了。
