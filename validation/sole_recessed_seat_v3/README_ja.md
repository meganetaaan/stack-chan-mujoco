# 溝端を開放した座面候補

v2で残った公称0.2mmの端壁を除去。溝の円弧中心をx43から44mmへ延ばし、
外面x47mmへ開放する。外形を増やす変更ではない。
座面1.6mmとヨーク公称残厚2mm、ねじの床側隙間0.8mmを維持。
左右とも有効な単一ソリッド。固定姿勢のヨーク・ブーツ・ねじ交差0、
スライド17姿勢で交差0。挿入を含む結果はrigid_sole_insertion_v4参照。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_sole_recessed_seat.py --slide-channel --open-channel-end --out /tmp/seat-open-end
```

端壁は保持要素として数えない。保持は頭部、座面、締結品で評価する。
ヨークの断面減少と座面の曲げ・締付け・クリープは未評価。
ワッシャ実部品未選定、連続経路・工具・公差の最終確認前。製造リリースではない。
