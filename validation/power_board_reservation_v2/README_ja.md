# 電源基板配置空間の検査 v2

縦置き80×25 mm案は4本のねじ先端と干渉し不採用。

寸法・位置はplan.json。基板領域と部品領域を既存8群の個別ソリッドと検査。基準は体積干渉なし、最小距離0.5 mm以上の公称比較。既存STEPのハッシュを照合してから実行した。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_power_board_reservation.py --layout vertical --out /tmp/board-reservation-v2
```

この矩形領域は配線済み基板ではない。98部品の配置配線、コネクタ、固定具、はんだ面、温度間隔、交換経路・全身動作・公差・変形は未確認。部品奥行16 mmにはフィルム品の公称13 mmが入るが、実装公差を保証していない。

既存の胴体外形・脚長・電池/UBEC位置は変更していない。v1/v2の失敗を残し、v3を機構との取り合い検討へ用いる。試作製造リリースではない。
