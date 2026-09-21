# CSD18540Q5BT実端子と電流方向

TI Rev.Bの1ページTop Viewを目視照合。1/2/3=source、4=gate、5/6/7/8=drain。
露出放熱パッドもdrain。中央パッドをGNDへ接続しない。
メーカーPDFのSHA256は候補JSONに保存。底面実装図の向きと混同しない。
CADフットプリントの中央パッド番号を勝手に9と決めず、ライブラリ採用時に照合する。

接続表はconnections.csv。両FETのdrainはPACK_FET_MID、CHG側sourceは
CELL_POS_FUSED、DSG側sourceはPACK_POS_PROTECTED。

```sh
python3 software/sim/circuits/check_bq76942_pack_paths.py
```

実端子表からsource→drainダイオードとONチャネルの有向グラフを作成。
両OFFは両方向不通、CHGのみONは充電方向に経路あり、DSGのみONは放電方向に経路あり、
両ONは両方向に経路あり。結果はreport.json。
実際のダイオード電圧・漏れ・降伏・ゲートの未確定状態・外部並列経路は含まない。
この検査で回路全体の逆流防止や遮断を合格にはしない。

出典：https://www.ti.com/lit/ds/symlink/csd18540q5b.pdf
