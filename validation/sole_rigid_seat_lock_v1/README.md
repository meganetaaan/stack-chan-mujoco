# 一体筒座候補（組立途中干渉で不採用）

名目完成形状は干渉なしだが、0.9 mm突出する筒座が足裏スライドを妨げる。最大重複7.57045 mm³。slide_audit.jsonに失敗を保存。別体座へ改める。

両候補とも完成状態の部品重複と下側工具包絡のみ確認。別体座の挿入経路、公差・摩耗・TPU変形後の床クリアランス、抜け・せん断強度は未検証。製造リリース前。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_sole_slide_lock.py --rigid-seat --out outputs/seat_lock_repro
```
