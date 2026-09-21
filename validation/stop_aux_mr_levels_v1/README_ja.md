# 停止用3.3 V領域のU11→U10 MR電圧

統合revBの接続を読み、U11出力とU10 MRが同一信号、両ICの電源が同じSTOP_AUX3V3であることを確認した。既存の設計区間3.207〜3.393 Vを使い、同じ電源電圧に対してHigh/Lowの余裕を計算した。

TPS3808 MRはHigh 0.7×VDD以上、Low 0.3×VDD以下。内部プルアップは最小70 kΩ。74LVC1G17は100 µA負荷でHighがVCC−0.1 V以上、Lowが0.1 V以下。MRプルアップによる吸込み電流上限48.47 µAで、100 µA条件内。High/Lowとも最小余裕0.8621 V。

出典:
- TI TPS3808 SBVS050N 6.5: https://www.ti.com/lit/ds/symlink/tps3808.pdf
- Nexperia 74LVC1G17 Rev16.1 表7: https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf

電源が有効でU11入力が正しい論理を示すという条件下で、この出力インターフェースは静的に成立する。U9→U11入力、途中電圧、電源投入順序、短パルス、出力容量、停止遅延の評価ではない。電源区間そのものも負荷・LDO・容量を含めた最終保証ではない。

再現: `.venv-engineering/bin/python software/sim/circuits/check_stop_aux_mr_levels.py`。
