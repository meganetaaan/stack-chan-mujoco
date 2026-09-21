# 足部の比較候補 revA（材料・保持性能は未確定）

TPU案の左右組立STEPと部品出典をrevA/に保存。現行工程向け再設計は[MATERIAL_CHANGE_ja.md](MATERIAL_CHANGE_ja.md)を参照。各側はブーツ、外付けナット用ヨーク、TPU足裏、スペーサー、10 mmねじ、外付けナットの6部品。サーボ/ホーン締結品/ハーネスは未収録。全身完成CADではない。

| 部品 | 左右合計 | 採用候補・注意 |
|---|---:|---|
| ブーツ | 2 | boot_low_head_candidate_v1 |
| ヨーク | 2 | sole_external_nut_v1。閉室/側面挿入案を混ぜない |
| TPU足裏 | 2 | sole_wide_seat_v1。嵌合公差・保持強度未確定 |
| スペーサー | 2 | SCW-SOLE-SPACER-01、呼び形状。端部仕上げ・製法未確定 |
| ねじ | 2 | NBK SLH-M2-10。8 mm旧案ではない |
| ナット | 2 | PTS A56202、ボス上面へ配置 |

inventory.jsonに元STEP・SHA-256・各部品体積を保存。組立STEPは同一座標の部品を束ねたもの。全12部品の有効単一ソリッドを確認したが、組立の出力成功は公差/強度/動作の合格ではない。

## 組立手順案

1. ねじ・ナット・スペーサーの実寸を測定し、足裏の挿入/スライドを無通電で確認。
2. スペーサーとねじを床側からセットし、上面ナットを工具で保持する。
3. 締付け条件は未確定。メーカー最大トルクを組立値として使わない。
4. 床側の頭沈み、ナットかかり、足裏の滑り/浮き、実工具経路を記録。

中立時のメーカーサーボ/ジンバルと工具予約空間はvalidation/external_nut_servo_clearance_v1で確認済み。実工具操作、全姿勢、緩み・クリープ、材料/造形、公差、負荷変形は未確認。#48への引継ぎ候補であり、強度試験用に条件が確定した状態ではない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_foot_candidate.py --out outputs/foot_candidate_new
```

外付けナット・10 mmねじについては、既存運動割当のもとでロール±0.34 radの連続隙間下限7.670 mmを確認（validation/external_nut_roll_bound_v1）。全身/ハーネス/公差変形の検証とは区別する。
