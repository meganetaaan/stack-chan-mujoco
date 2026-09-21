# 手動復帰回路 revI：基板上ボタンの接続統合

revHにB3U-1000PのSW1、3 kΩプルアップR15、74LVC1G17GVのU15とバイパスC15を組み込んだ。46部品159端子。既存43部品の端子接続は維持し、SW1の部品候補名だけを具体化した。U15がBUTTON_RAWを受け、U3のRAW_RELEASED_CONDITIONEDを駆動する。外部ケーブル接続は想定しない。

`validation/local_enable_button_v1/`の接点電流比較（約1.089〜1.249 mA）の構成を使用する。U1内部プルアップと追加R15が並列になる。R15の総合±1%は既存の設計比較条件であり、実部品はまだ未選定。U15追加によりBUTTON_RAW全体へMAX6816単体の入力保護定格を適用できない。

C15は選定済みC0G候補と同一。SW1/U15の基板フットプリント、実端子方向、筐体からの押下・過負荷防止、漏れ・ノイズ・ESD、全電圧範囲の受信条件は未確認。接続の統合は製造リリース、保護成立、通電許可ではない。単関節通電保留を維持する。

旧候補JSONのcandidate_not_integratedは単独案を作成した時点の履歴。現行組立は本ディレクトリとmanual_rearm_current.jsonを参照する。

再現：

```sh
python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --clamp-cause --permission-gate --pg-receiver --clear-sink --local-button --out /tmp/manual-rearm-revI-check
```

生成物は組立接続表であり基板配線済みデータではない。起動監視・外部停止・U11電源境界などの未完了項目は残る。

組立ファイルに結び付けた接点電流比較は `validation/local_enable_button_revI_v1/`。BUTTON_RAWの全接続を照合し、旧比較と同じ16端点の数値を再現した。ボタンの使用温度と入力漏れ試験条件の制約を明記している。

R15は後続の `manual_rearm_resistors_revI.json` でTNPW06033K00BYEA候補へ具体化済み。上記の未選定記述は接続統合時点の経緯であり、現行BOMはv4を参照する。回路適合・製造リリースの判断は変わらない。
