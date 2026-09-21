# 状態制御とGPIO出力の統合

power_runtime.cでC状態コアと出力反映処理を接続した。
出力書込み失敗はio_faultへ記憶し、その後の正常入力でもCLEAR要求を維持する。
初期化失敗も同じ扱いとし、動作中に故障フラグを解除するAPIは設けない。
boot関数は新しい起動時だけ呼ぶ前提で、呼出し側の実装は未完了。

統合時に、WAIT状態で実CLRがLowでも許可Lowを確認済みとする経路を修正。
実CLR解除を観測してから新しい許可を待つ。
GPIO書込み前に採取した入力で、書込み後の物理状態を確認したことにはしない。

検査は実際のC関数を模擬GPIOへ接続して行った。
正常起動、遅れたCLR解除、書込み失敗、その後の5回の正常入力、初期化失敗を確認。
変更後の状態モデル6,144遷移とC一致検査もpower_sequence_model_v3・power_sequence_c_v2で実施。

未完了：実MMIO、起動コード、実タイマー、入力の電気的有効性、非同期故障記憶、
CPU停止時の外部遮断。今回の故障記憶はCPUが処理を続ける場合のソフトウェア機能。
物理的な停止時間や通電可を証明しない。

再現（リポジトリルート、未作成の出力先）：

```sh
python3 software/sim/circuits/check_power_runtime.py --out /tmp/power-runtime-check
python3 software/sim/circuits/check_power_sequence_c.py --out /tmp/power-c-check
python3 software/sim/circuits/check_power_sequence_model.py --out /tmp/power-model-check
```
