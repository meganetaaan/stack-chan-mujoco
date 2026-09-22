# 公差を含む最小平坦座面の予備解析

加工部品案 `docs/prototype/mechanical/sole_spacer/specification.json` の最小外径5.95 mm、最大内径2.35 mm、径方向縁落とし各0.05 mmから、平坦座面を外半径2.925、内半径1.225 mmに設定。以前の外半径3、内半径1.15 mmと比べ面積は8.108%小さい。ボス自体の穴半径1.15 mmは変えていない。メッシュ生成器へ内側座面半径を追加し、ボス底面に円環を刻印した。

事前の幾何チェックは体積変化1e-6 mm³以内、CAD座面面積誤差1e-6 mm²以内、メッシュ面積誤差1%以内。今回のメッシュ座面積誤差0.6413%で合格。これは幾何の検証であり強度合格ではない。

1 mmメッシュ、締付力20 N、PETG相当の等方線形弾性E=1120 MPa、ν=0.35、座面の両側法線拘束。最大絶対主応力2.117634 MPa、最大変位0.00447349 mm。荷重合計は20 N、自由自由度残差ノルム2.44e-13 N。全積分点を評価した。公称座面の1 mm結果2.08350 MPaに対して約1.64%増加だが、異なる非構造メッシュの比較であり収束済みの増加率ではない。

未検証: 最小座面でのメッシュ収束、片側接触、スペーサーの弾性と最小厚さ0.85 mm、平面度、偏心、歩行荷重、クリープ。拘束した支持面は引張反力も許すので、実接合の接触成立を証明しない。既存の収束済み公称寸法解析への置換・Issueクローズは行わない。

再現（リポジトリルート、出力先は新規ディレクトリ）:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_sole_boss_bearings.py --seat-radius-mm 2.925 --seat-inner-radius-mm 1.225 --mesh-mm 1 --out outputs/minimum_bearing_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_boss_bearings.py --source outputs/minimum_bearing_repro
```

失敗記録: 最初の応力解析起動ではLD_LIBRARY_PATH指定を忘れ、gmsh読み込み時にlibGLU.so.1不足で終了した。解析は開始されず結果ファイルも生成されなかった。上記の環境変数を指定して再実行し正常終了した。
