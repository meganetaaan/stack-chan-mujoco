# 左右独立PG受信回路の比較案

既存revIのU12/U13、R10〜R13、C12/C13を左右へ展開した16部品46端子。
抵抗・コンデンサの型番は既存の候補選定表から取得。新規に仕様適合を保証するものではない。
左右間の共有ネットはLOGIC3V3とGNDのみ。接続はconnectivity.json、端子一覧はpins.csv。

再現：
```sh
.venv-engineering/bin/python software/sim/circuits/export_dual_pg_receiver.py --out /tmp/dual-pg
```

LEFT/RIGHT_EFUSE_PGは各遮断ICのPG出力へ、LEFT/RIGHT_PG_CONDITIONEDは起動回路へ接続する候補。
後者は電源遷移中の有効性まで保証したVALID信号ではない。
監視回路の有効性確認を伴って初めてsequencerのLEFT/RIGHT_PG_VALIDとして扱う。
既存単一受信回路は統合時に置換する。元の8部品へ16部品を追加して三重に数えない。

主回路への統合、左右PGの出力仕様、入力断線・High固定、部分給電、合計消費電流、
故障捕捉時間と独立UV/OV監視は未完了。ネット分離確認はERC・回路動作確認ではない。

TPS25981の定常PGレベルとの比較は`validation/dual_pg_25981_dc_v1/`。
High/Lowの条件付き分離は確認したが、電源遷移・故障捕捉の適合は未完了。
