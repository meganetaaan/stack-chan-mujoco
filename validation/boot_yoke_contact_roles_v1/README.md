# 接触面のmaster/slave指定による感度

0.5 mmの同じ形状・荷重・メッシュ・材料・アンカーを用い、master/slaveの指定だけを交換した。圧力最大値は5.524037から5.526602 MPaへ変化し、差は0.04643%。最大変位差はブーツ0.000529%、ヨーク0.000264%。事前の圧力10%・変位5%条件を満たす。新ケースの力の釣り合い・めり込みも基準内。

この条件では接触面指定が従来の13.1%のメッシュ間差の主因である証拠は得られない。指定変更で低い圧力を選んで合格扱いにはしない。メッシュ収束不合格はそのまま残る。局所模型の数値感度であり、材料・締結・製造承認ではない。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.5 --reverse-contact --out outputs/reproduce_reversed_contact
.venv-engineering/bin/python software/sim/structural/evaluate_boot_yoke_contact.py --source outputs/reproduce_reversed_contact
```

集計はevaluate_boot_contact_roles.py --source <plan.jsonとreversedを持つ親>。基準ケースはvalidation/boot_yoke_mesh_sensitivity_v1/h0.5。全入力・ソルバ出力・評価とSHAを保存。
