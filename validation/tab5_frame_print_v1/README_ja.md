# 座ぐりを反映した圧入前の枠

carrier_print.stepはインサート用直径4 mm下穴とTab5ねじ頭部の直径6 mm座ぐりを持つ、圧入前の設計候補。圧入後表示用の穴をそのまま造形する取り違えを避けるため、別ファイルとして保存する。

旧圧入前枠から154.193 mm³を除去。単一の有効ソリッド、体積22855.096 mm³。この枠に前回と同じインサート円筒除去を施すと、座ぐり追加済み圧入後近似と対称差体積0 mm³で一致する。

製作承認ではない。Tab5ねじ深さ、締付け、座面/根元強度、ABS/PETGの実造形条件・下穴補正と保持能力は未確認。ファイル名のprintは圧入前形状を区別する目的で、今すぐ印刷して組み付けてよいという意味ではない。正式CADの指し先は変更しない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_tab5_frame_print.py
```
