# 状態モデルの矛盾した入力順序への修正

旧版e14358bでは次の経路を受け入れていた。
1. 許可Lowを一度観測した後、ARMEDがLowのまま許可Highとなり、後からARMEDだけHighになるとSTARTへ進む。
2. 実CLRがLowのままでも新しい許可でSTARTへ進み、状態モデルの給電要求がHighになる。

前者は矛盾した許可を保持する欠落、後者はリセット観測を開始・運転条件に使わない欠落。
前回の全入力検査も、これらの禁止条件が検査式になかったため通過していた。
遷移数が多いことだけでは要求の網羅にならない。

修正：許可High時にARMED LowまたはCLR Lowを観測したらCLEARへ戻る。
START/RUNでもこれらの観測は給電要求を直ちに無効とし、次状態をCLEARにする。
有効なLow→High許可による起動は維持する。

before.jsonに修正前ソースのハッシュと再現結果、after/report.jsonに回帰結果を保存。
統合検査6,144遷移もpower_sequence_model_v2で再実行した。
実回路にはRESET_Nによる別のゲートがあり、この失敗は実機誤通電の証明ではない。
非同期応答とCLR回復時間の保証は引き続き未実装。

再現（リポジトリルート、未作成の出力先）：

```sh
python3 software/sim/circuits/check_sequence_invalid_order.py --out /tmp/sequence-order-check
python3 software/sim/circuits/check_power_sequence_model.py --out /tmp/sequence-v2-check
```
