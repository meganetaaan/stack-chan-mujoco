# ねじ逃げ付きリブ案の変形比較：未達

`plan.json` を解析前に保存し、既存0.2mm枠、同じ保存荷重・理想後端固定・E=1120MPa・ν=0.35を維持した。材料は仮定の等方性で、ABS/PETG実造形品の保証値ではない。

3mmメッシュの最大変位0.231898081mmで未達。直前rail-seat案0.238077068mmより約2.6%小さいが、双方のメッシュ差を含む比較なので厳密な改善量とはしない。各側2026.35mm³の追加に対して基準到達の証拠は得られなかった。

77409自由度・13770要素。自由節点の残差約2.98e−11N、外力仕事2.649709845Nmm、ひずみエネルギー1.324854922Nmmで数値釣合いを確認。局所最大応力を完了条件に用いない。3mmで変位未達の場合は2mmへ細分化しないという事前終了条件に従って停止した。

結論: 干渉の修正はできたが、変形枠は未達。正式候補へ採用せず、このリブ厚の走査を続けない。次の形状検討では支持位置・荷重経路に関する不確実性を先に扱う。今回の保存荷重は最新の全機体負荷包絡ではなく、支持接触・ねじ予圧・クリープ・全動作干渉も未検証。

再現（新しい出力先、メッシュは生成物）:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_yaw_deep_ribs.py --step validation/yaw_relieved_inward_ribs_v1/left_yaw_fixed_support.step --out /tmp/stackchan-relieved-ribs-fe
```
