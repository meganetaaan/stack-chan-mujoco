# R6 残差強化学習

現行外形と103 gの電池予約を含む0.855284 kgのモデルを使用する。
この段階はシミュレーション。電池・降圧回路の電気的適合と実機試験は未確認。
機構と電源の詳細は [REAR_BRIDGE_ja.md](REAR_BRIDGE_ja.md)、[POWER_ja.md](POWER_ja.md)。

## 初回の結果

同一の学習済み方策で、**固定条件20/20、ランダム化条件12/20**。
目標のランダム化18/20には届いていない。全40試行の実状態・観測・行動、失敗理由、
照合結果と再生動画を `validation/r6_residual_seed20260920` に公開する。
固定条件の10 m通過は約94.129秒。停止を含む109.5秒まで評価した。

ランダム化条件の失敗は関節限界2件、自己衝突1件、前進距離／到達時間不足5件。
後者では方角が約45–88度ずれた。初回観測には方角・横位置がなく、改善が必要。
30秒エピソードでの追加学習と、ノイズ付き外部方角・横位置観測を持つ次版を開発中。
この外部基準はIMUだけで実現する姿勢推定ではなく、実機に移す際の明示的な追加要件となる。

## 方策の構成

PPOが10軸の目標角補正を出力する。各軸の補正上限は±0.02 rad。
先行検証したCOM/IK歩容と静的トルク補償を事前知識として使い、その上の補正を学習する。
ゼロから歩容全体を発見した学習ではない。補正なし参照と学習済み方策は別に評価する。
初回学習は seed 20260920、32,768ステップ、4環境、12秒エピソード。
PPOの初期・学習済み重み、実行設定、全エピソードのMonitorログを `policies/r6_residual_seed20260920` に保存。

IMUはノイズ付き重力方向と角速度。速度・関節状態等は理想状態推定を仮定する。
方策は65次元観測を受け取り、位相・参照関節角・前回行動も観測する。
モデルの物理制約を外して学習しない。サーボはトルク・速度包絡、指令遅延、スルー・LPFを通す。
無負荷回転速度は駆動時のトルク包絡に使い、外力による逆駆動を不自然に遮断しない。
質量・重心・摩擦・トルク・速度・遅延・ノイズの範囲は設定JSONと
[GOAL_PROTOCOL_ja.md](GOAL_PROTOCOL_ja.md) に明記する。範囲は実機未同定。

## 再現

学習環境の実測バージョンは `runtime.json`。Python 3.14.7、MuJoCo 3.13.0、
Gymnasium 1.3.0、SB3 2.9.0、PyTorch 2.14.0、NumPy 2.5.3、CPUで実行した。
依存関係の直接指定は `design/requirements-r6-rl.txt`。完全な推移依存ロックではない。
OS・CPU・数値ライブラリ差による学習結果の差を避けるため、評価には公開済み方策を使う。

凍結したモデルを実行設定のパスへ配置する（既存出力を上書きしない）:

```bash
mkdir -p outputs
test ! -e outputs/design_r6_rear_bridge8_collision && \
  cp -a assets/r6_rear_bridge8_collision outputs/design_r6_rear_bridge8_collision
```

モデルから再生成する場合は `docs/REAR_BRIDGE_ja.md` のコマンドとCAD依存ロックを使う。
再生成結果は `assets/r6_rear_bridge8_collision/FROZEN_FILES.json` と照合する。
学習を再実行する:

```bash
python train_residual.py --config configs/r6/residual.json --out runs/r6_reproduction
```

学習済み方策の評価例:

```bash
python evaluate_residual.py --checkpoint policies/r6_residual_seed20260920 \
  --domain fixed --episodes 20 --seed 87000 --purpose acceptance \
  --out outputs/reproduce_fixed
python evaluate_residual.py --checkpoint policies/r6_residual_seed20260920 \
  --domain randomized --episodes 20 --seed 88000 --purpose acceptance \
  --out outputs/reproduce_randomized
```

全20件が終了するまで `manifest.json` の `complete` はfalse。
途中経過・短距離評価・未学習方策は受入成功に数えない。
既存結果を上書きせず、各試行に実現したプラント値・シード・停止理由・ハッシュを残す。

## 実状態の再生

`states.npz` は方策周期20 msごとのMuJoCo `mjSTATE_INTEGRATION` と最後の物理刻みの実状態、
観測・行動・最終サブステップトルクを含む。時刻・自由基底の位置姿勢・関節・速度・制御値等を保存する。
動画はこの実状態を `mj_setState` で復元し、参照軌跡による置換や姿勢補間をしない。
カメラのみが胴体を追う。保護・衝突監視と初回10 m通過は1 msごとの判定で、動画の50 fpsに依存しない。

```bash
MUJOCO_GL=egl python replay_residual.py --batch outputs/reproduce_fixed \
  --trial trial_00 --out outputs/reproduce_fixed_trial00.mp4
```

ffmpegが必要。動画と元状態・レポートのハッシュを同名JSONに保存する。
失敗が方策周期の途中なら、動画終端の時刻だけ最大20 ms未満の量子化が生じる。
合否の計時は記録されたシミュレータ時刻を使用する。

## 限界

飽和保護はシミュレーション上の仮定であり、電流・熱・電源・通信を同定した保護ではない。
接触形状にはCADとの近似と未モデル化部品が残る。成功が得られても実機受入の代替にはならない。
学習に使っていない乱数での20件の観測結果は、未知条件での成功率の統計的保証ではない。

## 方角観測を追加した版（固定20/20・ランダム化14/20）

`configs/r6/heading_residual.json` / `stackchan_rl/residual_heading.py` は70次元の別インターフェース。
外部基準による方角のsin/cos、横位置、世界座標の平面速度を追加する。
方角ノイズ標準偏差0.002–0.01 rad、横位置0.001–0.003 mを試行ごとに抽選。
固定条件では0.005 rad、0.002 m。これはIMU単独の積分ではなく、外部基準付き推定を仮定する。
実機実装では、その推定を実現するセンサー・遅延・欠測を改めて同定する必要がある。

物理・アクチュエータ・保護判定は旧版と同じ。ゼロ行動での状態一致をテストした。
報酬には方角・横ずれのペナルティを追加する。旧方策を初期値とする際には新しい入力列を0にして、
初期のactor出力とcritic値を保つことをテストした。最適化器は新しく作る。

```bash
python continue_residual.py --checkpoint policies/r6_residual_seed20260920   --out runs/r6_residual_seed20260921 --seed 20260921
python train_heading_residual.py --parent runs/r6_residual_seed20260921   --out runs/r6_heading_seed20260922
```

追加学習の結果を旧方策の20/20・12/20に混ぜない。
次の評価シードは `configs/r6/next_evaluation_seeds.json` に事前固定している。

両バッチを事前固定シードから実行するには、学習完了後に以下を使う。

```bash
python run_planned_r6_evaluation.py --checkpoint runs/r6_heading_seed20260922 \
  --out outputs/r6_heading_acceptance
```

方角観測版の初回学習では、親方策の `PPO.load` もグローバル乱数状態を再初期化する。
環境シード20260922–20260925と親方策に保存されたseed値20260920、および読み込み順を含めて再現する。
親方策の追加学習では20260921を明示設定したが、SB3の `set_random_seed` は保存属性 `seed` 自体を書き換えない。
単一の手動seed設定だけに置き換えない。実行ディレクトリの `rng_sequence_audit.json` に順序を記録した。

## 旋回応答を使った初期化とPPO（評価中）

`validation/yaw_authority` で左右膝目標差の旋回応答を確認した。
この応答を使う教師関数を記録済み観測上でニューラルactorへ近似し、
criticは新しく初期化してからPPOで追加学習する。実行時の解析的な旋回制御追加はない。
教師への関数近似の精度と、実際の歩行受入は別々に扱う。

```bash
python train_steering_initialized.py --parent policies/r6_heading_seed20260922 \
  --dataset validation/r6_heading_seed20260922 --out runs/r6_steering_seed20260923
python run_planned_r6_evaluation.py --checkpoint policies/r6_steering_seed20260923 \
  --seed-plan configs/r6/steering_evaluation_seeds.json --out outputs/r6_steering_acceptance
```

この候補は `assets/r6_base_collisions` の追加形状を含む。教師関数の初期化は8,000更新、
実MuJoCo上のPPOは32,768ステップ。親の読み込み後に新しい学習器をseed 20260923で生成する。
凍結済みの候補、初期値、全設定、データのハッシュを `policies/r6_steering_seed20260923` に保存する。

## 旋回初期化＋PPO版の確定評価

`validation/r6_steering_seed20260923` に全40試行と独立記録監査を保存。固定107000–107019、ランダム化108000–108019とも20/20。全試行で100秒以内に10 mを通過し、109.5秒まで物理的失敗なし。これは `assets/r6_base_collisions` と公開設定の仮定モデルに限る。5,475行動の再計算誤差は最大3.28e-7、初期方策からの行動変化RMSは0.010087。固定具追加後の再評価、電源同定、実機評価は未実施。

最新合格方策の固定・ランダム化試行00の全実状態再生動画を `validation/r6_steering_seed20260923/videos` に保存。各5,476フレーム、50 fps、実状態時刻0～109.5秒。動画ハッシュとフレーム数を検査済み。ロボットの補間や合成動作は使わない。
