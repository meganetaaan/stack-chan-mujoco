# 補強質量での旋回横移動量比較

軽量背面板・軽量ヨー支持部の質量感度モデルを用い、支持足から胴体重心目標までの横方向距離（inset）を比較した。既定25.5 mm、今回25.0/25.8/25.95 mm。初期・定常値を同じ値に設定する。値を増やすと重心目標を支持足から内側へ寄せる。

事前基準: 7秒継続、失敗なし、旋回90±1度、全記録中の関節限界まで0.005 rad以上。時間短縮の受入試験ではない。物理関節範囲・電流制限・モータモデルを変更していない。

|inset mm|停止時刻 s|旋回 deg|停止原因|
|---|---:|---:|---|
|25.0|2.777|22.511|右足首ロール下限|
|25.8|4.360|83.404|右足首ロール下限|
|25.95|4.383|85.625|右足首ロール下限|

全条件不成立。波形は有限値である。既定値を変更せず、試験引数としてのみ追加した。参照生成器が許す範囲[20,26) mmでの比較であり、範囲を広げて合格にしていない。

再現はlight_yaw_support_development_v1の手順でoutputs/light_plate_support_mass_v1を生成後、各値に対して:

```sh
.venv-engineering/bin/python software/sim/actuator/run_probe.py \
 --model outputs/light_plate_support_mass_v1 --out outputs/inset_25_8_repeat \
 --turn-inset-mm 25.8 --sign 1
.venv-engineering/bin/python software/sim/actuator/diagnose_limit_trace.py \
 --source outputs/inset_25_8_repeat --model outputs/light_plate_support_mass_v1 \
 --out outputs/inset_25_8_repeat/limit_diagnosis.json
```

summary.jsonは各report.jsonの終了理由・時刻・旋回角・最大電流と、limit_diagnosis.jsonの全関節最小余裕・有限値判定を集約したもの。成功条件は上記4条件すべての成立と有限値で判定する。元の衝突形状を使用した質量感度試験であり、実機・候補CADの干渉・前後進・90度3秒未満を保証しない。

次の検討は足首可動範囲の機構上の余裕と追従偏差。CAD検証なしに関節限界を拡大しない。
