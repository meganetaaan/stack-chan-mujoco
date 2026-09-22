# 左右の電圧窓監視を統合

revEへ `source_window_monitor_revB` の14部品を追加した。87部品・287端子。各TPS3700はSTOP_AUX3V3で動作し、同じ側の電源IC入力（変換器出力）を監視する。左右監視点・監視出力の取り違えや短絡がないことを配線別名を含めて確認した。

生の監視出力LEFT/RIGHT_SOURCE_WINDOW_ODは、ENやRESET_Nへ直結していない。監視ICは起動後最大450 µsまで出力が未確定で、電源喪失時も有効性の制約がある。これを既に起動条件を満たしたSOURCE_VOLTAGE_VALIDと同じ信号にしてはならない。

次の接続は、停止補助電源の有効性と監視ICの起動待ちを満たしてから左右の状態を受け入れる状態回路。異常後の正常復帰だけで再始動せず、既存のクリア確認と新たな手動操作を必要とする。状態回路の実装と時間条件は未完了。

追加した2個の監視IC・プルアップ・容量はSTOP_AUX3V3の電流予算へ加える。分圧抵抗の消費は各REGULATOR_OUT側に計上する。全電源の最大電流・熱・過渡・故障保護は未確認。実部品未選定の抵抗・容量があり、製造リリースではない。

再現:

```sh
.venv-engineering/bin/python software/sim/circuits/integrate_source_window_monitors.py --out /tmp/servo-power-rearm-revF
```
