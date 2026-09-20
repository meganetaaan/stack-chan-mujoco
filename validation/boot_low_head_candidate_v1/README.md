# 低頭ねじと足裏収納の候補

[NBK SLH-M2-6](https://www.nbk1560.com/en-US/products/specialscrew/nedzicom/socketheadcapscrew/SLH/SLH-M2/)を寸法検討候補とした。公称頭径3.8 mm、頭高さ1.3 mm、長さ6 mm、六角穴1.3 mm。寸法公差はこの表から確定していない。

収納深さ2.2 mmを維持し、半径を2.3から2.4 mmへ拡大した。左右のブーツと足裏は有効な単一ソリッド。足裏の公称残厚0.8 mmは維持するが、耐荷重・摩耗・局所座屈は未評価。

印刷による収納縮小0.2 mmを仮定した場合、公称ねじに対して軸方向0.7 mm、半径方向0.3 mmの余裕。さらに頭高さ・頭径のそれぞれに+0.1 mmを仮定すると0.6 / 0.25 mmとなり、残余0.2 mm基準に条件付きで合格。+0.1 mmは供給者公差ではなく感度条件であり、最悪公差保証とは区別する。

掲載の最大締付けトルク0.3 N·mを樹脂部品の許容トルクとして使用しない。ねじ長公差、不完全ねじ、座面とナットの強度、印刷中のナット挿入、工具、足裏保持・着脱は未完了。正式BOM採用および製造承認なし。

## 再現

`python3 validation/boot_low_head_candidate_v1/check_clearance.py`

CADはengineering環境でLD_LIBRARY_PATHに.tools/root/usr/lib/x86_64-linux-gnuを設定し、generator.py --out <未作成出力先>を実行する。寸法の出典と感度仮定、CAD入力SHA、結果を保存した。
