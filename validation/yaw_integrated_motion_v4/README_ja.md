# 統合v4のヨー可動部と固定52部品の隙間

## 設計判断

ねじ逃げ付き横リブを含む統合v4に対し、ヨーカプラ＋ロール支持の左右ヨー±15°を検査した。左右とも公称最小隙間2.082322 mm、角度サンプル間の移動上界0.273883 mm、公差0.2 mm/部品、変形0.2 mm/部品を控除した隙間下界は **1.008439 mm**。既存の残存隙間0.5 mm条件を、この限定された形状・動作範囲・配分条件で満たす。

最小サンプル姿勢は左+15°、右−15°。52部品を個別に照合した最近接相手は `body_shroud`（胴体外装）。その姿勢で支持部自体との距離は9.433981 mm。従来の支持部単体検査より胴体外装を含む検査が厳しく、補強リブだけを動作干渉の支配部と考えてはいけない。

## 0.2 mm配分の意味

ユーザー要求は外形・脚長を基本的に保ち、必要な動作を成立させること。0.2 mm/部品の変形配分、0.2 mm/部品の公差、0.5 mmの残存隙間はいずれも設計上の仮置きであり、材料仕様でもユーザーが指定した値でもない。

この形状対では公差・サンプル間移動・残存隙間を差し引くと、合計相対変形に使える幾何学上の予算は0.908439 mm。現在の合計配分0.4 mmより0.508439 mm大きい。しかし、この余裕を使って0.2 mmの基準を変更したり、支持部FE不合格を取り消したりしない。支持部の絶対変位と、胴体外装に対する可動部の相対変位は異なる。

一方、外側配線予約通路は公称1.3 mmで、既存控除0.8 mm後は0.5 mmと余裕がない。可動部―胴体間の余裕を、その配線通路へ流用できない。次の構造判断は、支持棚に取り付くサーボ・コネクタと支持開口の相対移動、取付接触・締結、および胴体外装の変形を分けて扱う。単に支持部の全体最大変位だけを下げる補強走査は行わない。

## 未確認・終了条件

- 脚全体の複合関節運動、サーボ実形状・全配線・工具は今回の可動形状に含まない。
- 公差・変形配分は実材料や実組立の保証ではない。現在支持部は保存荷重で0.220130 mmとなり、従来の暫定基準未達のまま。
- 1°間隔で計算し、剛体単軸回転の弧長上界を用いて角度間を保守的に控除した。下界が既存基準を超えたので角度刻みを細分化しない。
- 今回の結果で#5や#19をクローズせず、製作判定は保留。

## 再現

リポジトリルートから未使用の出力先で実行する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out /tmp/yaw-motion-v4 --fixed-assembly validation/yaw_integrated_candidate_v4/yaw_support_candidate.step --include-cradle --joint-limits --step-deg 1
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/identify_yaw_motion_neighbours.py --candidate validation/yaw_integrated_candidate_v4 --motion /tmp/yaw-motion-v4
```

`plan.json`に事前の基準・検査範囲、`report.json`に角度間控除を含む結果、`neighbours.json`に部品別距離と配分計算、NPZに角度別距離を保存。
