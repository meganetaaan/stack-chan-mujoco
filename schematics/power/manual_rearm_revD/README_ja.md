# 手動復帰・EN駆動候補 revD

revCへ独立ENクランプU9、直列抵抗R7、CT抵抗R8、バイパスC9を追加。27部品101端子。U8の4番はR7を介してENへ接続するよう個別候補から変更し、assembly_overridesに明記した。部品定格と静的収支はvalidation/main_enable_clamp_v1を参照。

U9のRESETはMAIN_EFUSE_EN専用で、U7のRESET_Nと接続しない。U9はeFuse入力側5 Vから給電し、負荷側バスや生電池からは給電しない。POWER_ENABLE_COMMANDの起動・停止監視は未設計のまま。復電時の自動再投入禁止、過渡と出力故障の検証も未完了であり、製造／通電用の完成回路ではない。

再現：`python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --out /tmp/manual_rearm_review`。出力先は未作成にする。SHA256はassembly.jsonに保存。revC以前は履歴として保持する。

## 確認済みの不成立条件

`validation/dual_supervisor_recovery_v1/`で、U9だけが低電圧停止しU7が許可を保持する公差内の反例を確認した。指令保持のままでは復帰時に自動再投入する。停止記憶と許可取消を実装しないrevD単体は再投入防止について不合格。静的ENクランプの成立と分けて扱う。
