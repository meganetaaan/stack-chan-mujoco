# 手動許可回路とOVP候補の統合接続表

既存manual_rearm_revIの46部品とOVP案12部品を読み、58部品・225端子を
pins.csvへ出力した。両回路の共通ネットはGND、LOGIC3V3、POWER_ENABLE_COMMAND。
同名部品の衝突を避けるためassembly列で識別する。主回路全体の部品数ではない。

左右各5箇所（OV分圧、UV分圧、FAULT受信、UBEC接続、過電流段接続）を未実装として
report.jsonへ明示した。複数端子が同じネットに属するだけで、有効な駆動源があると
判断しない。FAULTの受信、起動監視、保護段、回生吸収器は本接続表で完成していない。

pins.csvは部品番号のレビュー用。電気規則検査、SPICE、基板配線、電源状態や
故障時の成立検証ではない。controllerの現Rev.B図面再確認も残る。
実装する分圧・監視部品を追加後に再生成し、未実装表も実回路に合わせて更新する。

再現：

```sh
.venv-engineering/bin/python software/sim/circuits/export_ovp_integration.py --out /tmp/ovp-integration-recheck
```

出力先は未作成のディレクトリ。入力ファイルのSHA256を結果へ記録する。
