# 遅延回生時の吸収素子負担

電池切離し80 ms、回生注入300 msから1 A・20 msの既存ケースで、各回生抵抗と理想MOSスイッチの端子電力をngspice内部時間点で積分・最大値測定した。対象窓80 ms〜1 s。表示波形のピークから評価しない。

主枝の抵抗: 最大6.0315 W、吸収エネルギー0.0812168 J。
主枝の理想MOSスイッチ: 最大0.1222188 W、エネルギー0.00164573 J。
副枝の抵抗負担はほぼゼロ。この試験の注入を2本均等負担として定格を選定してはいけない。

バス最大5.588374 Vは追加計測前と一致。今回の事前基準は有限・非負の負担とバス6 V以下であり、部品の熱・パルス定格合格を示さない。MOSは抵抗性理想スイッチのため、スイッチング損失、SOA、温度依存性を含まない。全電源のエネルギー収支を閉じた結果ではない。

初回analysis/ではngspiceが測定名を小文字で出力し、Pythonの大文字J/Wを含む検索で後処理が失敗。ngspice自体は正常終了。ログ・入力・表示波形を保持。検索を大文字小文字を区別しないものへ修正し、completed/で再実行した。failed_attempt.jsonに後処理失敗を明記。

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/disconnect_absorber_energy
```

保存した生ログと表示波形は可逆gzip、圧縮前後ハッシュはmanifest.json。ngspice42。Issue #24は未完了。
