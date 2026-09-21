# 前端横板を含む統合候補：干渉で不採用

52部品へ前端横板案を統合。revB比12部品変更、40部品の形状/位置/幾何慣性不変。仮定密度による置換質量差+7.41205g。全機体の実質量ではない。

変更部品を含む546組を個別に検査したところ、左右の支持部とplate_2_screw/plate_3_screwに各7.865519mm³、計4件の新規重なりを検出した。0.01mm³基準に対して未達。この形状は不採用。

原因の切り分け: 前回の単体スクリプトは追加体積と複数部品を含むCompoundの共通体積を一括で計算し、0としていた。同じ追加体積を各ソリッドと個別に交差すると上記4件が再現した。従って一括Booleanの0を無干渉の根拠にできない。形状生成スクリプトを部品別検査へ修正し、結果を `yaw_connected_crossweb_pairwise_v1` に保存。元の失敗結果も履歴として保持した。

前回FEの0.196594mmという結果はこの干渉形状に対する数値であり、加工可能な案の証明ではない。ねじ逃げを変更した場合は剛性も再確認が必要。既存のねじを省略して合格にしない。

51部品モジュールの後方挿入通路は `yaw_crossweb_module_insertion_v1` で外装に対する名目検査を通過したが、内部干渉を解消しないため組立可能とは言えない。全動作・工具・配線・公差も対象外。

再現（未使用出力先へ）:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/package_yaw_support_candidate.py --out /tmp/stackchan-yaw-v3 --moments --rear-washer-dir validation/rear_washer_clearance_v1 --support-dir validation/yaw_connected_crossweb_v1 --plate-dir validation/yaw_connector_plate_relief_v2 --plate-washer-dir validation/yaw_plate_washer_v1
.venv-engineering/bin/python software/sim/structural/compare_yaw_integrated_candidate.py --candidate /tmp/stackchan-yaw-v3
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate /tmp/stackchan-yaw-v3
```

正式currentは据置き。次はねじ逃げを組み込んだ横板案を部品別に検査する。過去のCompound一括検査だけの結果は、全組立の無干渉保証として再使用しない。
