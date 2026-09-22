# 一致接触モデルの部材応力

仮の締付力20 Nで、C3D4積分点の非平均化主応力を評価。0.35 mmの最大絶対主応力はBOOT 2.04973 MPa、YOKE 3.27798 MPa。仮定の等方PETG許容値5.6 MPa以内。0.5→0.35 mmの最大絶対主応力変化は0.889%、3.100%で、事前の10%基準以内。

BOOTの最大位置・応力符号はメッシュ間で変化する。全形状・歩行荷重・締結剛性・積層異方性・クリープは未検証。これは局所締付力のスクリーニングでありIssue #18完了ではない。

## 再現

リポジトリルート、既存エンジニアリング環境を使用。新しい出力先へplan.jsonをコピーした後、以下を実行する。

```sh
mkdir outputs/stress_repro
cp validation/matching_boot_stress_v1/plan.json outputs/stress_repro/plan.json
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.5 --boot-mesh-dir validation/matching_boot_yoke_development_v1/mesh/boot --yoke-mesh-dir validation/matching_boot_yoke_development_v1/mesh/yoke --out outputs/stress_repro/h0.5
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.35 --boot-mesh-dir validation/matching_boot_yoke_refine_v1/mesh/boot --yoke-mesh-dir validation/matching_boot_yoke_refine_v1/mesh/yoke --out outputs/stress_repro/h0.35
.venv-engineering/bin/python software/sim/structural/evaluate_boot_contact_stress.py --source outputs/stress_repro
```

大きいDAT/FRDは可逆gzip圧縮。元SHA256はcompression.json。応力の順序はDATヘッダーのsxx,syy,szz,sxy,sxz,syzに対応する。
