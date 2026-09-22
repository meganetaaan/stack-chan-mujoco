# 補助起動SHDN接続の静的比較

TPS26601のSHDNはシステムGND基準でGPIOから制御するメーカー例がある。RTNは内部制御回路の基準で、GNDへ短絡しない。現在のPACK_RETURN基準の制御出力を、既存1 kΩ直列抵抗からSHDNへ接続する候補とする。10 kΩプルダウンはPACK_RETURNへ維持。

抵抗の総変動±1%を仮置き。ドライバーの3 V条件のVOH/VOL規定と、10 µAの漏れ配分を使う比較では、SHDN High2.169 V、Low0.373 V。比較基準High>=1 V、Low<=0.4 Vを満たす。送信電源0 V時は10 kΩが0.4 Vで39.60 µA吸い込み、eFuse10 µA＋送信Ioff10 µAの配分を上回る。

ただしTPS2660の10 µAはSHDN0.4 V条件の規定で、他電圧へ同じ大きさを割り当てた部分は設計仮定。全公差の保証値ではない。SHDNの動的入力、3S範囲、ドライバーの電源立上り/降下、ラッチ/リセット、残留電力と逆接過渡の包絡は未検証。信号基準の確認と静的候補の選定までであり、全状態合格ではない。

追加されるCTRL出力負荷の比較配分は3.6 V時0.341 mA。旧起動プローブの11.405 mAにはまだ含まれないので、同プローブを最新全負荷と扱わない。

根拠：[TPS2660 RevG](https://www.ti.com/lit/ds/symlink/tps2660.pdf) §7.1/7.5/9.3.5.5/9.3.5.7、[SN74LVC1G08 RevAA](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf) §5.5。

```sh
.venv-engineering/bin/python software/sim/circuits/check_aux_start_connection.py
```
