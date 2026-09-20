# r9製作候補のデジタル仕様

過去の検証に用いた `software/sim/mujoco/assets/r9_fast_turn_v1/` は変更しない。
このフォルダはそのモデルから生成した、今後のメカ・電源・制御の共通仕様。
現時点では **実物の組立・校正・製造強度を確認したものではない**。

| ファイル | 意味 |
|---|---|
| `robot.json` | 外形・脚長・全12軸の範囲・有限旋回設定。旧yaw無効フラグ等を修正 |
| `joints.json` | 軸順、バスID、モデルの軸・位置・正方向・ゼロ・制限・候補サーボ |
| `frames.json` | 右手座標、単位、エンコーダとの変換式 |
| `bom.csv` | 商用部品・予約枠・構造の質量配分。未選定部品は明記 |
| `mass_budget.json` | 慣性に使われるリンク別質量・重心・主慣性軸 |
| `geometry_inventory.json` | 既存メッシュの一覧（BOM質量へ二重加算しない） |

胴体128 mm角、大腿50 mm、下腿44 mm、足86×48 mmを基準にする。
総質量約0.91844 kgは設計モデル値で、実測質量ではない。
BOMの構造集計は他の配分を引いた残量であり、未確定のねじ長やコネクタ個数を捏造しない。
電池・変換器・インターフェース・配線の実型番は後続EPICで確定する。

`q=0`はCAD/MJCFの基準角で、立位でも可動域中心でもない。
組立規約として0 radを2048 count、正方向を右手回転と定義している。
実機の `calibrated_zero_count` / `calibrated_sign` は未測定のためnull。
デジタル仕様上の符号と実サーボの取付方向は、実機タスクで照合するまで同一と仮定して駆動しない。
電流制御等ではサーボ内部の位置制限を頼れないため、指令生成側の角度制限が必要。

```sh
.venv/bin/python software/sim/integration/build_prototype_spec.py
.venv/bin/python software/sim/integration/verify_prototype_spec.py
```

再生成はこのフォルダだけを更新し、凍結モデルは変更しない。
候補サーボの数値出典はROBOTIS e-Manualの
[XL330-M288-T](https://emanual.robotis.com/docs/en/dxl/x/xl330-m288/) と
[XC330-M288-T](https://emanual.robotis.com/docs/en/dxl/x/xc330-m288/)。
電気・機械応答のモデル化と不確かさの評価はEPIC #4で行う。
