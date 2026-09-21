# 111部品候補のKiCad接続読み戻し

統合候補からKiCadのレビュー用回路図を生成し、KiCad 7.0.11で実際にXMLネットリストを書き出した。111部品、接続334端子、明示NC37端子が元assemblyと一致した。大きい端子数の部品に合わせて行間と用紙を可変にし、111部品を従来固定A1用紙の外へ配置しないようエクスポータを修正した。

**部品選定・ERC・回路動作の合格ではない。** 元BOMでは11部品の型番が空欄。通常モードは型番不足で停止する。今回のみ明示オプション `--allow-unselected` を指定し、図面の値を `UNSELECTED` と表示した。report.jsonも `all_part_numbers_assigned=false` を記録する。部品記号は汎用passive端子、フットプリントなしであり製作へ使用しない。

| 空欄の参照番号 | 状態・次の設計判断 |
|---|---|
| LEFT/RIGHT_R_GATE、LEFT/RIGHT_C_GATE | 値と型番が未定。逆流保護のゲート動作、起動/遮断条件を確定してから選定 |
| LEFT/RIGHT_R_ILM | 1100Ωの計算候補のみ。注文型番・全温度/工程誤差と電流閾値の対応が未統合 |
| LEFT/RIGHT_R_OV_TOP/BOTTOM | 35.7kΩ/10kΩの計算候補のみ。異常入力時のOVLO端子範囲も未成立。型番を埋めるだけで保護合格にはならない |
| C_STOP_OUT | 別資料 `stop_output_capacitor_requirements.json` にGRM31CR71H475KA12L候補あり。assembly/BOMには未反映。容量・ESRの未検証を維持したうえで統合する必要あり |

初回の通常モードはLEFT_R_GATEの型番欠落を検出して停止した。未選定をダミーの実部品で隠すことはせず、明示表示するレビュー専用出力に切り替えた。生成済みKiCadを読み込んだ際には `schematic has annotation errors` の警告も出た。111部品の型番/全端子の一致は別途検査済みだが、KiCadの部品番号付与の修正も未完了である。警告なしの製作用回路図とは扱わない。

再現（未使用出力先）:

```sh
.venv-engineering/bin/python software/sim/circuits/export_manual_rearm_schematic.py --allow-unselected --assembly schematics/power/servo_power_logic_integration_candidate_v1/assembly.json --bom schematics/power/servo_power_logic_integration_candidate_v1/candidate_bom.csv --out /tmp/integrated-logic-review
kicad-cli sch export netlist --format kicadxml -o /tmp/integrated-logic-review/readback.xml /tmp/integrated-logic-review/manual_rearm.kicad_sch
.venv-engineering/bin/python software/sim/circuits/verify_manual_rearm_kicad.py --allow-unselected --assembly schematics/power/servo_power_logic_integration_candidate_v1/assembly.json --bom schematics/power/servo_power_logic_integration_candidate_v1/candidate_bom.csv --schematic /tmp/integrated-logic-review/manual_rearm.kicad_sch --netlist /tmp/integrated-logic-review/readback.xml --out /tmp/integrated-logic-review/report.json
```

現在の環境ではKiCad実行ファイルは `/tmp/stackchan-kicad-runtime/runtime/usr/bin/kicad-cli`、ライブラリ検索先は同runtimeの `usr/lib/x86_64-linux-gnu`。正式ポインタは変更せず、#6/#22/#24をクローズしない。
