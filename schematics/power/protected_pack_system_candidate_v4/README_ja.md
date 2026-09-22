# 196部品: クリア入力の波形整形候補

194部品v3に74LVC1G17GVと100 nFを追加した接続候補。製造リリースではない。

MCU PA4 → CTRL_RESET_RELEASE_N（CTRL3V3へ10 kΩ）→ 74LVC1G17GV → SN74LVC1G07DBVR → SYS__SEQUENCE_CLEAR_REQUEST → 既存74AUP1G06 → RESET_N。

新バッファはCTRL3V3で動作し、SC-74Aピン1 NC/2 A/3 GND/4 Y/5 VCC。既存OD段の入力のみ接続変更し、他の旧194部品のピン接続を保持した。新部品を含め196参照が一意。通常有効電源時の極性は従来どおり、MCU High/開放でクリア要求、Lowで他のリセット条件による解除を許可する。電源遷移中の保証を意味しない。

[入力不適合の根拠と再現](../../../validation/sequence_clear_input_v1/README_ja.md)を参照。入力速度無制限は[Nexperia Rev.16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)の条件による。これは出力速度、ブラウンアウト、全保護の成立証明ではない。

未完: 整形段の出力負荷・速度とDC余裕、MCU端子のリセット条件、OD出力RCと漏れ、全リセット負荷、電源遷移、電流・容量予算。以前のPSpiceデッキの負荷値は本候補を含まない。4未接続信号境界も引き継ぐ。製作HOLD。
