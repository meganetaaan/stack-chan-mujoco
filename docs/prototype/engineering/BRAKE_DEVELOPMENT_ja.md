# 回生吸収回路の開発評価

Issue #22〜#24の途中結果。保護回路の完成・実部品の適合を示すものではない。
従来の回生吸収なしの失敗結果は `validation/supply_development_v1/` に保持する。

## 回路と事前基準

5 Vバスに4.7 Ωの抵抗とローサイドMOSFETを直列接続する。
2.495 V基準、11.8 kΩ/10 kΩ分圧、ゲートから1 MΩの正帰還によりヒステリシスを与える。
コンパレータのオープンコレクタ出力と2.2 kΩプルアップでゲートを駆動する。
接続の正本は各ケースの `brake.cir`、実行前に保存したパラメータと基準は `plan.json`。

通常動作は従来どおり4.75〜5.25 V。1 A・20 msの回生故障注入は4.75〜5.8 Vとし、アクチュエータの6 V上限から0.2 Vの余裕を設けた。
故障注入に対する新しい設計基準であり、旧回路の不合格判定を変更しない。
抵抗の瞬時電力10 W以下、1試行の抵抗消費エネルギー0.15 J以下、エネルギー収支相対誤差1%未満を事前設定した。
これらは設計用基準であり、抵抗の購入仕様・実装温度の保証値ではない。

## 結果

|条件|最大バス電圧 V|抵抗エネルギー J|抵抗ピーク W|開発基準|
|---|---:|---:|---:|---|
|回生・公称|5.4760|0.10935|6.1944|合格|
|回生・遅い作動側|5.5924|0.11133|6.0401|合格|
|回生・早い作動側|5.3817|0.10886|6.2880|合格|
|既存12軸負荷・早い作動側|5.1440|約0|約0|合格|
|吸収回路の開放故障|25.7162|約0|約0|電圧不合格|

通常負荷では意図しない吸収動作はなく、全ケースのエネルギー収支相対誤差は9×10⁻⁶未満。
正常な吸収回路の3条件は限定的な感度確認であり、全公差・全温度・全負荷の最悪条件ではない。
開放故障でも規定の回生電流を継続して注入している。25.72 Vは実モーターの到達電圧予測ではない。

## 実部品との対応と限界

- [TI LM393B](https://www.ti.com/lit/ds/symlink/lm393.pdf)を念頭に、オープンコレクタ、オフセット、公称0.8 mAの回路負荷をモデル化した。応答時定数5/20 µsは保証値ではなく解析仮定。
- [TI TL431](https://www.ti.com/lit/ds/symlink/tl431.pdf)のB精度を念頭に基準電圧±0.5%を変化させた。温度変動、カソード電流依存、起動・安定性は未反映。基準源は理想的な制限電圧源であり、実部品検証には使えない。
- [Infineon IRLML6344TRPbF](https://www.infineon.com/assets/row/public/documents/24/49/infineon-irlml6344-datasheet-en.pdf)は候補。データシートのVDS上限30 V、VGS絶対最大±12 V、25℃でのオン抵抗最大37 mΩ（VGS=2.5 V）を確認した。解析の50/100 mΩは温度等を想定した仮定で、温度全域の保証値ではない。
- MOSFETモデルは2.5 Vで切り替わるスイッチ。しきい値、部分導通、ミラー効果、スイッチング損失、SOAは未再現。ゲート容量1.5/2 nFも等価仮定。
- **開放故障時のゲートはバス側へ引き上げられ、候補MOSFETの±12 V定格を超える可能性がある。ゲート保護も未成立。** このモデルの高電圧領域を実回路の健全性の証拠にしない。
- 抵抗の型番・温度上昇・繰返し回生の平均電力・筐体内放熱は未確定。10 Wという評価基準だけでは部品選定を完了できない。
- 吸収回路の開放故障に対して独立した対策が必要。電源入力を切るだけではモーター側の回生を除去できないため、モーター側に残るエネルギーと遮断位置を含めて設計する。

## 再現

[環境構築](ENVIRONMENT_ja.md)後、リポジトリルートで実行する。出力先は未作成のディレクトリを指定する。

```sh
.venv-engineering/bin/python software/sim/circuits/run_brake_probe.py --out outputs/brake_nominal_new
.venv-engineering/bin/python software/sim/circuits/run_brake_probe.py --out outputs/brake_late_new --corner late
.venv-engineering/bin/python software/sim/circuits/run_brake_probe.py --out outputs/brake_early_new --corner early
.venv-engineering/bin/python software/sim/circuits/run_brake_probe.py --out outputs/brake_normal_new --case normal --corner early
.venv-engineering/bin/python software/sim/circuits/run_brake_probe.py --out outputs/brake_open_new --case brake_open
```

`validation/brake_development_v1/` に全5ケースの計画、netlist、ログ、波形、判定と実行スクリプトのスナップショットを保存。
`trace.dat.gz` はngspiceの全列、`trace.npz` は評価用の選択列。保存時に両者の時刻・バス電圧の完全一致と全ファイルのSHA-256を確認した。
