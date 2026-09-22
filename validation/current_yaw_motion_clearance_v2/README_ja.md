# 現行ヨー支持部の全可動範囲スクリーニング

revBと同じ支持部CADをハッシュ照合し、カプラとロール支持枠の複合形状をヨー±15度で検査。左右61点ずつの距離から、点間の最大移動量0.137mmを差し引いて連続区間の下限を計算した。

既存条件の公差0.2mm/部品、変形0.2mm/部品をさらに差し引いても下限8.119mmで、既存残余隙間基準0.5mmを満たす。これらの公差・変形値はCodexの設計配分で、実際の製造精度・荷重変形の証明ではない。全身の干渉確認ではなく、支持部とこの可動複合部品の組合せに限定する。配線・全締結部品・他の脚部は含まない。

v1は記録軌道の角度範囲、v2はモデル関節限界までを含む。従来のoriginal行は比較用、ribbed_connection行が現行支持部を指す。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out /tmp/current-yaw-review --support-dir validation/yaw_backing_keeper_v2 --include-cradle --step-deg 0.5 --joint-limits
```
