# 直列クランプ用検出抵抗の配置案

LT4363代替構成の検討用であり、現行revM保護回路への採用ではない。既存80×25mm基板・C_STOP_IN配置を基礎に、左右WSLP2512候補を配置した。

[Vishay仕様書](https://www.vishay.com/docs/30122/wslp.pdf)の7〜10mΩ用ランド寸法（1.65×3.18mm、間隔4.06mm）を使用。電流用配線は外側、検出線はパッド内側から直角方向へ引き出す。2mm／0.2mmの線幅と取出し位置は設計案であり、電流・熱の適合を確認した値ではない。

2端子抵抗なので、検出線を分離しても端子・パッドの共有抵抗は残る。validation/series_sense_routing_v1の誤差予算に対し実配線の抵抗・熱を確認する。コントローラ、MOSFET、コネクタ等は未配置で、線端は未接続。完成回路・製造用基板ではない。

KiCad 7 CLIで読込み・F.Cu/Edge.CutsのSVG出力成功を確認した。全回路DRCや実装検証の合格ではない。

再現：`.venv-engineering/bin/python software/sim/circuits/place_series_shunts.py --out /tmp/series-shunt-layout-review`。
