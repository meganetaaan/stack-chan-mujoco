# シーケンスクリア駆動を加えた194部品候補

[前版191部品](../protected_pack_system_candidate_v2/README_ja.md)へSN74LVC1G07DBVR、入力10 kΩプルアップ、100 nFを追加。STM32G030F6P6の空き11番PA4をCTRL_RESET_RELEASE_Nへ割り当てた。旧191部品のピン差分はMCUのこの1ピンのみで、既存停止・手動許可回路は保持。

| 制御状態 | SYS側クリア要求とリセットへの寄与 |
|---|---|
| PA4 High | バッファ出力開放→既存1 kΩでクリア要求High→RESETをLowへ保持 |
| PA4 Low | バッファ出力Low→クリア要求Low→この経路はRESETを開放。他の停止/リセット源は有効 |
| PA4高インピーダンス、CTRL有給電 | 入力プルアップでHighへ戻す候補 |
| CTRL完全無給電、SYS有給電 | バッファIoff動作で出力開放。漏れ込みのHigh余裕は要確認 |

信号名は「リセット解除許可がLowで有効」を表す。Lowを出すだけで駆動が開始する構成ではなく、主許可/手動復帰などの条件が別に残る。ファームウェアは初期状態を解除禁止とし、起動条件を確認してからLowを出す契約とする。今回ファームウェア実装は行わない。

[TI SN74LVC1G07 RevAG](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf)のDBV端子表・L→L/H→Zの機能表とIoff機能、[ST DS12991 Rev6](https://www.st.com/resource/en/datasheet/stm32g030f6.pdf)のTSSOP20/PA4対応を照合。真理値表はアナログ動作の合格証拠ではない。

未完：MCUリセット時の端子状態/漏れ、バッファ電源遷移、出力漏れと1 kΩのHigh/Low余裕、入力容量と遷移速度、RESETのファンアウト/保持時間、追加負荷と容量の電源予算。CTRLが0 Vから有効範囲へ動く間の保証をIoff規定から外挿しない。最新の起動プローブへ追加負荷は未反映。

未接続境界はTab5許可・UV警告・左右レギュレーター許可の4ネット。既存12参照の部品未選定、保護協調・過渡解析も残り、動作回路/製作承認ではない。製作HOLD。

```sh
.venv-engineering/bin/python software/sim/circuits/connect_sequence_clear_driver.py
```
