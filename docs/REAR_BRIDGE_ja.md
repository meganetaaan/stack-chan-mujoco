# ジンバル横梁の移設と10 mシミュレーション

2026-09-19。ジンバルの横梁をモーター後方へ移し、短距離試験の終了動作での干渉を解消する候補。
外形・脚長・関節・電池配置は維持する。実機10 m・18/20試行の目標達成ではない。

## 機構変更

足首ピッチ座標で上側横梁の中心Xを−42から−55 mmへ移す。
寸法は8×34.9×2.4 mmから2.4×34.9×8 mm、中心Zは15.2から12.5 mm。
梁の断面積19.2 mm²は同じだが、断面二次モーメント9.216/102.4 mm⁴の向きが入れ替わる。
断面積が同じことは強度が同じことを保証しない。荷重経路・締結・プリント方向の検証が必要。

変更部品は左右ジンバルのみ。他36個のSTLはバイト単位で一致し、関節位置・軸・範囲も不変。
STEP/STL再読込み、単一ソリッド、閉じたメッシュ、MuJoCoコンパイルを確認した。
質量約855.284 g、公称外接寸法128×128×212.582 mm。脚は腿50 mm・脛44 mmのまま。

以前の干渉姿勢（0.52 m試験の行315）で腿／ジンバルの距離は約5.778 mmとなった。
以前の行315/320を衝突モデルで再生しても接触せず、衝突形状を無効化せずに改善できた。
新形状のジンバルもCADから凸形状へ分割し、B-rep未被覆体積0を確認している。

## 動力学結果

条件: 自由基底、外力補助なし、0.10 m/s参照、高さ−2 mm、前後COM−3 mm、
静的トルクによる目標角補正あり、slew=6 rad/s。理想IMU足首補正は使用しない。
全て同じ公称パラメータでの決定論的な試験で、外乱・個体差を加えていない。

| 周期 | 横inset | 計画ステップ | 実行時間 | 前進量 | 結果 |
|---|---:|---:|---:|---:|---|
| 0.25 s | 25 mm | 20 | 6.5 s | 0.522 m | モデル停止条件なし |
| 0.25 s | 25 mm | 60 | 14.641 s | 1.308 m | 接触停止 |
| 0.25 s | 25.8 mm | 60 | 16.5 s | 1.584 m | モデル停止条件なし |
| 0.27 s | 24 mm | 60 | 17.7 s | 1.725 m | モデル停止条件なし |
| 0.27 s | 25 mm | 60 | 17.7 s | 1.682 m | モデル停止条件なし |
| 0.27 s | 25.8 mm | 60 | 17.7 s | 1.645 m | モデル停止条件なし |
| 0.27 s | 24 mm | 400 | 109.5 s | 11.610 m | モデル停止条件なし |
| 0.27 s | 25 mm | 400 | 109.5 s | 11.323 m | モデル停止条件なし |

周期0.23秒の3条件と周期0.25秒・inset24 mmは3.5秒以内に接触停止した。
良好な条件があっても、広い範囲で安定する制御器が完成したとは言えない。

10 mを初めて超えた保存サンプルの時刻は、inset24/25 mmで94.10/96.48秒。
開始前の静止時間も含み、保守的な平均速度はそれぞれ約0.10627/0.10365 m/s。
補間値より遅いサンプル時刻を使っており、計測間隔によって速度を高く見積もらない。
`measure_forward_traversal.py` はこの単一シミュレーションの計測のみを行い、
実機や20試行の受入合格を出力しない。

inset24 mmは微小接触を計数する版で再実行し、109.5秒の全1 ms物理ステップで、
自己接触・足裏以外の床接触の最大力および侵入ステップ数がともに0だった。
侵入判定の数値許容値は1e−8 m。停止の力閾値より弱い接触も記録対象にした。
この再実行の関節・位置ログと参照軌道は元のinset24 mm試験とバイト単位で一致する。
既知の衝突する移設前モデルでも同じ計数器を試し、自己侵入1ステップ、最大力約1.271 Nを検出した。
**追加計数器の再実行は独立した成功試行として数えない。**

## CAD検証と未解決事項

- 新20ステップログの全325保存姿勢で、0.01 mm³を超える全機械部品組合せの干渉なし。
- 10 mを通過したinset24 mmログから25行おきと末尾を選んだ220姿勢も同じ検査に合格。
- いずれも連続掃引の証明ではない。CADと衝突モデルの双方に残る検証範囲を区別する。

固定クレードル・電池等の予約部品の衝突形状、その他の簡略形状の被覆、
剛性・配線・公差、サーボの連続定格、電池・5 V電源の電圧降下、保護停止、実機IMUは未検証。
温度・電圧・電流による保護停止は今回のモデルに実装していない。
本タスクで実機試行は未実施で、実機との比較結果もまだない。

## 再現

`design/leg_relief/README_ja.md` の環境と開口データを使用する。
各出力先は未作成にする。

```bash
.venv-cad/bin/python build_design.py \
  --out outputs/design_r6_rear_bridge8 --hip-half-spacing-mm 22 \
  --battery-layout design/battery_layouts/internal_lower_envelope.json \
  --underside-cutouts design/leg_relief/underside_cutouts.json \
  --leg-clearance-relief --boot-collar-relief --rear-gimbal-bridge
.venv-cad/bin/python add_gimbal_collisions.py \
  --design outputs/design_r6_rear_bridge8 --out outputs/design_r6_rear_bridge8_collision
.venv-dynamics/bin/python validation/verify_opening_variant.py \
  --baseline outputs/design_r6_leg_collar_relief --candidate outputs/design_r6_rear_bridge8 \
  --expected-meshes left_ankle_gimbal.stl right_ankle_gimbal.stl --out outputs/rear_bridge_invariants.json
.venv-dynamics/bin/python probe_reference_gait.py \
  --design outputs/design_r6_rear_bridge8_collision --speed .1 --step-period .27 \
  --height-offset-mm -2 --com-forward-offset-mm -3 --com-inset-mm 24 \
  --static-compensation --slew 6 --steps 400 --out outputs/rear_bridge_long_run
python measure_forward_traversal.py --run outputs/rear_bridge_long_run --out outputs/traversal.json
.venv-cad/bin/python check_design_clearance.py \
  --design outputs/design_r6_rear_bridge8 \
  --trajectory-csv validation/rear_bridge/rear_long_i24_contact_audit/trajectory.csv \
  --stride 25 --out outputs/long_sampled_cad.json
.venv-dynamics/bin/python -m unittest tests.test_forward_traversal tests.test_reference_gait
```

全条件のコマンド、生CSV、report、圧縮参照軌道、距離計測、CAD検査は `validation/rear_bridge/`。
参照軌道JSONはgzipで可逆圧縮している。報告にはモデル・実行コードのSHA-256を含める。
微小接触計数追加前の診断コードはコミット`e00f114`。計数追加後も制御や停止閾値は変えていない。
