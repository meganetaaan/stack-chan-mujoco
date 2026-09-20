# 歩行ログから作る胴体底面開口

胴体128 mm立方体、腿50 mm、脛44 mm、足94×52 mm、股間隔44 mmを維持した候補。
`underside_cutouts.json` は既存開口と3条件の実測関節姿勢から得た追加開口を含む。
`provenance.json` に生成元と生ログのSHA-256を保存している。

脚の各CAD部品と底板厚さの水平スラブの交差を計算し、そのXY境界箱を各方向1.5 mm拡張する。
左右それぞれの凸包に既存開口を含め、外周壁と追加2 mmの縁を残す条件で生成した。
開口は底板のみを切り、外周寸法・脚長・関節位置・電池位置は変えない。
1.5 mmは抽出姿勢に対する設計余裕であり、連続動作の最小隙間や製造公差を保証しない。

## 再生成

先に `design/README_ja.md` に従い `outputs/design_r6_battery_lower` を生成する。
出力先は存在しないディレクトリを指定する。

```bash
.venv-cad/bin/python derive_underside_cutouts.py \
  --design outputs/design_r6_battery_lower \
  --trajectory validation/reference_gait/fast_crouched/trajectory.csv \
  --trajectory validation/reference_gait/medium_crouched/trajectory.csv \
  --trajectory validation/reference_gait/slow_comp/trajectory.csv \
  --stride 10 --margin-mm 1.5 --out outputs/underside_gait_reproduce
.venv-cad/bin/python build_design.py \
  --out outputs/design_r6_gait_opening --hip-half-spacing-mm 22 \
  --battery-layout design/battery_layouts/internal_lower_envelope.json \
  --underside-cutouts design/gait_opening/underside_cutouts.json
.venv-cad/bin/python check_design_clearance.py \
  --design outputs/design_r6_gait_opening \
  --trajectory-csv validation/reference_gait/fast_crouched/trajectory.csv \
  --stride 10 --out outputs/gait_opening_fast_clearance.json
```

同じ検査を `medium_crouched` と `slow_comp` に対して行う。高速・中速の検査は
残る干渉のため終了コード1、低速の抽出姿勢は終了コード0となる。
検査は10行おきと末尾行を含む。全時間ステップや連続掃引ではない。

形状・関節の不変条件とMuJoCoコンパイルは次で再検査する。

```bash
.venv-dynamics/bin/python validation/verify_opening_variant.py \
  --baseline outputs/design_r6_battery_lower \
  --candidate outputs/design_r6_gait_opening \
  --out outputs/gait_opening_invariants.json
```

## 結果と残課題

`validation/gait_opening/` に検査結果を収録。

- 高速9姿勢・中速15姿勢・低速25姿勢の全機械部品組合せを検査。胴体との体積干渉は0。
- 高速の2姿勢に脚内部干渉が残る。右膝／足首ジンバル3.191 mm³、左クレードル／膝1.854 mm³。
- 中速の4姿勢に計5件の脚内部干渉が残る。最大は左膝／足首ジンバル6.135 mm³。
- 低速の25姿勢では体積閾値0.01 mm³を超える干渉なし。
- 元モデルとのSTL比較では胴体シェルだけが変更され、他37部品はバイト単位で一致。
  関節位置・軸・可動範囲と身体パラメータも一致。MJCFは17 qpos・16速度・10アクチュエータでコンパイル。
- CAD質量は約856.485 g。開口拡大により約2.082 g減少した。

この結果は既存ログの関節姿勢を変更後CADに適用したもので、変更後モデルによる歩行成功ではない。
底板の強度・荷重経路、ねじ・配線・公差、全歩行範囲の隙間、簡略衝突形状の精度は未検証。
次はクレードルとジンバルの干渉位置を特定し、荷重経路を保つ局所修正を検討する。
