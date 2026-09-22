# 拡大座面候補の組立検査と余裕

外径6 mmスペーサー候補を対象に、足裏挿入・スライド・スペーサー挿入・ねじ挿入を検査。左右160件に名目体積干渉なし。結果はcompleted/report.json。連続掃引や変形、公差を保証しない。

名目頭部沈み0.8 mmから必要残余0.2 mmを差し引くと、公差・足裏圧縮・摩耗の合計許容枠は0.6 mm。これを満たす実公差値はまだ設定していない。孔と軸の名目半径すきまの和は0.5 mmだが、TPU変形・ねじ曲げを含む横変位の上限ではない。clearance_budget.jsonに未割当項目を保存。

初回は入力CADディレクトリの相対パス処理で検査前に失敗。パスを絶対化する修正後にcompletedへ再実行した。最初のplan.jsonは失敗実行の記録として保存。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/check_sole_lock_assembly.py --cad-dir validation/sole_wide_seat_v1/cad --out outputs/wide_assembly_repro
```

次は拡大座面モデルの収束・接触と、TPU固定穴/傘部の荷重負担を評価する。Issueは未完了。
