# 左右PGを統合した手動再始動回路の比較案 revJ

revIの単一PG受信8部品をrevBの左右受信16部品で置換し、54部品182端子にした。
残る38部品の接続・属性はrevIと一致。旧PG信号の残存なし、左右配線の両端を確認。
interconnectsの2配線は導通するPCB配線で、ネットリスト化で省略しない。

この統合はPG受信部に限定。既存のMAIN_EFUSE_ENは単一駆動のままで、
左右の給電制御全体を完成させたものではない。UV/OV監視と起動状態回路も未実装。
従来の電気特性比較を回路全体へ拡張して合格とはしない。

```sh
.venv-engineering/bin/python software/sim/circuits/integrate_dual_pg_manual_rearm.py --out /tmp/manual-rearm-revJ
```

assembly.json、pins.csvは接続候補。実装基板やERC済み回路図ではない。
候補BOMの旧revI部品と重複して購入・合算しない。
manual_rearm_current.jsonの確定対象はまだ切り替えず、比較候補として参照する。
