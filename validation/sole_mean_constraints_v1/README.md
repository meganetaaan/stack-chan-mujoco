# 体積重み付き平均拘束の入力案

点拘束近傍の応力集中を切り分けるため、`sole_fixed_anchors_v1/h07/contact.inp` のBOUNDARYを平均拘束へ置換。材料・接触・荷重・メッシュは維持し、旧アンカーRF出力は除去した。まだソルバー実行・接触成立の検証はしていない。

各四面体体積の1/4を各節点へ配分し、部品体積で正規化する。重心を原点に、平均並進Σw uと平均回転に対応するΣw(r×u)をゼロとする。ボスはx,y並進とz回転の3式、スペーサーは6式。これにより単一節点を固定せずに剛体モードを除く。各部品の剛体モード行列との積のランク3/6を確認した。

*EQUATIONは第1変数が従属自由度になるため、列ピボット付きQRと行変換で従属列を単位行列化した。他式の従属変数が独立項へ混入しないようゼロ化し、各従属自由度は1式のみへ使用する。変換誤差は最大1.6e-16。参照は[CalculiX 2.21公式マニュアル](https://www.dhondt.de/ccx_2.21.pdf)の*EQUATIONおよびMPCの説明。

制約は初期座標を用いた線形平均で、大回転に対して客観性が保証された拘束ではない。対象は微小変形の予備締付解析。拘束反力・拘束仕事・接触力平衡・ピーク応力・メッシュ依存性を評価しない限り、点拘束より妥当と結論しない。従属自由度の消去による行列密度増加の計算負荷も未評価。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/build_sole_mean_constraints.py --source validation/sole_fixed_anchors_v1/h07 --out outputs/sole_mean_constraints_repro
```

constraints.npzに変換前後の拘束行列と節点IDを保存。plan.jsonは構築前の基準。ソルバー完了やIssue完了を主張する成果物ではない。
