# 外径6 mmスペーサー候補

スペーサー外径4→6 mm、TPUの通過穴4.4→6.4 mm。厚さ0.9 mm・ねじ頭沈み0.8 mmを維持。ヨークとナットボスの形状は変更せず、支持面を拡大。左右の完成状態で部品重複なし。

20 N、1 mmメッシュ、剛な法線支持の同条件で最大絶対主応力2.08350 MPa、変位0.00443851 mm。外径4 mmの同メッシュ6.53959 MPaから低下。ただし別々のメッシュで、収束・片側接触・スペーサー自身の変形は未確認。仮許容5.6 MPa内という予備結果のみ。

穴拡大に伴うTPU横荷重/切欠き強度、部品公差、組立経路、スペーサー製品仕様は未評価。ねじ頭はスペーサーに座りTPUを直接締め付けない。部品は製造リリース前。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_sole_slide_lock.py --rigid-seat --separate-seat --seat-radius-mm 3 --out outputs/wide_seat_repro
.venv-engineering/bin/python software/sim/structural/mesh_sole_boss_bearings.py --seat-radius-mm 3 --mesh-mm 1 --out outputs/wide_bearing_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_boss_bearings.py --source outputs/wide_bearing_repro
```

初回はmeshファイル名1.0と1の不一致で解析開始前に失敗。生成コードの書式を統一し、同一メッシュを正しい名前へ変更して解析した。結果の再生成は上記コマンドで可能。
