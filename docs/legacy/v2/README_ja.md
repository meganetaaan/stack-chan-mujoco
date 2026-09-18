# R5-A PPO学習キット v2 — 停止方策から、離床・前進を探索する版

対象はA案（横置きTab5、128 × 128 × 128 mmのボディ）です。**MJCF、形状、質量・慣性、サーボ上限、61次元の観測、10次元actionの意味・スケールは変更していません。** 同じ仮想環境で実行できます。モデルとメッシュを同梱しています。

今回の変更は学習目的、接地イベントの判定・診断、重みの引き継ぎ、best選択です。**学習済み方策は同梱していません。改修版で歩けると実証したものではありません。** 作成環境で実行できたテストと未実行項目は `TEST_REPORT_ja.md` に区別して記録しています。

`12秒完走 / forward=-0.005 / landings=[0,0]` は「成功」ではなく、検証済みの歩数がゼロという結果です。接地判定のしきい値未満の動きなどもあり得るので、ログだけから足を全く浮かせていない、立位が完全に習得済み、報酬だけが原因、とは断定しません。

## 1. 旧学習結果を残して配置

ZIPをWSLの `~/stack-chan-mujoco` へコピーした場合です。MuJoCoとSB3が動いている仮想環境を有効にした状態で実行します。

```bash
cd ~/stack-chan-mujoco
unzip stackchan_r5a_rl_v2.zip
cd stackchan_r5a_rl_v2

# 追加の学習ライブラリーはありません。未導入の場合だけ実行します。
python -m pip install -r requirements.txt

python -m unittest discover -s tests -v
python smoke_test.py --subproc
```

旧フォルダー `../stackchan_r5a_rl/` と `runs/stand`, `runs/walk` は消しません。旧チェックポイントの保存フォルダーは `model.zip` だけではなく、`config.json`, `interface.json`, `metadata.json`, `READY` を含む全体が必要です。

`smoke_test.py` は短い学習・保存・読込み・再開と、v2へのactor転送を確認します。歩行の習得を試す長時間学習ではありません。エラーで止まった場合は、長時間学習へ進まずそのログを確認してください。

## 2. Stage 1：0.02 m/s固定で「足を上げて、一歩進む」

```bash
python train.py --config configs/walk_step1.json \
  --init-from ../stackchan_r5a_rl/runs/stand/best \
  --num-envs 4 \
  --total-timesteps 1000000 \
  --run-dir runs/walk_step1
```

`--task walk` もStage 1の設定を指します。**旧 `runs/walk/best` の `--resume` ではなく、`--init-from` と新しいrun-dirを使います。** `--resume` は保存された旧報酬を引き継ぐため、この改修を適用する操作にはなりません。

初期値には旧standを使う手順です。旧walkを初期値に使う場合も `--init-from ../stackchan_r5a_rl/runs/walk/best` で指定できます。どちらが有利かは未比較です。Stage 1では、actor（行動の平均値を決めるネットワーク）の重みだけを引き継ぎ、critic（価値推定）とoptimizerを新しくします。探索用の `log_std` を−1.0へ設定します。旧モデルで探索分散が実際に縮んでいたかは、ユーザーの重みがないため確認できていません。引き継ぎ前後の値は `transfer.json` に記録します。

100万ステップは初回の試行量です。成功や収束を保証する回数ではありません。5万遷移ごとの評価で、前進量・左右の着地数・前進を伴う着地数・挙動分類を表示します。途中でも `best/` を再生して確認できます。

```bash
python play.py --checkpoint runs/walk_step1/best --command 0.02

python evaluate.py --checkpoint runs/walk_step1/best \
  --commands 0.02 --episodes 20 \
  --out outputs/walk_step1_eval.json \
  --trajectories outputs/walk_step1_trajectories

python check_stage.py --evaluation outputs/walk_step1_eval.json
```

Stage 1の成功には、12秒完走、姿勢・接触条件に加えて、おおむね **前進25 mm以上、左右それぞれ2回以上の有効着地、左右それぞれ1回以上の前進を伴う着地、交互の切替3回以上** が必要です。25 mmは最初の学習段階の到達目標で、0.02 m/sの速度を12秒間正確に追従したことを意味しません。Stage 2では距離条件を厳しくします。

`check_stage.py` は保存した評価データを読むだけです。各指令で60%以上の成功をデフォルトの進級目安とし、不合格なら終了コード2を返します。これは設計した目安で、統計的な信頼性や実機安全性の認定ではありません。

### 学習を追加する場合

```bash
python train.py --resume runs/walk_step1/latest \
  --num-envs 4 --total-timesteps 1000000 \
  --run-dir runs/walk_step1
```

これはv2で保存したチェックポイントを再開するので、v2の報酬のまま継続します。`--total-timesteps` は追加する遷移数です。Ctrl+C時は `interrupted/` へ保存します。そこから再開する場合は `latest` を `interrupted` に置き換えます。シミュレーターの途中状態や乱数状態までの完全復元ではありません。

## 3. Stage 2：0.02〜0.04 m/sの連続歩行

Stage 1の別seed評価と映像を確認してから進みます。自動的に学習時間だけで次の段階へ移す処理は入れていません。

```bash
python train.py --config configs/walk_step2.json \
  --init-from runs/walk_step1/best \
  --num-envs 4 --total-timesteps 2000000 \
  --run-dir runs/walk_step2

python evaluate.py --checkpoint runs/walk_step2/best \
  --commands 0.02,0.04 --episodes 20 \
  --out outputs/walk_step2_eval.json
python check_stage.py --evaluation outputs/walk_step2_eval.json
```

Stage 2では指令距離の50%以上、左右それぞれ2回以上の前進着地を要求します。Stage 1と報酬式が共通なので、actorとcriticを引き継ぎます。探索分散も引き継ぎ、optimizerだけ新しくします。

## 4. Stage 3：停止と0.02〜0.06 m/s歩行の統合

```bash
python train.py --config configs/walk_step3.json \
  --init-from runs/walk_step2/best \
  --num-envs 4 --total-timesteps 2000000 \
  --run-dir runs/walk_step3

python play.py --checkpoint runs/walk_step3/best --command 0.04
python evaluate.py --checkpoint runs/walk_step3/best \
  --commands 0,0.02,0.04,0.06 --episodes 20 \
  --out outputs/walk_step3_eval.json
python check_stage.py --evaluation outputs/walk_step3_eval.json
```

ここで初めて20%の停止指令を混ぜます。停止中には離床・前進・交互着地の報酬や「足踏みなし」の罰則は入りません。停止試験と各速度試験を分けて評価するため、停止だけ成功して歩行失敗を覆い隠さない設定です。

## 5. 主な変更

| 項目 | v2の扱い |
|---|---|
| 速度追従 | 指令に対する相対誤差で評価。正の指令に対して速度ゼロなら速度報酬ゼロ。係数2→8 |
| 前進 | 胴体が新たに到達した前進距離を報酬化。同じ区間の前後揺動で繰り返し得点しない |
| 荷重移動 | 遊脚側の荷重を減らす連続報酬。反対足の支持が必要 |
| 位相と接触 | 両足接地のまま遊脚位相の部分点を取らない。期待される接触の組合せで評価 |
| 離床・着地 | 高さ・滞空時間・反対足支持を満たすイベントを評価。接地確認40 ms |
| 交互歩行 | 同じ足の連打による離床・通常着地ボーナスを抑制。前進着地も別計測 |
| 停滞 | 正の指令中、有効着地なし1.5秒を過ぎると罰則を徐々に加える。上限付きで、停滞だけでは強制終了しない |
| 過剰な抑制 | action変化、関節速度、トルク、消費仕事、home姿勢への拘束を弱める。物理的なトルク上限は変更しない |
| bestの選択 | 報酬よりも指令別の成功、前進、左右の実歩数を優先 |
| 初期化 | Stage 1だけactor転送＋critic/探索の再初期化。旧立位の価値関数を新報酬に持ち込まない |

`audit_rewards.py` で、旧・新報酬を人工的な状態に当てはめて比較できます。

```bash
python audit_rewards.py
```

これは報酬関数だけの数値テストです。人工状態が力学的に実現できること、PPOがそこへ到達できること、歩行に成功することの証拠ではありません。

## 6. もぞもぞ状態と接地判定を切り分けるログ

評価JSONとCSVには次を記録します。

- `raw_unloads`：荷重しきい値を下回った回数。ノイズや小さい揺動を含みます。
- `qualified_liftoffs`：高さ2 mm・滞空80 ms・反対足支持を満たした離床。
- `valid_landings`：上記離床後に40 ms接地が確認された着地。
- `forward_landings`：さらに足が離床前より4 mm以上前進し、その足の過去の前進位置も更新した着地。
- `event_rejections`：高さ不足、滞空時間不足、反対足支持不足、接地確認前の再離床。
- `behavior`：`no_verified_steps`, `one_sided_stepping`, `stepping_in_place` など。成功判定とは別の診断名です。

`landings=[0,0]` でも `raw_unloads` が多く高さ不足なら、脚が全く動かないケースとは異なります。数値だけでなく `play.py` でも確認します。CSVは接地荷重・足底最低高さ・目標角・実角・トルク・各報酬を含みます。

```bash
tensorboard --logdir runs --host 127.0.0.1 --port 6006
```

`eval/left_forward_landings`, `eval/right_forward_landings`, `eval/locomotion_score`, `reward_per_second/velocity`, `reward_per_second/unload`, `reward_per_second/no_step` を追加しています。`best` が存在していても、全評価が失敗していれば成功方策ではありません。

## 7. 互換性と残る制限

旧チェックポイントは新フィールドを補完して読み込みますが、旧報酬はversion 1のままです。旧方策の再生・評価・同一報酬での再開は可能な設計です。`configs/walk_legacy.json` に旧歩行設定を残しています。

新規学習のv2設定は `env.walk_objective_version=2` です。学習時間、報酬値、幾何モデルの変更とI/O互換性は別問題なので、`interface.json` のモデルハッシュ等の照合は残しています。関節やactionスケールの不一致を無視して転送する機能はありません。

自由な胴体をトルクで駆動する経路は旧版と同じです。ルート姿勢の強制移動、架空の支持力、接触の一括無効化、強い仮想サーボへの差し替えはしません。接地イベントは50 Hzで標本化しており、全1 kHz接触を捕捉した判定ではありません。短い衝撃、実部品・配線との干渉、発熱・電圧低下、実機への転送、走行は未検証です。

観測にはシミュレーター由来の速度・高さ・接触情報を使います。また報酬の接地履歴・前進記録は内部状態で、61次元観測に履歴全体を追加していません。これは互換性を優先した設計で、学習の容易さを保証しません。

詳細は `docs/DESIGN_ja.md`、変更一覧は `CHANGELOG_ja.md`、旧キットの説明は `docs/legacy/` です。
