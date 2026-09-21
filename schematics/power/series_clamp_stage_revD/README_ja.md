# 専用停止バッファ接続と直列抵抗修正

74LVC1G17GVを専用バッファとして追加。既存の主EN配線に負荷を追加せず、左右SHDNを駆動する。入力に10kプルダウン、電源に100nFの候補を置いた。指令・LOGIC3V3は未認定の外部インターフェース。

[Nexperia Rev.16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)のVCC3V、IOH=-24mA、-40〜85℃のHIGH下限は2.3V。前回の2.4Vという仮置きを修正した。直列1k・プルダウン10kの公差端では、SHDN入力電流を0としても2.087Vとなり2.1V条件を満たさない。この失敗値を保存した。

直列抵抗を470Ωへ変更すると同条件で2.195Vとなる。ただしSHDNのHIGH入力電流、実際の電源/温度/出力負荷、指令側の入力閾値・10k負荷を確認するまで全接続の合格ではない。125℃までの別の出力電圧保証は転用しない。

低電源時、出力固着、クールダウンを含む再投入は未確認。パッシブの品番も未確定。製造承認は保留。

再現：`.venv-engineering/bin/python software/sim/circuits/add_series_shutdown_driver.py --out /tmp/series-driver-review`。
