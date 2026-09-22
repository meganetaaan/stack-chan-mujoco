# revN: 電圧監視出力からOVLOを駆動する比較候補

**遮断時間の監査により、唯一の高速過電圧保護としては採用しない。現行ポインタはrevMを維持し、製造・給電を許可しない。** 詳細は `validation/window_ovlo_timing_v1/README_ja.md`。 revMの入力12.6 V時のOVLO端子範囲問題を解消するための代替接続。低電流TLV431の精度を外挿する案とは別方式である。

左右それぞれ既存TPS3700のSOURCE_WINDOW_OD → SN74LVC1G14DBVR → 29.4k/21k分圧 → TPS259813L OVLOとする。分圧上側をレギュレータ出力から切り離す。各インバータはSTOP_AUX3V3給電、100nF局所バイパス。抵抗候補TNPW060329K4BYEA/TNPW060321K0BYEA。102部品331ピンであり、PCB配置済みを意味しない。

| 状態 | 監視出力 | インバータ出力 | 意図する動作 |
|---|---|---|---|
| 監視電源正常・入力範囲内 | High | Low | OVLOによる禁止を解除。ENと手動再始動条件は別途必要 |
| 監視電源正常・入力UVまたはOV | Low | High | 各脚のOVLOを直接禁止側へ駆動。ソフトウェア応答を待たない |
| 監視電源起動中・喪失 | 不定 | 不定 | この経路単独では保証しない。既存EN側停止経路との統合検証が必要 |
| 監視信号の固着・断線 | 不定 | 不定 | 未検証。正常と仮定しない |

## 今回の評価と変更の影響

既存のSTOP電源比較範囲3.207～3.393 V、抵抗総誤差配分±1%、インバータVOH≧VCC−0.1 V、OVLO漏れ±0.1 µAを用いた異常出力時の比較は1.278～1.431 V。事前基準は1.224 V超かつ1.5 V未満。最大出力負荷68.1 µAで100 µAのVOH規定条件内に収まる。総誤差配分・電源範囲自体の裏付けは未完了。

正常Low時の計算はOVLO漏れ仕様の0.5 V下限より下を外挿するため、合格証拠には使わない。TPS25981のピン説明はactive-low enableとしての使用を明示するが、この抵抗を介した駆動の全条件を保証するものではない。

過電圧の検出点は既存TPS3700の窓監視に移る。従来のTPS25981分圧による検出点・応答時間を引き継ぐとはしない。窓監視の遅延、配線容量、インバータ、分圧、eFuse遮断を含めた時間評価が必要。サーボの6 V制約は変更しない。インバータは緩い入力変化を受けられるSchmitt型を選び、通常のSN74LVC1G04案は採用しない。

`validation/stop_supply_budget_revN_v1/report.json` は追加部品の電源端子と分圧駆動電流も含む条件付きDC比較で2.622 mA。LDO接合温度・起動成立の証明ではない。revMの再実行値1.466 mAは既存結果と一致した。

## 採否を決める次の検証と終了条件

- TPS3700出力負荷・Schmitt入力の適合、端子Low時の駆動成立を確認する。
- 窓監視起動、STOP電源低下・断、eFuseのみ無給電、信号固着・断線で、ENとOVLOを含む保護動作を確認する。
- 入力過電圧に対する遅延・端子過渡・サーボ出力電圧を評価する。仕様から最大値を証明できない場合は、仮定波形の追加だけで合格にせず別の保護方式へ戻る。

以上を満たすまではcurrentをrevNへ変更しない。未完了の設計検証を実測Issueへ移さない。#6および関連Issueは開いたままとする。

再現:

```
.venv-engineering/bin/python software/sim/circuits/integrate_window_ovlo.py --out /tmp/ovlo-revN-new
.venv-engineering/bin/python software/sim/circuits/budget_stop_supply.py --assembly /tmp/ovlo-revN-new/assembly.json --out /tmp/ovlo-budget-new
```

資料: TI SN74LVC1G14 SCES218AA October 2025 (ピン、VOH/VOL、Schmitt入力)、TPS25981 SLVSGG6D September 2026 (pin2、6.3、6.5、6.6)、TPS3700データシート。URLはscreen.jsonに保存。
