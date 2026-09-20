# ヨー支持部の背面壁と取付座の補強候補

前回、4か所の取付座を固定した支持部が変位0.3921 mm、最大絶対主応力12.5025 MPaで不合格となったため、背面の局所剛性を増やす。
背面壁を3 mmから8 mmへ内側に厚くし、取付座半径を4 mmから6 mmへ広げた。
左右とも外側の境界箱は変更しない。脚長も変更しない。取付穴径3.4 mm・取付穴位置は維持した。

追加質量は前候補から片側7.355 g、左右14.711 g（PETG仮定密度1,270 kg/m³）。
壁厚増加により旧12 mmボルトでは不足する。M3×20 mmを候補とすると呼び積層13.9 mmに対し残りねじ長6.1 mmとなるが、締結部品の実購入寸法と内部干渉の確認は未完了。

## 判定条件

以前の右旋回記録、左支持部の2.661 sの荷重を固定し、E=1,120 MPa、ν=0.35、4取付座面の理想固定で再解析する。
変位0.2 mm以下、最大絶対主応力・von Mises応力5.6 MPa以下。
メッシュ4・3・2 mmで評価し、最後の2段階の変位差5%以下、最大絶対主応力差10%以下を求める。
計画・基準・入力ハッシュは実行前に保存する。前回の失敗記録は維持する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/reinforce_yaw_back.py --out outputs/yaw_back_reinforced_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_yaw_back.py --step outputs/yaw_back_reinforced_new/left_yaw_fixed_support.step --out outputs/yaw_back_screen_new
```

## 未完了範囲

この試験は以前失敗した一荷重の再評価であり、全荷重の証明ではない。取付座の相手となる背面構造・ボルト接触・保持・座屈は未検証。
厚くした部分、拡大した座とボルト長変更の干渉、公差、工具アクセス、追加質量を反映した負荷、材料感度の再評価が必要。

## 追加案

背面壁8 mm・座半径6 mmの案は、最終2 mmメッシュで変位0.20692 mmとなり不合格。
最大絶対主応力3.84956 MPaは許容値内だが、最後の2メッシュの差が10%を超え、応力収束の基準も未達だった。
この結果を踏まえ、リブも3 mmから5 mmへ内側に厚くした案を評価する。外側の境界箱と脚長は維持する。
この案の追加質量は補強前のボルト座付き候補から左右合計25.684 g。前述の14.711 gにさらに上乗せして合計40 gとなる意味ではない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/reinforce_yaw_back.py --out outputs/yaw_back_reinforced_thick_new --rib-thickness-mm 5
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_yaw_back.py --step outputs/yaw_back_reinforced_thick_new/left_yaw_fixed_support.step --out outputs/yaw_back_screen_thick_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out outputs/yaw_back_clearance_new --include-cradle --support-dir outputs/yaw_back_reinforced_thick_new
```

## リブ5 mm案の結果

最終2 mmメッシュでは変位0.14978 mm、最大絶対主応力3.38855 MPa、von Mises応力2.84362 MPa。
最後の2メッシュの差は変位2.38%、最大絶対主応力7.93%で、今回の単一荷重の4判定基準を満たした。
左右旋回の記録角度範囲におけるカップリング・ロール受けとの隙間は、公差・仮定変形・角度刻み補正後で最小8.1876 mm。
この隙間結果は対象の部品対に限定され、全身・ボルト・工具・配線の干渉成立を意味しない。

全ての失敗・合格条件を `validation/yaw_back_reinforcement_development_v1/` に保存する。
解析中の `outputs/yaw_back_reinforced_v2/` への参照は、同証跡フォルダ内の同名ディレクトリへ対応する。内容の一致はSHA-256で検証できる。
