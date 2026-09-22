# 実ベルト候補を反映した包絡検査：不合格

候補はVELCRO ONE-WRAP 31013（黒、幅1/2inch=12.7mm、5yardロール）、200mm切出し×2本。
[メーカーTDS Rev05](https://www.velcro.com/wp-content/uploads/sites/44/2019/08/General-Use-VELCRO%C2%AE-Brand-ONE-WRAP%C2%AE-Tape-TDS.pdf)で品番と幅を確認。
同資料の剥離0.5PIW・せん断23PSIは平均参考値。許容荷重に使わず、18lb等の別資料値も流用しない。
資料の厚さ上限は確認できていない。単層2.5mmは設計空間予約で、メーカー保証値ではない。
旧案1.5mmを確定仕様として扱うのをやめ、閉じ部の二重厚み5mmを全周に予約した。
ガイド幅は13.7mmへ変更。公称幅に対する左右0.5mm余裕も造形保証ではない。

事前条件plan.jsonに対し、トレー単体・電池・ベルト間の体積干渉はないが、周辺10組で干渉。
左右のヨー支持、金属板、ねじ・ワッシャ・ナットに重なる。採用不可。
閉じ部をどこに置いてもよい空間は確保できない。

寸法計算の目安：内周矩形28.4×37.5mm、単層中心線を矩形で置くと周長141.8mm、
200mmとの差58.2mm。ただし実曲げ・重なり外周・締付けの影響を含まないため有効係合長ではない。
200mmは加工候補であり、組立前に経路と必要係合長の検証が必要。
追加試行v3では厚みを変えず閉じ部を上側へ限定して原因を区別する。

再現：`LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_lb020_retention_v2.py`。
