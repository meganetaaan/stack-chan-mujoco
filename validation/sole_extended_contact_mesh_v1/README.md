# 縁落としを含む接触候補面

従来のcontact集合はCAD同士で共有する平坦円環面のみ。最大圧力が外周r=2.925 mmに出ても、その外側の縁落としが変形後に接触する可能性を判定できない。平坦部のみの収束検査を続ける前に、このモデル範囲を明示して候補面を追加した。

`--contact-extensions`を追加。元の平坦接触面は変更せず、ボス底面z=−19の残り部分と、スペーサー上端の2つの45度縁落とし面をそれぞれcontact_extensionとして出力。新しい面は平坦接触パッチと重複しない。スペーサーの縁落とし面はCAD面積1.843796 mm²、メッシュ1.846386 mm²（誤差0.1404%）。ボス対向追加面はCAD37.681308 mm²、メッシュ37.806716 mm²（0.3328%）。既存の体積保持・接触面座標一致・各面積誤差1%以内を維持した。

追加面の最外縁/最内縁は初期隙間0.05 mmを持つ。初期の接触と誤認しない。面の対応は一致節点の組ではないため、現在のprobe_sparse_sole_contact.pyは追加タグを読むだけでは利用しない。対向面への投影・初期隙間・荷重転送を実装・検証してから評価する。今回の成果は接触候補のメッシュ準備であり、拡張接触解析の合格ではない。

縁落とし面への接触が実際に発生するか、この省略が圧力非収束の主因かはまだ不明。以前の結果や不合格判定は保持する。接合強度・Issue完了は主張しない。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.5 --out outputs/sole_extended_contact_mesh
```
