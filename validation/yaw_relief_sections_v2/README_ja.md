# 配線ポートを外側1個に限定した開口比較

個別給電案は各サーボのポート1個だけを使用する。この既存方針に合わせ、左は外側Y=34mm、右はY=-34mmだけを開口する候補へ変更した。内側ポートの開口をやめても必要な12軸の接続数は減らない。内側ポートにはケーブルを挿さない。誤接続防止カバーは未設計で、カバーを加える場合は別の干渉確認が必要。

開口中央X=-14mm、厚さ0.1mmの有限スライスで断面積を比較。金属板は旧33mm²→両ポート20.2mm²→外側のみ26.6mm²（旧比80.6%）。支持棚のZ86〜100mm範囲は94.6→69.0→81.8mm²（86.5%）。他4断面もreport.jsonに保存。断面積比は強度比・剛性比ではない。

片側の除去体積は金属板75.989mm³、支持棚151.979mm³。単一ソリッド、追加外形なし、取付軸周辺材料保存を再確認。使用ポートのハウジング隙間1.640mm、予約通路隙間1.3mmを維持する。現行revB未更新。開口による荷重経路・変位・疲労と実配線の確認は残る。

再現：既存板生成に`--outside-port-only`、棚生成に同フラグと`--plate-dir validation/yaw_connector_plate_relief_v2`を付ける。断面比較は以下。
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/compare_yaw_relief_sections.py --plate-dir validation/yaw_connector_plate_relief_v2 --shelf-dir validation/yaw_connector_shelf_relief_v2 --out /tmp/yaw-sections-review
```
