# クリア要求プルアップの回路データ候補

revMを基にR14だけをTNPW12061K00BYEA（1 kΩ）に変更した比較用アセンブリとBOM。98部品・317ピンの接続は維持され、他部品の変更がないことを生成時に確認する。既存R_STOP_INPUTと同じ注文候補を使用する。

従来100 kΩは保存済み漏れ予算でHighを保証できず、直流対策の10 kΩは50 pF仮定で立上がりが不足した。1 kΩの計算根拠は`validation/sequence_clear_edge_v1`。これは部品・接続をレビュー可能にする候補であり、正式な回路図や現在版を置き換えない。

採用前条件: 総容量50 pF以下の根拠、基板漏れを含むHigh電圧、Low時3.428 mAのGPIO・電源収支、入力遷移規定の適用、温度・経年を含む抵抗±1%枠を確認する。起動制御MCUは未統合。リセット、電源投入・低下、故障時動作の適合は別途必要。

再現（出力先未作成）:

```sh
.venv-engineering/bin/python software/sim/circuits/package_clear_pullup_candidate.py --out /tmp/clear-pullup-candidate
```

currentポインタはrevMのまま。製造リリース・#24完了ではない。KiCad回路図・基板へは未反映。
