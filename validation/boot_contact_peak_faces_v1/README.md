# 接触圧最大値を含む面の追跡

CalculiX DATの最終接触圧から最大値のslave element/faceを取得し、入力ブーツメッシュの該当三角面へ対応付けた。1/0.7/0.5 mmで最大圧力は5.958389 / 6.356316 / 5.524037 MPa。

3ケースとも該当面は外周半径3 mmにも穴半径1.15 mmにも接していない。頂点半径はおよそ1.85〜2.28 mmで、面の位置はメッシュごとに変わる。外周や穴縁の特異点と断定して最大値を除外する根拠はない。接触面の離散化・両面メッシュ対応・荷重面の分割の影響を調べる必要がある。

DATはこの出力形式で接触評価点の座標を与えないため、保存した座標は三角面の頂点と重心であり最大値の正確な座標ではない。幾何診断のみで、収束基準変更や製造承認は行わない。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/locate_boot_contact_peaks.py --out outputs/reproduce_contact_peak_faces
```

新規出力先を指定。参照DAT・メッシュのSHAと全対応情報を保存。
