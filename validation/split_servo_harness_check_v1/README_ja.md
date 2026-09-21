# 配線候補表の端子割当検査

36端子の網羅、重複、軸ID、コネクタ割当、GND/V+/DATAを検査した。
左右電源の取り違え、V+/DATA交換、GND欠落、端子重複、ID違い、
別軸への同一コネクタ名割当の6ケースを入力表へ注入し、全て拒否を確認した。
生成器内部のassertだけでなく、書き出したCSVを独立に読み直す。

この検査は表の論理接続を対象とする。ケーブルの実導通、未記載ジャンパー、
端子カバー、信号回路、電流容量、電圧降下や誤挿入防止形状は検査しない。
表が正しいことは製作・通電リリースではない。

再現（リポジトリルート、Python標準ライブラリのみ）：
```
python3 software/sim/circuits/verify_split_servo_harness.py --csv schematics/power/split_servo_harness_revA/connections.csv --out NEW_DIRECTORY
```
