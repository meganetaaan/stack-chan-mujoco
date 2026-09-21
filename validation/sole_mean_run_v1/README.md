# 平均拘束の実行失敗記録

元の16桁一般表記係数はCalculiX 2.21の*EQUATION読込みでエラーとなり、計算開始前に終了した。`failed_input.inp`と`failed_input_solver.log`を保存。係数を小数12桁の指数表記へ変更した入力は読込みを通過した。係数長制限が原因と推測するが、パーサ内部の原因を確定してはいない。

`check_serialization.py`は出力INPの9式を読み戻して保存行列と比較し、事前上限1e-11以内を確認する。従属列の微小丸め値をゼロ化した分も誤差に含む。

修正版を実行した最初の試行は会話中断を挟み、再確認時にプロセスが存在せず、完了ログもなかった。`solver.log`はその記録で、終了理由は不明。停止を確認した後、同じ入力を4 GiB仮想メモリ上限で再実行した。

上限付き実行は入力読込み後、行列構築のmast1配列のメモリ確保で終了コード16。最大RSS 4,002,048 KiB、経過6.24秒。`bounded_solver.log`にtime -vの計測とエラーを保存。応力・変位・拘束残差の最終結果は得られていない。平均拘束を合格とする根拠はない。

全節点を結ぶ多点拘束を自由度消去すると疎行列に多数の結合が加わるため、現在の方式は計算量上の問題がある。4 GiB制約下では実行不可だったという結論であり、一般に解析不能とはしない。次の候補は、同じ平均拘束をラグランジュ乗数で扱う疎な連立系、または強さを段階的に下げて影響を検証できる分布ばね。単に上限を増やして繰り返す方針にはしない。

再現（入力生成・丸め確認）:

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/build_sole_mean_constraints.py --source validation/sole_fixed_anchors_v1/h07 --out outputs/mean_constraints_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python validation/sole_mean_run_v1/check_serialization.py
```

メモリ上限付き実行は新しい出力フォルダへcontact.inpをコピーし、そのフォルダで `ulimit -v 4194304`、専用ライブラリパスとOMP_NUM_THREADS=1を設定して`/usr/bin/time -v <repo>/.tools/root/usr/bin/ccx -i contact`を実行した。評価計画と元の構築チェックは保存するが、構築チェックの成功をソルバー成功と読み替えない。
