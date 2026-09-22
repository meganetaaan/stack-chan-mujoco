# インサート案を含む胴体アセンブリ

LB-020・トレー・ベルト・Tab5着脱枠を含む111部品のSTEPを更新した。旧4ナットを4インサートに置換し、枠を圧入後の表示用近似へ変更。ナット蓋/レールはこの構成に含めない。

新規部品が関係する1,449組を検査し、0.01 mm³を超える体積干渉は0。全体外形は前のアセンブリと同じX[-67.7,64]、Y[-66,66]、Z[0,128] mm。旧ナット4個を除く共通107部品のうち体積変更は枠1個、106個は体積不変。これは同一形状を数学的に保証する比較ではない。

圧入後の枠はインサート外径円筒分を除去した近似。樹脂の溶融・収縮・盛り上がりや保持強度を再現しない。造形にはこのassembly.step内の枠を使わず、`validation/tab5_insert_candidate_v1/carrier_print.step`を寸法候補として参照する。

静的な統合確認であり、全脚の動作、公差・変形、締付け、熱、ケーブル、Tab5対枠の別の4ねじは未評価。新しい電源基板も実装寸法未確定で、この胴体へ統合していない。残した部品同士の過去の未確認事項を今回の干渉0で解除しない。正式CAD/BOM・全身質量・MuJoCoの指し先は未変更、製作HOLD。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/integrate_serviceable_torso_v2.py
```

report.jsonに入力ハッシュと部品順を保存。comparison.jsonは前統合候補との部品名・体積・外形比較。
