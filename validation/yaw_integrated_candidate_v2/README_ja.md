# ヨー支持の統合比較 v2

v1の支持棚を `yaw_rail_seat_v1` へ置換。配線開口、深い側面リブ、専用ワッシャーを維持し、外装横桟との公称干渉を接触座へ置き換えた。現行ポインターrevBと正式BOMは未変更、製造未承認。

52部品中12点がrevBから変更、40点の形状・位置・幾何慣性は維持。既存の密度仮定による置換質量差はrevB比+4.62821 g。全身質量・実造形質量ではない。

変更部品を含む546組を再確認し、新規重なりなし。v1で残っていた外装―左右支持棚の各370.875 mm³の重なりも0となった。公称接触は意図したものだが、ねじと座面の同時組立、公差、予圧、荷重分担の成立は未確認。

この検査は546組を対象とし、残る未変更部品同士を新たに検査したものではない。全身、配線、工具を含む干渉合格とは扱わない。v2はv1支持から材料を除去する変更だが、荷重変形と強度は再評価が必要。旧FE結果での製造承認はしない。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_yaw_support_candidate.py --out validation/yaw_integrated_v2_reproduce --moments --rear-washer-dir validation/rear_washer_clearance_v1 --support-dir validation/yaw_rail_seat_v1 --plate-dir validation/yaw_connector_plate_relief_v2 --plate-washer-dir validation/yaw_plate_washer_v1
.venv-engineering/bin/python software/sim/structural/compare_yaw_integrated_candidate.py --candidate validation/yaw_integrated_v2_reproduce
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate validation/yaw_integrated_v2_reproduce
```

出力先は未使用のものを指定する。接触座単体の設計根拠は `validation/yaw_rail_seat_v1/README_ja.md`。
