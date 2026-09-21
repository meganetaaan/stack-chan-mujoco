# 手動復帰候補revH

revGへU14 74AUP1G06GW、入力プルアップR14、局所バイパスC14を追加。43部品150端子。SEQUENCE_CLEAR_REQUESTがHighならRESET_NをLowへ引く。入力開放時の既定要求はHigh。駆動元の実装・クリア時間の保証は未完成。

静的比較と限界：`validation/sequence_clear_sink_v1/README_ja.md`。従来のPG受信部・ENクランプ・手動許可接続は変更していない。電源喪失時の独立停止をこの出力段で代替しない。通電／製造リリースなし。

再現：`python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --clamp-cause --permission-gate --pg-receiver --clear-sink --out /tmp/manual-rearm-revH-review`。
