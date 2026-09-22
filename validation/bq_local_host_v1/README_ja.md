# BQ側ローカル制御ホストの接続確認

**接続候補を追加。製作HOLD。** STM32G030F6P6と周辺10部品を追加し、電池保護側100部品、
全体223部品とした。旧SYS側シーケンサー候補とは別の役割・別の電源・別の端子割当である。
既存ファームウェアをそのまま書き込める設計ではない。実機実装やEPIC7の歩行制御は含まない。

## 選定と接続

一次資料：[ST DS12991 Rev6](https://www.st.com/resource/en/datasheet/stm32g030f6.pdf)。
Figure4のTSSOP20図を目視照合し、Table14のAF6を確認。
電源はBQのREG1、基準はCELL_B_MINUS。主FET後段のSYS電源がOFFでも設定するための構成。
REG1の条件付き3.0〜3.6VはMCU動作範囲2.0〜3.6Vに含まれるが、起動や給電能力の合格ではない。

| 端子 | 割当 | 接続 |
|---|---|---|
| 1 | PB7 / I2C1 SDA AF6 | BQ SDA、既存2.21kΩプルアップ |
| 20 | PB6 / I2C1 SCL AF6 | BQ SCL、既存2.21kΩプルアップ |
| 4 / 5 | 電源 / GND | BQ_CTRL3V3 / CELL_B_MINUS |
| 6 | NRST | 100kΩプルアップ・100nF、TPS3808へ接続 |
| 7 | PA0 | BQ_MAIN_REQUEST_RAW、外部許可ラッチ/AND経由でBOTHOFFへ |
| 8 | PA1 | BQ_AUX_REQUEST_RAW、外部許可ラッチ/AND経由。境界ドライバー未実装 |
| 9 | PA2 | BQ_ALERT_N |
| 17 | PA12 | TPS3431へのハートビート、10kΩプルダウン |
| 18 / 19 | PA13 / PA14 | SWDIO / SWCLK |

PB8は端子1のPB7と同じ外部端子なので同時にSCLとして使えない。
端子20のPB3/PB4/PB5も含め、不使用の共有GPIOはアナログ・プルなしに保つ。
内部クロックを使用する候補。クロック分周・I2Cタイミング・ブート設定はまだ未選定。

デカップリング候補は100nF C0Gと4.7µF X7R。4.7µFは実効容量・REG1安定性・
充電電流が未確認。既存のREG1出力1µFと並列になるため、追加前の起動計算は完成証拠に使わない。
電流予算にはMCU本体だけでなくI2C/ALERT、許可出力、将来の境界回路と監視回路を含める。

## 未完了の設計

- 外部電源監視リセットの時間応答。TPS3808候補の静的検算はbq_host_supervisor_v1を参照。
- CPU停止監視と許可保持回路を追加。電気的適合・復帰処理は未完成。bq_watchdog_latch_v1参照。
- CELL_B_MINUSとPACK_RETURN間の境界ドライバー。AUX端子同士を単純直結しない。
- BQ CRC通信と全設定の読戻し、設定前のFET状態、電源低下時の禁止と再始動方針。
- BQ側のLow出力仕様、MCUのしきい値・漏れ、無給電注入、容量を含むI2C適合。
- 書込み用接続の部品・配置。プローブ給電やPC接地によるシャント迂回を防ぐ構成。

これらは設計事項として#21〜#24に残る。新しい電源監視回路の設定と接続が揃うまで
ホストの実動作試験を合格扱いにしない。レベル・電流・リセットの机上条件が揃った後に
起動／設定失敗／CPU停止のモデルへ進み、同じ未確定条件を使う追加シミュレーションは行わない。

## 再現

```sh
.venv-engineering/bin/python software/sim/circuits/integrate_bq76942_candidate.py
.venv-engineering/bin/python software/sim/circuits/integrate_system_power.py \
  --out schematics/power/system_power_integration_candidate_v1
.venv-engineering/bin/python software/sim/circuits/check_bq_local_host.py \
  --out validation/bq_local_host_v1
```

20端子の処置、I2Cと電源の接続、共有端子の不使用指定、SWD/NRSTの独立を検査する。
接続検査はコードがGPIO設定を実行したことや電源過渡・停止性能を証明しない。

PA3（端子10）はBQ_ARM_EDGEへ変更済み。再起動だけで自動ARMしないこと。
