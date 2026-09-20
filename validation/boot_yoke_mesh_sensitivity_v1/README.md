# 両部品弾性接触のメッシュ比較：接触圧未収束

1 mmと0.5 mmのケースを追加し、validation/boot_yoke_deformable_contact_v1の0.7 mm結果と比較した。3条件とも計算完了・合反力・めり込みの基準内。最後2メッシュの最大変位変化はブーツ0.5584%、ヨーク2.0308%で5%以内。一方、最大接触圧変化は13.0937%で10%の基準を超え、全体判定は不合格。

固定支持体の収束結果を両部品弾性モデルへ継承できない。接触端部形状、アンカー、局所切断、メッシュの影響を確認し、圧力の最大値を除外する等の基準変更で合格させない。

同じ局所モデル・20 Nの仮荷重・1000000 N/mm³のペナルティに限る。実部品応力、締結予圧、材料、歩行荷重は未検証。強度・製造承認なし。

## 再現

engineering環境でLD_LIBRARY_PATHに.tools/root/usr/lib/x86_64-linux-gnuを設定する。

```sh
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 1 --out outputs/reproduce_joint_h1
.venv-engineering/bin/python software/sim/structural/evaluate_boot_yoke_contact.py --source outputs/reproduce_joint_h1
```

0.5 mmについても新規先へ実行する。集計はevaluate_boot_yoke_mesh_sensitivity.py --source <plan.jsonとh1/h0.5を持つ親>。中間メッシュの既存出力はSHA付きで参照。初回集計は相対パス処理で停止し、絶対パスへ正規化して再実行した。ソルバ計算の再実行は不要だった。全新規ソルバデータを保存。
