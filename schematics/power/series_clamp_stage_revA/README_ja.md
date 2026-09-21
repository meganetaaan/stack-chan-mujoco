# LT4363-1直列保護の端子接続案

左右各8部品、計16部品58端子の接続をassembly.jsonに記録した。回路CAD・製造用ネットリストではなく、次の回路統合の入力となる接続表。現行revMは変更していない。

入力SOURCE_5V → MOSFETドレイン → ソース → 4mΩ抵抗2個 → SHUNT_LOW出力。SNS/OUTは2抵抗の両端へ接続し、FB分圧は出力側。VCCは電池直結にせず入力側の変換器電源を参照する。12nFタイマーと100nFバイパスは容量案で品番未選定。

[LT4363 Rev.C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf)のMSOP-12/-1端子表を使用。7番と9番はGND。-2の7番OV接続を転用しない。接続検査は電源・ゲート・検出両端・直列抵抗の整合を確認するだけで、アナログ回路動作の証明ではない。

SHDN/UVは未設計インターフェースで、動作回路として放置できない。FLT/ENOUTの受信・プルアップも未選定。単一MOSFETのボディダイオードは逆流を遮断しないため、逆流遮断と負荷側回生吸収を別途統合する。ゲート安定性・過渡・SOA・タイマー最大値・再投入条件の確認まで通電用設計にはしない。

再現：`.venv-engineering/bin/python software/sim/circuits/build_series_clamp_stage.py --out /tmp/series-clamp-stage-review`。
