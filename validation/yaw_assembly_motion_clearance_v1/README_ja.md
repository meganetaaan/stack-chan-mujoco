# ヨー固定組立全体との旋回隙間

現行revBの52部品を含む固定組立STEPと、左右のヨーカプラ＋ロール支持枠を比較。モデル関節限界±15度を1度刻みで検査した。左右とも最小サンプル距離2.082322mm、点間移動上限0.273883mm。既存の製作公差0.2mm/側と変形配分0.2mm/側を差し引いた連続範囲の隙間下限は1.008439mmで、既存基準0.5mmを満たす。

これは指定形状の剛体回転についての条件付きスクリーニング。配分値はCodexの仮置きであり、実際の印刷精度・荷重変形の証明ではない。TPU等の材料変更時も変形配分を自動的に満たすとは扱わない。全身の可動脚、配線、工具、関節限界外の動作は対象外。#5の完了判定には使用しない。

再現（リポジトリルート）：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out /tmp/yaw-assembly-review --fixed-assembly board/mechanical/prototype/yaw_support_candidate/revB/yaw_support_candidate.step --include-cradle --step-deg 1 --joint-limits
```

入力形状ハッシュはreport.json、基準と限界はplan.json、各角度の距離は左右npzに保存。
