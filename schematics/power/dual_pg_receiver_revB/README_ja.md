# PG配線の断線時にLowへ落とす配置候補

revAのプルアップR10を各eFuseのPG端子側へ置き、PG_SOURCEから受信側EFUSE_PGまでの配線を
interconnectsに明記した。これらは導通するPCB配線で、追加抵抗や未接続ネットではない。
R11/R12は受信側に配置。16部品46端子は不変で、部品型番もrevAを継承する。

配線が導通する公称状態ではrevAと同じ回路。PG_SOURCEから受信部までの断線時は
プルアップが受信部から切り離され、受信分圧下側抵抗でLowへ落ちる。
`validation/pg_trace_open_v1/`の定常比較では最大8.3325mVで、立下り閾値最小387mV未満。
受信側にプルアップを残す旧配置なら、この断線でHighになり得るため採用しない。

eFuse端子とプルアップの間の断線、High固定、GND断線、入力部品故障は未対応。
時定数と電源遷移の適合は未評価。PCB実配線の検査前であり、全断線対応とは扱わない。

```sh
.venv-engineering/bin/python software/sim/circuits/export_dual_pg_receiver.py --out /tmp/dual-pg-revB
.venv-engineering/bin/python software/sim/circuits/check_pg_trace_open.py --out /tmp/pg-open
```
