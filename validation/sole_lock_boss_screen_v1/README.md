# 足裏ロック用ナットボスの締付力スクリーニング

左ボスを8×8 mm、z=-19..-11.6 mmで切り出し、底面完全固定・ナット空洞床面へ20 Nを与えた。E=1120 MPa、ν=.35の仮定PETG。1/.7/.5 mmの二次四面体で評価。

最細最大変位0.00328670 mm、最大絶対主応力1.89778 MPa。事前基準0.2 mm/5.6 MPa以内。最後2メッシュ間の変位変化0.379%、応力2.430%で5%/10%基準内。

ただし荷重面は空洞床全面で実ナット4×4 mmの接触ではなく、支持も実際の別体スペーサーの環状接触ではない。20 Nは仮定であり承認締付力ではない。歩行せん断・ねじ・TPU・クリープ・異方性・全体ヨーク強度は未確認。この狭い局所評価だけでIssueを閉じない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_sole_lock_boss.py --out outputs/sole_boss_repro
```

次はナットとスペーサーの実接触面に合わせた境界条件へ変更する。全積分点応力・節点変位・反力はfields_*.npzに保存。
