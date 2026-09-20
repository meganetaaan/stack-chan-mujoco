# アクチュエータ解析の再現

リポジトリルートから実行する。Python環境は [モノレポ手順](MONOREPO_ja.md) の runtime lock を使用する。GUI・GPU・実機接続は不要。既存出力を上書きしないため、再実行時は新しい出力先を指定する。

## 保存結果の検査

```sh
.venv/bin/python software/sim/integration/verify_prototype_spec.py
.venv/bin/python -m unittest discover -s software/sim/actuator/tests -v
.venv/bin/python software/sim/integration/audit_actuator_results.py --root validation/prototype_epic4_v1 --out outputs/review_audit.json
```

監査は試験時のソースハッシュ、4動作からの関節範囲・最大負荷、12単関節の時系列、34片脚条件の追従・電流・端子電圧・トルク・電力収支・支持荷重、左右の負荷出力の一致を検査する。衝突と保護停止はシミュレーターの観測記録を参照する。実機での定格・信頼性を証明する検査ではない。

## シミュレーションを再実行する

以下の出力先が存在しない状態で実行する。`outputs` はリポジトリの作業用出力先。

```sh
.venv/bin/python software/sim/actuator/capture_workload.py --out outputs/repro_turns
.venv/bin/python software/sim/actuator/capture_translation_workload.py --out outputs/repro_translation
.venv/bin/python software/sim/actuator/merge_workloads.py --turns outputs/repro_turns --translation outputs/repro_translation --out outputs/repro_workload
.venv/bin/python software/sim/actuator/run_suite.py --workload outputs/repro_workload --out outputs/repro_suite
.venv/bin/python software/sim/actuator/run_load_sweep.py --workload outputs/repro_workload --out outputs/repro_sweep
.venv/bin/python software/sim/actuator/run_probe.py --sign 1 --out outputs/repro_fullbody_left
.venv/bin/python software/sim/actuator/run_probe.py --sign -1 --out outputs/repro_fullbody_right
.venv/bin/python software/sim/actuator/export_loads.py --source outputs/repro_fullbody_left --out outputs/repro_loads_left
.venv/bin/python software/sim/actuator/export_loads.py --source outputs/repro_fullbody_right --out outputs/repro_loads_right
.venv/bin/python software/sim/actuator/thermal_screen.py --trace outputs/repro_fullbody_left/trace.npz --out outputs/repro_thermal
```

`run_suite.py` は4プロセスで片脚を解析し、単関節12軸を実行する。`plan.json` に試験前の閾値・条件・ソースハッシュを保存する。`summary.json` と各条件の `report.json`、`trace.npz` を確認する。負荷スイープは限界を調べるため過負荷の不合格を含む。全36点が合格することを要求していない。

## 保存した結果

[証跡フォルダー](../../validation/prototype_epic4_v1/) 内の対応は次の通り。

| 出力 | 内容 |
|---|---|
| actuator_workload_v2 | 左右旋回・前進・後退の4動作と12軸要求 |
| actuator_suite_v2 | 単関節12軸、片脚34条件、実行コマンド・事前計画 |
| actuator_load_sweep_v2 | 2型番×3電圧×6負荷、失敗ケースを含む36点 |
| actuator_fullbody_load_left_v1 / right_v1 | 新モデルによる7秒の全身負荷取得。90度精度の合否試験ではない |
| load_export_left_v1 / right_v1 | 同一時系列を回路・構造解析向けに変換したNPZ・圧縮CSV・座標系定義 |
| actuator_thermal_v2 | 左全身負荷を600秒繰り返す18熱パラメータ条件、およびピーク電流保持の定常推定 |
| audit.json | 保存時系列を独立に再計算した監査結果 |

単関節12/12、片脚34/34が設定した追従・制限条件を満たした。片脚の最大追従誤差は0.068315 rad（閾値0.15 rad）。負荷スイープは24/36点が整定し、解析トルク上限の125%を要求する6点はすべて不合格として保存した。熱推定の18条件は600秒以内に70°Cへ達しなかったが、ピーク電流を保持した場合には70°Cを超える仮定条件がある。連続定格を新たに設定する根拠にはしない。

## 解釈の範囲

片脚支持は胴体の水平移動・姿勢を拘束し、鉛直方向を自由にした試験治具。振出しは胴体固定・床なし。独立した片脚倒立や歩行成功率を示すものではない。前進・後退は現行r9の指令0.04 / −0.02 m/sであり、実機目標0.10 m/sの達成ではない。

新モデルの全身旋回は左右とも約88.5度となり、90度±1度の基準を満たしていない。旧r9モデルの基準試験は別途保存しており、この差を隠して置換しない。全身制御への統合調整は後続EPICの課題。機構・電源への出力はモデル推定値で、製作・実測は本EPICの対象外。
