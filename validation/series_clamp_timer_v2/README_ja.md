# 検出抵抗の温度変化を反映したタイマー評価

series_sense_resistor_v1の最大比較電流6.842A／MOSFET電力50.048Wをタイマー計算へ接続した。参照するクランプ設計のSHA-256が一致しない場合は計算を拒否する。

10nFの典型時間1.111msで55.60mJ、12nFの1.333msで66.72mJとなる。電圧とタイマー典型式は未変更で、電流増加に応じてエネルギーだけが増えることを確認した。保証最大時間・エネルギー上限ではない。

PSMN2R4-30YLDのSOA図を今回も検証できず、採用判断は保留。メーカーPDFへの直接取得はHTML、販売店のメーカーPDF取得はHTTP/2エラー、閲覧ツールのスクリーンショットは失敗した。図の数値は転記・推定していない。図の確認に加え、適用温度・保証タイマー上限が必要で、エネルギー総量だけをSOAの代用にしない。

再現：

```sh
.venv-engineering/bin/python software/sim/circuits/size_series_clamp_timer.py --sense-report validation/series_sense_resistor_v1/report.json --out /tmp/series-timer-v2-review
```
