# 最新電源配置でのTab5取り外し経路

## 再現

リポジトリルートで、未作成の出力先を指定する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_tab5_service_clearance.py --packaging-report board/mechanical/prototype/power_packaging_revA/report.json --out /tmp/tab5-service-recheck
```

統合配置に記録した全入力STEPのハッシュを照合してから検査する。
旧converterを残したままUBECを重複追加することを避け、最新トレイrevB・
左右UBEC・ベルト包絡・電池・TTL・ヨー支持部を対象にした。

## 結果と設計判断

Tab5全体の境界箱を前方(+X)17mm移動した連続掃引領域について、
対象7群との交差体積は全て0。途中姿勢の離散サンプルではない。
最小距離はヨー支持部との0.4mm。他は8.55mm以上。
これは公称形状の取り外し経路の確認であり、取り外し可能な組立の認定ではない。
17mmは既存本体前面X=64mmからさらに5mm外へTab5後面を出す仮置き距離。
手・工具・コネクタの必要空間から決めた距離ではない。

電池交換の候補順序は、無給電にして配線を外し、Tab5固定を解除して前方へ退避、
ベルトを解除し、電池を9mm上げて51mm前へ取り出す。
後半の電池経路は`validation/battery_extraction_revB_v1/`の証跡による。
固定具と配線の実設計が済むまでは実機作業手順として使用しない。

次の設計ゲートは0.4mmに対する寸法公差・組立ずれ・支持部変形の積み上げ。
必要余裕が残らなければ局所固定形状または取り外し方向を変更する。
無干渉という結果だけを理由に既存の動作余裕基準を引き下げない。
支持ねじ・工具、UBEC固定、追加保護基板、配線、実ベルトの留め具は未モデル化。
これらを追加した時点で同じ掃引検査を更新する。
