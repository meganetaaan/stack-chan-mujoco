# 幾何学的に固定したアンカーでの細分化

スペーサー底面へ(32.1,6,−19.85)、(37.9,6,−19.85)、(35,8.9,−19.85) mmの点を刻印し、ボスの既存頂点2点とともに拘束した。解析生成器は指定点から1e-7 mm以内の節点がなければ停止する。`anchor_coordinates.json`に0.7・0.5 mmで5点が完全一致する確認を保存。最近傍節点位置の変動を解消した。

同じ20 N荷重・仮定材料・接触法で両ソルバー正常終了。面積誤差1%以内、接触三角形座標一致。

事前に従来の変形変化5%、圧力・応力変化10%、個別アンカー力・モーメント比1e-4を維持。結果は変形変化ボス4.071%、スペーサー3.549%で基準内。圧力3.94671→4.79054 MPa（21.381%）、ボス主応力2.21485→2.56417 MPa（15.772%）、スペーサー主応力16.7083→33.4509 MPa（100.205%）で収束基準外。個別アンカー力・モーメント比も両メッシュで基準外。

`peak_locations.json`では、最細スペーサーのピーク要素25415がアンカー節点を含み、重心はアンカーから0.02883 mm。粗メッシュのピーク要素はアンカーを含まない。最細側の点拘束近傍での集中が疑われるが、要素を除外して合格にはしない。ボスのピークはナット床側で、アンカー節点を含まない。位置ずれだけが非収束原因ではないことが確認された。

次は点拘束による局所集中と接触離散化を切り分け、必要なら剛体運動を平均的に制限する拘束方式を検討する。実部品の支持境界の裏付け、材料・ペナルティ感度、歩行荷重、接合強度は未完了。比較JSONの`opposite`は共通比較器の歴史的なキー名で、この記録では細メッシュh05を指す。

再現（rootから。出力先を新規にする）:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
for h in 0.7 0.5; do
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --fixed-anchor-points --mesh-mm "$h" --out outputs/fixed_mesh_$h
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_spacer_contact.py --fixed-anchor-points --mesh-mm "$h" --boss-mesh-dir outputs/fixed_mesh_$h/boss --spacer-mesh-dir outputs/fixed_mesh_$h/spacer --out outputs/fixed_analysis_$h
cp validation/sole_spacer_anchor_audit_v1/anchor_plan.json outputs/fixed_analysis_$h/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sole_spacer_anchors.py --source outputs/fixed_analysis_$h
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/evaluate_sole_spacer_contact.py --source outputs/fixed_analysis_$h
done
mkdir -p outputs/fixed_compare
cp validation/sole_fixed_anchors_v1/comparison_plan.json outputs/fixed_compare/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_anchor_positions.py --baseline outputs/fixed_analysis_0.7 --variant outputs/fixed_analysis_0.5 --out outputs/fixed_compare
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_contact_stress.py --baseline outputs/fixed_analysis_0.7 --variant outputs/fixed_analysis_0.5 --out outputs/fixed_compare
```

DAT/FRDが2 MBを超える場合は可逆gzipで保存。ハッシュはmanifestおよび各compression.json。
