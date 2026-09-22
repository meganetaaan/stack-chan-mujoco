# 現行固定ヨー組立とメーカーサーボ形状

旧`yaw_manufacturer_fit_v1`の配置仮説を使い、検査対象を現行revBの52部品固定組立へ拡大した。ケース包絡が既存モデルの20×34×23mmに一致することを確認。

左右ともケースとコネクタ本体の体積交差は0。ケースは接触（距離0）を含み、公差余裕は未証明。コネクタ本体から固定組立への最小距離は3.1mm。嵌合側ハウジングとケーブルは含まないため、この値で配線が取り付くとは判定しない。

背面アイドラ群は左右それぞれ約525.796mm³交差する。旧記録と同様に装着状態は不合格。現行設計は元からアイドラなしであり、今回の合格化のために除いたものではない。全サーボ部品・固定ねじ・出力側可動部・公差・強度を含む適合判定は未完了。

v1実行はCAD変換APIの例外で検査前に停止。v2では旧検査と同じ回転・平行移動APIへ変更し、判定基準は変更していない。

再現（メーカーSTEPの取得URL・ハッシュは`servo_reference_geometry_v1`）：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_current_manufacturer_fit.py --step /path/to/XL-XC-330.stp --out /tmp/yaw-current-fit-review
```
