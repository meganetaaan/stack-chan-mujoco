# 背面カバーを介する荷重伝達の確認

最新のヨー支持部は、取付座4面の理想固定モデルで解析されていた。実機ではその面は背面カバーに接し、カバーから胴体の四隅へ荷重を伝える必要がある。
元のr9 STEPを調べると、カバーはx=-64〜-62.2 mm（厚さ1.8 mm）、幅128 mm、高さ128 mm。
カバーの胴体取付穴はy=±59 mm、z=8/120 mm、半径1.65 mm。胴体の対応するボス外半径は4.6 mm、穴半径は1.25 mm。
胴体のこの穴はM3の通し穴ではなく、ねじ加工・インサート・保持方法を確定する必要がある。
支持部の取付穴はy=±19/±33 mm、z=58/82 mmであり、その位置に胴体の受けはない。

## 解析条件

左右同時の記録荷重を使うため、独立した荷重面を複数扱う機能を追加した。
面ごとに力・モーメントの6成分を保持する分布荷重を組み立て、荷重原点間のモーメント移動も検査する。
単一面の旧APIは互換ラッパーとし、保存済み6独立解との変位・応力・反力の相対差6×10⁻¹²未満を確認した。

使用するのは右旋回記録2.661 sの左右同時荷重。新しい穴配置で保存したボルト群の原点（x=-62.2 mm、y=±26 mm、z=70 mm）での荷重を使用する。
カバー内面の四隅で、ボスに対応する半径4.6 mmの領域を理想固定する。荷重面は支持部の半径6 mmの4座に対応する領域を左右別に選択する。
領域は表面三角形の重心で選ぶ近似であり、真の接触・締付け面圧を再現していない。

材料仮定はE=1,120 MPa、ν=0.35。基準は変位0.2 mm、最大絶対主応力・von Mises応力5.6 MPa以下。実行前の計画に保存する。
片側だけを負荷する2ケースと、左右同時の1ケースを同じ剛性行列で解き、左右の場の和と同時負荷の場の相対差1×10⁻⁸未満も検査する。
片側ケースは解析器の確認用であり、左右同時の評価と区別する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_shared_factorization.py --reference validation/reinforced_all_loads_development_v1/yaw_reinforced_bounds_v1 --out outputs/multiregion_compatibility_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_back_cover.py --out outputs/back_cover_load_new
```

## 範囲

単一時刻・単一メッシュの開発評価。四隅のボス・胴体の柔軟性、ねじ接触、保持、材料異方性、座屈を証明しない。
理想固定で失敗した場合はカバーの設計変更が必要。合格しても荷重経路全体の成立には胴体側と接合の確認が残る。

## 樹脂カバーの失敗と構造板候補

元の1.8 mm樹脂カバーは、左右同時荷重で最大変位1.89490 mm、最大絶対主応力17.23535 MPaとなり、両基準に不合格だった。変位が板厚と同程度なので、線形解析値は実変形の予測値ではなく、この構成を棄却する指標として扱う。

穴・通風スリットを保持した厚さ2 mmの6061-T6板を候補として生成した。内面x=-62.2 mmを保ち、背面のみ0.2 mm張り出す。計算質量86.77 g、旧樹脂カバー36.73 gに対し50.04 g増える。この追加質量は既存の動作荷重に未反映であり、最終評価にはモデル更新が必要。M3x16のナット先端からの公称突出量は1.9 mmとなる。

材料根拠と仮定は`board/mechanical/engineering/backplate_material.json`に保存する。今回の予備評価はE=68,300 MPa、ν=0.33、許容応力120 MPa、許容変位0.2 mm。購入材の証明書・板厚公差・電気絶縁は未確定。

生成には面全体の押出しを使用する。初回の薄層追加・ブーリアン結合は有効な単一ソリッドにならず棄却した。DXF投影の汎用行列変換もCADカーネルで拒否されたため、剛体回転・並進へ修正した。生成後のSTEPは有効な単一ソリッドで体積を確認し、DXF再読込ではmm単位、128×128 mm、監査エラーなしを確認した。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_backplate.py --out outputs/backplate_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_back_cover.py --step outputs/backplate_new/rear_structural_plate.step --material-config board/mechanical/engineering/backplate_material.json --out outputs/backplate_load_new
```

構造板候補の左右同時荷重では、最大変位0.022879 mm、最大絶対主応力12.73405 MPaとなり、今回の単一時刻・理想四隅固定の予備基準を満たした。左右解の重ね合わせ検査も合格。メッシュ収束、全荷重ケース、胴体・締結の柔軟性と追加質量を含む評価は未完了であり、EPICの合格とはしない。

解析計画・ネイティブ場・メッシュ・CAD・DXF・材料設定・コードスナップショットは`validation/back_cover_development_v1`に保存した。

## 3段階メッシュの判定

同じ形状・材料・荷重・拘束で4/3/2 mmメッシュを比較した。左右同時荷重の最大変位は0.022690/0.022879/0.022820 mm、最大絶対主応力は13.9168/12.7341/14.5742 MPa。最後の2段階を細かい側の値で割った相対差は、変位0.257%、最大主応力12.626%、von Mises応力5.752%。既定の変位5%・応力10%の収束判定は**不合格**。応力の絶対値が材料許容以下でも、収束した設計とは扱わない。

最大主応力の評価点は、4/3 mmではy≈54.6、z≈116.3 mm、2 mmではy≈56.4、z≈13.0 mmであり、いずれも四隅の固定領域付近にある。粗密で最大点が移る。固定領域を面重心で選択する近似と理想拘束の境界が関与する可能性があり、接触面を幾何学的に分割したメッシュと実際の接合条件で再評価する必要がある。最大点を除外して合格へ変更しない。

追加の場・メッシュ・判定・反力・コード・ハッシュは`validation/backplate_convergence_development_v1`に保存。3 mmの証跡は既存の`validation/back_cover_development_v1/backplate_load_v1`を使用する。

```sh
.venv-engineering/bin/python software/sim/structural/check_backplate_convergence.py --analyses validation/backplate_convergence_development_v1/backplate_load_4mm_v1 validation/back_cover_development_v1/backplate_load_v1 validation/backplate_convergence_development_v1/backplate_load_2mm_v1 --out outputs/backplate_convergence_new
```
