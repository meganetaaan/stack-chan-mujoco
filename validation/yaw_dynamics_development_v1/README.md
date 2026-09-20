# 12軸候補の実MuJoCo開発診断

全条件で失敗しており、前進・旋回・動作切替の合格実績ではない。正式な固定20/20・ランダム化18/20評価は未実施。評価基準を緩和していない。

`assets/r7_yaw_candidate_v1` は股関節ヨー2軸を追加した別モデル。全12軸はトルク駆動で、浮遊ベースに補助力・姿勢拘束・重力補償はない。従来のトルク・速度制限、遅延、40 msフィルタ、関節制限、転倒・非足裏接触・自己衝突判定、飽和保護を使用する。動作中に1秒以上有効着地がない場合も停止する。

今回のヨー指令は両方ゼロ。関節を固定したのではなく、有限のモータトルクでゼロへ追従させる。12軸化で質量・支持構造が変わったときの前進基礎動作を調べた。制御器は参照姿勢＋静的トルク補償で、学習済み方策の補正は使っていない。

| ケース | 停止時刻 s | X移動 m | 左右有効着地 | 停止理由 |
|---|---:|---:|---|---|
| legacy_transfer | 3.243 | 0.2385 | [2, 1] | walking_interrupted |
| recomputed | 2.809 | 0.1631 | [2, 2] | self_collision |
| height2 | 3.272 | 0.1214 | [1, 2] | continuous_saturation |

- legacy_transfer: 旧10軸参照を使用し、静的トルクだけ総質量比で補正。着地中断で失敗。
- recomputed: 新質量・重心で参照姿勢と静的トルクを再計算。右股関節ロールモータと右膝モータが約0.00584 mm侵入し、自己衝突で失敗。
- height2: 再計算時に姿勢高さを2 mm上げた。右足首ピッチの連続飽和が0.25秒に達して保護停止。胴体や脚部品の寸法を伸ばしたものではない。

再計算では、ヨー角ゼロのときだけヨーリンクの質量・慣性を胴体へ合算して旧5軸脚のCOM計算を使う。これは参照計算の等価化で、実MuJoCo内のヨー自由度・質量・慣性を消す処理ではない。元の12軸の質量と一致することを検査する。

## モデルの変更と限界

総質量は0.924558434879 kg。追加モータケース、内部の固定支持棚・支柱、回転側カップリング、切り詰めた旧ブラケット、ヨー軸を避けるトレイ支持リブをCADで定義し、質量・慣性を再集計した。バッテリー位置・外形・脚長・足形状を維持し、TTL基板は上方12 mmへ仮移設した。

モータケースは18 gの一様分布近似。固定支持・回転カップリングは試験用の形状で、メーカー出力軸位置・ホーン・ねじ・実軸受の適合を確認した製作データではない。剛体支持を仮定し、強度・たわみは未検証。初期姿勢の衝突がないことは、全可動域のCAD干渉や組立可能性の証明ではない。

初期版では回転支持がトレイ支持リブを貫通していた。公開候補では実際のリブ形状を軸の外側へ迂回させて衝突形状・慣性を更新した。衝突除外を追加せず、既存の親子リンク間衝突を有効にする設定を維持した。

## 再現

CADの元データは `docs/REPRODUCE_MOUNTED_ja.md` に沿って生成する。未使用の出力先を指定する。

```sh
.venv-cad/bin/python build_yaw_dynamics_candidate.py --cad-design outputs/design_r6_base_collisions --out outputs/new_yaw_candidate
python generate_yaw_zero_reference.py --cad-design outputs/design_r6_base_collisions --design outputs/new_yaw_candidate --out outputs/new_yaw_reference
python probe_yaw_dynamics_candidate.py --design outputs/new_yaw_candidate --reference outputs/new_yaw_reference/reference.json.gz --static-torque-scale 1 --duration 7.48 --out outputs/new_yaw_trial
python -m unittest tests.test_yaw_dynamics_candidate tests.test_yaw_kinematics -v
```

height2は参照生成へ `--height-offset-mm 2` を追加。legacy_transferはprobeの `--reference` と `--static-torque-scale` を省略し、durationは既定の6秒。

モデルの質量収支、旧リンクのゼロ角座標・モータ上限の保持、joint_mapとMJCFの整合性、初期自己衝突、親子接触の有効化、12チャンネルの飽和保護、6軸運動学を計8テストで確認した。各診断は実積分状態・ターゲット・トルク・失敗時接触・ソースハッシュを保存している。
