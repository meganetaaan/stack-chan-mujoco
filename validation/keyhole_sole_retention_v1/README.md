# キーホールによる無変形組立候補（途中干渉で不合格）

既存TPU傘径8 mmを半径4.2 mmの挿入穴へ通し、x方向8 mm滑らせて半径3 mmの保持端へ移動する案。ヨーク形状は左右とも有効な単一ソリッド。旧保持穴候補から各797.135 mm³を追加除去。

下から挿入5姿勢、水平移動5姿勢を左右で検査。ヨークとの重複はないが、x=8 mmではブーツとの重複20.0414 mm³、x=6 mmでは4.76898 mm³がある。したがって現位置でブーツ装着後に無変形組立できるとは認めない。全軌道・公差・サーボとの組立途中の干渉も未評価。

次は突起位置または挿入方向を修正し、滑り戻り防止の機械ロックを追加する必要がある。単に穴を広げ続けず、ヨーク断面欠損の強度と工具アクセスも比較する。候補は未採用、Issue #20は未完了。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_keyhole_sole_retention.py --out outputs/keyhole_repro
```

足裏はsole_retention_concept_v1のSTEP、ブーツはboot_low_head_candidate_v1のSTEPを使用。変更STEPはヨークのみ。組立途中の失敗をreport.jsonに保持。
