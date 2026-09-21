# 先端逃げ比較は不採用 — 元CADの穴を確認

局所穴R1.6、Z=-12.81〜-12.0 mmの切削候補を生成した。片足3.244661 mm³を除去し、ナット受け面を維持したが、この加工を必要とする前提が誤っていた。

元CADの全8ねじ軸で、半径1 mm・Z=-13.4〜-12.0 mmの先端包絡と交差0。ナット室上端Z=-12.8 mmを閉じた天井と見なした前回の一次元計算は、既存のねじ穴を無視していた。追加加工案は採用せず、現行組立はrevCのままとする。

これは公差後の穴径や軸ずれ、ねじ先端・不完全山、ナット強度、最終ねじ長を承認する結果ではない。誤判定と加工候補を履歴として残す。

再現（リポジトリ直下）:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_original_boot_tip.py
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_boot_tip_relief.py --out /tmp/boot-tip-relief
```
