# 埋込みナットと低頭ねじの公称配置確認

低頭ねじは公称頭径3.8、高さ1.3、軸径2、首下長さ6 mmの包絡として配置。角ナットは最大対辺4、厚さ1.2 mmの角柱から直径2 mmのねじ包絡を除いたモデル。公称値の出典はvalidation/boot_low_head_candidate_v1/source_review.json、validation/boot_fastener_dimension_review_v1/source_review.json。ねじ形状や面取りを再現したメーカーCADではない。

左右8取付位置すべてで、ねじ・ナットとブーツ・ヨーク・足裏の体積重なりは0 mm³。ねじとナット間のねじ山接触はモデル化せず、ねじかかり・締結強度は判断しない。

ブーツを+Z方向に造形し、z=−12.8 mmで停止する仮定で、停止時点までの形状を半空間で切り出した。ナット底面をz=40から−14.6へ下ろす間の全ナット包絡を包含する4×4×55.8 mmの直方体と、造形済み形状との干渉は全8箇所で0 mm³。離散姿勢検査ではなく、この軸方向挿入の包絡確認である。

公差、ナット傾き、挿入工具・ノズル・ベッドとの干渉、造形途中の支持、再開後の屋根造形、回り止め・引抜き・予圧・疲労、足裏の着脱保持は未確認。この結果は製造や組立工程全体の承認ではない。ナットの公称最大寸法を使った直進経路に限定する。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/check_captive_boot_hardware.py --out outputs/reproduce_captive_hardware
```

未作成の出力先を指定する。事前条件、入力SHA、部品別干渉と各金物包絡STEPを保存した。
