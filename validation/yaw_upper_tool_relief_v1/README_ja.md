# AF4工具候補に合わせた上面補強の逃げ

Wera 2069 Micro 05118120001を工具候補とする。メーカー資料：
https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05118120001.pdf
対辺4 mm、軸径5.7 mm、軸長60 mm、柄長97 mm、全体157×13×13 mm。
公表寸法は製造公差の保証ではない。ソケット深さ・入口面取り・許容保持トルクは未確認。

追加した上面補強だけのねじ逃げ半径を3.3→4.0 mmへ変更。
元の支持部・金属取付板・ねじ位置は維持。片側追加体積4561.042 mm³。
組立外形不変、固定部品・メーカーサーボへの追加干渉なし、ポート通路1.3 mmを維持。
この変更後の剛性は未評価で、以前の変形合格を転用しない。
正式候補v6を上書きしない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_upper_tool_relief.py --out /tmp/yaw-upper-tool-relief
```
