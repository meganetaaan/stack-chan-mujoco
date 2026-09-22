# 左右電源監視を停止回路へ接続した194部品候補

v4のクリア波形整形回路を維持し、左右TPS3700のOUTA/OUTBを既存SYS__RAIL_HEALTH_Nへ接続。不要になる左右出力プルアップを削除した。旧194部品v3とは別の構成。

[判断・再現・未確認事項](../../../validation/source_window_reset_connection_v1/README_ja.md)を参照。電源投入・異常検出から遮断までの時間・部分給電での成立は未検証。製造ネットリストやPCBリリースではない。

TAB5_START_ALLOW、PACK_UV_WARN_N、左右REGULATOR_ALLOWの4信号は引き続き未接続。左右変換器の起動許可はSYSリセットに依存しない経路で設計する。既存CTRLの部分負荷表とPSpice v3はv4を基準とする履歴であり、本変更後の全電源評価ではない。CTRLに直結した部品変更はないが、SYS/STOP_AUXの負荷と停止時間は再評価する。
