# 前端横壁を深くする案：不採用

前端横壁の下端をZ78から70 mmへ延長。外形・脚長・関節軸・既存形状・ねじ逃げを維持した。
左右それぞれ684.944 mm³の追加。材質・密度が未確定のため重量確定やMuJoCo慣性更新は行っていない。

最新比較組立v5の固定部品およびメーカーサーボCADとの追加体積干渉なし。
サーボCADまで3.5 mm、既存ポート通路まで1.3 mm。
動作全域・工具・配線・印刷性・実締結の成立を意味しない。

既存38ケースの直接評価済み最大変位荷重を使用。E1120 MPa、ν0.35、
理想後部固定・分布荷重の条件を維持し、3 mmメッシュで一度比較した。
変位0.220130→0.216713 mm（約1.55%低減）で0.20 mmを満たさない。
外力仕事とひずみエネルギー、自由節点の残差は整合した。
局所応力値は材料許容・締結モデルが未確定なので強度合否には使わない。

事前の停止条件に従い2 mm細分化は実行しない。小さい改善量を収束済み効果とは扱わない。
この案単独で変位不足を解消できる証拠がないため、正式候補v5へ反映しない。
前端にエネルギーが集中することは、横壁だけの延長が有効である証拠ではなかった。
次案は棚板自身の断面または荷重を伝える支持点の変更を検討し、
同じ横壁の深さだけの探索を続けない。試作HOLD・Issue未完了を維持。

再現（各出力先は未作成）：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_front_web_deeper.py --out /tmp/yaw-front-geometry
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_yaw_front_web_deeper.py --step /tmp/yaw-front-geometry/left_yaw_fixed_support.step --out /tmp/yaw-front-fe
```
