# 局所片側接触のメッシュ・ペナルティ感度

事前計画でメッシュ1/0.7/0.5 mm、ペナルティ10000/100000 N/mm³の6条件を評価。全条件でソルバ完了、力の釣り合い、めり込み量の基準を満たした。最後2メッシュの変位変化は0.302%/0.380%、接触圧最大値の変化は1.46%/4.10%でそれぞれ5%/10%の基準内。

ただし最細メッシュでペナルティ10000→100000の変位変化は6.628%となり、1%基準に不合格。元の不合格結果はreport.jsonに保持した。

不合格を受け、追加計画extension_plan.jsonを先に定義して1000000 N/mm³の最細メッシュを実行した。100000→1000000の変位変化は0.7764%で1%以内、力の釣り合い・めり込みも合格。ただし1000000におけるメッシュ収束は未確認であり、全解析条件が完了したとしない。

固定支持体、局所座面、C3D4、仮の20 Nという制限は継続。圧力・変位の数値感度であり、実ヨークや締結強度・材料・クリープ・歩行荷重の検証ではない。製造承認なし。

## 再現

engineering環境とLD_LIBRARY_PATHを使用し、各ケースで次を実行する。出力先は未作成ディレクトリを指定。

```sh
.venv-engineering/bin/python software/sim/structural/probe_boot_seat_contact.py --mesh-mm 0.5 --penalty 100000 --out outputs/reproduce_boot_contact_case
.venv-engineering/bin/python software/sim/structural/evaluate_boot_seat_contact.py --source outputs/reproduce_boot_contact_case
```

plan.jsonの3×2条件とextension_plan.jsonの追加条件を再現する。集計はevaluate_boot_contact_sensitivity.py --source <同じフォルダ構成の親>。追加比較は2ケースのmax_displacement_mmの比の差の絶対値であり、extension_report.jsonに記録。全ソルバデータを同梱。
