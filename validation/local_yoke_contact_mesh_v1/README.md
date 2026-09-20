# 実ヨーク形状の局所接触メッシュ

新ヨーク左後取付部をx=[−38,−30],y=[−18.5,−10.5],z=[−19,−16] mmで切り出した。ブーツ支持面の半径3 mm環状面と、ねじ頭座面の半径1.9 mm環状面を分割し、物理グループboot_contact/head_bearingとして保存。中央穴半径は1.15 mm。

CAD面積はそれぞれ24.119577598 / 7.186393195 mm²。体積を変更せず、1/0.7/0.5 mmの3メッシュで面積誤差は最大0.642%となり、事前基準1%以内。固定ブロックの代わりに実ヨークの局所弾性を解くためのメッシュ準備である。

まだブーツと組み合わせた接触解ではない。切り出し側面は周辺ヨーク剛性を省略しており、金物の公差・丸み・予圧・荷重分担・クリープ・全身の歩行荷重は未反映。強度・製造承認なし。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_local_yoke_contact.py --out outputs/reproduce_local_yoke
```

未作成出力先を指定。実CADのSHA、局所STEP、面積・体積保存の判定、全メッシュを同梱。
