# 停止用出力コンデンサ候補を反映した統合v2

111部品/371端子の候補を維持し、`C_STOP_OUT`の型番を、既存選定資料に基づく **GRM31CR71H475KA12L** へ設定した。4.7µFの公称値と接続は変更していない。データシートに基づく選定資料・未検証条件を部品項目へ保持し、BOMに型番を反映した。その他の元98部品は変更していないことを生成時に検査する。

型番未設定は11個から10個になった。未設定行のBOM状態は`unselected`とし、選定候補と区別する。型番が入っていても適合性や調達を保証しない。特にC_STOP_OUTはDCバイアスと温度の複合容量、経時変化、ESR、過渡・安定性が未確認で、選定資料の`qualification=false`を維持した。旧負荷計算を新しい製作合格の証跡にしない。

KiCadのレビュー図と読戻しは `validation/integrated_logic_kicad_review_v2`。111部品、334接続端子、37明示NCの一致を確認。汎用端子記号・フットプリント未割当・annotation警告は残り、ERC/動作保証はない。未選定10部品はUNSELECTED表示。

再生成:

```sh
.venv-engineering/bin/python software/sim/circuits/integrate_logic_supply_candidate.py --include-stop-cap-candidate --out schematics/power/servo_power_logic_integration_candidate_v2
```

回路図再現はv1レビューREADMEのassembly/BOM/出力パスをv2へ変更する。正式currentポインタは据置き、電気的成立・製作リリースなし。

## 外付け逆流阻止FETの残件

2026-09-22にTI TPS25981のSLVSGG6D（2026年9月改訂）7.3.9を確認した。TPS259813xはDVDTで外付けN-FETを駆動し、停止状態の逆流阻止を提供する。動作中の回生遮断を保証するものではない。現接続にはDVDT―ゲート間の未選定抵抗とゲート―GNDの未選定コンデンサがあり、数値を埋めるだけでは立上り/遮断・MOSFETゲート電荷・負荷容量の整合が成立しない。汎用RCを仮置きして保護合格にはしない。

参照: [TI TPS25981 datasheet](https://www.ti.com/lit/ds/symlink/tps25981.pdf) 7.3.9、7.3.3。今回、この最新版の全パラメータを旧解析へ再照合したわけではない。ゲート部品の最終選定前に当該版の駆動条件と最終負荷を確認する。
