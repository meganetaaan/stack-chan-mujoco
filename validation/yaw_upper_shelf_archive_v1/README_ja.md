# 上面補強案の保存荷重全体評価

38履歴・266000時点を3 mmメッシュの6単位荷重解で評価。
三角不等式上限は最大0.207202 mmで、その値だけでは0.20 mm以下を証明できなかった。
これは実変位超過ではない。隣接するyaw_upper_shelf_archive_resolution_v1で
上限超過の全56時点を直接合成し、残り265944時点は三角不等式上限で判定した。
組合せた全時点上限は0.199809 mmで、線形FEの節点変位条件を満たす。
この値は実際のピーク値ではなく、異なる二種類の評価を合わせた保守的上限。

材料E1120 MPa・ν0.35、理想後部固定、接着相当分布荷重、左右対称仮定を維持。
単一メッシュでの全履歴評価であり、前回の一荷重2 mm比較を全ケースの収束証明としない。
最新質量、接触・締結、座屈、実印刷材料の強度は未確認。製造リリースではない。

再現（出力先は未作成）：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --current-shelf --step validation/yaw_upper_shelf_v1/left_yaw_fixed_support.step --out /tmp/yaw-upper-archive
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/resolve_yaw_bound_exceedances.py --archive /tmp/yaw-upper-archive --out /tmp/yaw-upper-resolution
```
再生成可能なメッシュ・単位解・履歴配列はGit対象外。判定と入力ハッシュを保存する。
