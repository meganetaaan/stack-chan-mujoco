# ねじ逃げ付き横板の統合比較

52部品中、revBからの変更対象12部品、残る40部品の形状/位置/幾何慣性は不変。仮定密度PETG1270/SUS7930kg/m³で置換質量差+6.802906g。全機体重量や実造形重量ではない。

変更部品を含む546組を部品別に検査し、新規重なり0件。v3の支持部―固定ねじ4件の干渉は解消した。元からの重なりはoverlap_report.jsonに保持しており、これらを自動的に意図した接触と認定しない。全1326組や全身動作を今回検査したわけではない。

正式currentと製作用BOMは据置き。FEはねじ逃げ後の形状で再評価する。前案の0.196594mmをこの形状の結果として使用しない。造形、締結、工具、公差、ハーネス、全荷重は未確認。

再現（新しい出力先）:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_yaw_support_candidate.py --out /tmp/stackchan-yaw-v4 --moments --rear-washer-dir validation/rear_washer_clearance_v1 --support-dir validation/yaw_crossweb_screw_relief_v1 --plate-dir validation/yaw_connector_plate_relief_v2 --plate-washer-dir validation/yaw_plate_washer_v1
.venv-engineering/bin/python software/sim/structural/compare_yaw_integrated_candidate.py --candidate /tmp/stackchan-yaw-v4
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate /tmp/stackchan-yaw-v4
```

## 全組合せへの追加検査

`--all-pairs` で52部品の全1326組も検査した。新規増加は0件。ただし既存から残る重なりが12組あり、左右のthreaded_backing_plateとkeeper各2点（各3.392920mm³）、後部ボルト各4本（各6.479535mm³）である。ねじ山の簡略表現などが原因かは別の形状・締結照合が必要で、今回自動的に許容しない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate /tmp/stackchan-yaw-v4 --all-pairs
```

全組合せを検査したことと、全組合せの干渉が成立したことは区別する。残存12組の分類が未完である。
