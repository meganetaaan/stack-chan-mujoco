# 丸み付き座面端の候補

45度縁落としと平坦面の境界を接線連続にする案として、4本の円形縁にR0.05 mmフィレットを追加。外径5.95、内径2.35、厚さ0.85 mmの公差端条件を維持。平坦座面は外半径2.925・内半径1.225 mmで従来と同じ。CADは単一有効ソリッド。

これは製造リリースではない。半径0.05 mmは現行仕様案の最大縁落とし幅を使った比較候補で、半径の下限・公差・加工工具・検査方法は未確定。応力を通すために任意の丸みを付与して合格とはしない。CADが接線連続でも、三角形メッシュでは別途形状近似誤差の確認が必要。

従来の0.5 mmメッシュ設定では丸み追加面のCAD面積2.04794 mm²に対してメッシュ1.85178 mm²、誤差9.5787%。既存の1%基準外のため応力計算には使用しなかった。mesh/に失敗結果を保持。

curved_mesh/は曲率1周32分割相当、最小サイズ0.005 mmとした再生成の出力先。計算の完了と面積基準は同フォルダのreport.jsonで確認する。report.jsonがなければ未完了であり、合格として扱わない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_minimum_sole_spacer.py --rounded-edges --out outputs/sole_rounded_cad
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --curvature-points 32 --spacer-step outputs/sole_rounded_cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.5 --out outputs/sole_rounded_mesh
```

曲率指定なし・丸み指定なしの既定動作を維持。元の鋭い縁で圧力が未収束だった証跡は削除しない。丸み候補の接触平衡・収束・強度は未検証。

## 曲率32分割メッシュの完了結果

生成完了。丸み面積誤差0.116146%、ねじ頭座面1.096790%で、座面の1%基準を満たさず不合格。接触三角形は片側532,146個。丸みの改善をもって全体合格としない。強度計算には未使用。局所曲率の等方細分化により大規模化しており、次に座面境界の分割と要素数を見直す。

生メッシュ3個は合計約1 GiBのためgitに含めず、ローカルに保持。curved_mesh/mesh_inventory.jsonにサイズ・節点数・要素数・SHA-256を保存。上記コマンドで再生成できるが、ライブラリ版や並列実行条件によってバイト一致は保証しない。report.jsonは完了した検査結果。manifest_preliminary.jsonは完了前の履歴であり現在のREADMEのハッシュではない。
