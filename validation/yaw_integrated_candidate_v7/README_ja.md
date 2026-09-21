# 工具逃げ修正後の統合比較v7

v5の左右支持部を工具逃げ半径4 mmの上面補強へ置換。残り50部品を保持。
各支持部の追加体積はv5比4561.042 mm³。材料密度は未確定で質量は確定していない。
全1326組の静的比較でrevB比の新規体積干渉フラグ0。
既存のねじ包絡重複はそのまま記録し、締結成立と扱わない。

v6より逃げを増やした形状の比較版。正式版ポインタは変更しない。
動作隙間のv6結果をv7の実行済み検査として扱わない。
部品属性、幾何モーメント、v5からの変更差分を保存。
実ソケット嵌合、材料、締結、荷重への質量反映、全組立工程は未確認。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/integrate_yaw_upper_shelf.py --support-dir validation/yaw_upper_tool_relief_v1 --out /tmp/yaw-v7
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate /tmp/yaw-v7 --all-pairs
```
