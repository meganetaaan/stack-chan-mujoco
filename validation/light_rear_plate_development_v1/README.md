# 背面板の軽量化候補

2 mmアルミ背面板の内側に角半径3 mmの開口2箇所を追加。外形・角の固定穴・ヨー固定穴を維持し、86.757→68.151 g、18.606 g削減。胴体接触面積1483.903 mm²と、角4組・ヨー8組のワッシャー投影接触面積各29.405 mm²を保持した。単一の有効ソリッド、接触面積差0.001 mm²以下、5 g以上の削減という事前幾何基準を満たした。

ヨーワッシャーは以前の組立包絡体を板表面へ軸方向移動して投影面を確認したもので、締結スタックやねじ長さの検証ではない。構造解析は未実施であり、元の背面板の剛性・応力の結果をこの形状に流用しない。現行候補指定は変更しない。

質量のみを反映した左旋回は3.550秒、51.020度で関節角制限により停止。未軽量化候補の3.155秒・36.098度から停止時刻と到達角は変化したが、7秒継続・90±1度には未達。配線・未列挙部品25 g仮定、元の衝突形状、元の制御条件を保持した。歩行成立と構造成立の両方が必要であり、本候補を製造承認しない。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/lighten_rear_plate.py --out outputs/light_rear_plate_v1
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/mujoco/build_mass_sensitivity.py \
 --out outputs/light_plate_mass_v1 --residual-grams 25 \
 --rear-plate outputs/light_rear_plate_v1/rear_structural_plate.step
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/light_plate_mass_v1 --out outputs/light_plate_mass_left_v1 --sign 1
```

今後は支持部軽量化、足首動作余裕、軽量板の接触を含む構造解析を継続する。CAD・質量設定・失敗波形を保存し、元の凍結モデルは変更しない。
