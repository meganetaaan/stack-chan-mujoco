# 丸角足裏の2系列の荷重監査

足配置25.8/25.95 mmそれぞれ7000時刻×左右の空間力学釣合いとCAD座標変換を確認。力学残差は力1.78e-15 N以下、モーメント1.67e-16 N·m以下。座標変換残差は力5.33e-15 N以下、モーメント3.98e-13 N·mm以下。全基準合格は数値入力の整合性に限定される。

local*/contacts_local.jsonl.gzに接触位置・力、wrenches.npzにヨーク下面中心での合力を保持。入力系列は各plan.jsonに記録。モデル階層は両足首が葉ボディであることを確認。使用scene.xmlのハッシュはmodel_source.json。

## 再現

丸角16分割モデルを既存生成スクリプトでoutputs/rounded_sole_fine_v1へ用意する。以下の25.8を25.95へ置き換えてもう一系列も実行する。

```sh
.venv-engineering/bin/python software/sim/structural/audit_foot_equilibrium.py --source validation/rounded_sole_posture_v1/inset25.8 --out outputs/equilibrium25.8_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/export_foot_contact_loads.py --source validation/rounded_sole_posture_v1/inset25.8 --model outputs/rounded_sole_fine_v1 --out outputs/local25.8_repro
```

両系列とも旋回角90±1度は未達。最新CAD質量・TPU変形・部品別慣性配分は未反映。合力のみから局所応力は確定しない。次は実接触位置を利用し、足裏からヨークへの荷重分布をモデル化する。Issue完了ではない。
