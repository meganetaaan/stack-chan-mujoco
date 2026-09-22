# 工具逃げ変更後の一荷重剛性再評価

既存の直接評価済み最大変位荷重、E1120 MPa・ν0.35、理想固定、分布荷重を維持。
3 mmメッシュ変位0.133772 mm、2 mmメッシュ0.135102 mm。
両方0.20 mm以下、変化率0.995%で既定の10%以下条件内。
残差と仕事・エネルギーの整合も通過。

工具逃げ変更前の全履歴合格を、新形状の全履歴合格へ転用しない。
局所応力・実締結・造形材料・最新質量・組立は未確認。製造リリースはfalse。
再生成可能なメッシュはGit対象外。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_yaw_upper_shelf.py --step validation/yaw_upper_tool_relief_v1/left_yaw_fixed_support.step --out /tmp/yaw-tool-relief-fe
```
