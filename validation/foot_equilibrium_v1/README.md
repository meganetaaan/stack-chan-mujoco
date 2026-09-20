# 足部の空間力学釣合い

記録した7000時刻×左右足についてI*a+v×*(I*v)=cfrc_int+cfrc_extを確認。力残差最大1.78e-15 N、モーメント残差4.17e-17 N·m。接触力を接触座標から世界座標へ回転し、作用点からsubtree COMへ移した独立合計はcfrc_extと一致。

2.447秒の左足では、世界鉛直の床反力9.00335 N、足首反力-8.45156 N、差0.55179 N。MuJoCoのcaccには重力に関する規約が含まれるため、この差を純粋な並進加速度項だけと解釈しない。足部質量・慣性と重力を省略した静的荷重モデルは修正が必要。

空間代数は公式実装を参照：https://raw.githubusercontent.com/google-deepmind/mujoco/3.3.0/src/engine/engine_util_spatial.c 。実行環境の記録データに対する釣合いで検証した。モデル階層の葉ボディであることと外力設定の明示的監査は別途必要。数値残差一致は構造強度の証明ではない。

```sh
.venv-engineering/bin/python software/sim/structural/audit_foot_equilibrium.py --out outputs/foot_equilibrium_repro
```

次は接触位置と力を足部CAD座標へ変換し、分布反力と部品慣性の形で全体モデルへ適用する。
