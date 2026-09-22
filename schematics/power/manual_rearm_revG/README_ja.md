# 手動復帰候補revG：PG受信部を追加

40部品141端子。revFの既存32部品の接続を保存し、U12 TPS3700DDCR、U13 Nexperia 74LVC1G17GV、R10〜R13、C12/C13を追加した。PGをRESET_NやENへ直結しない。起動監視本体は未実装で、通電許可ではない。

## 接続

- 主eFuse pin13 → MAIN_EFUSE_PG。R10=150 kΩでLOGIC3V3へ。
- R11=1 MΩとR12=330 kΩで分圧しU12 pin3へ。U12 pin5とU13 pin5は同じLOGIC3V3。
- U12 pin1 → PG_CONDITIONED_OD、R13=10 kΩでLOGIC3V3へ。U13 pin2で受け、pin4 → PG_CONDITIONEDを起動監視へ渡す。
- 受動部品は値候補。注文コードと温度を含む総合公差は未確定。

## 静的比較と範囲

分圧側は`validation/pg_receiver_budget_v1/`。出力側はU12漏れ0.3 µA＋U13入力漏れ1 µA、10 kΩ±1%を比較するとHigh下限3.19387 V。Low時の負荷上限は343.727 µA（プルアップ全電圧＋入力漏れ）で、U12の1.3 V給電／0.4 mA規定点以内。Low上限0.25 Vを比較に用いる。

U13公表しきい値の列挙点全体で最大VT+=2.79 V、最小VT−=0.46 Vとの余裕はHigh0.40387 V、Low0.21 V。ただし離散供給電圧点から実電源区間への極値保証は未確認。出力先の負荷としきい値は起動監視の部品選定時に確定する。U13はSchmitt入力で入力立上り／立下り時間制限なし。出典は個別候補JSONのメーカー資料。

## 起動時の有効性

U12はVDDが1.8 Vを超えてから最大450 µsの間、正しい出力を保証しない。単調投入で共通LOGIC3V3が安定し、U7の180 ms以上のリセット期間が正しく成立する場合、450 µsの待ち時間を覆える。ただしこれは条件付きの順序比較である。

短い電源低下、局所的電源断、U7の停止伝搬とラッチの最小クリア幅、RESET_N外部駆動は未確認。PGが一瞬HighでもSTART/RUNへ進まないという全電源順序の保証は未完了。PG配線・OUTA配線の断線はプルアップにより正常側へ寄るため、断線検出を実装したとはしない。これらは#24の机上残件。

## 再現と終了条件

```sh
python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --clamp-cause --permission-gate --pg-receiver --out /tmp/manual-rearm-revG-review
```

新規出力先を使う。今回の終了条件はPG入力から起動監視入力までの端子接続を具体化し、既存停止接続を変えていないことを照合すること。回路全体の合格、起動監視実装、実機試験の完了条件とは別。
