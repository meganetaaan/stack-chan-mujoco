# 高精度電源の周波数・ブートストラップ抵抗候補

目的は未選定のRT/RBOOTを具体化し、局所出力容量の必要条件を固定すること。追加波形で仮定を通す作業は行わず、設定値の算術と部品仕様を照合して終了する。

[TI TPSM63610 RevA](https://www.ti.com/lit/ds/symlink/tpsm63610.pdf)の5V例は1MHz、表7-1の推奨範囲は500〜1400kHz。式5からRT15.8kΩを選ぶと公称0.997992MHz。抵抗初期±0.1%だけの変動は0.997033〜0.998952MHzだが、発振器自身の誤差・抵抗温度/経時変化を含む保証範囲ではない。

RTはpin12−AGND、RBOOTはpin2−pin3に100Ωとする。後者はTIの効率/EMIの妥協案を出発点にした。最終的なパルス損失・温度・EMI適合は未確認。RBOOTを対GNDへ接続しない。

[Vishay TNPW仕様](https://www.vishay.com/docs/28758/tnpw_e3.pdf)の0603、±0.1%、25ppm/K、標準包装の範囲/品番体系から、TNPW060315K8BEEAとTNPW0603100RBEEAを候補とした。各2個。調達可否と製造BOM確定は別。品番候補と接続は `schematics/power/precision_passives_candidate.json`。

## 容量の配置と評価条件

5Vでは局所COUTの実効合計75µF以上が必要。TI例のGRM32ER71A476ME15Lを3個なら公称141µFで、総残存率53.19%以上が必要になる。仮に初期公差−20%を別に控除する感度計算なら、その他要因で66.49%以上が必要。これはサプライヤのDCバイアス/温度/経時特性を確認済みという意味ではない。CFFは表7-1の22pFを値候補とし、型番未選定。

COUTはREGULATOR_OUT−PGND、つまり下流eFuse/逆流FETの手前へ置く。サーボ電源をOFFにすると切り離される容量を、コンバータの必要局所容量に算入しない。逆にこの局所容量を、サーボ側常設放電抵抗の対象容量へ無条件に加えない。ON時には接続される下流容量と負荷がループ安定性・突入へ影響するため、その状態は別途評価する。

入力は最低10µF×2というTI推奨を出発点に、VIN1/VIN2それぞれの近傍とPGND帰路を必要とする。入力電圧/リプル電流/ダンピング未確定のため型番と合否は未確定。

再現：`python software/sim/circuits/check_precision_passives.py --out validation/precision_passives_candidate_v1`

残る設計はEN/UVLO、実品コンデンサ/分圧、負荷時入力、熱/実装、起動/負荷過渡/回生。今回の周波数・抵抗候補の追加による通電リリース、現行Pololu回路置換、Issue完了はない。
