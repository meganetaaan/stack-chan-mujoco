# 逆流防止FETの駆動条件確認

結論：配線予算の3mΩを1.15mΩへ引き下げる根拠は得られなかった。3mΩ自体も25°C・所定VGS条件の比較値に留める。抵抗値の変更で前回の配線不足を通さない。

## 今回解消する不確実性と終了条件

現113部品候補のFET接続とメーカーの駆動条件を照合し、低抵抗値へ置換可能かを判断する。外付けゲートの保証範囲が見つからなければ、その不足を具体化して資料探索を終了し、仮想ゲート波形/未確定RCの掃引を追加しない。

## 接続の確認

`review_pololu_reverse_gate.py`は左右それぞれについて以下を検査した。接続整合の確認であり電気動作の合格ではない。

- eFuse pin6 OUT = Q_REVERSE pin1–3 S = INTERNAL_OUT
- Q_REVERSE pin5–8 D = SERVO_BUS
- eFuse pin7 DVDT → 未選定R_GATE → Q pin4 G
- 未選定C_GATEはGからGNDへ接続

測定/評価するVGSはREVERSE_GATE−INTERNAL_OUT。REVERSE_GATE−GNDでも、REVERSE_GATE−SERVO_BUSでもない。VDSはSERVO_BUS−INTERNAL_OUT。停止・電源消失・回生では各点の電位が別々に変わるため、ゲートの対GND電圧だけでストレスを評価しない。

## 資料上の限界

[TI TPS25981 Rev.D](https://www.ti.com/lit/ds/symlink/tps25981.pdf) §7.3.9/Fig7-8は共通ソースの外付けFET駆動を示す。しかし§6.5には今回のゲート負荷を伴う定常DVDT−OUTの定量的MIN/MAXを確認できない。§6.3のVIN+5Vはコンデンサ耐圧の条件で、ゲート電圧下限ではない。Fig7-7の内部ゲートとPGの説明も外付けVGS保証へ流用しない。

[Vishay SiSS80DN Rev.B](https://www.vishay.com/docs/77684/siss80dn.pdf) §Specificationsの抵抗最大値はVGS2.5Vで3mΩ、4.5Vで1.15mΩ、10Vで0.92mΩ。25°C、ID10Aのパルス試験条件が付き、実機の高温連続抵抗の保証ではない。しきい値電圧も大電流で低抵抗になる条件ではない。絶対最大VGS+12/−8Vは動作目標にしない。

TIのQODはINTERNAL_OUT側にある。逆流防止FETがOFFになるとサーボバスからこの抵抗へ流す経路は遮断されるため、QODだけでSERVO_BUSの残留電荷を排出できると扱わない。独立した放電・回生処理が必要な設計課題として残る。

## 次に満たす条件

|状態|必要な確認|現状|
|---|---|---|
|定常ON|実VGS下限と温度に対応したRDS(on)、熱損失|未成立|
|起動・再投入|既充電バスを含むVGS/VDS、突入、RCと電荷の整合|RC未選定|
|停止・入力消失|外付けFET停止時間、逆流、正負VGSストレス|未成立|
|過電圧・回生|入力側とサーボ側を区別したエネルギー経路、放電|設計未完了|

実測では差動測定で上記ネット間電圧を記録する。ただしRC・保護素子の設計不足を測定Issueへ移して閉じない。メーカーの定量条件が不足する候補を維持するならベンチでの特性確認が必要であり、それを全個体・温度の保証と混同しない。別駆動方式を採用する場合も低抵抗だけでなく停止と異常時の成立まで同時に判断する。

再現：`python software/sim/circuits/review_pololu_reverse_gate.py --out validation/pololu_reverse_gate_review_v1`

今回の結論による正式回路変更、BOM確定、Issueクローズはない。資料検査結果と回路の未成立を分けて記録した。
