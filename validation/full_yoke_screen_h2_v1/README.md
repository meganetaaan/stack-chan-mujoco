# ヨーク細分化と境界条件の監査

3→2 mmで最大変位0.762626→0.766864 mm。主応力4.47947→7.11845 MPaで未収束、仮許容5.6 MPaも超える。最大変位位置は(46.598,-16.5,-19) mm、最大応力は(5.893,-8.763,-15.907) mm。

積分点でアフィン荷重を再構成し、力・モーメントの保存を確認した。底面積の33.66%に負のzトラクション、引張合計2.98644 Nがある。節点荷重の符号ではなく、積分点の荷重密度で判定。これは接着のない足裏接触として不適切であり、全体強度を認定できない。

次は圧縮のみの分布または実床接触分布と部品慣性を使用する。境界条件を修正する前にこの変位を根拠に補強形状を確定しない。現行の不合格・未収束記録は残す。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_full_yoke.py --mesh-mm 2 --out outputs/yoke_h2_repro
.venv-engineering/bin/python software/sim/structural/audit_yoke_screen_fields.py --source outputs/yoke_h2_repro
```

最初の監査実行はLD_LIBRARY_PATH未設定によりlibGLUのロードに失敗した。上記設定で再実行し完了した。解析結果には影響しない。
