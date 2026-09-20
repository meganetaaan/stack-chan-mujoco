# 0.35 mmへの局所接触メッシュ細分化：未収束

形状・荷重・接触係数を維持し、両部品のメッシュを0.35 mmへ細分化。CAD面積保存とメッシュ面積誤差1%以内を確認し、接触計算と合反力・めり込み判定は合格。

最大接触圧は4.891514 MPa。前回0.5 mmの5.524037 MPaとの差は約11.45%で、10%の収束条件をなお満たさない。ブーツ最大変位0.002612279 mm、ヨーク0.005024735 mmは前回との変化5%以内。圧力が下がっただけで合格としない。全体数値判定は不合格。

実機強度の合否ではなく、局所接触モデルの数値収束確認。切断・アンカー・材料・ねじ剛性・歩行荷重の制限は継続。製造承認なし。

## 再現

engineering環境とLD_LIBRARY_PATHを使用し、以下を新規出力先へ実行する。

```sh
.venv-engineering/bin/python software/sim/structural/mesh_boot_nut_patch.py --mesh-mm 0.35 --out outputs/reproduce_boot035
.venv-engineering/bin/python software/sim/structural/mesh_local_yoke_contact.py --mesh-mm 0.35 --out outputs/reproduce_yoke035
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.35 --boot-mesh-dir outputs/reproduce_boot035 --yoke-mesh-dir outputs/reproduce_yoke035 --out outputs/reproduce_contact035
.venv-engineering/bin/python software/sim/structural/evaluate_boot_yoke_contact.py --source outputs/reproduce_contact035
```

比較値は新値/基準値−1の絶対値。基準はvalidation/boot_yoke_mesh_sensitivity_v1/h0.5。全メッシュ・入力・ソルバ出力・事前条件を保存。
