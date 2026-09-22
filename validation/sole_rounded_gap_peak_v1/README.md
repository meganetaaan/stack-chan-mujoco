# 丸み候補の接触圧ピーク位置

保存したsole_rounded_contact_v1の変位を使い、master/slave投影三角形の全重なり多角形頂点でP1鉛直隙間を評価。三角形ごとの面積被覆誤差最大2.44e−11で、1e−8基準内。

最小隙間−4.8303891e−5 mmは、座標(33.3872220, 8.4401992, −19)の一致した平坦接触三角形頂点に発生。初期隙間0、boss鉛直変位−0.0001487445 mm、spacer鉛直変位−0.0001004406 mm。ペナルティ1e6 N/mm³との積は48.30389095 MPaで、保存した切断積分解析の最大圧と整合する。初期干渉の修正量ではなく、今回の変位解の差である。

この位置診断だけでは、実接触圧の正しさやピークのメッシュ収束を示さない。ピークを除外せず細分化比較へ渡す。微小変形・固定鉛直法線・線形三角形・数値クリッピングの範囲であり、実曲面・有限回転の厳密な接触境界ではない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/bound_projected_contact_gap.py --mesh-dir validation/sole_rounded_local_mesh_v1 --source validation/sole_rounded_contact_v1 --mesh-mm 0.5 --out outputs/sole_rounded_gap_peak
```

CLIに入力ディレクトリ/サイズ指定とハッシュを追加。従来の既定入力と隙間計算法は維持。
