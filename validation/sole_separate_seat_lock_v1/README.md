# 別体スペーサーによる足裏固定候補

外径4、内径2.3、厚さ0.9 mmの別体スペーサーを、足裏スライド後に下側から挿入。ねじはヨークとスペーサーを締結し、TPUへの直接の締付圧縮を避ける。名目ねじ頭沈み0.8 mm、ナット先端突出1.1 mm。材質・製品公差・締付力は未選定。横荷重はねじ軸・スペーサー・TPU孔へ伝わるため各接触強度が必要。

両候補とも完成状態の部品重複と下側工具包絡のみ確認。別体座の挿入経路、公差・摩耗・TPU変形後の床クリアランス、抜け・せん断強度は未検証。製造リリース前。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_sole_slide_lock.py --rigid-seat --separate-seat --out outputs/seat_lock_repro
```
