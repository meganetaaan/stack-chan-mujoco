# 疎行列の平均拘束付き接触診断

`probe_sparse_sole_contact.py`を追加。既存の同一三角形接触メッシュを使い、P1微小ひずみ弾性、体積重み付き平均拘束9式をラグランジュ乗数として連立する。拘束自由度の消去で行列を密にしない。接触は対応節点の面積重み付き法線ペナルティ（1e6 N/mm³）、負ギャップのみ有効とするactive-set。摩擦なし、初期法線、材料・締付力は既存仮定。CalculiXの有限変形surface-to-surface接触とは同一ではない。

0.7 mm結果は `../sole_sparse_mean_v1`、0.5 mm結果はh05。連立系12198/18633自由度、非零483221/761122。計測した解法部分は約1.14/2.78秒（メッシュ読込・組立前処理を含まない）。両ケースとも初期の全接触集合で収束。接触力合計20 N、平衡残差約6e-13 N以下、平均拘束残差5e-17以下、平均拘束の分布反力ノルム合計/20 Nは6e-14以下。食込みは最大2.80e-6 mm。今回の条件では離間が起きておらず、離間する条件のアルゴリズム検証は未実施。

事前の細分化判定: 変位変化5%、圧力・主応力変化10%。変位は両部品基準内だが、圧力15.17%、ボス応力15.81%、スペーサー応力101.37%で不合格。全積分点を評価しピークを除外していない。スペーサー応力16.70→33.63 MPaという増加は平均拘束でも残った。従来の点拘束位置とピーク要素の近接だけから、点拘束を主因と断定できない。次はピーク要素品質と縁落とし形状の離散化を監査する。

構築・数値釣合いが通ることはソルバーの独立検証や接合強度の証明ではない。解析的な接触ベンチマーク、離間、ペナルティ・メッシュ・材料感度、有限変形の影響、歩行荷重は未検証。

再現:

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --mesh-dir validation/sole_fixed_anchors_v1/mesh07 --out outputs/sparse_contact07
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --mesh-dir validation/sole_fixed_anchors_v1/mesh05 --mesh-mm 0.5 --out outputs/sparse_contact05
```

拘束力は乗数から復元し、接触力・外力・内力とともに釣合いを確認する。fields.npzに変位、圧力、ギャップ、面積重み、拘束力、乗数、全積分点応力を保存。plan.jsonは解析開始前に生成。元の平均拘束失敗記録は保持し、今回の方式で置換して隠さない。
