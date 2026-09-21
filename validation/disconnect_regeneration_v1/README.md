# 電池切離し後の回生注入

電池を80 msで切り離し、100〜120 msに1 Aの電流を駆動バスへ戻す試験。振幅・約20 msの持続は既存supply_regeneration_v2のストレス試験を引き継ぎ、立上り/立下りを1 µsとした。停止後の実モータ回生を再現したと主張しない。EPIC4の左右記録は合計電流が常時正で、この注入を記録波形の実測最大と呼ばない。

360 Ω×2本の放電枝、公差側378 Ω、Cout=960 µF、既存の二重回生吸収・補助電源・ENモデルを使用。試験前plan.jsonの判定は切離し後バス最大6.0 V以下。

結果: ngspice内部時間点での最大は5.588319 Vで今回の電圧基準を満たす。終端まで数値解析が完了。バスは回生開始時約4.45 Vから上がるため、回生がなかった放電試験のRC式だけでは評価できない。通常運転の4.75〜5.25 V基準を停止後に適用した結果ではない。

これは1つの注入時刻・振幅に対する電圧試験。遅い回生、長時間の回生、ブレーキ枝故障、放電抵抗故障、吸収抵抗やMOSFETのエネルギー/温度、停止後のサーボ状態・実回生量・実総容量は未検証。回生の発生/継続を機構と電気で連成したモデルではない。Issue #24全体の保護成立とは扱わない。

再現:

```sh
.venv-engineering/bin/python software/sim/circuits/run_disconnect_residual.py --bleed-ohms 378 --cout-uf 960 --regen-a 1 --out outputs/disconnect_regeneration
```

analysis/report.jsonのbus_after_disconnect_max_Vを事前plan.jsonの基準と照合し、ルートreport.jsonへ保存。表示波形の補間点から最大値を判定しない。生ログと表示波形は可逆gzip圧縮、圧縮前後のSHA-256はmanifest.json。ngspice42を使用。
