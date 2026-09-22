# 111部品候補からの電流見積り更新

対象は `schematics/power/servo_power_logic_integration_candidate_v1/assembly.json`。既存集計スクリプトに入力指定を追加し、統合候補を直接読み込む。直接抵抗集計と出力経由集計の入力SHA256が一致しない場合は停止する。型番不明のICをゼロ電流と判断しない。

結果は `summary.json`。ロジック直結抵抗11本、出力経由負荷、将来MCU出力の予約、既存IC静的参考値、MCUコア参考2.9mA、今回追加した出力ポリマー漏れ22µAを合わせ9.89956mA。漏れは25℃・5分という指定条件だけの値で、温度全域の保証ではない。MCU自体は統合回路に未実装。従来の20mA連続選定目標は変えず、残り10.10044mAを未配分として残す。保証された余裕ではない。

電池側の分圧2組と入力放電抵抗は12.6V・抵抗−1%で計475.784µA。RTNを通常動作時のGND相当とした参考値で、逆接時には適用しない。これはLOGIC3V3の出力負荷へ加算しない。保護ICの消費やLDOのGND電流も別で、今回の集計に含まない。

過去のIC資料の試験条件と限界は `logic_ic_current_review_v1/v2`、MCUは `sequence_mcu_current_v1` を維持する。入力途中電圧の追加消費、動的電流、ボタン内部プルアップ、未実装MCU周辺、基板漏れ等は残る。小計を全電流の保証上限として使わず、起動モデルのピークにも流用しない。

再現は新しい出力先を使う（最初の2ツールは既存ディレクトリの上書きを拒否する）。保存済み結果の厳密再生成では対象出力を退避してから以下を実行する。

```sh
.venv-engineering/bin/python software/sim/circuits/audit_direct_rail_loads.py --assembly schematics/power/servo_power_logic_integration_candidate_v1/assembly.json --out validation/integrated_logic_loads_v1/direct
.venv-engineering/bin/python software/sim/circuits/audit_output_rail_loads.py --assembly schematics/power/servo_power_logic_integration_candidate_v1/assembly.json --direct-report validation/integrated_logic_loads_v1/direct/report.json --out validation/integrated_logic_loads_v1/output
.venv-engineering/bin/python software/sim/circuits/catalog_logic_current.py --assembly schematics/power/servo_power_logic_integration_candidate_v1/assembly.json --out validation/integrated_logic_loads_v1/ic_catalog.json
.venv-engineering/bin/python software/sim/circuits/summarize_integrated_logic_loads.py
```

試験範囲は接続に基づく負荷の棚卸し更新。部品追加で見積りが古いままになる問題を解消したが、通常/異常時の回路動作はまだ未検証。
