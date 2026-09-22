# 手動復帰・EN駆動候補 revC

revBにU8（74LVC1G17GV）、入力／出力プルダウン、バイパス候補を追加した23部品89端子の接続候補。製造用回路図ではない。個別候補のSHA256はassembly.json。

POWER_ENABLE_COMMANDは未設計の起動・停止監視から受ける境界で、ENABLE_PERMISSIONへの直結は禁止。PGの起動待ちと運転中喪失の処理はまだ含まない。MAIN_EFUSE_ENをTPS259823の6番に接続する候補だが、電源低下途中のOFF保証は未完了。RESET_Nの停止入力、生ボタン入力保護、指令段も未完了。

U8は解除タイマー用のU4とは別部品。抵抗・バイパスの型式は未選定。無通電の配線レビュー用途に限定し、通電許可や#24完了の根拠としない。

生成：`python3 software/sim/circuits/package_manual_rearm_candidate.py --supervisor --en-driver --out /tmp/manual_rearm_review`。出力先は未作成にする。出力段の静的根拠はvalidation/main_enable_driver_v1/README_ja.md。
