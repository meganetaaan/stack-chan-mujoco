# 足部組立比較 revB

最新の増厚座面・端部開放溝と、0.8mm接地層をまとめた左右各7部品。
ブーツ、ヨーク、保持部、接地層、ワッシャ、ねじ、ナットを含む。
旧スペーサーと旧一体TPU足裏は置換済み。revAの部品を重ねて追加しない。

42組の部品間で公称体積交差0。接触する面は交差0でも存在するため、
接着・締付け・荷重伝達の成立とは区別する。足首サーボ、ホーン締結品、ハーネスを含まない。

各部品の体積・重心・重心まわりの体積慣性テンソルをinventory.jsonへ記録した。
密度rho[g/cm³]を選定後、質量はvolume_mm3*rho*1e-6[kg]、
慣性はvolume_inertia_mm5*rho*1e-12[kg m²]へ変換する。
中実・一様密度の形状値で、インフィル・積層の空隙や実部品の省略形状は未反映。
直方体の解析解と平行移動後の不変性をinertia_check.jsonで確認した。
材料未確定部へ仮の密度を入れて全身質量の確定値とはしない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/export_current_foot_inventory.py --out /tmp/foot-revB
```

材料・ワッシャ型番・締付け・強度・造形条件は未確定。製造リリースではない。
MuJoCoの質量・慣性への反映も未完了。

剛性3部品にPETG候補密度を適用した比較は`validation/foot_rigid_inertia_v1/`。
片足約50.39gだが、接地材・締結品・サーボ等を含む足全体の値ではない。
