# 装填治具の剛性確認

経路検査で残った変形余裕0.10 mmに対し、組立時の横力1 Nを設計評価荷重として、2×2 mm軸を確認した。1 Nは設計上の評価条件で、実際の挿入・引抜き力を測定した値ではない。

材料の参考値は[Outokumpu Coreデータシート](https://www.outokumpu.com/-/media/files/products/core/outokumpu-core-range-datasheet.pdf)の20℃での弾性係数200 GPa。計算は10%低減した180 GPaとする。この低減は設計仮定であり、購入部材の最低保証値ではない。

固定端片持ち梁の計算で、従来の2×2 mm軸の変位は上側3.334 mm、下側3.187 mm。0.10 mm以内に収める力は軸単体でも約0.03 Nに限られる。軸以外の柔軟性を考慮する前に不合格となる。

6×6 mm軸の候補は軸単体で0.03588 mm。支持部を内側へ移し、横送りを9 mmとした経路で、締結部品を含む交差0件・工具すきま不合格0件を確認した。CAD上の軸・支持部・頭部を一体化した鋼製部材として、3/2/1.5 mmの3段階メッシュで解析した。

## 有限要素解析

柄側のx=80 mmを固定し、ナット中心に作用する力の合力・モーメントを頭部の面へ与える。E=180 GPa、ν=0.3。各方向1 Nの3単位応答から、力の大きさが1 N以下の任意方向に対する節点変位の最大特異値を計算した。応力は3応答のノルムによる保守的な上限。全節点内挿位置での最大値や実接合の柔軟性を保証するものではない。

| 治具本体 | 最細分の節点変位上限 mm | 主応力上限 MPa | 変位収束 | 応力収束 |
|---|---:|---:|---|---|
| 上側 | 0.042899 | 11.12294 | 合格 | 不合格 |
| 下側 | 0.074671 | 13.11080 | 合格 | 不合格 |

応力の暫定許容100 MPaは購入部材の強度証明に基づくリリース値ではない。絶対値がこの値以下でも、既定の応力差10%以内を満たしていない。ばね指、その接触・把持力、柄の保持、部品の接合は今回の解析に含まれず、治具全体は未検証。

この結果から複雑な装填治具案をリリースせず、造形途中に金具を配置する案を次の接触解析候補とする。`EMBEDDED_REAR_NUT_PROCESS_ja.md`を参照。

## 再現

```sh
.venv-engineering/bin/python software/sim/structural/screen_jig_shaft.py --out outputs/jig_shaft_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_nut_loading_jig.py --body validation/nut_loading_jig_development_v1/captive_rear_nuts_wide_v1/body_shroud.step --out outputs/jig_stiff_new --path-mode lift9 --tool-profile stiff6 --fastener-check on
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_jig_core.py --step outputs/jig_stiff_new/1_8_core.step --nut-z-mm 8 --out outputs/jig_core_lower_new
```

上側は`1_120_core.step`、`--nut-z-mm 120`。結果と不合格記録は`validation/jig_stiffness_embedded_development_v1`に保存する。
