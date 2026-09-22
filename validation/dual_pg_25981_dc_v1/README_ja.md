# TPS25981から左右PG受信回路への定常レベル比較

既存PG受信計算を、TPS25981のPG漏れ上限3µA、弱プルアップ時Low上限0.8Vへ変更。
資料SLVSGG6Dの8ページを参照。元のTPS259823条件は引数省略時の既定値として保存。
左右受信器は同一回路なので1チャンネルの端点計算を共用する。

既存の電源比較3.207〜3.393V、抵抗総誤差±1%、比較器入力電流±25nAを保持。
64端点でHigh下限0.597873V > 立上り最大0.404V、Low上限0.207730V < 立下り最小0.387V。
PGの吸込み電流比較上限22.8735µAは26µAの仕様試験点以下。

この結果は定常条件の比較。試験点間の電流依存性、PG説明の型番適用範囲、
供給電圧全域、比較器の起動不定時間、断線、パルス捕捉、左右合計の電源負荷は未確認。
入力が不定でも正常と読めないことを保証する結果ではない。

```sh
.venv-engineering/bin/python software/sim/circuits/check_pg_receiver_budget.py --out /tmp/pg-25981-repro --detector-pdf /tmp/pg-tps3700.pdf --efuse-pdf /tmp/tps25981-screen.pdf --efuse-part TPS25981 --pg-leak-max-a 0.000003 --pg-low-max-v 0.8
```

PDFはそれぞれTI公式のtps3700.pdfとtps25981.pdfを用意する。評価に用いた版のハッシュはreport.json。
比較器の既存条件の出典はvalidation/pg_receiver_budget_v1。製造可・全故障対応の判定ではない。
