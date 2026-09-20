# ヨー支持部リブ中央の軽量化

左右の5 mmリブ中央に、三角形の角を半径2 mmで丸めた開口を設けた。支持部1個37.460→34.082 g、左右合計6.757 g削減。外接寸法、後壁・締結座、z>=87 mmの支持棚の形状は保持した。これは公差・実締結・造形品質の合格ではない。

構造スクリーニングは既存の代表荷重1ケース、PETG E=1120 MPa、許容応力5.6 MPa、変位0.2 mm、背面座の理想固定で実施。4/3/2 mmメッシュ、最終2段階の変位差5%・主応力差10%を事前基準とした。全荷重・補強後負荷・接触・座屈・疲労・クリープの評価ではない。詳細判定はstrength/report.json参照。

軽量背面板と本支持部を組み合わせた質量感度試験は、胴体629.333 g。左旋回3.558秒・51.860度で右足首ロール−0.2801453 radが下限−0.28 radを超え、停止した。停止直前の指令は−0.245437 radで、実関節の追従偏差が残り余裕を消費している。軽量化だけでは現制御条件の旋回を成立させられていない。制限値は変更しない。

再現（全出力先は新規ディレクトリ）:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/lighten_yaw_support.py --out outputs/light_yaw_support_v1
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/screen_yaw_back.py \
 --step outputs/light_yaw_support_v1/left_yaw_fixed_support.step --out outputs/light_yaw_strength_v1
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/mujoco/build_mass_sensitivity.py \
 --out outputs/light_plate_support_mass_v1 --residual-grams 25 \
 --rear-plate validation/light_rear_plate_development_v1/cad/rear_structural_plate.step \
 --support-dir outputs/light_yaw_support_v1
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/light_plate_support_mass_v1 --out outputs/light_plate_support_left_v1 --sign 1
.venv-engineering/bin/python software/sim/actuator/diagnose_limit_trace.py \
 --source outputs/light_plate_support_left_v1 --model outputs/light_plate_support_mass_v1 \
 --out outputs/light_plate_support_left_v1/limit_diagnosis.json
```

CADと失敗波形を残し、既存の候補指定を上書きしない。残部品25 gは未確定の仮定であり、旧衝突形状を使った感度試験を現CADの動作保証とは扱わない。

今回の代表荷重結果: 最細2 mmで最大変位0.170529 mm、最大絶対主応力4.114784 MPa。3→2 mmの変位差2.32%、主応力差5.11%で、限定したスクリーニング基準を満たした。
