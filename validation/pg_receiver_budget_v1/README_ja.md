# PG受信回路の選定比較

TPS259823のPGをTPS3700DDCRのINA+で受ける候補を定義。主遮断器PG→1 MΩ→INA+、INA+→330 kΩ→GND、PGを150 kΩでLOGIC3V3へプルアップする。OUTAは10 kΩプルアップし起動監視のSchmitt入力へ渡す（受信部未選定）。RESET_Nへ直結しない。端子接続は`schematics/power/pg_receiver_candidate.json`。

目的はPGの停止時Lowと成立時Highを受信可能かの判断。終了条件は公表条件を用いたDC分離と負荷比較を行い、残る保証範囲を明示すること。未知のサーボ負荷や時間波形の掃引はしない。

64公差端点の節点方程式から、検出入力High下限0.6411 V、Low上限0.2042 V。比較する上昇しきい値最大0.404 V／下降最小0.387 Vを分離する。PG吸込負荷の保守上限22.874 µAは26 µA規定点以下。抵抗は総合±1%を仮置きし、部品・温度・基板漏れを確定した保証ではない。

根拠：[TPS25982](https://www.ti.com/lit/ds/symlink/tps25982.pdf) p9、[TPS3700](https://www.ti.com/lit/ds/symlink/tps3700.pdf) p4〜7。後者の入力電流±25 nAはVI=6.5 Vの条件、PG漏れ1.7 µAは5 V／10 kΩ条件。今回の電圧へ比較適用しており、全動作域の保証と表現しない。PDF SHAはreport.json。

TPS3700の電源立上り後最大450 µsは判定未確定。既存ラッチの遅延が長いというだけで、全投入順序の保護を合格にしない。POR未満、出力受信しきい値、停止伝搬時間、PG固着High・配線断線の扱いも未解決。OUTAは開放時Highになるため、断線を正常と判断する経路を残す。この回路単体で独立保護を成立させたとはしない。

## 再現

```sh
curl -fsSL https://www.ti.com/lit/ds/symlink/tps3700.pdf -o /tmp/pg-tps3700.pdf
curl -fsSL https://www.ti.com/lit/ds/symlink/tps25982.pdf -o /tmp/pg-tps25982.pdf
python3 software/sim/circuits/check_pg_receiver_budget.py --out /tmp/pg-receiver-review --detector-pdf /tmp/pg-tps3700.pdf --efuse-pdf /tmp/pg-tps25982.pdf
```

出力先は新規。これはDC計算であり、過渡回路シミュレーション／実測ではない。#24の実部品化を一段進める候補で、Issue未完了と通電保留を維持する。
