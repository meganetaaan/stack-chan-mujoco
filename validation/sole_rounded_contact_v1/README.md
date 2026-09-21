# 丸み付きスペーサーの局所接触平衡

sole_rounded_local_mesh_v1（面積基準内）のR0.05候補へ、従来と同じ±20 Nの座面荷重と平均剛体モード拘束を適用。小変形P1、固定鉛直法線、摩擦なし、ペナルティ1e6 N/mm³、重なり三角形ごとの接触領域切断積分。材料E=1120/193000 MPa等と荷重は仮定で、実締付条件を確定したものではない。

2回のNewton修正後、平衡残差3.28e−9 N、接触合力20.000000004 N。数値ゲートを満たすが、最大接触圧48.3039 MPa、boss最大絶対主応力6.37799 MPaであり、強度合格とはしない。boss変位0.00417176 mm、spacer変位0.000156846 mm。鋭い縁の既存結果とは形状・メッシュが異なるため、数値の大小を改善効果と即断しない。

sole_rounded_peak_audit_v1で全積分点を含む応力ピークを調査。bossのピーク要素は半径2.92826 mm付近、平均比品質0.36574、最小高さ0.00582157 mm。ピークを除外せず保持する。圧力ピーク位置そのものはこの応力要素監査から断定しない。次の段階でglobal .35 mm、曲率24、円周96のメッシュを比較する。3段階の最終収束判定、実材料・予圧・歩行荷重・クリープは未完了。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir validation/sole_rounded_local_mesh_v1 --mesh-mm 0.5 --out outputs/sole_rounded_contact
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sparse_sole_elements.py --source outputs/sole_rounded_contact --mesh-dir validation/sole_rounded_local_mesh_v1 --mesh-mm 0.5 --out outputs/sole_rounded_peak_audit
```

plan.jsonの従来scope/limitationsにはnode-lumpedとあるが、clipped_contact=trueが今回の積分方式。fields.npzのpressure_MPa等は投影サンプル値であり、その単純加重和を最終接触合力としない。最終合力はcontact_force_N、切断積分はclipped_integration.jsonを参照。joint_verified=false。
