# ヨー支持部の初期構造解析

Issue #17・#18の設計途中の記録。製作用の完了判定ではない。

## 条件

EPIC #4の36条件から抽出した、左股関節ヨーの最大モーメント時刻の実際の力・モーメントを用いた。異なる時刻の成分最大値は合成していない。
関節のヨー角でベース座標へ回転し、親から子への反力の符号を反転して支持部へ適用した。原点はベース座標の(-5,26,62) mm。
モーター投影下の棚下面へ線形分布荷重を適用し、表面積分で6成分の合力・モーメントが一致することを検査した。

PETGの材料仮定は `board/mechanical/engineering/materials.json`。E=1400 MPa、ν=0.35、応力スクリーニング値7 MPa、変位上限0.20 mmを試験前に固定した。
背面x=-61.5 mmを全面固定した理想接合であり、実際のねじ・壁の柔らかさをまだ含めない。
Gmshの四面体メッシュに2次変位要素を用い、4・3・2 mmの3段階で解析した。応力は全積分点を対象とし、特異点を除外していない。

## 比較

| 形状 | 最終メッシュの変位 | 最大絶対主応力 | 判定 |
|---|---:|---:|---|
| 現行r9 | 8.135 mm | 26.33 MPa | 変位・応力不合格。応力も未収束 |
| 両側にリブを追加 | 2.440 mm | 37.03 MPa | 不合格。リブが背面の狭い支持壁へ直接つながらない |
| リブを幅36 mmの背面壁につなぐ | 0.1504 mm | 1.956 MPa | この1荷重・理想固定のスクリーニング条件では合格 |

最後の形状は3→2 mmメッシュで変位差約0.31%、最大主応力差約1.52%。ただし単一荷重の結果であり、全荷重・締結・接触・座屈を確認したものではない。
最初の8 mmという線形解析結果は小変形仮定からも外れるため、実物の正確なたわみの予測として扱わず、現設計を棄却する指標とする。

支持部単体の外側包絡は変更していない。PETG密度1.27 g/cm³による追加質量は左右合計約23.8 g。
新たな背面幅と既存胴体の接合部は調整が必要で、追加リブが動作軌道・配線に干渉しないことも未確認。
サーボ軸の内部軸受の許容荷重を本解析から保証しない。荷重経路と外部支持・締結の設計は続ける。

## 再現

[環境手順](ENVIRONMENT_ja.md)のライブラリパスを設定し、リポジトリルートから実行する。出力先は毎回新しいものを指定する。

```sh
.venv-engineering/bin/python software/sim/structural/check_beam.py --out outputs/beam_check_new
.venv-engineering/bin/python software/sim/structural/extract_load_cases.py --out outputs/support_loads_new
.venv-engineering/bin/python software/sim/structural/screen_yaw_support.py --loads outputs/support_loads_new/loads.json --out outputs/support_baseline_new
.venv-engineering/bin/python software/sim/structural/build_yaw_support.py --wide-back --out outputs/support_candidate_new
.venv-engineering/bin/python software/sim/structural/screen_yaw_support.py --loads outputs/support_loads_new/loads.json --step outputs/support_candidate_new/left_yaw_fixed_support.step --out outputs/support_candidate_screen_new
```

`--wide-back`を省略すると途中のリブのみの形状を再生成できる。
既知解との照合では、40×10×4 mmの片持ち梁の端面へ1 Nを加え、Euler–Bernoulliの変位との誤差1.64%、最終2段階の差0.20%を確認した。梁理論と3D完全固定の差があるため、完全一致は要求していない。
各解析の計画・荷重・メッシュ・変位・応力・不合格記録は `validation/yaw_support_development_v1/` に保存した。
