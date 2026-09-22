# 丸角足裏の衝突モデル候補（動作失敗）

凍結r9を変更せず別モデルを生成。左右足裏の矩形box衝突を既存sole_TPUのmesh衝突へ変更。MuJoCoでコンパイル後、全ボディ質量・慣性・重心・慣性姿勢・関節可動域の完全一致を確認。

同じ制御・5 V・遅延10 msで、2.801秒、25.3405度時点にjoint_limitで停止。元の7秒・88.5327度動作を再現せず、未採用候補。停止までの姿勢・荷重・接触力を保存。可動域や電流上限を緩和していない。

これは既存STLの凸包を用いた剛体接触。丸角の離散化、凸包と実CADの距離、ポケットの非凸形状、TPU変形は未検証。形状変更と接触アルゴリズム変更の影響が混在するため、失敗原因を丸角半径だけに断定しない。次は停止関節と接触点・支持範囲を確認する。

```sh
.venv-engineering/bin/python software/sim/mujoco/build_rounded_sole_collision.py --out outputs/rounded_sole_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/actuator/run_probe.py --foot-loads --model outputs/rounded_sole_repro --out outputs/rounded_probe_repro
```

scene.xmlは差分確認用。メッシュとreferenceは上記生成コマンドで凍結資産からコピーする。構造解析へ適用する全動作荷重はまだ確定していない。
