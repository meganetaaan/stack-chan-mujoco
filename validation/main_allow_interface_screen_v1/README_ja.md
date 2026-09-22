# 主起動許可インターフェースの静的比較

送信側SN74LVC1G08の電源0 V時Ioff最大10 µAと、受信74LVC1G17の入力漏れ最大1 µAを同じ向きへ合算し、10 kΩ＋総変動1%で入力0.1111 Vを得た。共通GND、追加漏れ/蓄積電荷なしという静的比較。受信電源1.8/2.3/3.0/4.5/5.5 Vの表にある下降閾値下限を下回る。表の間の電圧やブラウンアウト時へ保証を外挿しない。

追加入力プルダウンの負荷を3.6 V/9.9 kΩ＋入力漏れ1 µAで配分すると0.364636 mA。CTRL側の既知部分電流予算は16/32/64 MHz比較で6.005/8.005/11.405 mAとなる。全最大電流ではなく、前の未計上項目は継続。旧11.041 mAを最新接続の全負荷として使わない。SYS側にはバッファ静止電流、動的/中間入力電流、追加100 nFの充電を別計上する必要がある。既存の出力10 kΩは二重に追加しない。

電源断バッファのIoff 2 µAだけなら出力側10 kΩで20.2 mV相当だが、これはノード全体の上限ではない。後段SN74HCS11の電源断入力漏れは、VCC=6 Vでの漏れ規定を流用できないため未確定。双方通電時の全公差信号余裕、0<VCC<動作下限の出力、RESET保持と復帰順序は未検証。インターフェース全体は未合格、製作HOLD。

根拠：
- [TI SN74LVC1G08 RevAA](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf) §5.5/7.3.2。
- [Nexperia 74LVC1G17 Rev16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf) §10/10.1、-40〜125℃列。
- [TI SN74HCS11 RevB](https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf) §5.5の漏れ試験条件。

判定条件はplan.json、部品接続/BOMと以前の電流予算のハッシュはreport.json。未知項目をゼロとして波形を生成していない。

```sh
.venv-engineering/bin/python software/sim/circuits/screen_main_allow_interface.py
```
