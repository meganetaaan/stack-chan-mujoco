# 質量・重心・慣性の単独変更による切り分け

前回の補強候補は3.155秒で左足首ロールが0.2800455 radとなり、上限0.28 rad＋監視許容1e-5 radを超えた。質量、重心、慣性を各々単独で置換する診断モデルを作成し、同じ7秒左旋回を実行した。これは製造可能な部品配置ではなく因子切り分けである。

|置換因子|時間 s|旋回 deg|終了理由|
|---|---:|---:|---|
|質量のみ|2.782|23.394|右足首ロール下限超過|
|重心のみ|7.000|87.788|予定時間終了|
|慣性のみ|7.000|88.635|予定時間終了|

質量のみでは右足首ロール−0.2802381 rad、下限−0.28 rad。単独の質量増加で停止を再現したため、軽量化と足首ロール余裕の確保を次の設計方針とする。重心・慣性の相互作用や全荷重条件の影響を否定した結果ではない。継続した2条件も90±1度には未達である。

各モデル生成前の基準はmass_plan.jsonに保存。変更した慣性情報はMuJoCoと既存姿勢計画の双方に入力されるため、計画への影響も含む比較である。元の衝突形状、電流制限、関節限界、制御パラメータを維持した。記録した停止トレースは有限値である。角度監視閾値を緩和して合格に変更してはいない。

再現例（caseをmass_only、com_only、inertia_onlyに変更し、各出力先も変更）:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/mujoco/build_mass_sensitivity.py \
 --out outputs/mass_factor_mass_v1 --residual-grams 25 --case mass_only
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/mass_factor_mass_v1 --out outputs/mass_factor_mass_left_v1 --sign 1
.venv-engineering/bin/python software/sim/actuator/diagnose_limit_trace.py \
 --source outputs/mass_factor_mass_left_v1 --model outputs/mass_factor_mass_v1 \
 --out outputs/mass_factor_mass_left_v1/limit_diagnosis.json
```
