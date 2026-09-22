# v4の公称座面・頭/軸検査

16座面の欠損面積は既存0.001 mm²基準内。ねじ頭/軸対板・支持の32交差も既存0.01 mm³基準内。旧v3の座面欠損は形状変更により解消した。

これは公称幾何48項目だけの確認。プリロード、座面面圧、板曲げ、樹脂クリープ、実部品公差、首下丸み、ナット/工具/周辺干渉は証明しない。manufacturing_release/strength_verifiedはfalse。

再現：check_yaw_plate_seats.py --relocated --candidate-version v4 --front-axis-mm 8.1 --out <新規先>。実行環境は他CAD検査と同じ。
