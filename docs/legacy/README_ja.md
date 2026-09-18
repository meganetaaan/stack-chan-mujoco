# R5-A ｽﾀｯｸﾁｬﾝ — CPU MuJoCo / Gymnasium / SB3 PPO 学習キット

対象は **A案（横置きTab5・128 × 128 × 128 mmの立方体ボディ）**です。10軸のMJCF、メッシュ、質量・慣性、サーボ仕様を同梱しており、以前のZIPからファイルを移す必要はありません。CadQuery、ROS、CUDAはこのスクリプトの実行要件ではありません。

**配布時点で学習済み方策は含んでいません。** 作成環境ではNumPyベースの40テストが合格しましたが、MuJoCo / Gymnasium / Stable Baselines3の取得がネットワーク障害で失敗しました。実エンジンを必要とする9テスト、PPO学習、GUI再生は未実行です。APIの照合と物理エンジンを使わないテストは、物理実行・学習成功を保証しません。`TEST_REPORT_ja.md` に実行記録を収録しています。

## 1. WSL2で配置・インストール

現在MuJoCoが動いている仮想環境を使います。以下はZIPを `~/stackchan-mujoco` にコピーした場合です。

```bash
cd ~/stackchan-mujoco
unzip stackchan_r5a_rl.zip
cd stackchan_r5a_rl
source ../.venv/bin/activate
python -m pip install -r requirements.txt
```

仮想環境が別の場所にある場合は、その環境を有効にしてください。Python 3.11 / 3.12を想定したコードです。作成環境での構文・オフラインテストはPython 3.13.5で行いました。`requirements.txt` は互換範囲であり、実行確認済みのロックファイルではありません。SB3とGymnasiumに加えMuJoCo・NumPy・TensorBoardを導入します。PyTorchはSB3の依存として入ります。

以下のコマンドは、原則としてこのREADMEのあるフォルダーで実行します。学習はCPUを明示指定しているため、AMD GPUへの学習ライブラリーの設定は不要です。

## 2. 最初に実行するチェック

```bash
python check_env.py
python -m unittest discover -s tests -v
python smoke_test.py --subproc
```

`check_env.py` は、A案のコンパイル、名前に基づく関節・アクチュエーター対応、乱数seed再現性、SB3の環境契約、表示あり／なしモデルの物理量の同一性を確認します。続いてゼロaction（home姿勢を目指すPD制御）を試し、何秒生存したかと終了理由を出力します。

`PASS_ENVIRONMENT` はソフトウェアの接続が通った意味です。**ゼロactionで立てたことや、学習済み方策の成功と同じ意味ではありません。** PDの結果は `outputs/preflight.json` の `pd_baseline` に別記します。初期姿勢の深い自己干渉やXMLの不整合はエラーにして止めます。エラーを無視して学習しないでください。

`smoke_test.py --subproc` は2プロセスで、短いPPO学習 → 保存・評価 → 再開 → 歩行設定への重み転送までを通します。数百ステップの接続テストであり、歩行を獲得するための学習ではありません。結果と各段階のログは `runs/smoke_日時/` に保存します。

テスト出力に `skipped` がある場合、その項目は合格ではなく未実行です。

## 3. 立位方策を学習

```bash
python train.py --task stand \
  --num-envs 4 \
  --total-timesteps 1000000 \
  --run-dir runs/stand
```

初期設定は4環境のCPU並列実行です。1エピソードは10秒、方策は50 Hz、物理計算とPD制御は1 kHzです。home姿勢を基準に、初期傾き約±2°、小さな関節角・速度の乱れから始めます。

ここでの「立位学習」は、立った状態の近くから姿勢を維持・修正するタスクです。**床に倒れた状態からの起き上がり学習ではありません。** 胴体の固定、空中支持、外力による姿勢矯正、軌道への強制移動は入れていません。

100万は最初の試行予算であり、収束に十分な回数という保証ではありません。値は全並列環境を合計した遷移数で、PPOのロールアウト単位に切り上がる場合があります。一定時間での学習成功や、実機での成功は保証しません。

5万遷移ごとに学習とは別seedで評価します。成功率、生存時間、報酬の順に比較して `best/` を保存します。**`best` があること自体は成功を意味しません。** すべて失敗している場合にも、その時点での最良候補を保存します。

## 4. GUI再生と、別seedでの定量評価

```bash
python play.py --checkpoint runs/stand/best --random-reset

python evaluate.py --checkpoint runs/stand/best --episodes 20 \
  --out outputs/stand_eval.json \
  --trajectories outputs/stand_trajectories
```

GUIでは実際にMuJoCoを積分して方策を実行します。目標姿勢を描くだけの旧HTMLビューアーとは異なるコード経路です。`--random-reset` を省略すると、まずhomeからの再生になります。`--speed 0.5` は表示速度だけを落とし、物理の時間刻みは変更しません。`--headless` では画面を出しません。

評価は重み選択にも使っていないseedをデフォルトで使用します。立位の合格は、10秒を完走し、転倒・足底以外の床接触・自己接触がなく、高さ、傾き、位置ずれ、両足支持率を満たすことです。報酬だけでなく `success_checks` の各項目を確認できます。

`evaluate.py` の終了コード0は評価処理が完了した意味です。ロボットの成功率はJSON中の `success_rate` で別途確認します。

## 5. 立位の重みを引き継いで歩行を学習

立位の定量評価とGUIを確認してから実行します。

```bash
python train.py --task walk \
  --init-from runs/stand/best \
  --num-envs 4 \
  --total-timesteps 3000000 \
  --run-dir runs/walk

python play.py --checkpoint runs/walk/best --command 0.04

python evaluate.py --checkpoint runs/walk/best \
  --commands 0,0.02,0.04,0.06 --episodes 20 \
  --out outputs/walk_eval.json \
  --trajectories outputs/walk_trajectories
```

歩行設定は前進指令0.02～0.06 m/sと、20%の確率の停止指令を使います。12秒エピソードで、指令は開始後0.5秒待ち、1秒かけて滑らかに立ち上げます。左右交互の離床・接地を探索しやすくする弱い位相報酬を加えていますが、関節の正解軌道は与えていません。

立位と歩行は **61次元の観測、10次元のaction、actionの意味・スケールを共通化**しています。歩行に移るときに観測次元を後付けで変えません。`--init-from` はactorとcriticの重みを引き継ぎ、新しいタスクのoptimizerで学習します。

歩行評価では、実際の前進量・速度誤差・姿勢に加え、十分な離床時間と高さを持つ左右の着地を数えます。足を滑らせるだけ、初期落下、接触の細かなチャタリング、両足同時の跳躍だけでは歩行合格にならないようにしています。これは設計した評価基準であり、どんな不自然な解も排除できる保証ではありません。数値と映像を両方見てください。

この設定は最初の低速歩行用です。走行・大きな蹴り出し・転倒復帰を学習する設定ではありません。特に飛行時間への罰則があるので、走行には別のタスク設計が必要です。

## 6. 中断と再開

Ctrl+Cで `interrupted/` に保存します。定期保存は `latest/` と `checkpoints/step_.../`、正常終了時には `final/` にも保存します。

```bash
python train.py --resume runs/stand/interrupted \
  --num-envs 4 \
  --total-timesteps 1000000 \
  --run-dir runs/stand
```

`--total-timesteps` は再開時も **追加** する遷移数です。`--resume` は重みとoptimizerを読み込みますが、物理状態、途中のロールアウト、プロセス乱数状態を完全復元するものではありません。エピソードはリセットして再開するので、ビット単位で完全連続した学習ではありません。

`--resume` と `--task/--config` は併用できません。タスク・報酬を変えるときは、別のrun-dirと `--init-from` を使います。保存単位は **フォルダー全体** です。`model.zip` だけを移動せず、`config.json`, `interface.json`, `metadata.json`, `READY` も保持してください。モデル内容・関節順序・制御スケールの不一致は読み込み時に拒否します。

## 7. ログと負荷調整

```bash
tensorboard --logdir runs --host 127.0.0.1 --port 6006
```

ブラウザーで `http://localhost:6006` を開きます。`eval/success_rate`、`eval/mean_duration_s`、`robot/max_tilt_deg`、各報酬成分を確認できます。TensorBoardを不要とする場合は学習コマンドに `--no-tensorboard` を付けます。

```bash
python benchmark.py --num-envs 1 4 6 --vector-steps 300
```

上記はこのモデルでの実測遷移数/秒を比較するベンチマークです。並列数を増やして速くなるとは限りません。出力される所要時間は物理環境の測定に基づく概算で、PPO更新・評価・ファイル保存時間を含みません。

`--num-envs 1 --vec dummy` で単一プロセスの問題切り分けができます。GUIは `play.py` だけで使用し、学習ワーカーにはOpenGLコンテキストを作りません。各プロセスの数値計算スレッド数を1に抑え、多重並列による競合を避けています。

## 8. 動画と推論モデルの書き出し

```bash
python -m pip install -r requirements-video.txt
python play.py --checkpoint runs/walk/best --command 0.04 \
  --episodes 1 --record outputs/walk.mp4

python export_policy.py --checkpoint runs/walk/best --out outputs/actor
```

動画には実際のMuJoCo描画環境が必要です。`export_policy.py` はTorchScriptのactorとI/O仕様を出力し、SB3の決定論的出力との一致を確認します。ONNX、実機通信、実機安全制御はこのキットの対象ではありません。観測にはシミュレーターからしか得られない速度・高さ・接触情報を含むので、そのまま実機へ転送しないでください。

## 9. 含まれるファイル

| ファイル | 用途 |
|---|---|
| `train.py` | PPO学習、並列化、評価、保存、再開、タスク間転送 |
| `check_env.py` | 実MJCFのコンパイル、SB3契約、home-PDの診断 |
| `smoke_test.py` | 学習 → 保存 → 読込み → 再開 → 歩行への転送の接続テスト |
| `evaluate.py` | 別seed・複数速度で定量評価、JSONと軌跡CSV |
| `play.py` | MuJoCo GUI再生、低速表示、動画、headless再生 |
| `benchmark.py` | CPU並列数ごとの環境処理速度 |
| `export_policy.py` | TorchScript actorとI/O契約の書出し |
| `stackchan_rl/` | Gymnasium環境、サーボ近似、報酬、評価基準、保存処理 |
| `configs/` | 立位、低速歩行、ロバスト立位、接続試験用のJSON |
| `assets/r5a/` | A案の元MJCF・メッシュ・サーボ情報・由来とハッシュ |
| `tests/` | 物理エンジン不要のテストと実MuJoCo/SB3テスト |
| `validation/` | 配布前に実行できた検査と、実行できなかった検査の記録 |
| `docs/DESIGN_ja.md` | 観測・出力・報酬・終了条件・制御仕様 |

## 10. 機械・モデルについて残る制限

A案の元データは変えていません。約826 gは仮定を含むモデル質量です。元モデルの関節範囲、質量・慣性、トルク上限、摩擦・接触代理形状を保持します。headlessモードでは表示専用メッシュだけを除去します。

元レポートで両脚を外向きに約6.5°ずつ開いた特定姿勢に腿の干渉があります。今回の目標角度に `left_hip_roll - right_hip_roll <= 10°`（対称なら各5°）という探索ガードを加えました。共通方向への股ロールはそのまま使えます。ただし、これは限られた既存検査を受けた保守的な探索制約で、他の関節角との全組合せや連続掃引の非干渉を保証しません。MJCFの物理ストッパーを架空に増設したものでもありません。

サーボ上限は元設計のシミュレーション用の仮定を使います。ストールトルクを連続定格としては使わず、XMLの上限より強い仮想モーターへ変更していません。電源電圧降下、温度、バックラッシュ、実モーターの同定、ブーツの変形は未再現です。衝突形状はCADそのものではなく、元MJCFの箱等の代理形状です。隣接剛体の衝突フィルターも元データを継承しています。

環境の接触・成功判定は方策周期50 Hzで標本化します。毎物理ステップのサーボピークトルクは記録しますが、全ての短時間接触イベントや連続掃引を捕捉する保証はありません。初回のRLではこのモデルを利用しますが、成功した方策について別途高分解能の接触・CAD検査が必要です。

## 11. よくある診断

| 症状 | このキットでの扱い |
|---|---|
| `ModuleNotFoundError` | 仮想環境と `python -m pip install -r requirements.txt` を確認。`python -m pip` と実行Pythonを揃える |
| `Reset has >0.5 mm self-penetration` | エラー内のgeom名と `outputs/preflight.json` を確認。衝突を一括無効化して学習を続けない |
| `PASS_ENVIRONMENT` だがPDは転ぶ | 環境契約と固定目標PDの成績は別。学習後の評価と比較するためのbaseline |
| 起動直後に全エピソード終了 | `failure_reason` を確認。自己接触・非足底接触・数値警告は単なる報酬調整では解決しない場合がある |
| 報酬だけ伸びて足を滑らせる | `valid_landings`, `success_checks`, 軌跡CSV、GUIを確認する。歩行成功としない |
| `EOFError` / worker起動エラー | `--num-envs 1 --vec dummy` と `check_env.py` で元の例外を確認する |
| GUIだけ失敗する | 学習はheadless。既に動作したWSLg側で `python -m mujoco.viewer` と同じ仮想環境・端末を使う |
| `interface mismatch` | A/B違い、元XML変更、actionスケール変更など。互換でないpolicyを黙って読み込ませない |
| `run-dir ... is not empty` | 新しいrun-dirを使うか、保存済みチェックポイントから明示的に再開する |

公式APIの照合先は `docs/DESIGN_ja.md` の末尾に記載しています。
