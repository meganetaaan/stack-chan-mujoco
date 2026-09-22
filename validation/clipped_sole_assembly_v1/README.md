# 実形状の切分け接触力・剛性の組立検証

master/slaveの重なり多角形を704三角形へ分割し、頂点隙間を各部品のP1変位へ結ぶ行列Gを保存計算する。各三角形内のg<0領域について、検証済み `clipped_contact_triangle.integrate` の力と接線剛性をGᵀf、GᵀKGで全体へ組み立てた。対応面の被覆誤差1.54e-13。

保存変位に対する接触力合計20.121396866 N。独立のスカラー積分20.121396869 Nとの差2.53e-9 Nは事前1e-7 N以内。作用反作用残差2.57e-15 N、原点(35,6,−19)回りモーメントも1.4e-15 Nmm未満。

固定乱数方向（seed 2301）・変位刻み1e-8 mmの中央差分に対し、力の方向微分と負の接線剛性作用の相対差8.8123e-6で事前1e-5以内。この1方向のチェックは全方向・全接触状態の検証を代替しない。単体解析解の検証は `clipped_contact_triangle_v1`。

この結果は古い変位を固定した組立検証であり、新しい力20.1214 Nを20 Nと釣り合わせた平衡解ではない。次に接触力・剛性を平衡反復へ入れる。接触圧収束、材料仮定、歩行荷重、接合強度、Issue完了は未達。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/check_clipped_sole_assembly.py --out outputs/clipped_sole_assembly_check
```

作用反作用の配分は同じGを転置して行う。初期平面への鉛直投影・微小変位・摩擦なしという範囲を維持する。
