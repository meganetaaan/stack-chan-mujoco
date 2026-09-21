# アンカー位置180度変更の感度

ボス・スペーサーのアンカー目標座標を(35,6)回りに180度移動。メッシュ・材料・荷重・接触ペナルティは `sole_spacer_anchor_audit_v1` と同一。制約する成分も同じ。位置変更のみの診断であり、実部品の設計変更ではない。

事前基準は接触圧ピーク変化10%、変形ピーク変化5%。変形は各部品の全節点変位から最小二乗の微小剛体並進・回転を除いた残差ノルムを使う。異なる基準点による絶対変位の差を変形差と混同しない。これは微小回転近似の診断であり、有限ひずみの厳密な不変量比較ではない。

結果: 接触圧ピーク3.98515→4.10202 MPa（+2.933%）。非剛体変位ピークの変化はボス0.0000240%、スペーサー0.005056%。いずれも位置感度基準内。

ただし個別反力のノルム合計/20 Nは1.53567e-4、各モーメントのノルム合計/(20 N×3 mm)は1.49254e-4で、元の1e-4基準を両方超える。したがって位置感度が小さいことを理由に反力監査を合格へ変更しない。接触数値モデル全体・接合強度とも未認定。メッシュ・接触法・材料感度、歩行荷重等は残る。

再現:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_spacer_contact.py --opposite-anchors --out outputs/sole_opposite_repro
cp validation/sole_spacer_anchor_audit_v1/anchor_plan.json outputs/sole_opposite_repro/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sole_spacer_anchors.py --source outputs/sole_opposite_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/evaluate_sole_spacer_contact.py --source outputs/sole_opposite_repro
mkdir -p outputs/sole_position_comparison
cp validation/sole_anchor_position_v1/comparison_plan.json outputs/sole_position_comparison/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/compare_sole_anchor_positions.py --baseline validation/sole_spacer_anchor_audit_v1 --variant outputs/sole_opposite_repro --out outputs/sole_position_comparison
```

基準ケースの `evaluation.json` は今回保存済みDATから追加生成した。比較スクリプトは節点座標と変位を用い、ケースごとの剛体成分を個別に除く。DATは可逆圧縮、入力と生データのハッシュを保存した。
