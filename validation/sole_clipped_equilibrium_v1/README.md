# 切分け接触積分による平衡解

固定3点投影接触の解を初期値とし、実際のg<0領域を切り分けて接触力・接線剛性を毎回再組立するNewton補正を追加。部材の小ひずみ弾性と平均拘束は同じ。反復上限20、平衡残差1e-7 N、平均拘束残差1e-8という基準で停止判定する。今回の初期値近傍の全Newton更新には線探索を用いていないため、任意荷重への収束保証はしない。

初期残差0.0369115 N→0.00332322→3.90632e-5→7.36188e-9 N。3回の更新で基準内。切分け接触力合計20.0000000165 N、平均拘束残差9.17e-21、分布拘束力ノルム合計/20 Nは1.85e-14。最大食込み4.85760e-6 mmは0.01 mm以内。

接触圧ピーク4.85760 MPa、ボス最大主応力2.45834 MPa、スペーサー15.79931 MPa。全重なり三角形頂点の隙間最小値から圧力ピークを評価する。古い解の単純な再積分20.1214 Nを採用せず、新しい接触力で平衡を解き直した。

fields.npzのpressure_MPa/gap_mm/contact_area_mm2は元の投影積分点でのサンプルで、これらの積を合計しても今回の接触力にはならない。正しい全体組立接触力はcontact_force_N、領域内ピーク・接触面積・エネルギーはclipped_integration.json。reportの歴史的なconverged_active_set/active_setキーは、このモードでは切分けNewtonの収束判定を表す。

実行時間約32.6秒は初期接触解とNewton補正を含み、前処理の一部は含まない。初期座標鉛直投影、摩擦なし、仮定材料・20 Nの限定モデル。新方式のメッシュ収束、材料・締付力の裏付け、歩行荷重、接合強度は未確認。Issue完了ではない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --clipped-contact --mesh-dir validation/sole_extended_contact_mesh_v1 --mesh-mm 0.5 --out outputs/sole_clipped_equilibrium
```

--clipped-contactは投影接触の初期解を自動的に作る。従来の一致節点・固定点積分の既定動作は維持。関連の単体・組立検証はclipped_contact_triangle_v1とclipped_sole_assembly_v1を参照。
