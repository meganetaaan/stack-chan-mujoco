# ジンバル・軸受外周の衝突モデル追加

従来のモデルでは、CADで分かっていた腿／ジンバルと脛／ジンバルの干渉を検出できなかった。
ジンバルの衝突形状が欠け、腿と脛の軸受外周も簡略形状に含まれていなかったためである。
この追加モデルはその既知の見逃しを修正する。ロボット全体の衝突形状が完成したという意味ではない。

## 生成方法と形状の近似

`add_gimbal_collisions.py` は生成済みCADのジンバル輪郭を読み、側板を三角柱へ分割する。
軸穴は塞がず、円環を24個の凸な柱に分割。左右各ジンバルは側板・円環・梁の計62形状となる。
CADと生成形状のB-rep差分では未被覆体積0、余分な体積は片側約8.450 mm³。
円環外側は外接多角形、内側は内接多角形を使い、半径方向の張り出しは最大約0.091 mm。

腿と脛の軸受外周も各24分割の円環を追加する。左右の4部品に計384形状を追加。
中央の軸穴を残すが、小さい締結穴は保守的に埋めている。この4部品全体の被覆保証ではない。
ジンバルと合わせて508個の凸形状を追加し、親子リンクの接触フィルタを無効化する。
同一剛体内の部品同士は引き続き物理エンジンの接触対象外なので、CAD検査を併用する。

MJCFだけを更新する実験用パッチ。CAD・外形・質量・慣性・関節・電池位置を変更しない。
URDFの衝突形状にはまだ反映していない。既存の設計出力を上書きせず別ディレクトリに生成する。

## 確認結果

既存の0.52 m試験の関節角を静的に再生した。床接触を除外するため基底を上方へ移すが、
内部の相対位置は変わらない。この再生は動力学試験ではない。

- 比較用5姿勢（CSVデータ行0、50、100、200、300）は変更前後とも接触なし。
- CADで干渉した2姿勢（行315、320）は従来モデルで検出なし。
  追加後は腿／ジンバルと脛／ジンバルの両方を検出する。
- 質量、慣性、慣性座標、関節位置・軸・範囲、摩擦・減衰・アーマチュア、アクチュエータ制限、
  初期関節姿勢をコンパイル後の配列で比較し、変更なし。38個の表示STLもバイト単位で一致。
- 同じ20ステップの動力学試験は6.220秒・523.153 mmで腿／ジンバルの接触停止となった。
  以前は同じ条件を6.5秒まで停止せず完了していたため、見逃しに基づく合格扱いを防げる。

停止時の実CAD距離は約0.019 mm、重なり0 mm³。円環の最大約0.091 mmの張り出し範囲内にあり、
物理形状の接触より前に保守的な衝突形状が当たったと解釈できる。
CADで実際に重なる行315/320の検出とは区別する。
この程度の隙間で実機の公差・たわみ・制御誤差まで安全とは言えないため、
衝突判定を弱めず、終了動作と腿・脛・ジンバル間の必要な隙間を設計する。

検査データは `validation/gimbal_collision/`。
固定クレードルと電池・回路等の予約部品には衝突形状がまだなく、その他の形状も部分的に簡略化されている。
全歩行範囲のCAD検査、形状被覆、実機10 m歩行は未完了。

## 再現

`design/leg_relief/README_ja.md` に従って元候補を生成する。出力ディレクトリは未作成にする。

```bash
.venv-cad/bin/python add_gimbal_collisions.py \
  --design outputs/design_r6_leg_collar_relief --out outputs/design_r6_gimbal_bearing_collision
.venv-dynamics/bin/python replay_self_contacts.py \
  --design outputs/design_r6_gimbal_bearing_collision \
  --trajectory validation/com_reference/com_long_inset25/trajectory.csv \
  --rows 0 50 100 200 300 315 320 --out outputs/patched_replay.json
.venv-dynamics/bin/python replay_self_contacts.py \
  --design outputs/design_r6_leg_collar_relief \
  --trajectory validation/com_reference/com_long_inset25/trajectory.csv \
  --rows 0 50 100 200 300 315 320 --out outputs/baseline_replay.json
.venv-dynamics/bin/python validation/verify_collision_patch.py \
  --baseline outputs/design_r6_leg_collar_relief --candidate outputs/design_r6_gimbal_bearing_collision \
  --baseline-replay outputs/baseline_replay.json --candidate-replay outputs/patched_replay.json \
  --out outputs/collision_regression.json
.venv-dynamics/bin/python probe_reference_gait.py \
  --design outputs/design_r6_gimbal_bearing_collision --speed .1 --step-period .25 \
  --height-offset-mm -2 --com-forward-offset-mm -3 --com-inset-mm 25 \
  --static-compensation --slew 6 --steps 20 --out outputs/collision_gait_probe
```

診断コマンドの終了コード0は記録完了を表す。歩行成功の判定ではない。
ヘッドレス診断は衝突に使うメッシュを保持し、表示専用メッシュだけを除去するよう修正した。
