# 丸角衝突形状の細分化（失敗継続）

86×48×3 mm、半径3 mmを維持し、四分円16分割の解析的頂点を生成。入力ポリゴンの円弧弦誤差は3*(1-cos(pi/64))=約0.003614 mm。コンパイル後の質量・慣性・重心・慣性姿勢・関節範囲は凍結r9と完全一致。

既存制御で2.799秒、25.1884度時点にjoint_limit。粗いSTL候補の2.801秒・25.3405度と近く、細分化だけでは停止を解消しない。形状精度が全動作で収束したとまでは主張しない。凍結モデルと関節範囲は変更していない。

モデルは剛体凸包。上面のねじポケットやTPUの変形を表さない。collision_plan.jsonの一般的な旧文言「existing visual sole mesh」に対し、この試行はarc_segments=16とscene.xmlの解析的頂点を使用した。次は支持姿勢の余裕を確認する。

```sh
.venv-engineering/bin/python software/sim/mujoco/build_rounded_sole_collision.py --arc-segments 16 --out outputs/rounded_fine_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/actuator/run_probe.py --foot-loads --model outputs/rounded_fine_repro --out outputs/rounded_fine_probe_repro
```

scene.xmlは参照用。依存資産は生成コマンドでコピーする。構造解析用の成功した全動作荷重はまだ得られていない。
