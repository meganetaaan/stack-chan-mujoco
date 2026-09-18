# R5-A PPO v3 — Stage 1.5「歩容整形」

v2の `runs/walk_step1/best` を初期値に、0.02 m/sの前進を維持しながら、前後の揺れ・指令の急変・左右の偏り・強い着地を抑える版です。立位からやり直しません。

**A案のMJCF・メッシュ・慣性・サーボ・PDゲイン・トルク上限・61次元観測・10次元action・指令フィルターは変更していません。** モデル一式を同梱。追加ライブラリーはありません。`--task walk` は互換性のためv2のStage 1のままです。今回の学習は必ず `--config configs/walk_refine.json` を指定します。

**実行済み：134件のオフラインテスト合格。未実行：MuJoCo/SB3等を必要とする22件、学習・GUI・ユーザーの既存方策との物理比較。** この環境では依存パッケージ取得先の名前解決に失敗しています。改修による歩容改善を実証した配布物ではありません。`TEST_REPORT_ja.md` を参照。

## 1. 旧フォルダーを残して展開

現在MuJoCoとSB3が動作しているWSLの仮想環境を有効にして実行します。

```bash
cd ~/stack-chan-mujoco
unzip stackchan_r5a_rl_v3.zip
cd stackchan_r5a_rl_v3

python -m unittest discover -s tests -v
python smoke_test.py --subproc
```

未導入の環境では `python -m pip install -r requirements.txt` が必要です。`smoke_test.py` は短い学習・保存・再開・歩行への転送・整形への転送・評価を通す接続試験で、歩行の習得試験ではありません。失敗しても衝突やトルク上限を無効化せず、ログを確認してください。

## 2. 今回歩いた方策から整形を開始

```bash
python train.py --config configs/walk_refine.json \
  --init-from ../stackchan_r5a_rl_v2/runs/walk_step1/best \
  --num-envs 4 \
  --total-timesteps 500000 \
  --run-dir runs/walk_refine
```

**旧 `stand/best` ではなく、前進0.194 mを出した `walk_step1/best` を使用します。最初の切替には `--resume` を使いません。** `--resume` は保存時の報酬設定を維持する操作です。チェックポイントは `model.zip` だけでなく `config.json`, `interface.json`, `metadata.json`, `READY` を含むフォルダー全体が必要です。

方策の行動平均を決めるactorと学習済みlog_stdを引き継ぎます。新報酬用のcriticとoptimizerは新規。探索幅をStage 1の−1.0に戻して歩容を大きく壊すことはしません。学習率は0.00015→0.00005、entropy係数は0.01→0.001、clipは0.2→0.15、target_klは0.03→0.015にします。これらは最初の試行値です。

開始時、転送直後の方策を新しい基準で6回評価し、`initial_evaluation.json` と `initial/`、`best/` へ保存してからPPO更新を始めます。25,000遷移ごとの評価で改善を確認します。**改善がなければ `best/` が開始時の方策のまま残ります。** `final/` は最後の更新結果、`best/` は評価で選ばれた候補で、同一とは限りません。

50万ステップは初回の追加予算です。収束・改善の保証や所要時間の約束ではありません。新しい品質計測は1 kHzで行うため、v2よりCPU負荷が増える可能性があります。

## 3. まずGUIなしで評価

```bash
python evaluate.py --checkpoint runs/walk_refine/best \
  --commands 0.02 --episodes 20 \
  --out outputs/walk_refine_eval.json \
  --trajectories outputs/walk_refine_trajectories

python diagnose_gait.py --evaluation outputs/walk_refine_eval.json \
  --out outputs/walk_refine_diagnosis.json
```

各エピソードの `failed=[...]` に、失敗した条件を直接表示します。`failure_reason=None` は「時間上限まで走った」という状態で、全成功条件の達成とは別です。物理的な歩行条件と整形条件はそれぞれ `success_checks`, `quality_checks` に分け、両方が合格したときだけ `is_success=true` です。

途中経過を `walk_refine_eval.partial.json` に保存し、全試行の完了後に本番JSONを書き出します。`.partial.json` は未完了で、進級・正式な比較には使いません。評価コマンドの終了コード0は処理完了を示し、歩行成功を示すものではありません。

再生は独立したコマンドで行います。

```bash
python play.py --checkpoint runs/walk_refine/best \
  --command 0.02 --episodes 1 --random-reset
```

`evaluate.py` はビューアーもOpenGLコンテキストも作らず、GUIの描画経路から分離しています。`GLXBadDrawable` のドライバー側原因を特定・修復したわけではありません。画面が閉じた際の確認とビューアー属性更新時のlockを加えていますが、GLX問題の解消を保証しません。

以前の `play.py` は既定で同じhome姿勢から3回再生します。提示された `episode=0..2` はその出力形式です。20回の評価が完了したかは、評価JSONと端末の終了状態を確認してください。v3の `evaluate.py` は各回のseedを記録し、既定では初期姿勢に乱れを入れます。

## 4. v2の方策と同じ条件で比較する

旧チェックポイントを**新しいコード・新しい計測条件**で再評価します。保存済みの重み・旧設定は変更しません。

```bash
python evaluate.py \
  --checkpoint ../stackchan_r5a_rl_v2/runs/walk_step1/best \
  --config configs/walk_refine.json \
  --commands 0.02 --episodes 20 --seed 20000 \
  --out outputs/before_refine.json \
  --trajectories outputs/before_refine_trajectories

python evaluate.py --checkpoint runs/walk_refine/best \
  --config configs/walk_refine.json \
  --commands 0.02 --episodes 20 --seed 20000 \
  --out outputs/after_refine.json \
  --trajectories outputs/after_refine_trajectories

python diagnose_gait.py --evaluation outputs/after_refine.json \
  --baseline outputs/before_refine.json \
  --out outputs/refine_comparison.json
```

比較では同じ指令・seed・初期化条件・モデル・報酬・評価条件であることを検査します。単に旧版JSONと新品JSONを並べて、未計測の1 kHzピークを推定しません。20回試行の比較は統計的有意差や実機安全性の認定ではありません。

診断用の初期目安は「平均前進量を旧方策の85%以上かつ80 mm以上に維持」「左右それぞれ平均2回以上の前進着地」「ピッチ角速度RMSを10%以上低減」「指令変化・ピーク荷重が5%超悪化しない」「転倒・異常接触が増えない」です。条件ごとの成否を返し、結果だけで自動進級はしません。

## 5. 何を変えたか

| 項目 | v3の内容 |
|---|---|
| 前進・離床 | v2の速度報酬、前進記録、離床・有効着地・前進着地を保持 |
| ピッチの揺れ | 胴体ローカルY軸の角速度二乗に係数0.20の追加罰則。ロールには追加しない |
| ピッチ姿勢 | ±8°までは追加の角度罰則なし。越えた部分を緩やかに抑制。姿勢固定や補助力はない |
| action変化 | 係数0.01→0.06。さらに二階差分に0.025。出力の意味・slew/PD/遅延はそのまま |
| 左右の偏り | 直近4秒の**前進を伴う着地**の左右差を評価。差1回は許容。過去の偏りは窓から消える |
| 連打 | 同じ足の有効着地が続くと小さな罰則。交互着地ボーナス0.15→0.25 |
| 着地荷重 | 各足の鉛直床反力を機体全重量mgで正規化。2.5倍を越えた部分の二乗を抑制 |
| 接近速度 | 40 ms以上の非支持後の接地で、接触点の下向き接近速度を評価。初期落下・短いチャタリングは除外 |
| bestの選択 | 前進・両脚の有効歩数・接触・姿勢の条件を通った候補で品質を比較。動かなくなった方策を滑らかさだけで選ばない |

ピッチ・荷重の**報酬用の計測は物理刻み1 ms**です。50 Hzの最終フレームだけを見て衝撃や高周波振動を見落とすことを避けるためです。初期落下を除くため最初の0.5秒は品質集計から除外します。CSVは50 Hzで、各区間のRMS/ピークを記録します。1 kHz全生波形のCSVではありません。

MuJoCo `mj_step` が直前に解いた動力学段階の速度・床反力を読みます。積分後のqposとの時刻差は最大1刻み程度あり、連続時間の最大荷重・厳密な着地インパルスではありません。接近速度は接触点の剛体速度 `v + omega × r` を使った代理量です。実材質の柔らかさや実モーターを同定した結果ではありません。

既存の「歩数」判定は互換性のため50 Hzのままです。1 kHz側の `raw_touchdown_counts` は別の診断量で、歩行成功や着地ボーナスの回数には使いません。サーボの最大トルクや摩擦を増やして問題を隠す変更はありません。

## 6. 品質の合格条件とログ

整形ステージの歩行条件は従来の高さ・傾き・自己接触・非足底接触チェックを維持し、前進量を `max(80 mm, 指令距離の50%)`、左右各2回以上の前進着地にします。速度条件も保持します。

追加の品質目安は、ピッチ角速度RMS ≤1.0 rad/s、ピッチの振れ幅 ≤25°、正規化actionの1周期差分RMS ≤0.25、左右前進着地数の差から1を引いた値/総数 ≤0.20、同じ足の連続着地割合 ≤0.25、各足のピーク鉛直荷重 ≤4.0 mgです。例えば5対4は許容、5対2は偏り条件に不合格です。これらは**設計上の初期判定値であり、サーボ定格・機構強度・人に対する安全上限ではありません。**

評価JSONには `pitch_rate_rms_rad_s`, `roll_rate_rms_rad_s`, `body_pitch_peak_to_peak_deg`, `peak_sole_load_bw`, `action_delta_rms`, `target_error_rms_rad`, 既存のトルク・飽和率、`failed_checks` を保存します。TensorBoardは `eval_quality/*`, `eval_failed/*`, `robot_quality/*` を追加しています。

ヘッドバンギングの原因は、現時点では報酬だけとは断定できません。接触時の力、目標追従誤差、トルク飽和が大きければ、制御・機構・接触モデルも原因候補です。今回の変更は、それを計測して切り分けつつ歩容を改善する最初の試行です。

## 7. 中断・再開と次段階

v3の学習を中断した場合はv3の保存物から再開します。

```bash
python train.py --resume runs/walk_refine/interrupted \
  --num-envs 4 --total-timesteps 500000 --run-dir runs/walk_refine
```

`--total-timesteps` は追加の遷移数です。途中のシミュレーター/RNG/rolloutを完全復元するものではありません。

整形が未達のまま速度だけ上げません。20回評価・映像・比較を確認してから、整形報酬を保持する `configs/walk_step2_smooth.json`（0.02〜0.04 m/s）へ移れます。旧 `walk_step2.json` はv2設定のままです。

```bash
python check_stage.py --evaluation outputs/after_refine.json
# 上記の基準・映像を確認した後に実行する次段階
python train.py --config configs/walk_step2_smooth.json \
  --init-from runs/walk_refine/best --num-envs 4 \
  --total-timesteps 2000000 --run-dir runs/walk_step2_smooth
```

負荷測定は `python benchmark.py --config configs/walk_refine.json --num-envs 1 4 6`。頭部形状、可動域、姿勢への補助力は一切変更しません。実機への転送や大きな蹴り出し・走行は今回の対象外です。

## 8. 公式API確認先

MuJoCoの速度はrot:lin順、接触力はcontact frameで返る仕様を確認して実装しています。API確認と実エンジンテストは別です。

- MuJoCo `mj_objectVelocity` / `mj_contactForce`: https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html
- MuJoCo passive viewer: https://mujoco.readthedocs.io/en/stable/python.html
- SB3 PPO: https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html

旧説明は `docs/legacy/v2/`、元設計情報は `docs/R5_source_report.md`、今回のソース差分は `validation/changes_from_v2.patch` に収録しています。
