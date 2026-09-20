# 接触荷重のCAD座標変換

7000時刻の左右足接触をankle_roll局所座標へ変換。力N、位置mm、接触偶力とモーメントN·mm。ヨーク下面中心(1,±6,-19)へ作用点を移した合力は、cfrc_extの独立変換と力5.33e-15 N・モーメント3.13e-13 N·mm以内で一致。モデル生成によって左右足首ボディに子ボディがないことも確認。

サンプル2446では左3点接触、右は非接触。左の局所Fz=9.00339 N、取付面中心Mx=-204.31998 N·mm。静的反力とは異なることを保持し、慣性項を勝手に床荷重へ吸収しない。

注意：接触点は矩形衝突形状の角付近（x=-39/47、y=-18/30）。実CADは半径3 mmの丸角なので、これらの角点を実CADへそのまま点荷重として与えるのは不適切。衝突形状と実足裏の整合、TPUによる荷重分布、部品ごとの慣性配分を解決してから構造解析へ適用する。圧力中心だけの一致は局所応力の正しさを保証しない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/export_foot_contact_loads.py --out outputs/foot_local_repro
```

contacts_local.jsonl.gzに全接触点、wrenches.npzに全合力、plan.jsonに座標と判定基準、report.jsonに誤差と対象時刻を保存。構造強度は未認定。
