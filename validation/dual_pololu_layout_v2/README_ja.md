# メーカー断面図を反映した電源予約形状v2

メーカーreg34c図（2025-10-15）を目視確認。5V版は基板上6.1 mm、
板厚1.57 mm、基板下1.8 mmで合計9.47 mm。v1の9.017 mm予約は不足していた。
これは比較値の訂正であり、v1をそのまま製造に使用しない。

基板端公差±0.3 mmを対向辺の双方へ加え、予約形状43.8×32.4×9.47 mmで再検査。
中心[-25,±31,108] mmを維持した113比較は体積干渉なし、最小隙間2.80 mm。
高さ公差・実装位置の公差は資料未確認で、全公差での合格ではない。

M2用穴φ2.18、穴パターン25.4×38.9 mm、穴位置公差±0.1 mm。
短辺方向の端距離は2.2/4.2 mmで非対称なので、基板中心へ穴配置を単純対称化しない。
DXFの穴座標抽出・端子のネット対応・固定具形状は未完了。
下面1.8 mmの部品に接触しない保持面と絶縁を設計する必要がある。
高電流用穴φ2.18・間隔5 mmはコネクタの電流定格を意味しない。

出典・ファイルハッシュ・読取寸法はschematics/power/dual_pololu_mechanical.json。
PDF/DXFのURLから再取得可能。旧v1の失敗寸法・ハッシュは履歴として保持。
再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_dual_pololu_layout.py --out /tmp/dual-pololu-layout-v2
```
