# 足部剛性3部品のPETG質量・慣性比較

foot_candidate/revBのブーツ・ヨーク・保持部に、既存Prusament PETG候補の典型密度
1.27g/cm³を適用した。製品を手持ち材と同一と仮定したものではなく、設計比較の材料選択。
片足50.39284g。左右各3部品の重心と重心まわり慣性を、平行軸の定理で合成した。
合成慣性の正定値性と主慣性の三角不等式を確認。左右の結果をreport.jsonへ保存。

接地材・ねじ・ナット・ワッシャ・サーボ・ホーン締結品・ハーネスを除外。
中実CADの計算で、実造形重量・材料強度・クリープを保証しない。
全身や足首ボディの慣性として直接MuJoCoへ代入しない。
残る部品の寄与とCADからMJCFへの座標変換を確認したうえで統合する。

```sh
.venv-engineering/bin/python software/sim/structural/calculate_foot_rigid_inertia.py --out /tmp/foot-rigid-inertia
```
