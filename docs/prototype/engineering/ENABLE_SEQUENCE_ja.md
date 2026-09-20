# DC/DC有効化の遅延条件

既存の1 ms指令遅延を実装へ進めるため、[Pololu D42V55F5](https://www.pololu.com/product/5571)のEN端子を確認した。ENは内部1 MΩでVINへ引き上げられ、0.5 V未満で停止、1 V超で有効化できる。内部抵抗公差・入力電流の詳細は未確認。

遅延生成候補は[TPS3840](https://www.ti.com/lit/ds/symlink/tps3840.pdf)のDL30。3.3 V±2%の常時給電を仮定し、CTを4.7 nF（温度・バイアスを含む有効公差±5%）とした条件計算を `validation/enable_sequence_development_v1` に保存した。常時給電LDOとコンデンサの型番は未選定。

計算上の容量起因遅延下限は1.5966 msで、先行するゲート保持ICの450 µs起動待ちに対し1.1466 msの余裕がある。3.3 V電源の下限は監視ICの解除しきい値上限より64 mV高い。出力LowとEN停止しきい値の差は0.3 V。正の内部起動時間を下限計算から省いている。これらは条件付きの端子・時間余裕で、実回路の成立確認ではない。

**重要な未解決点は、3.3 V電源が立ち上がる前にENがバッテリーへ引き上げられること。** 遅延ICを直結するだけでは早期起動を防げない。制御電源が無い間もENを停止レベルに保つ回路を追加し、その後に遅延解除する必要がある。電池投入・抜去・瞬断・残留電荷を含む回路シミュレーションが必要。

DL30のしきい値は3.3 V制御電源の監視用であり、2S電池の過放電保護ではない。実装はまだ候補段階で、回路BOMの承認済み部品には追加していない。

```sh
.venv-engineering/bin/python software/sim/circuits/check_enable_sequence.py \
  --out outputs/enable_sequence_reproduction
```
