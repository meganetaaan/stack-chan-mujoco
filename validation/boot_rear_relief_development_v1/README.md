# ブーツ後部内壁の局所逃がし候補

前候補は左−0.2975 radで、ロール座標のブーツ(-30.5,-15.166318,-8.528940)とフレーム(-29.4,-15.166318,-8.528940) mmが接近し、隙間1.1 mmに数値余裕がなかった。右は鏡像。

上部開口を維持し、ブーツ座標x=[−31,−29],y=[−18,18],z=[−14,0] mmの直方体を追加除去した。実際の追加除去は約4.99844 mm³/側。両側とも有効な単一ソリッド。現行r9からの総除去は約1749.127 mm³/側。

±0.34 radにおけるブーツと候補フレームの連続隙間評価は、各側57サンプル、28区間で全範囲を覆った。最小区間下限は1.101401093 mmで、事前の1.1 mm基準に合格。区間下限には0.00001 mmの数値余裕を既に控除している。これは指定剛体部品対に限った結果であり、全機構の合格ではない。

今回の加工はz≤10 mmにも入るため、旧候補の下部不変の主張は引き継がない。維持を確認した領域はz≤−15 mmのみ。取付部の局所形状、荷重経路、強度、丸み、製造性、外観は要評価。0.2 mmのたわみ予約は実際のたわみ検証ではない。ソフトウェア可動範囲拡張や製造承認は行わない。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/relieve_boot_bridge.py --out outputs/reproduce_boot_rear_relief
.venv-engineering/bin/python software/sim/structural/certify_native_yoke_gimbal.py --gimbal-dir validation/native_yoke_gimbal_wider_relief_v1/cad --moving-dir outputs/reproduce_boot_rear_relief --moving-part boot_shell --out outputs/reproduce_boot_rear_clearance
```

出力先は未作成のディレクトリを指定する。ソーススナップショット、入力SHA、事前条件、全区間下限とサンプルを同梱。生成スクリプトの説明文のみ実行後に修正した。
