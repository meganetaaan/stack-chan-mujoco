# 加工座金を反映した115部品の質量対応

旧台帳から未継承だったSCW-YAW-REAR-WASHER-01×8の比較質量を追加。各旧STEPと現在組立内のソリッドは双方向差集合体積1e-6 mm³未満、参照密度7930 kg/m³×現在体積と旧質量は1e-12 kg以内で一致した。追加合計0.879672 g、数値78件の小計0.410591870 kg。

これはSUS304の参照密度と加工提案寸法による値で、メーカー公称重量・保証上限ではない。鋼種や公差を確認済みの市販品と扱わず、加工可否・曲げ/座面・締付けは未確認。元の[座金設計](../rear_washer_clearance_v1/README_ja.md)の条件を継承する。

残る密度未割当15件は造形7点・MYG市販座金8点。部品質量未定22件は前版と同じ。MYGカタログ印刷p256を再確認し、PWU3-7-05の公称7/3.2/0.5 mmと材質ステンレスを確認したが、鋼種・寸法公差・重量は同ページにない。SUS304密度を無条件に割り当てない。確認記録とPDFハッシュはdocs/prototype/mechanical/pololu_mount_fasteners/rear_candidate.json。

前回「購入座金16点」と呼んだ分類は、加工品8点と市販品8点の誤りだったため訂正した。全機質量/重心/慣性は引き続き未確定。今回追加分を全機完成や製作承認に読み替えない。製作HOLD。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/reconcile_current_torso_mass.py --include-yaw-washer-mass
```

引数なしの旧台帳は保存。その他の仮定・未収録部品は[前版](../current_torso_mass_v1/README_ja.md)を参照。
