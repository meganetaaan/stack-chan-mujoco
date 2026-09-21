# 解除タイマーMRの駆動バッファ

HCS11→SN74LVC1G34DBVR→TPS3808 MRを候補へ反映。共通電源3.207〜3.393 V、入力条件成立、追加負荷なしという前提で静的インターフェースを照合した。

HCS11が駆動する入力漏れ最大2 µAは20 µAの出力保証条件内。High余裕1.107 V、Low余裕0.700 V。LVC1G34が吸い込むMRプルアップ電流上限48.47 µAは100 µAの規定負荷内で、MRのHigh／Low余裕はいずれも0.8621 V。3.3 VにないmA駆動点の補間は不要になった。

入力条件や電源が有効でない時まで保証した結果ではない。LVC入力の10 ns/V制限、HCS出力の実負荷時エッジ、電源投入・低下、独立クリア経路は残る。停止信号をこの解除タイマー経由にしない。バッファ出力へ別のプッシュプル出力を並列接続しない。前回のHCS直結案は不承認のまま保存する。

再現：`python3 software/sim/circuits/check_release_mr_buffer.py --out <未作成ディレクトリ>`。planを計算前に保存し、解析的な端点確認で終了する。追加負荷が変わらない限り波形掃引は行わない。

出典（2026-09-21確認）：[TI LVC1G34 SCES519O](https://www.ti.com/lit/ds/symlink/sn74lvc1g34.pdf)、[TI HCS11](https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf)、[TI TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf)。#24／製造リリースは未承認。
