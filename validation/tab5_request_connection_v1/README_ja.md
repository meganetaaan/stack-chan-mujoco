# Tab5起動要求の全体候補への接続

**Tab5枝の未接続起動許可をPA7へ割り当て、209部品候補v7を作成した。** 起動停止の論理接続までで、回路全体の動作確認やファームウェア実装ではない。

## 接続判断

[STM32G030F6P6のTable12](https://www.st.com/resource/en/datasheet/stm32g030f6.pdf)でTSSOP20の14番がPA7であることを確認。現候補の同端子は未使用だった。

PA7 → 74LVC1G17GV → SN74LVC1G08DBVR → 既存1 kΩ直列抵抗 → TPS26601 SHDN、という接続にする。ANDのもう一方はCTRL_LATCH_PERMIT。PA7側は10 kΩでPACK_RETURNへ落とし、追加IC各1個に100 nFを置く。SHDNの既存10 kΩも維持する。

シュミット入力は無給電/高インピーダンス移行時の緩やかな入力を受けるための選定。バッファ出力からAND入力への速度と電源途中状態は別途確認が必要。部品根拠：[74LVC1G17](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)、[SN74LVC1G08](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf)。

SYS側電圧監視リセットをTab5起動の前提に加えない。CTRLのウォッチドッグ/監視が許可ラッチを解除すると、PA7がHighのままでも正常給電範囲の論理上はTab5許可が落ちる。原則は次のとおり。

| CTRL許可 | Tab5状態契約からの要求 | Tab5起動許可 |
|---|---|---|
| Low | 任意 | Low |
| High | Low | Low |
| High | High | High |

## 通常停止と異常停止

既存`tab5_restart_model.py`のtab5_allowをPA7へ出す契約にする。生の開始ボタンを直接出力しない。通常停止では先に駆動許可を落とし、Tab5を給電したまま現在の終了処理に対応する応答を待つ。制御系の監視異常では応答待ちより許可解除を優先する。

再起動には電源OFFの確認、既存契約の待ち時間、新しい開始要求が必要。駆動開始には別途準備完了と手動再ARMを必要とし、Tab5を給電しただけでサーボを動かさない。起動要求端子はLowを先に設定してから出力モードへ切り替える。

論理契約の5状態と7入力の640組について「CTRL許可がないとTab5給電許可なし」「駆動許可にはTab5許可・有効電源・準備完了・停止なし」を確認し、[全組合せ](contract_combinations.csv)へ保存。既存の再起動イベント8ケースも再実行した。これは状態契約の照合で、GPIO・検出器・実回路の応答を再現するSPICEではない。OFF確認、ready、shutdown_ackの実信号は未配線/未実装。

## 電気条件と追加負荷

受信IC・抵抗が同じであることを端子/品番で照合して、[補助起動の静的比較](../aux_start_connection_v1/README_ja.md)を条件付きで適用した。比較値はSHDN High 2.169 V、Low 0.3733 V。抵抗の総変動±1%、他電圧への10 µA漏れ配分は設計仮定であり、全電圧・温度保証ではない。

Low側のノード余裕は26.69 mV。プルダウンを受信IC GNDへ戻す条件で、送信側GNDの正方向電位差に換算した比較限界は29.31 mV。この値を配線の許容仕様として確定しない。SHDN周りを大電流帰路の電圧降下から分離し、電源遷移・実配線の電位差を含めて再評価する。GND pin17とRTN pin15を混同して短絡しない。

追加の抵抗負荷比較は0.7042 mA、CTRL側容量は公称200 nF。IC消費、漏れ、切替電流、許可ラッチの増えた駆動負荷は別。旧PSpice v3にも今回の追加分は含まれず、全電流上限ではない。

## 残件と完了条件との差

明示未接続ポートはPACK_UV_WARN_Nだけになったが、未設計機能全体を1件と数えない。Tab5のILIM値、選定100 nFの起動/熱適合、実入力負荷、検出/通信、逆流、異常復帰、制御電源の完全な負荷予算、基板・配線は残る。PTH置換比較も別案として未統合。

#21の全負荷/部品仕様適合、#22の全レール解析、#23の過渡/熱、#24の異常時検証は本接続だけでは満たさない。Issueは未完、製作HOLD。

再現（リポジトリルート）：

```sh
.venv-engineering/bin/python software/sim/circuits/connect_tab5_request.py
.venv-engineering/bin/python software/sim/circuits/check_tab5_restart_model.py
```

入力ハッシュと比較値は[report.json](report.json)。既存部品で変更した端子表はMCUだけで、停止回路の接続は維持した。後続の[立上り設定選定](../../schematics/power/tab5_startup_parameter_candidate_v1/README_ja.md)によりTAB5__C_DVDTへ100 nF部品を割り当てた。
