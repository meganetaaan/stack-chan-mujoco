# Tab5取付ねじを含む115部品の胴体候補

座ぐり付き枠とSLH-M3-8×4を統合した。外形はv2と同じX[-67.7,64]、Y[-66,66]、Z[0,128] mm。造形前形状は`validation/tab5_frame_print_v1/carrier_print.step`、本assembly.step内の枠は圧入後近似。

変更部品に関わる1,899組を検査した。交差フラグはTab5簡略モデルとねじ4本の各10.579 mm³のみ。これは未解決のねじ形状/深さ条件として分類し、合格や「干渉0」に置き換えない。その他の新規組合せに0.01 mm³超の体積干渉なし。旧部品同士の未確認事項は継続。

このモデルに含まれないもの：新しい制御/保護基板と配線、造形公差、たわみ、締付け・保持能力、全脚の動作。取付ねじ4本を残した抜取り経路は[別検査](../insert_carrier_removal_v2/README_ja.md)で公称干渉フラグなし。配線・工具・公差・保持は未確認。Tab5の実効ねじ深さや内部接触を確認するまで製作HOLD。正式CAD/BOM・全身質量・MuJoCoの指し先は未変更。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/integrate_serviceable_torso_v3.py
```

後続の[選定工具アクセス検査](../current_face_tool_access_v1/README_ja.md)により、Tab5固定ねじは顔ユニット単体で操作する順序を採用。本体装着中は工具干渉あり。側面ねじの公称工具・抜取り経路も同115部品で照合した。形状変更や締結承認ではない。
