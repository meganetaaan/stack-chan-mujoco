# 実ナット寸法に合わせた幅4.6 mm比較

PTS A56202を外装用8個の寸法候補とした。メーカー販売ページはM2×0.4、二面幅3.70〜4.00 mm、厚さ0.80〜1.20 mmを示す。2026-09-21確認。最低注文数500個で、小量調達先は未確定。質量・許容締付け力は未取得。

出典: https://www.pts-uk.com/products/nuts/square-nuts/metric-a2/a56202

v1の4.4 mm幅は既存の各面±0.2 mm仮定で幅余裕0となるため、仮定を変更せず幅4.6 mmへ変更した。高さ1.8 mmは維持。最大ナットに対し誤差後の総隙間は幅0.2 mm、高さ0.2 mm。片側隙間ではない。実造形の合格証拠でもない。

最小二面幅3.7 mmの正方形対角は約5.233 mm、最大開口幅は5.0 mm。この単純モデルではねじ軸を中心とする全周回転はできない。ただし角の形状、壁の変形、ねじ締付け反力、開口方向への逃げを含む回り止め強度の保証ではない。

8経路すべてで公称の連続掃引交差0、左右とも単一ソリッド、受け面より下の除去0。片足の除去49.392 mm³。v1より8.208 mm³増える。強度や工具空間は未確認のため、統合CADのrevDはまだv1のまま。採用時に組立・慣性を更新する。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_boot_nut_side_entry.py --slot-width-mm 4.6 --out /tmp/boot-nut-v2
.venv-engineering/bin/python software/sim/structural/check_boot_nut_slot_budget.py
```
