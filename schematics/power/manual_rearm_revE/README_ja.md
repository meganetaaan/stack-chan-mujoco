# 手動復帰候補 revE：停止原因とENの分離

32部品118端子の接続候補。revDのU9 RESETをRAIL_HEALTH_N（10 kΩでLOGIC3V3へプルアップ）へ変更し、U7 MRへ伝える。正常なEN Lowがラッチをクリアする帰還は作らない。U11（Nexperia 74LVC1G17GV）で5 V側へ信号を渡し、U10（TPS3808G01DBVR）のMRへ接続する。U10 RESETがENをクランプする。

U10はSENSEとVDDをEFUSE_INPUT_5Vへ接続し、CTは開放（解除12〜28 ms）。入力電源が正常な場合にMRの状態を反映させる用途であり、G33の低電圧検出器を並列追加するものではない。U7 MRへ5 Vを直接入力しない。変更箇所をassembly_overrides、源データSHA256をassembly.jsonに保存。

`validation/clamp_cause_recovery_v1/`では、落ち着いた状態でU7/U9のどちらが先に作動しても保持許可が解除されることを確認した。実指令POWER_ENABLE_COMMANDの取消、PG起動監視、短い低電圧パルス、両電源喪失、未給電逆流、入力しきい値の全電圧域は未確認。revE単体を自動再投入防止の合格とはしない。

再現：`python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --en-clamp --clamp-cause --out /tmp/manual_rearm_review`。未作成出力先を指定。revDは失敗履歴として残す。製造／通電リリースなし。
