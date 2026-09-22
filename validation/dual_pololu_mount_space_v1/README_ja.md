# 電源基板固定具の公称空間検査

公式STEP: https://www.pololu.com/file/0J2219/d42v110fx-step-down-voltage-regulator.step

## 結論

4個の取付穴はDXFとSTEPで対応し、STEPのXYにDXF左下原点をそのまま対応できる。PCB下面Z=0、上面Z=1.5748 mm、部品側は+Z。ロボット座標への配置は未実施。

外径4・内径2.2・高さ3 mmの下面スペーサと、直径3.8・高さ1.3 mmの上面ねじ頭の予約形状を検査した。いずれも基板・部品との体積重複0。下面部品との距離は最小1.417 mm、上面部品との距離は最小0.796 mmで、事前設定した公称0.5 mmのスクリーニングを通過した。これは公差込みの成立確認や電気的絶縁確認ではない。スペーサ底面Z=-3に平板を置いた場合、モデル下面部品Z=-1.8との公称空間は1.2 mmだが、実際の台座・ねじ・ナット・工具は未設計。

## 図面とモデルの違い

共通STEPは上面部品高さ8.0 mm、全高11.3748 mm。5V版図面の上面6.1 mm、丸め全高9.47 mmとは異なる。共通モデルに対する結果を5V版部品配置の保証としない。既存layout_v2は5V図面外包形状であり、このSTEPの配置検査ではない。型式別部品占有域と高さの対応は未確認。

## 解析の修正記録

初回は穴位置照合を1e-6 mmで要求して停止した。STEP穴中心にはDXF換算値と0.00003 mmの差がある。DXFの桁丸めを扱うため照合許容差を0.002 mmへ変更した。これはデータ対応の許容差で、干渉判定・0.5 mm空間条件・物理的な穴公差は変更していない。

## 再現

依存: CadQuery。
```sh
curl -L https://www.pololu.com/file/0J2219/d42v110fx-step-down-voltage-regulator.step -o /tmp/pololu-reg34c.step
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_pololu_mount_space.py /tmp/pololu-reg34c.step --out validation/dual_pololu_mount_space_v1
```
入力SHA256はreport.jsonに記録。先にplan.jsonで寸法・基準・終了条件を定義した。銅箔・絶縁・ねじの噛合い・締付力・実スペーサ選定・全身配置・配線・公差を残し、製作リリースはfalse。追加の形状探索は行わない。
