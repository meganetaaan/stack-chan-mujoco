# 固定具を含む左右電源基板の機体配置

## 結論

既存候補位置XY=(-25,±31) mmを維持できる公称空間がある。基板・スペーサ・ねじ頭を全て包む直方体43.8×32.4×12.5748 mmで、固定部52点、トレイ、電池、Tab5、TTLとモジュール相互の113組を比較し、重複なし、最小隙間2.80 mm。事前の公称0.5 mmスクリーニングを通過した。部品の詳細形状より保守的な外包形状なので、この配置のためだけに詳細モデルの追加解析は不要。

## 配置と基準

layout_v2の下面部品の高さを保持し、PCB下面をZ=105.065 mmとした。左右とも公式STEPを回転せず、長辺を機体X、部品面を+Zへ向ける設計案。変換はreport.jsonのstep_translation_mm、8本の取付軸はmount_axes_mm。短辺方向の穴列の偏りを保持し、左右鏡像にはしていない。

下面スペーサの高さ3 mm、上面ねじ頭の直径3.8・高さ1.3 mmは前回の予約寸法。共通STEPの上面高さ8 mmを含めるため、5V版図面6.1 mmより高い外包形状とした。XYには前回の基板外形公差拡張を含む。全部のモデルと固定具が外包形状に収まることを検査し、Z範囲は102.065〜114.6398 mmとなった。

## 残る設計

この検査は固定先や保持強度を証明しない。基板下面から3 mmのスペーサを支持する台座、ねじ軸・ナット、配線・端子、工具の出し入れ、動的脚干渉、絶縁、冷却は別途必要。共通STEPと5V版の型式差、部品・取付公差は未確定。型式差を今回の外包形状で全て包含できる保証とはしない。実部品選定と固定台座が次の作業であり、空間だけを再検査する探索は行わない。

## 再現

依存: CadQuery。入力SHA256はreport.json。
```sh
curl -L https://www.pololu.com/file/0J2219/d42v110fx-step-down-voltage-regulator.step -o /tmp/pololu-reg34c.step
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_pololu_mounted_layout.py /tmp/pololu-reg34c.step --out validation/dual_pololu_mounted_layout_v1
```
製作リリースとIssue完了は変更しない。
