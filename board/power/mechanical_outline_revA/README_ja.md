# 電源基板の機械外形候補

80×25×1.6 mm、M2向け候補穴φ2.4 mmを4箇所。各穴周囲6 mm角を両面の配線・部品禁止領域に設定した。穴径・禁止領域は設計仮定であり、ねじ・ナット・固定具の採用は未確定。禁止領域を除く平面積1856 mm²が残るが、98部品が配置配線できる証明ではない。

ロボット座標への変換と穴座標はdimensions.json。位置は配置空間v3内に保ち、外形を広げていない。機構向けSTEPはロボット座標、KiCadファイルはローカル平面の基板データ。

KiCad 7で読込み、SVGおよびSTEPへの出力を確認。KiCadは4穴と1.6 mm厚を認識し、出力STEPと機構CADの体積差はverification.jsonのとおり。電気回路・銅箔・配線のDRC合格ではない。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_power_board_outline.py --out /tmp/power-board-outline
kicad-cli pcb export step --output /tmp/power-board-check.step /tmp/power-board-outline/power_outline.kicad_pcb
```

未完了：取付先と固定具、強度、配線・コネクタ、はんだ面の突出、全回路の適合。基板製造へ発注するデータではない。
