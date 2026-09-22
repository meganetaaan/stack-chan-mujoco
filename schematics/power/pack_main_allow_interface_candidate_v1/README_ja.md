# 主起動許可の電源ドメイン間接続候補

## 判断

CTRL側MAIN_START_ALLOWをSYS側SN74HCS11の4番へ直接配線する案は採用しない。CTRLが3.3 Vで動き、SYS__LOGIC3V3が0 Vとなる組合せで、受信入力の推奨範囲0〜VCCを外れる。入力クランプへ流れる経路があり、直結のまま起動順序を仮定して適合としない。電流値・損傷は今回算出していない。

[TI SN74HCS11 RevB](https://www.ti.com/lit/ds/symlink/sn74hcs11.pdf)の端子表と§5.1/5.3に基づく判断。絶対最大のクランプ電流を通常動作許容として使わない。

## 3部品の候補

受信側SYS__LOGIC3V3で給電する74LVC1G17GV、入力側10 kΩプルダウン、100 nFデカップリングを追加する案。出力はSYS__SEQUENCE_ENABLE_REQUESTへ接続し、既存SYS__R_SEQUENCE_OFF（10 kΩ）を使う。assembly.jsonとCSVに実品番・ピン・配置条件を保存。正式システムには未統合。

[Nexperia 74LVC1G17 Rev16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)は入力5.5 V耐圧と電源断時Ioff、GVの2番入力/4番出力/5番電源を規定する。電源0 Vの仕様が、途中の低電圧全域の正常論理動作まで保証するわけではない。

SYS__U3の3番ENABLE_PERMISSIONと5番RESET_Nを残すので、通常論理として出力6番には許可・リセット解除・今回のシーケンス要求の全てが必要。停止/手動復帰経路をバイパスしない。MAIN_START_ALLOWをシーケンス要求として使うには、CTRL側で起動条件を満たす制御仕様が必要で、単なるMCUのHigh出力で完成とはしない。後続で別シーケンサを使う場合は二つの出力を同じネットへ結ばず、条件の結合を再設計する。

## 確認と終了条件

今回は直結可否と実部品接続候補まで。既存両回路から出力/入力ピン、既存プルダウン、停止/手動復帰の入力が保たれることを検査した。通電・遅延・過渡波形や異常時動作の証明ではない。

次の確認には、双方の電源公差でのHigh/Low余裕、受信電源立上り/降下中のRESET保持、送信無給電時の漏れ、入力プルダウンの負荷と両電源の電流予算を含める。部分給電を含む全状態の条件がそろうまで接続完成としない。LOGIC_START_ALLOW、UV検出、Tab5連携、電力経路は別の未完項目として残る。製作HOLD。

再現：

```sh
.venv-engineering/bin/python software/sim/circuits/build_pack_main_allow_interface.py
```

[静的漏れ・負荷比較](../../../validation/main_allow_interface_screen_v1/README_ja.md)を追加。電源0 Vの送信側に対する条件付きLow比較と追加電流のみで、全状態の合格ではない。
