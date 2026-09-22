# 補強質量を反映した旋回感度試験

元モデルの胴体慣性を補強4部品と締結部品48個のCAD概算へ置換する。旧25 g枠を除去し、未列挙の配線・締結部品を別途25 gと仮定する。残部品25 gは確定BOMでも上限保証でもない。位置・分布は旧予約体のまま。形状・接触は元r9のままで、候補形状の干渉合格を判定する試験ではない。

質量モデル生成時に7秒継続・有限値・90±1度という確認条件を保存した。左右とも関節角制限で途中終了したため不成立。元モデルも90±1度は満たしていないことに注意。

|モデル／方向|終了時刻 s|旋回 deg|最大電源電流 A|終了理由|
|---|---:|---:|---:|---|
|元r9／左 再確認|7.000|88.533|0.55984|予定時間終了|
|補強質量／左|3.155|36.098|0.72382|joint_limit|
|補強質量／右|3.153|-35.856|0.72546|joint_limit|

元r9の旋回角・最大電流はEPIC4の保存結果と一致した。補強候補の胴体質量は654.695 g。元の522.940 gから約131.755 g増える。胴体重心xは9.651→−2.944 mm。質量、重心、慣性を同時に変更した比較なので、どの因子が停止の主因かはまだ分離できていない。

再現（出力先は新規ディレクトリを指定）:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/mujoco/build_mass_sensitivity.py \
 --out outputs/reinforced_mass_sensitivity_v1 --residual-grams 25
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/reinforced_mass_sensitivity_v1 --out outputs/reinforced_mass_left_v1 --sign 1
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/reinforced_mass_sensitivity_v1 --out outputs/reinforced_mass_right_v1 --sign -1
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --out outputs/mass_baseline_recheck_v1 --sign 1
```

全波形をtrace.npzに保存。失敗途中の波形を正常7秒歩行の電源負荷として代用しない。次は軽量化・重心配置と追従余裕を検討し、候補CADの衝突形状も反映したモデルで検証する。今回の結果からIssueを完了扱いにはしない。
