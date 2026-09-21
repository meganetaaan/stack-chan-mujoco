# 足部revE — 公差比較済みナット開口を統合

revDの外装を幅4.6 mmの `validation/boot_nut_side_entry_v2` へ置換した。30部品、210組の公称体積交差0。全形状が有効な単一ソリッド。元の脚長・足部外寸を維持する。

開口幅の変更は既存の各印刷面±0.2 mm仮定を保持した設計変更。最大ナットに対する総隙間は幅・高さ各0.2 mm。強度、回り止め、工具空間、実造形適合の合格ではない。ねじ穴は後加工候補だが工具・仕上げ公差未確定。

硬質3部品をPETG典型密度1.27 g/cm³で換算した質量は50.330115 g/足。旧revB比較から0.062728 g/足減少する。体積慣性も新外装から再計算した。接地材・金属締結品・ホーン類・配線を含む足全体の慣性ではなく、MuJoCoへ部分値を投入していない。

入口は `../current.json`。旧revDを現行形状と混在させない。加工・組立の候補手順は `validation/boot_nut_side_entry_v1/README_ja.md`、寸法と根拠はv2のREADMEを参照。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/export_current_foot_inventory.py --include-boot-hardware --boot-dir validation/boot_nut_side_entry_v2 --out /tmp/foot-revE
.venv-engineering/bin/python software/sim/structural/calculate_foot_rigid_inertia.py --inventory board/mechanical/prototype/foot_candidate/revE/inventory.json --out /tmp/foot-rigid-revE
```

外装ねじの工具軸確認: `validation/boot_driver_access_v1`。Wera 05118064001の軸包絡は足裏除去時に8箇所とも交差0。接地層を装着すると全箇所で通過を妨げるため、外装締結後に足裏を取り付ける。柄・手・トルクは未確認。
