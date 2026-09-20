# ナット座局所モデルの片側接触プローブ

左後ナット座の0.7 mmメッシュをC3D4としてCalculiXへ渡し、座面下面を完全固定した支持ブロックと摩擦なし片側接触させた。ナット公称接触面に合計20 Nの固定方向節点荷重を面積配分で与える。面内剛体運動のみ最小拘束。ペナルティ係数は100000 N/mm³。

計算完了、支持反力20 N、力の釣り合い相対誤差3.015e−13、最大めり込み2.218285e−5 mmで事前基準を満たした。出力された接触点の圧力範囲は0.007823〜2.218285 MPa。今回の出力点では隙間が負で、離間を観測したケースではない。離間を許す定式化と、実際に開離・再接触を検証することは別である。

このモデルは固定支持体への片側接触で、実ヨークの弾性やナットの圧力再配分は含まない。単一の一次四面体メッシュ、仮の20 N、局所切断形状であり、二次要素の前回結果と応力値を直接比較しない。メッシュ・ペナルティ感度、開離・再接触、歩行荷重、締結予圧・クリープ・強度の検証は未完了。製造承認なし。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/probe_boot_seat_contact.py --out outputs/reproduce_boot_contact
.venv-engineering/bin/python software/sim/structural/evaluate_boot_seat_contact.py --source outputs/reproduce_boot_contact
```

新規出力先を指定。入力デッキ、ソルバ出力、実行ファイルSHA、評価値と事前条件を保存した。ソルバ終了だけで合否を判断せずevaluation.jsonを確認する。
