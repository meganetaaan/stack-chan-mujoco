# ナット公称接触面だけに荷重を与えた局所FE比較

検証済みのnut_bearing面へ20 Nの下向き合力を与え、pad_bottomをnormal_zで支持した。1、0.7、0.5 mmの3メッシュを使用。最細で変位0.002439384 mm、最大絶対主応力2.244843 MPa、von Mises応力1.910846 MPa。事前の変位・応力・最後2メッシュ変化率の4条件を満たした。

同じ支持条件でナット空間底面全体へ荷重を分散したモデルと比較すると、変位は約25%、最大主応力は約20%増加。面分割によってメッシュ自体も変わるため、差の全量を荷重範囲だけの影響とは断定しない。荷重を広げた近似の結果を、実接触面の結果として流用しない。

公称接触範囲への分布荷重であり、圧力分布を解く接触解析ではない。支持は引張反力も許し離間を扱わない。切り出した左後座のみ、等方線形弾性、仮の20 N荷重。実際の予圧や他座面、EPIC3/4の歩行荷重、クリープ、異方性、座屈は未検証。締結強度・製造承認なし。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/screen_boot_nut_patch.py --out outputs/reproduce_nut_footprint_fe
```

新規出力先を指定。メッシュはvalidation/boot_nut_patch_development_v1、今回の変位・応力配列と荷重整合・残差・エネルギーは本フォルダに保存。
