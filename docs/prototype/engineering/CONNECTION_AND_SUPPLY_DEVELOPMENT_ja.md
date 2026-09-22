# 締結・電源の開発スクリーニング

Issue #17・#18・#22・#24の作業途中。以下だけでは各Issueの完了条件を満たさない。

## 接合候補

元の支持部の背面x=-61.5 mmと背面カバーの内面x=-62.2 mmの間には0.7 mmの隙間がある。
支持部に0.7 mmの一体座を設け、隙間をカバーの曲げで吸収しない形状を作った。
左右それぞれ4本のM3通しボルト、3.4 mmの穴、呼び12 mmの軸長を候補とし、工具の直線アクセス用の包絡も出力した。
呼び形状の頭部は既存背面から3.5 mm突出する。ねじ・座金・ナットの実購入品公差、締付け手順と保持は未確定。
カバーはまだ単なる相手部品であり、背面の構造板や胴体への荷重伝達を検証する必要がある。

`yaw_fasteners.json` にボルト群座標・材料基準・仮定を試験前に保存した。
[Bossardの材料資料](https://www.bossard.com/global-en/-/media/bossard-group/website/documents/technical-resources/en/f-004-en.pdf)のM3・強度区分8.8を参照し、有効断面積5.03 mm²、保証応力580 MPa、安全率2を使用。
剛体・等剛性のボルト群で6成分の力とモーメントを保存し、こじり作用の仮定倍率2を加えた。
軸力の絶対値を引張スクリーニングに用い、樹脂面圧は厚さ3 mmで計算した。これは接触・こじり・締付け保持の証明ではない。

片脚34条件と全身左右2条件から左右計266,000時刻を評価した結果、ボルト相当応力は最大7.603 MPa（基準290 MPa）、樹脂面圧は最大1.599 MPa（仮定基準5.6 MPa）。
ボルトそのものの静的強度より、支持壁・相手部品・締付け保持の確認が次の課題になる。

```sh
.venv-engineering/bin/python software/sim/structural/check_bolt_group.py --out outputs/bolt_group_new
.venv-engineering/bin/python software/sim/structural/build_yaw_connection.py --out outputs/yaw_connection_new
```

## 電源の初期モデル

`run_supply_probe.py` はEPIC #4の12軸合計電流をngspiceへ渡す。
7.4 V電池、内部抵抗0.1 Ω、変換効率85%、等価出力インピーダンス、1,000 µF出力容量、配線抵抗、3 Wの制御機器負荷を仮定した。
実部品の内部回路を同定したモデルではない。電池・保護部品・Tab5負荷の確定や公差掃引も未完了。
変換器の入力電流に出力源の電力と変換損失を反映し、電池・配線・容量・インダクタのエネルギー収支を検査する。

既存負荷の解析では動作電圧4.964〜5.004 V、エネルギー収支の相対誤差約7.3×10⁻⁷だった。
別の故障注入では、負荷を除去して1 Aを20 ms回生側へ流し、回生を吸収できないモデルの過電圧を確認した。
最大25.88 Vという結果は規定電流源による故障注入の値であり、実モーターがその電圧まで1 Aを供給し続けるという予測ではない。
この試験の電圧ゲートは不合格のまま保存した。回生吸収・過電圧遮断・実際のエネルギー上限は次段階で設計する。

```sh
.venv-engineering/bin/python software/sim/circuits/run_supply_probe.py --out outputs/supply_probe_new
.venv-engineering/bin/python software/sim/circuits/run_supply_probe.py --regeneration-test --out outputs/supply_regeneration_new
```

再現環境は [ENVIRONMENT_ja.md](ENVIRONMENT_ja.md)。機構記録は `validation/yaw_connection_development_v1/`、電源記録は `validation/supply_development_v1/`。
生のngspice列は `trace.dat.gz` に圧縮保存している。np.loadtxtで再読込みできる。
