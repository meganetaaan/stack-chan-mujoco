# 電池トレイ revB: ベルト横ずれガイド

revA外側に4本のリブを追加。内側間隔11mm、仮置きベルト幅10mmに片側0.5mm。
リブは1.5×1.5×9.5mm、中心X15.3/42.7、Y±6.25、Z67.75。
床や壁を薄くする切欠きは設けず、外側へ一体化した。
単一の有効ソリッド、候補電池・ベルト・ヨー組立・Tab5との体積重なりなし。
接触を含むため距離0は合格クリアランスを意味しない。

ガイドは横ずれを幾何学的に制限する案で、ベルト外れやリブ強度の保証ではない。
実ベルト・バックル・幅公差・重なり・プリント方向・電池面圧は未確定。
0.5mmは配置用仮定で、メーカー公差や実機合否基準ではない。

電池交換経路も本revBで再検査した（validation/battery_extraction_revB_v1）。
Tab5とベルトを外した状態で9mm上げ、前方51mm抜く連続箱掃引は干渉なし。
ケーブル・手指・公差を含む交換の成立は未確認。製作リリース・強度合格ではない。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_battery_strap_guides.py --out /tmp/tray-guide-new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_battery_extraction.py --tray /tmp/tray-guide-new/tray.step --out /tmp/tray-guide-service-new
```
