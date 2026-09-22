# 停止入力のローカル抵抗網

左右SHDNへ各1kΩ直列・10kΩプルダウンを追加した。外部ポートは共通ドライバ入力へ集約したが、ドライバ本体は未選定。既存MAIN_EFUSE_ENへそのまま追加すると負荷条件が変わるため接続しない。

抵抗総合±1%の比較で、SHDN=0.4Vにおける正方向漏れ許容は合計39.60µA。IC側の8µAを引くと外部ドライバ側31.60µAが残る。ドライバHIGH下限を2.4Vとする設計要求では、SHDN=2.1Vに達するために許される入力吸込みは84.91µA。これはドライバを確認した値ではない。

[LT4363 Rev.C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf)のSHDN境界条件に基づく静的検討。電源低下中のIC/ドライバ状態、HIGH入力電流、リセット期間・クールダウン、出力固着は未確認。プルダウンだけで停止保証とはしない。実部品抵抗の選定・温度配分も未完了。

再現：`.venv-engineering/bin/python software/sim/circuits/add_series_shutdown_network.py --out /tmp/series-shutdown-review`。
