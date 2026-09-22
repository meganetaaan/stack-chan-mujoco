# 入力フィルムコンデンサの配置候補

80×25 mm基板の中央、ローカル(u,v)=(40,12.5) mmにC_STOP_INを配置。部品候補MKS2C042201K00JSSDの公称胴体7.2×7.2×13 mmと5 mmリードピッチを使用した。基板から0.5 mm浮かせ、背面リード突出1.5 mm、穴φ0.8 mm・パッドφ1.6 mmは設計仮定。

胴体は予約奥行16 mm内に入り、既存8群・基板への体積干渉なし。4取付穴周辺の6 mm角禁止領域からも外れる。KiCadで6穴を認識してSTEP出力し、機構CADとの基板体積差を確認した。KiCadには部品3Dモデルを埋め込んでいないため、部品包絡は別のC_STOP_IN.stepで確認する。

KiCadの端子1=STOP_LDO_INPUT、2=GNDを設定。銅箔接続は未配線。回路98部品中、実配置した電気部品はこの1個のみ。完成基板の搭載・熱・製造性を証明したものではない。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/place_stop_input_film.py --out /tmp/film-placement
kicad-cli pcb export step --output /tmp/film-board.step /tmp/film-placement/power_placement.kicad_pcb
```

実部品公差、はんだフィレット、基板穴公差、曲げ・振動保持、固定具と配線は未確認。部品外形を理由に筐体や脚長は変更していない。製造リリースはfalse。
