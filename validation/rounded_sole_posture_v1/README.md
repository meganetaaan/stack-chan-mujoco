# 丸角足裏での足配置感度

既存turn-insetパラメータ25.8/25.95 mmを事前指定。両方とも7秒を停止なしで完了。右足首ロール最小可動域余裕は0.008013/0.011203 rad。旋回角88.95714/88.91381度で90±1度の事前基準には不合格。基準を緩和せず、全系列を保存する。

丸角で全期間の荷重を取得できたが、最新CAD質量や全接触形状は未反映。左右・前後・停止の全条件を保証しない。姿勢パラメータの感度確認でありEPIC7以降の制御実装の完了ではない。構造解析入力として利用する際もこの限界を明示する。

## 再現

rounded_sole_fine_v1のREADMEに従ってモデルをoutputs/rounded_sole_fine_v1へ生成後、以下を実行する。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/actuator/run_probe.py --foot-loads --model outputs/rounded_sole_fine_v1 --turn-inset-mm 25.8 --out outputs/posture_repro/inset25.8
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/actuator/run_probe.py --foot-loads --model outputs/rounded_sole_fine_v1 --turn-inset-mm 25.95 --out outputs/posture_repro/inset25.95
cp validation/rounded_sole_posture_v1/plan.json outputs/posture_repro/plan.json
.venv-engineering/bin/python software/sim/actuator/evaluate_sole_posture.py --source outputs/posture_repro
```

plan.jsonは実試験開始前に固定した判定条件。probeのreport.jsonとtrace.npz、圧縮接触記録を保存。元モデルの可動域・電流上限は変更していない。
