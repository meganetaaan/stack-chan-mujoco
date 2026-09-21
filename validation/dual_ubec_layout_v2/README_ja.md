# 左右UBECの公称搭載配置

HOBBYWING 30603000の43.1×32.3×12.5mm包絡を、中心(-25,±31,108)mmへ配置。
元の±25mm配置(v1)では各UBECとTTLが195.53mm³重なった。
左右各6mm外へ移動したv2で、検査対象との重なりは0。
最短距離はTTLへ2.85mm、ヨー組立へ3.75mm。外形の拡張は行っていない。
電池の持上げ・前方取出し掃引箱との距離は21.45mm。

旧専用変換器は置換する前提で対象から除外。新UBECのリード線・外部スイッチ・
コネクタ・保持具・断熱/放熱空間・追加保護基板はまだ配置していない。
したがって搭載完成や熱・電気定格の合格ではない。電池交換の手指空間も別。
この検査の終了条件は包絡と既存主要部品および電池経路の重なり確認。
次はこの配置で配線出口と保持方法を設計する。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_dual_ubec_layout.py --y-mm 31 --out /tmp/dual-ubec-new
```

v1は同じコマンドで--y-mm 25。失敗形状と結果を保持している。
