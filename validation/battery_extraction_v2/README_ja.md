# 電池交換経路の公称CAD検査

直線6方向はいずれも障害あり。上方は胴体外殻、前方はトレイとTab5が遮る。
失敗経路もreport.jsonに保持した。

候補の交換手順は、電源を切って電池配線とストラップを外し、Tab5を取り外した後、
電池を9mm持ち上げ、前方へ51mm移動する。各区間の掃引箱と現行CADとの
体積重なりは0。前方移動の終点で電池後端X69mmとなり、胴体公称前端X64mmを越える。
9mmは高さ73mmのトレイ壁を電池底面74mmで越えるための公称設計値で、
公差・膨張・手指空間の合格値ではない。

掃引箱は直線移動中の箱の占有領域そのものであり、離散姿勢の抜けを避けている。
Tab5自体の取外し手順・ねじアクセス・ケーブル余長、電池端子・膨張・緩衝材は未確認。
旧変換器・TTL形状を保持した検査なので、新UBEC配置後に再検査する。
この結果は交換経路候補を示し、最終組立・実機交換の合格を示さない。
前方に追加の蓋穴を作る前に、このサービス経路を製作図へ反映する。

初期結果は../battery_extraction_v1/、外殻を個別識別した結果は
../battery_extraction_v1_identified/に保存。v2が前方サービス経路を含む現行評価。

再現：
```
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_battery_extraction.py --out NEW_DIRECTORY
```
