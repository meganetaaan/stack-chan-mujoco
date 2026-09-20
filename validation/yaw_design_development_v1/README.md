# 旋回補正の拡大と股関節ヨー用モータの収納検討

現行10軸の左右股関節ピッチに逆向きの定数補正を与え、振幅0.035/0.05 rad、周期0.27/0.32秒、足上げ4/6 mmの全8条件を試した。モータのトルク・速度・遅延・保護停止条件、関節制限、床摩擦は変更していない。すべて開発用seed310001であり、予約済み受入seedは未使用。

短時間診断を完走しても、片足の有効着地が1回だけの条件がある。速度または両足の着地が不足し、この探索から目標旋回を達成したとは言えない。根本的な10軸の不可能性を証明したものでもない。

| 条件 | 終了時刻 s | 実測yaw速度 rad/s | 左右有効着地 | 結果 |
|---|---:|---:|---|---|
| p0.27_h4_a0.035 | 2.908 | 0.044476989074896195 | [1, 1] | walking_interrupted |
| p0.27_h4_a0.05 | 2.001 | None | [0, 0] | walking_interrupted |
| p0.27_h6_a0.035 | 7.480 | 0.03860018123357091 | [1, 11] | 短時間診断完走 |
| p0.27_h6_a0.05 | 2.662 | 0.038912776544078036 | [1, 0] | walking_interrupted |
| p0.32_h4_a0.035 | 8.680 | 0.09521873684932465 | [11, 1] | 短時間診断完走 |
| p0.32_h4_a0.05 | 2.740 | 0.11790075252542183 | [1, 0] | walking_interrupted |
| p0.32_h6_a0.035 | 8.680 | 0.08113536354748131 | [10, 11] | 短時間診断完走 |
| p0.32_h6_a0.05 | 8.680 | 0.07377183707549531 | [11, 1] | 短時間診断完走 |

## 胴体内の静的CAD確認

既存のXL330ケース寸法20×34×26 mmを、26 mm方向が鉛直になる仮のケース包絡として2個配置した。左右中心Yは±22 mm。ケースの出力軸位置や取付部品を確定したモデルではない。既存の脚姿勢、バッテリーとその取付部品、胴体外形を含むCADに対して実体積交差を計算した（検出閾値0.01 mm³）。

X=-35/-25/-15 mm、Z=65/75/90 mmの9配置は、現在の基板位置ではすべて干渉した。TTL基板の包絡だけをZ方向へ12 mm移す仮配置では、X=-35または-25 mm、Z=75 mmの2配置で、両ケースと既存部品の体積交差がなかった。基板自身の移設先にも交差は検出されなかった。ケース間のY方向間隔は10 mm。

胴体・脚長・足形状・バッテリー位置は変更していない。静的ケース収納の候補が見つかっただけであり、出力軸位置、モータの固定・支持軸受、脚側取付、回転中の干渉、配線・工具の空間、強度、慣性、制御は未設計・未検証。製作可能な12軸設計や歩行成功を示す資料ではない。

## 再現

```sh
python probe_signed_reference.py --cad-design outputs/design_r6_base_collisions --speed 0 --step-period .32 --step-height-mm 6 --residual-scale-rad .035 --constant-action 0 1 0 0 0 0 -1 0 0 0 --out outputs/new_yaw_probe
.venv-cad/bin/python screen_hip_yaw_space.py --design outputs/design_r6_base_collisions --mount validation/battery_mount_review_v2 --out outputs/new_yaw_space.json
.venv-cad/bin/python screen_hip_yaw_space.py --design outputs/design_r6_base_collisions --mount validation/battery_mount_review_v2 --ttl-shift-z-mm 12 --out outputs/new_yaw_space_ttl12.json
```

各実行のソーススナップショット、状態、参照軌道、診断reportを保存した。CAD確認は形状読込と体積交差によるもので、動力学計算ではない。
