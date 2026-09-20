# 胴体・背面板の接触面監査

現行候補の18部品を読み込み、17接触面と全153部品対を検査した。公称初期形状で期待する接触面を確認でき、意図しない重なりはない。これは強度・締付け・公差込み組立の合格判定ではない。

入力は `board/mechanical/engineering/rear_connection_candidate.json` が指定する埋込みナット式胴体と2 mm背面板。検査計画には入力全ファイルのSHA-256を保存した。結果と接触面STEPは `validation/rear_contact_geometry_development_v1/audit_v1`、実行時ソースは同階層の `source_snapshot` に保存している。

|接触面|各接触面積 mm²|数|
|---|---:|---:|
|胴体―背面板|1483.902830|1|
|ねじ頭―外側座金|15.715817|4|
|外側座金―背面板|29.405307|4|
|胴体―内側座金|19.195131|4|
|内側座金―ナット|18.619430|4|

全接触面で面法線は逆向き、部品間距離は0。検査は接触面積1 mm²以上、距離1e-6 mm以下、意図しない重複体積0.01 mm³以下を事前基準とした。ねじ外径とナット内径の簡略円筒が各3.887721 mm³重なる4対を明示的に除外している。この重複は実ねじ山形状を表しておらず、このまま接触メッシュに使用できない。

## 次の解析で必要な条件

胴体―背面板には四隅以外の周縁接触もある。従来の四隅完全固定モデルの反力を、実締結部のねじ荷重と見なしてはならない。17面の片側圧縮接触、締付け、ねじ結合部の剛性、接触の開離を含むモデルが必要である。接触面STEPは共有領域を表す監査用の面であり、体積メッシュ上の接触要素への対応付けは未実施。

ねじ結合部は、実ねじ山形状または根拠を示した等価接続モデルへ置き換える。重複する簡略円筒をそのまま結合して強度合格を主張しない。初期締付け力、摩擦係数、材料特性、拘束と釣合い、接触ペナルティ感度、メッシュ収束を別途検証する。現時点では締付け力も荷重経路も未検証であり、Issue #17・#18の完了証跡には不足する。

## 再現

リポジトリルートから、未作成の出力先を指定する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
  .venv-engineering/bin/python software/sim/structural/audit_rear_contact.py \
  --out outputs/rear_contact_audit_reproduction
```

実行環境はCadQuery 2.8。公称CADの初期接触のみを対象とし、公差・表面粗さ・変形・摩擦・締付け後の接触状態を含まない。ねじの嵌合と実際の組立可否も別判定とする。

## 接触メッシュの準備

`software/sim/structural/mesh_rear_contact.py` は監査済み接触面で現在の胴体・背面板を分割し、接触名をGmsh物理面グループとして保持する。`validation/rear_contact_mesh_development_v1` に公称3 mm指定の体積メッシュ、分割後BREP、計画・結果・ソースを保存した。胴体20,260節点、背面板6,815節点。接触面積のCADとの差は最大0.641315%で、事前基準1%以内。分割による体積変化は相対1e-8未満。両側のメッシュ節点は独立しており、接触ソルバーでの非整合面対応が必要である。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
  .venv-engineering/bin/python software/sim/structural/mesh_rear_contact.py \
  --out outputs/rear_contact_mesh_reproduction --mesh-mm 3
```

この段階では締結金物のメッシュ・ねじ接続・締付け・負荷・接触求解は含まない。面積一致は応力のメッシュ収束を保証しない。

## 締結金物を含む接触面定義

`--include-hardware` を指定して18部品を個別にメッシュ化し、`export_rear_contact_ccx.py` でCalculiXの節点・C3D4要素・接触面定義に変換した。結果は `validation/rear_contact_assembly_mesh_development_v1` に保存。31,167節点、85,766要素、17接触対（34面グループ）。全接触三角形がただ1つの四面体外表面に対応すること、四面体体積が正であること、各接触対の平均外向き法線が逆向きであることを確認した。要素面番号はCalculiX 2.21マニュアル7.43節に従う。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
  .venv-engineering/bin/python software/sim/structural/mesh_rear_contact.py \
  --include-hardware --out outputs/rear_contact_mesh_all_reproduction
.venv-engineering/bin/python software/sim/structural/export_rear_contact_ccx.py \
  --mesh-dir outputs/rear_contact_mesh_all_reproduction \
  --out outputs/rear_contact_ccx_reproduction
```

出力 `mesh_surfaces.inp` はメッシュと面定義のみであり、実行可能な解析デッキではない。材料・荷重・拘束・ねじ接続・締付けをまだ含まない。ねじの外径包絡体とナット内径の重なりを保持した準備モデルなので、ねじ部は実形状または検証された等価モデルへ変更する必要がある。C3D4の剛性・薄板曲げ精度も未検証で、現メッシュによる強度判定は行っていない。
