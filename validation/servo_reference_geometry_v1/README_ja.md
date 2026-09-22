# X330メーカー形状の確認

ROBOTIS eManualの図面リンクからPDFとSTEPを取得。PDFの1ページを描画して確認した。図面は2020-05-28の参考図で、公差付き製造図ではない。ケース20×34×23mm、側面の2コネクタを確認。コネクタ基準位置・ケーブル出口の寸法は未記載。

STEPは妥当な15ソリッド。図面との外観対応からソリッド13・14が左右のコネクタ候補で、範囲はX=±6.1〜±9.9、Y=-14〜-4、Z=-16.4〜-7.2mm。ただし範囲中心を嵌合面やケーブル出口と同一視しない。STEPの出力軸・ケース面を現行モデルへ合わせる変換と、挿入済みEHRハウジング／曲げ逃げの追加が次の作業。

メーカー元データはリポジトリへ複製せず、取得URLとハッシュ、派生した形状範囲を記録した。モデル・経路の変更はまだ行っていない。

再現：report.jsonのdownload_urlからSTEPを取得し、次を実行する。
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/inspect_servo_reference.py --step /path/to/XL-XC-330.stp --out /tmp/servo-reference-review
```
