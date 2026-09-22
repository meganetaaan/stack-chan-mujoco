# 個別アンカー反力・モーメントの監査

前回の `sole_spacer_contact_probe_v1` と同じメッシュ・材料・荷重・境界条件で、RF出力をTOTALS=ONLYからTOTALS=YESへ変更し、個別節点力も出力した。ソルバー正常終了。形状・接触条件は変更していない。

事前に `anchor_plan.json` で、各節点の力ノルム合計/20 N、各節点のモーメントノルム合計/(20 N×3 mm)をそれぞれ1e-4以下と定めた。モーメント原点は(35,6,−19) mm。合計の前にノルムを取ることで反力の相殺を合格理由にしない。

力比1.41841e-4、モーメント比1.37913e-4で両基準とも不合格。スペーサーのz反力には−0.001410、+0.000162、+0.001248 Nがあり、合計ではほぼ相殺する。合計力が小さいことだけでアンカーが無影響とは言えない。原点回りの合計モーメントは約(0.003655,−0.004609,0) Nmm。

結果は拘束の影響を再評価する必要を示す。数値の大きさだけで実部品の破損や設計全体の不成立とは断定しない。基準を後から緩和しない。次は拘束位置・メッシュ感度を比較し、剛体運動を除去する拘束と局所変形への干渉を区別する。材料値・締付力の仮定、歩行荷重、接合強度は依然未検証。

再現:

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sole_spacer_contact.py --out outputs/sole_anchor_repro
cp validation/sole_spacer_anchor_audit_v1/anchor_plan.json outputs/sole_anchor_repro/
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_sole_spacer_anchors.py --source outputs/sole_anchor_repro
```

DATは可逆gzip。解析用モデルと仮定は前回README参照。Issueを閉じる証跡ではない。
