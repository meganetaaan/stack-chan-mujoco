# 工具逃げ修正後の全保存荷重評価

対象は工具逃げ半径4.0 mmの新形状。3 mmメッシュの6単位荷重解を再計算した。
38履歴266000時点のうち265874時点は三角不等式上限が0.20 mm以下。
残り126時点は直接合成し、その範囲の最大は0.159501 mm。
組合せた全時点の保守的上限は0.199965 mmで既存変位条件内。
上限0.199965 mmは実ピーク値ではなく、境界近くの三角不等式上限を含む。

前形状の結果を流用せず、修正CADのハッシュ・単位解・荷重履歴のハッシュを保存。
最新質量・実締結・印刷材料・公差や連成変形を保証しない。
一荷重の2 mm比較は別保存で、全履歴のメッシュ収束を証明したものではない。
強度許容は未確定、工具嵌合・組立も未成立なので製造リリースしない。

再現（出力先は未作成）：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --current-shelf --step validation/yaw_upper_tool_relief_v1/left_yaw_fixed_support.step --out /tmp/yaw-tool-archive
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/resolve_yaw_bound_exceedances.py --archive /tmp/yaw-tool-archive --out /tmp/yaw-tool-resolution
```
再生成可能なメッシュ・単位解・履歴配列はGit対象外。
