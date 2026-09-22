# 上面補強の一荷重変位比較：限定条件で通過

既存38ケースの直接評価点で最大変位となった荷重を使用。
荷重点[-5,26,62] mm、理想後部固定、E1120 MPa・ν0.35、
分布荷重・線形等方性という既存条件を維持。

| メッシュ | 最大変位 mm |
|---|---:|
| 3 mm | 0.133233 |
| 2 mm | 0.134530 |

双方0.20 mm以下、変化率0.973%で事前の10%以下条件を満たした。
残差・仕事とエネルギーの整合も通過。旧形状の同じ荷重の3 mm結果は0.220130 mm。
この比較を局所応力の収束や実材料強度の合格に拡張しない。

次段階は全荷重での変形範囲、締結座面・工具・動作時干渉、
追加質量による荷重変化の確認。材料製品・造形条件、実締結の保持・クリープ、
最新電池配置は未確定。正式候補への採用・Issue完了・通電試作許可は未成立。

再現（出力先未作成）：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_yaw_upper_shelf.py --out /tmp/yaw-upper-fe
```
幾何生成と変更条件の根拠は隣接するyaw_upper_shelf_v1/README_ja.mdを参照。
