# ヨー支持の統合比較候補（製造未承認）

配線開口付き金属板、下方へ深くした側面リブ、ヨー専用ワッシャーを一つの52部品組立へ統合した。現行ポインターrevBは変更していない。これは部分候補を混在させずに評価するための比較パッケージであり、製造リリースではない。

## 統合確認

変更は支持棚2点、金属板2点、支持板ワッシャー8点の計12点。残る40点の原資料・体積・重心・慣性がrevBと一致することを確認。質量は部品を置換した差として計算し、元部品への二重加算を避けた。均一中実PETG 1270 kg/m³、金属7930 kg/m³の既存比較仮定で差は+6.31217 g。実造形・実測の質量ではない。重心計算用の一次モーメント差と組立原点まわりの慣性差も保存した。

変更部品を含む546組の固定部品ペアを比較し、新規の重なり増加は0.01 mm³以下。しかし、胴体外装と左右支持棚の重なり各370.875 mm³が旧revBから残る。接合の意図・組立方法が確認されておらず、**この重なりが残ったまま組立可能とは判断しない。** 「新規干渉なし」は既存干渉の承認ではない。

`validation/yaw_integrated_motion_v1` で組立全体とヨーカプラ＋ロール支持の組をヨー±15°、1°刻みで確認。最小距離2.08232 mm、サンプル間上限0.273883 mmと公差・変形の仮配分0.8 mmを控除すると1.00844 mm。これは限定可動群の確認で、全身・配線・工具・実変形を保証しない。棚の変位配分0.2 mmは別の保存荷重解析で未達のため、この余裕だけで完成扱いにしない。

## 残る阻害要因

- 胴体外装と支持棚の既存重なりを意図・荷重経路と照合し、別部品としての組立を成立させる。
- 棚の保存荷重最大変位0.237657 mmは0.2 mm配分未達。
- 金属板―棚の引張り荷重経路、接触離間、ねじ・ナット・座面保持と予圧が未確認。
- 全身最新質量、配線、材料許容値、造形・組立工程、全荷重／全動作の確認が未完了。

これらを実機Issueへ移して#17〜#20を完了にしない。BOMの正式置換・current.json更新・製造リリースは未実施。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_yaw_support_candidate.py --out validation/yaw_integrated_reproduce --moments --rear-washer-dir validation/rear_washer_clearance_v1 --support-dir validation/yaw_deep_side_ribs_v1 --plate-dir validation/yaw_connector_plate_relief_v2 --plate-washer-dir validation/yaw_plate_washer_v1
.venv-engineering/bin/python software/sim/structural/compare_yaw_integrated_candidate.py --candidate validation/yaw_integrated_reproduce
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate validation/yaw_integrated_reproduce
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out validation/yaw_integrated_motion_reproduce --step-deg 1 --include-cradle --joint-limits --fixed-assembly validation/yaw_integrated_reproduce/yaw_support_candidate.step
```

出力先は未使用のものを指定。形状、幾何慣性、入力ハッシュ、変更照合、既存重なりを含む結果を保存する。
