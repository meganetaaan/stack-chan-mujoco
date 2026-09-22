# 座面追加後ブーツの連続隙間再確認

座面を追加したブーツCADを用いて±0.34 radを再評価した。フレームとの区間下限は左右とも1.101401093 mmで、事前基準1.1 mmに合格。各側57サンプル、28区間で全範囲を覆う。

サーボについては新旧ブーツの差分をCADで抽出し、追加部分が4ソリッド、19.295662078 mm³/側であることを確認した。追加部分とメーカーCAD15部品のX方向区間は、数値余裕控除後でも4.99999 mm以上離れる。ロール回転はX座標を変えないため、この下限は全角度で成立する。旧ブーツとサーボの既存下限2.289530449 mmと組み合わせ、新ブーツ全体にも同じ下限が成立する。

この論証は指定された剛体モデル、以前の回転部品の割当とCAD数値余裕の仮定に依存する。座面とヨークの意図した接触は別途確認済みだが、ねじ・ナット・配線・他脚・床・全身軌道・実際のたわみは今回の対象外。公差やたわみの予約値を実測・解析で保証したものではない。製造承認およびIssue完了は未達。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/certify_native_yoke_gimbal.py --gimbal-dir validation/native_yoke_gimbal_wider_relief_v1/cad --moving-dir validation/boot_seats_development_v1 --moving-part boot_shell --out outputs/reproduce_seated_gimbal
.venv-engineering/bin/python software/sim/structural/bound_boot_seat_additions.py --out outputs/reproduce_seated_servo
```

未作成の出力先を指定する。入力SHA、全区間下限、追加形状とサーボの組合せ別下限を保存した。
