# 左右の共通EN接続

revCのMAIN_EFUSE_ENを左右TPS259813Lの1番端子へ接続した。72部品・249端子を維持。U8→4.7 kΩ→共通EN、ENに39 kΩプルダウン、U10 RESETがENをLowへ引く。左右の電源出力を短絡する変更ではない。

既存のLOGIC3V3/STOP_AUX3V3区間3.207〜3.393 V、抵抗総合±1%を条件に、両ENの漏れ計0.2 µAとU10 RESET漏れ0.3 µAを含めて評価した。High下限2.764712 V、必要上限しきい値1.224 Vを上回る。High時のU8出力負荷は100 µA規定内。Lowを強制するU10の吸込み上限0.729407 mAは、VOL最大0.4 Vを規定する1 mA以内。出力OFFしきい値最小1.073 Vに対し0.673 Vの余裕。

根拠:
- TPS25981 SLVSGG6D、6.5: https://www.ti.com/lit/ds/symlink/tps25981.pdf
- TPS3808 SBVS050N、6.5: https://www.ti.com/lit/ds/symlink/tps3808.pdf
- 74LVC1G17 Rev16.1、表7: https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf

最低消費状態のしきい値最小0.45 Vに対しては0.05 Vしか余裕がなく、配線のGND差を無視して最低消費電流を保証しない。ここでの判定対象は定常の出力OFF。

## 残件

- コマンドと停止クランプが正しい時点で発生することを仮定した出力段の計算。U9/U11入力、起動状態回路、途中電圧、立上り順序、短パルスは未確認。
- ENを論理制御に使用するため、変換器出力の低電圧判定は独立監視側で設計する。内蔵IN低電圧保護だけでサーボ電圧の適合を主張しない。
- 共通EN配線の固着・断線・部品故障、停止遅延と出力残留エネルギーは未評価。
- 抵抗の型番・総合公差、LDO電圧区間、コンデンサ・総電流は未確定。

定常インターフェースの確認であり、完全な既定OFF回路や保護合格ではない。

再現:

```sh
.venv-engineering/bin/python software/sim/circuits/connect_common_servo_enable.py --out /tmp/common-servo-enable
```
