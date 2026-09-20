# 背面板の取付面を分割したメッシュ

従来の解析では、面三角形の重心が円内にあるかどうかで固定・荷重の対象を選択していた。3段階メッシュの最大主応力差が12.6%となったため、その近似の影響を分離する。

`mesh_backplate_patches.py`はCADカーネルで内面に12個の環状領域を作る。四隅は外半径4.6 mm・穴半径1.65 mm、支持部の荷重面は外半径6 mm・穴半径1.7 mm。円盤と板を分割した後、板の境界に属する環状面だけを抽出し、穴内に残る円盤を荷重面から除く。板の体積変化1×10⁻⁶ mm³未満、各面積と解析的な環状面積との差1×10⁻⁶ mm²未満を検査する。

対象面はGmshのphysical groupとして保存し、有限要素ソルバーはその面IDを使う。隣接三角形の重心で範囲を再選択しない。インポート後の領域が板の外部境界に属することと、環状面積誤差1%未満も検査する。形状関数は二次だが、幾何境界は直線の弦で近似するため、板内部の要素寸法だけでなく円周分割数も増やす。

最初の円周32分割メッシュは細かい寸法を内部へ拡張し215,888要素になった。解析中にメッシュ規模を確認し、その解析は中断した（完了結果なし）。境界の細分寸法を内部へ拡張しない設定に変え、円周32分割・板内部3 mmでは18,434要素となった。環状面積誤差はどちらも0.6413%であり、領域精度を落として要素数を減らしたものではない。

3 mm・円周32分割の同時荷重では最大変位0.023008 mm、最大絶対主応力11.75894 MPa。左右単独解の重ね合わせは一致し、四隅反力との釣り合い残差も最大1.92×10⁻⁸未満。従来の単一領域APIについて、保存済み6単位解との変位・応力・荷重・反力の一致を確認した。

次段階は板内部2 mm・円周48分割、さらに1.5 mm・円周64分割。評価基準は既存の変位0.2 mm、応力120 MPa、最後の2段階の変位差5%・応力差10%。単一荷重時刻、理想固定、追加質量未反映という制約は変わらない。接触・締結・胴体の柔軟性を証明するものではない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_back_cover.py --step validation/back_cover_development_v1/backplate_2mm_v3/rear_structural_plate.step --material-config board/mechanical/engineering/backplate_material.json --conformal-patches --mesh-mm 3 --circle-points 32 --out outputs/backplate_conformal_3mm_new
```

## 3段階の結果：収束不合格

| 内部寸法 / 円周分割 | 要素数 | 最大変位 mm | 最大絶対主応力 MPa | von Mises MPa |
|---|---:|---:|---:|---:|
| 3 mm / 32 | 18,434 | 0.023008 | 11.75894 | 11.48372 |
| 2 mm / 48 | 36,886 | 0.023121 | 13.48041 | 12.07575 |
| 1.5 mm / 64 | 61,909 | 0.023213 | 21.18892 | 14.50916 |

最後の2段階の差は変位0.396%、主応力36.38%、von Mises16.77%。各段階の値自体は許容範囲内だが、応力の収束は不合格。1.5 mmの主応力最大点は(x,y,z)=(-62.272,56.438,11.826) mmで、四隅固定領域の縁付近。3 mmの最大点は荷重面の穴付近、2 mmは別の隅に移っており、変位の安定だけで局所応力の妥当性を判断できない。

面重心による領域選択をなくすだけでは問題を解消できなかった。実際の座面接触・ねじ・ボスの柔軟性を含むモデルを作り、幾何近似・局所要素品質と境界条件の影響を切り分ける。応力最大点を除外して合格にしない。

証跡は`validation/backplate_patch_development_v1`。3 mmの実行時には円周分割のCLI指定がまだなく固定値32だったが、保存コードの既定値32で同じ設定を再現できる。`physical_group_compatibility_v1`は既存の6単位解との回帰確認であり、独立ソルバーによる新たな検証ではない。

```sh
.venv-engineering/bin/python software/sim/structural/check_backplate_convergence.py --analyses validation/backplate_patch_development_v1/backplate_conformal_3mm_v2 validation/backplate_patch_development_v1/backplate_conformal_2mm_v1 validation/backplate_patch_development_v1/backplate_conformal_1p5mm_v1 --out outputs/backplate_patch_convergence_new
```
