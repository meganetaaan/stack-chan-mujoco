# 電源基板の取付穴座標

目的は固定具設計へ渡す穴中心と非対称配置を確定すること。終了条件はメーカーDXFの4取付穴を抽出し、外形・穴ピッチを寸法PDFの丸め精度内で照合すること。強度・固定具成立の合格判定ではない。

出典: https://www.pololu.com/file/0J2218/reg34c-drill.dxf
照合図: https://www.pololu.com/file/0J2217/d42v110fx-step-down-voltage-regulator-dimensions.pdf

DXFに単位指定はない。外形1.7×1.25と図面43.2×31.8 mmの照合によりinchとして換算した。穴は円ではなく直交する十字線で、23組を抽出した。未使用BLOCK中の円を穴位置と解釈しない。取付穴4個は端にある大径十字線として識別し、ピッチ38.862×25.4 mmが図面38.9×25.4 mmと一致することを確認した。

DXFビュー左下を原点、長辺をXとした中心座標(mm): (2.159,4.191)、(41.021,4.191)、(2.159,29.591)、(41.021,29.591)。短辺方向の穴列中央は基板中央から1.016 mm偏る。図面の公差±0.1 mmは残り、小数桁を製造精度としない。DXFビューと基板表裏・ロボット座標の対応はまだ確定していないので、左右反転を含む配置変換は行わない。

再現:
```sh
curl -L https://www.pololu.com/file/0J2218/reg34c-drill.dxf -o /tmp/reg34c-drill.dxf
.venv-engineering/bin/python software/sim/structural/extract_pololu_drill.py /tmp/reg34c-drill.dxf --out validation/dual_pololu_drill_v1/report.json
```
依存: ezdxf。入力SHA256を固定し、異なるファイルなら停止する。電気端子のネット名、部品下面の固定具逃げ、ねじ頭、組立工具、保持強度は未評価。次は公式STEPで表裏と穴周辺の部品占有域を照合して固定具を設計する。
