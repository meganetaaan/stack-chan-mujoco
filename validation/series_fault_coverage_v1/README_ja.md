# 直列保護の故障条件の適用範囲

メーカー表のVCC=12V条件を用いた抵抗下限での比較では、出力0VでFET電力53.616W、出力3Vで62.988Wとなる。前回の過電圧比較51.510Wだけでは全故障を代表できない。シャント電圧をFET両端電圧から控除し、入力電力＝FET＋抵抗＋出力の整合を確認した。

これらも全条件の保証上限ではない。通常5V・故障12.6Vでの電流制限保証、出力1〜3Vの移行域、実装・配線・検出誤差、過電流時の遮断時間は未確認。過電圧用の典型タイマー時間をこの電力へ掛けて最悪エネルギーとはしない。

MOSFETの線形SOA図は引き続き未確認。メーカー別URLからのPDF取得もHTTP403で、画像座標を読めたとは扱わない。通電用部品の採用判定は保留し、次の確認は電流制限の実使用条件への適用と、過電流タイマーの時間上限を含む動作点へ絞る。

資料：[LT4363 Rev.C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf)、電気特性表4ページ。

再現：
```sh
.venv-engineering/bin/python software/sim/circuits/check_series_fault_coverage.py --out /tmp/series-fault-review
```
