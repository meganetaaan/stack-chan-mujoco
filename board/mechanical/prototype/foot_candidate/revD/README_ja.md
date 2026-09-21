# 足部revD — ナットを印刷後に入れる比較構成

revCの外装を `validation/boot_nut_side_entry_v1` に置換した。左右30部品、210組の公称体積交差0。形状は全て有効な単一ソリッド。脚長・足部寸法は維持し、外装側面にナット挿入口を設けた。

部品数はrevCと同じ。8個の外装ナットは封入から横挿入に変わる。部品の型番・材料・公差・締付け・強度は未確定で、製造リリースではない。片足41.184 mm³の樹脂除去により、以前の硬質3部品慣性はそのまま使用しない。inventory.jsonに新しい体積・重心・体積慣性を記録した。

比較の理由、組立順、挿入経路、未確認事項は `validation/boot_nut_side_entry_v1/README_ja.md` を参照。工具空間、穴仕上げ公差、ナット受け部強度の確認後に採否を確定する。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/export_current_foot_inventory.py --include-boot-hardware --boot-dir validation/boot_nut_side_entry_v1 --out /tmp/foot-revD
```
