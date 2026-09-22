# ヨー支持組立 revB（未承認候補）

後部ワッシャー8点をSCW-YAW-REAR-WASHER-01 revA案へ変更した。内径拡大だけで、公称外形と配置は維持する。52部品中、残り44部品の入力・体積・名称はrevAと一致することをchange_check.jsonに記録。

全組立STEPと密度未割当ての幾何モーメントを保存した。旧revAの解析は履歴として保持し、新形状の強度評価へそのまま転用しない。首下逃げはvalidation/rear_washer_clearance_v1、限定された軸方向公差はvalidation/rear_washer_stack_v1を参照。実座面、偏心、締付け、曲げ、全公差での干渉・製造可否は未確認。

再現（リポジトリルート）：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_yaw_support_candidate.py --out /tmp/yaw-revB-review --moments --rear-washer-dir validation/rear_washer_clearance_v1
```
