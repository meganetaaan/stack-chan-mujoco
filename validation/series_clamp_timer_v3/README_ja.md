# 2直列WSLF案に対応する故障負荷比較

現行のLT4363代替案で使用するWSLF25124L000FEA×2／脚の比較結果を読み込み、検出抵抗下限と55mV閾値の整合を確認した。温度・はんだ試験変化を条件付きで含む最大電流7.041664Aに対し、12.6V故障時のFET電力比較は約51.51W、12nF典型タイマー式によるエネルギーは68.665mJ。旧v2の66.716mJは旧抵抗構成の履歴とする。

銅配線による電流低下は合格側に見込まない。負方向の検出誤差、未評価の経時変化、実際のはんだ工程、タイマー最悪値、過渡、線形SOAは未確認。この値は最悪故障エネルギーの保証でも、MOSFETの合格判定でもない。容量・保護回路の採用は保留。

再現：
```sh
.venv-engineering/bin/python software/sim/circuits/size_series_clamp_timer.py --out /tmp/series-timer-review --shunt-comparison validation/shunt_stability_comparison_v1/report.json
```
