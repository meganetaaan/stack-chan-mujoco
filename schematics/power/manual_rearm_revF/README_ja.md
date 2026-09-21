# 手動復帰候補 revF：投入許可をEN指令へ反映

revEから部品を増やさず、U3 SN74HCS11PWRの未使用第2ゲートを使用。32部品118端子。端子3=ENABLE_PERMISSION、4=SEQUENCE_ENABLE_REQUEST、5=RESET_N、6=POWER_ENABLE_COMMANDとし、出力をU8の2番へ接続する。

指令は「ラッチの投入許可 AND 起動監視の要求 AND 停止クリア解除」。起動監視の要求がHighに残っても、許可取消またはRESET_N LowでEN指令を落とす。POWER_ENABLE_COMMANDは外部入力ではなくなった。外部未設計境界はSEQUENCE_ENABLE_REQUESTへ変更した。PGの起動不能を避ける監視・タイマー・故障保持は依然未実装。

U3第1ゲートはボタン解除確認のまま。第3ゲートの入力はGND、出力NCを維持。部品個別候補の未使用端子記述を上書きする箇所はassembly_overridesに記録した。

検証はvalidation/permission_gate_v1。停止から復帰しただけでは指令を再びHighにしない定常論理を確認した。RESET_Nの入力負荷が1個増えるため、全電圧域の入力適合・過渡は再評価が必要。通電・製造リリースなし。

再現：`python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --clamp-cause --permission-gate --out /tmp/manual_rearm_review`。出力先は未作成にする。
