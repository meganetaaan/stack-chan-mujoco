# 主eFuse EN出力段の候補

Nexperia 74LVC1G17GV＋出力39 kΩ／入力220 kΩのプルダウンを評価候補とする。入力は起動・停止監視後のPOWER_ENABLE_COMMANDであり、手動復帰DFFのENABLE_PERMISSIONへ直結して監視を省略しない。端子と接続はschematics/power/main_enable_driver_candidate.jsonおよびmanual_rearm_revCに保存した。

根拠：[Nexperia Rev16.1、表7](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)、[TI TPS25982 RevD、6.5](https://www.ti.com/lit/ds/symlink/tps25982.pdf)。出力電圧は100 µA規定、ENの有効化しきい値最大1.23 V、最低消費状態のしきい値最小0.59 Vと比較する。

仮置き電源3.207〜3.393 V、抵抗総合±1%では出力負荷最大87.98 µA、High下限3.107 V、Low上限0.1 V。電源が有効で入力論理が成立している場合の静的出力段比較である。入力側のプルダウン＋漏れ比較は16.58 µAで、将来の指令出力段にもこの負荷を計上する。指令元が未設計なので入力論理の適合までは証明していない。

Ioff最大2 µAとEN漏れ0.1 µAを加算する無給電比較では0.08272 V。ただしIoffの公表試験条件はVCC=0 VかつVIまたはVO=5.5 V。0〜1.65 Vの途中電圧で同じ漏れモデルが成立するとは扱わない。電源がゆっくり落ちる／再上昇する場合のEN Lowを保証できず、完全な既定OFF回路としては未承認。静的比較の合格を通電許可に使わない。

抵抗値はユーザー要求ではなく、バッファの保証負荷とプルダウンの両立を狙った設計候補。温度を含む総合±1%の実抵抗品、バイパス品、配線容量、電源低下応答、指令段、独立した停止経路は未確定。バッファ出力固着HighやeFuse逆流はこの回路で解決しない。

追加解析はこの静的比較で終了。次は低下中電源での禁止経路と指令段を実部品で設計し、それを対象に過渡を評価する。未規定区間を理想バッファで補ったシミュレーションは行わない。

再現：`python3 software/sim/circuits/check_main_enable_driver.py --out /tmp/main_enable_driver_review`（出力先は未作成にする）。plan.jsonに事前条件、report.jsonに計算結果を保存する。#24は未完了。
