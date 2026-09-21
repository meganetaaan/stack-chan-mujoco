# D42V110F5×2の公称配置比較

旧UBEC中心[-25,±31,108] mmを保持。長辺をXへ向け、
43.2×31.8×9.017 mmの直方体を配置した。
高さは公表9 mmと0.355 inch換算の大きい方を使用したが、製造公差の上限ではない。

v7固定52部品、既存3S電池・トレイ・Tab5・TTLと左右モジュール相互を合わせて113比較。
追加体積干渉なし、最小公称距離3.10 mm（TTL）。位置探索や外形拡大は行っていない。

基板の予約直方体であり、端子台・はんだ・配線曲げ・固定具・絶縁距離・放熱は含まない。
既存UBECを取り除く置換案なので旧UBECと重ねて干渉判定していない。
動作部の全姿勢・取り外し経路・保護回路基板は未確認。
次は取付穴・高電流端子・部品高さをメーカー寸法図で照合して保持方法を決める。
3.10 mmを必要絶縁距離・熱余裕の合格値とは扱わない。

比較用の左右STEPを保存。正式配置・BOM・MuJoCo・質量台帳のポインタは未変更。
再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_dual_pololu_layout.py --out /tmp/dual-pololu-layout
```
寸法出典はschematics/power/dual_pololu_candidate.json。確認条件と入力ハッシュはplan/report.json。
