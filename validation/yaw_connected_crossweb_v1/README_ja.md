> 訂正: 統合後の部品別検査で固定ねじ4本との干渉が判明。形状の「追加干渉なし」は撤回する。変形計算の数値は保存するが、この形状を製作候補として採用しない。詳細は `validation/yaw_integrated_candidate_v3/README_ja.md`。

# 深い側面リブをつなぐ前端補強板

rail-seat候補に、X8..11.6、Y=cy±18、Z78..88mmの横板を追加した。前の外側横板案と異なり、既存の深いリブ（Xが10まで）と重なるため単一ソリッドになる。新しい固定点やレールの引張支持は追加しない。

事前の条件は外形不変、有効単一ソリッド、追加干渉0.01mm³以下、コネクタ通路1.3mm以上。左右とも通過した。追加体積は各1096mm³、メーカーサーボ形状との追加部分の距離3.5mm、通路1.3mm。左右の支持部同士を連結したものではなく、各支持部内の両側リブをつなぐ。

この形状検査は追加部分のみ。全関節動作、ハーネス、工具の挿入経路、プリントの造形方向・サポート除去は未確認。正式候補へは未採用。

再現:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_connected_crossweb.py --out /tmp/stackchan-crossweb
```

構造比較は `yaw_connected_crossweb_deformation_v1`。既存0.2mm枠と保存荷重を維持し、事前に定めた条件で終了する。
