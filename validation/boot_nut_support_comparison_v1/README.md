# ナット座の支持条件比較

完全固定モデルの最大応力は全3メッシュで座面外周付近。上下方向のみを拘束し、面内の剛体運動を3自由度で止めるnormal_z支持を追加した。既定の完全固定は維持し、梁の解析解比較も再実行して合格。

同じ局所形状・20 N荷重・材料・3メッシュで、最細結果は変位0.001949541 mm、最大絶対主応力1.867033 MPa。仮の変位・応力・最後2メッシュの変化率の4条件に合格。ただし支持条件の感度比較であり、小さい応力を理由に実機代表モデルとして採用しない。

normal_zは引張反力も許す拘束で、離間を扱わない。二次要素の節点反力の符号だけで面圧の符号も断定しない。局所切断・荷重面拡張・材料等方性・予圧省略などは未解決。実接触と離間を含む解析が必要で、強度・製造承認なし。

## 再現

engineering環境でLD_LIBRARY_PATHに.tools/root/usr/lib/x86_64-linux-gnuを設定する。

```sh
.venv-engineering/bin/python software/sim/structural/screen_boot_nut_seat.py --support-mode normal_z --out outputs/reproduce_normal_seat
.venv-engineering/bin/python software/sim/structural/check_beam.py --out outputs/reproduce_beam_regression
```

未作成出力先を指定。旧結果はvalidation/boot_nut_seat_fe_development_v1。全メッシュと応力変位配列を保存。保存処理の初回は標準Pythonにnumpyがなく停止し、engineering環境で再実行した。解析本体への影響なし。
