# シーケンス用MCUからクリア要求を駆動する候補

STM32G030F6P6のPA11（TSSOP20 pin16）をU14=74AUP1G06GW pin2へ接続する条件を確認。既存端子候補と現行revMの接続を照合し、R14を100 kΩから10 kΩ（TNPW060310K0BYEA、総合公差予算1%）へ置換する接続提案を作成した。現行回路へは未統合。

## 静的な結果

共通LOGIC3V3が3.207〜3.393 Vの有効範囲にある場合だけを評価。既存の保守的MCU漏れ予算10 µA+44×70 nAの全量をこの信号へ割り当て、AUP入力の-40〜85℃上限0.5 µAを加えた。基板表面の漏れは含めない。

| R14 | GPIO高インピーダンス時の信号下限 | High 2.0 V条件 | GPIOがLowへ引く最大負荷 |
|---|---:|---|---:|
| 100 kΩ | 1.83542 V | 示せない | 34.8 µA |
| 10 kΩ案 | 3.06984 V | この予算では成立 | 343.2 µA |

MCU出力の比較条件はVDD≥2.7 V、6 mAまでのCMOS出力仕様を使用。High下限2.807 V、Low上限0.4 Vで、U14の2.0/0.9 V入力条件にそれぞれ0.807/0.5 Vの余裕。10 kΩ案の負荷は6 mA条件未満。全端子電流・MCU消費を含む電源予算は別途必要。

100 kΩで必ず実機故障すると述べているのではない。上記の保守的漏れ予算から既定Highを証明できない、という判断。10 kΩ案もDC比較の通過であり、独立した故障遮断や起動完了を意味しない。

## 実装前に残す事項

GPIOの内部プルを無効とし、出力モードへ切り替える前に出力データHighを設定する。未書込み・リセット中・電源喪失時にはこの静的計算を流用しない。電源投入時の入力立上がり、AUP入力の遷移時間条件、寄生容量、基板漏れ、電源予算、外部リセット、両CLR観測と状態機械を確認する。10 kΩを置いただけで起動シーケンサー完成とはしない。

一次資料：

- [ST DS12991 Rev6](https://www.st.com/resource/en/datasheet/stm32g030f6.pdf)、pp61,64：IO漏れ予算と出力電圧条件。今回再確認。
- [Nexperia 74AUP1G06 Rev12](https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf)、pp5–6：入力電流・論理レベル。85℃欄を使用し、125℃値と混在させない。

再現：

```sh
.venv-engineering/bin/python software/sim/circuits/check_sequence_clear_driver.py --out validation/sequence_clear_driver_reproduce
```

出力先は未使用のものを指定。plan.jsonに先行条件、connection_proposal.jsonに部品・端子・配線変更案、report.jsonに元回路のハッシュと計算結果を保存。製造未承認。
