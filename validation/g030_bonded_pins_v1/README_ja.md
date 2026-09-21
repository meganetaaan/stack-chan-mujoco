# G030代替候補の端子所有権

STM32G030F6P6でも必要な入力11・出力3とSWD・NRSTを確保できる。
ただしC011の設定を流用しない。TSSOP20には複数のGPIOが同じ物理端子へ
接続される箇所がある。未使用GPIOを独立した出力として初期化すると競合し得る。

| 物理端子 | 使用ポート | 同じ端子の未使用ポート |
|---|---|---|
| 1 | PB7 | PB8 |
| 2 | PC14 | PB9 |
| 15 | PA8 | PB0、PB1、PB2 |
| 19 | PA14（SWCLK） | PA15 |
| 20 | 予備 | PB3、PB4、PB5、PB6すべて未使用 |

未使用側をanalog、プル抵抗と代替機能を無効とする設定条件を作成。
9個の未使用別名ポートを誤ってoutputにした設定を検査で拒否した。
これは設定条件の検査で、レジスタ書込み・ROM起動中の動作を検証したものではない。

PC14/PC15に影響するRTCレジスタはシステムリセットだけでは初期化されないため、
起動処理で扱う必要がある。PA9/PA10へのリマップも無効の条件とする。
G030の電源監視をC011のプログラマブルBORと同じと仮定しない。

代替候補の定義はschematics/power/sequence_controller_candidate/g030_controller.json。
現行回路revIへ未統合。前段負荷・電源断・初期化・停止時間は引き続き未確認。

再現（リポジトリルート、未作成の出力先）：

```sh
python3 software/sim/circuits/check_g030_bonded_pins.py --out /tmp/g030-pins-check
```

出典：ST DS12991 Rev 6 pp.29〜34。候補JSONのURLを参照。
