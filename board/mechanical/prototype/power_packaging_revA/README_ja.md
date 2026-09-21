# 電源部品配置の統合候補

packaging.stepはヨー支持組立、Tab5、旧TTL、候補電池、トレイrevB、
仮置きベルト包絡、左右UBEC包絡の8群を名前付きでまとめた検討用CAD。
旧電池・旧トレイ・旧変換器を追加で重ねていない。

全28群間の静的体積重なりは数値判定1e-6mm³以下。
書出し後のSTEPは有効で59ソリッド、入力体積合計との差7.4e-9mm³。
これは寸法・公差の保証ではなく、書出しで大きな形状欠落がないことの確認。

内部で接触する箇所や、ヨー組立群内の既存接触は、この群間判定の範囲外。
脚、全身動作、配線、端子、ベルトバックル、UBEC保持具・スイッチ、保護基板、
公差・変形・放熱を含まない。全身組立完了・強度合格・通電許可ではない。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/assemble_power_packaging_candidate.py --out /tmp/power-packaging-new
```

入力パスとハッシュ、全組合せはreport.jsonを参照。
