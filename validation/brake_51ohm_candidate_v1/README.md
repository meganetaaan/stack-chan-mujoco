# 回生吸収抵抗5.1 Ω案

4.7 Ω案の変動感度で定格超過を検出したため、公称5.1 Ω・初期公差+5%の5.355 Ωを両回生枝に設定。放電用378 Ω×2本とは別の部品。電池切離し80 ms、回生注入300 msから1 A・20 ms、Cout960 µFを維持。

結果: バス最大5.588374 Vで事前6 V以下を達成。主抵抗ピーク5.57921 W・0.0811966 J、理想スイッチピーク0.104187 W・0.00151628 J。初期公差側での吸収可能性を確認しただけで、上限抵抗の全温度・経時包絡、枝故障、熱、寄生インダクタンスを含む最終検証ではない。

CLIの--brake-ohmsは回生枝の実評価抵抗値を指定する。従来既定4.935 Ωを維持。部品候補カード4.7 Ωをこの試験だけで置き換えない。

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --brake-ohms 5.355 --bleed-ohms 378 --cout-uf 960 --regen-a 1 --regen-start-s .3 --out outputs/brake_51ohm_candidate
```

ngspice42の内部点measで判定。生ログと表示波形は可逆gzip、ハッシュをmanifest.jsonに保存。Issue #24未完了。
