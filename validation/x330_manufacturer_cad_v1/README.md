# XL/XC-330メーカーSTEP

[ROBOTISダウンロードページ](https://robotis.com/service/download.php?no=1987)のJavaScriptが案内する[STEP実ファイル](https://www.dropbox.com/s/qlzmp8mlvzrxmzu/XL,XC-330.stp?dl=1)を取得した。HTML応答ではなくISO-10303-21形式であること、CadQueryで読み込めること、15ソリッドで形状が有効であることを確認した。原本は変更せず保存。出典とSHA256はsource.json。

メーカー座標系の全体外接寸法は20×34×29 mm。範囲はX[-10,10]、Y[-24.5,9.5]、Z[-22.5,6.50000016] mm。これはホーン等を含むファイル全体の寸法であり、仕様表のケース奥行26 mmと混同しない。回転軸・固定部・可動ホーン・アイドラーを分離してロボット座標系へ配置する必要がある。

円筒面の半径・軸方向・軸上位置をcad_inspection.jsonへ保存した。円筒面だけからねじ規格、部品名称、組立公差、許容荷重を推定してはいない。別部品間で同じ円筒軸が重複し得るため、面一覧をそのまま穴数と解釈しない。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/inspect_manufacturer_step.py \
 --step validation/x330_manufacturer_cad_v1/XL_XC_330.stp \
 --out outputs/x330_cad_inspection_repeat.json
```

次に部品と回転軸を識別して足首の軸包絡体を置換する。現段階では機体のCAD・質量・関節限界は未変更。金属ホーンHNX330-N101への適合は別途確認する。
