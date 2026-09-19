# R5-A PPO v4 — 40 msフィルター込みで歩容と速度追従を整える

対象はA案（横置きTab5・128 × 128 × 128 mmボディ）です。v3の
`runs/walk_refine/best` を初期値に使います。モデル・メッシュを同梱しています。
**学習済み方策は同梱していません。旧runを上書きせず、新しいrunに学習します。**

今回は実行済みの比較試験で用いた「速度制限の後段の40 msローパス」を正式な
制御経路にしました。物理モデル、サーボのトルク・速度上限、PDゲインは変更して
いませんが、**制御系の動力学は変わります**。観測61次元、action10次元を維持し、
新しい制御条件でactorを微調整します。実行テストの実施範囲は
`TEST_REPORT_ja.md` に記載しています。v4での歩行改善・収束は未実証です。

## 1. 配置と接続テスト

現在MuJoCo/SB3が動く仮想環境を有効にして実行します。追加の依存はありません。
ZIPを `~/stack-chan-mujoco` にコピーした例です。

```bash
cd ~/stack-chan-mujoco
unzip stackchan_r5a_rl_v4.zip
cd stackchan_r5a_rl_v4

python -m unittest discover -s tests -v
python smoke_test.py --subproc
```

`smoke_test.py` は短いPPO更新、保存・再開、旧制御からLP40へのactor転送、
評価までの接続試験です。歩容の習得試験ではありません。失敗したら長時間学習へ
進まず、出力先の `stage_*.log` を確認してください。依存があるWSLでは実MuJoCo/
SB3テストも走ります。`skipped` は合格ではなく未実行です。

未導入の環境だけ `python -m pip install -r requirements.txt` を実行します。
動いている環境のライブラリーを、この変更のためだけに更新する必要はありません。

## 2. v3の歩けた方策から、0.02 m/s固定で学習

```bash
python train.py --config configs/walk_lp40.json \
  --init-from ../stackchan_r5a_rl_v3/runs/walk_refine/best \
  --num-envs 4 \
  --total-timesteps 500000 \
  --run-dir runs/walk_lp40
```

**最初の切替は `--init-from` です。`--resume` は使いません。**
`model.zip` だけではなく、`config.json`、`interface.json`、`metadata.json`、
`READY` を含む旧チェックポイントフォルダー全体を保持してください。

actorと学習済みの探索幅 `log_std` は引き継ぎます。新しい報酬と制御条件に合わせ、
critic・optimizerは新規にします。学習率3e-5、entropy係数0.0005、clip 0.15、
target_kl 0.015です。学習開始前に新条件で6試行を評価し、`initial/`と`best/`を保存。
以後25,000遷移ごとに評価します。**改善しなければbestはinitialのままです。**
50万は初回の試行量で、成功を保証する回数でも早期終了条件でもありません。

`--task walk` は互換性のため旧v2 Stage 1を指したままです。
**今回の学習では `--config configs/walk_lp40.json` を指定してください。**

## 3. 新しい初期状態で20回評価

```bash
python evaluate.py --checkpoint runs/walk_lp40/best \
  --commands 0.02 --episodes 20 --seed 40000 \
  --out outputs/walk_lp40_eval.json \
  --trajectories outputs/walk_lp40_trajectories

python diagnose_gait.py --evaluation outputs/walk_lp40_eval.json \
  --out outputs/walk_lp40_diagnosis.json
```

40000番台は学習中のモデル選択用seed（10000番台）と、既に調べたフィルター比較
（20000番台）から分けた検証用です。後からこの結果でチューニングした場合は、
そのseedも未知条件の検証とは扱えません。

再生は独立して実行します。チェックポイントのLPF設定を自動で読みます。

```bash
python play.py --checkpoint runs/walk_lp40/best \
  --command 0.02 --episodes 1 --random-reset
```

`evaluate.py` はOpenGL/ビューアーを起動しません。WSLg/GLXドライバーの問題を
修復したものではありません。

## 4. 学習前後を同じ条件で比較

`initial/`は旧actorに40 msフィルターを組み合わせた**新条件の基準方策**です。
フィルターなしの旧v3と比べて、フィルターの効果を「学習の効果」と数えません。

```bash
python evaluate.py --checkpoint runs/walk_lp40/initial \
  --commands 0.02 --episodes 20 --seed 40000 \
  --out outputs/walk_lp40_before.json

python diagnose_gait.py --evaluation outputs/walk_lp40_eval.json \
  --baseline outputs/walk_lp40_before.json \
  --out outputs/walk_lp40_comparison.json

python check_stage.py --evaluation outputs/walk_lp40_eval.json --min-success 0.8
```

0.307 mから指令相当の約0.220 mへ減速した場合を悪化としないため、v4の比較は
「距離85%維持」ではなく、指令距離からの誤差で判断します。次段階へ自動進級
しません。80%以上の総合合格に加え、v4の進級判定では試行群全体の自己接触・
足裏以外の接触がないことも確認します。これは試験上の目安で、実機安全認証では
ありません。結果JSON、接触記録、映像を分けて確認します。

## 5. 再開

```bash
python train.py --resume runs/walk_lp40/latest \
  --num-envs 4 --total-timesteps 500000 --run-dir runs/walk_lp40
```

Ctrl+C時は `interrupted/`、正常終了時は `final/` にも保存します。
`--total-timesteps` は再開時も**追加**する遷移数。保存済みのLPF・報酬・評価設定を
維持します。物理状態や途中のrollout、乱数状態までの完全復元ではありません。

## 6. 制御・報酬の変更

制御経路は

```text
50 Hz action → 目標角の可動域/開脚制約
             → 1 kHz速度制限 → 1 kHz・40 msローパス
             → 最終速度ガード → 元の10 ms指令遅延 → PD → 元のトルク/速度制約
```

フィルターは `alpha = 1-exp(-physics_dt/0.040)`。
初期状態、slew状態、LPF状態、遅延キューをresetごとに同じhome値で初期化します。
比較試験の処理と数値的に一致させるため、元のServoBankを最後に呼ぶ実装を維持。
最終速度ガードは正常な初期化では冗長ですが、削除していません。

観測の39〜48番 `filtered_target_offset` は**LPF後・通信遅延前の目標角**です。
29〜38番 `previous_action` は生の方策出力のままです。遅延キューやLPF前のslew
内部状態、イベント履歴全体を観測へ追加していないため、完全なMarkov状態では
ありません。今回は既存actorの継承を優先した設計です。

| 項目 | v4 |
|---|---|
| 前進報酬 | 新規到達距離を「現在の指令速度 × 20 ms」で上限制限。余りを後で支払わない。係数1.5→0.5 |
| 速度追従 | 係数8を維持。正の速度指令で静止した場合は速度報酬ゼロ |
| 速度超過 | 係数0.4→1.0。現在の指令に対し、最終指令の10%に相当する余裕を越えた超過を二乗罰則 |
| 生action一階差分 | 係数0.06→0.60 |
| 生action二階差分 | 係数0.025→0.15 |
| 前進着地・交互着地 | 直前の実際の有効着地と反対脚の場合だけ加点。同じ足の連打で前進着地ボーナスを取れない |
| 同一脚の連続着地 | 係数0.08→0.25。前回の加点イベントではなく実測イベントを基準に判定 |
| 交互ボーナス | 係数0.25→0.30。反対脚かつ前進を伴う着地が必要 |
| ピッチ・荷重・モデル | v3のまま。サーボ強化、補助外力、衝突無効化はしない |

歩数の生カウント・離床高さ2 mm・滞空80 ms・接地確認40 ms・前進4 mmの条件は
変更していません。新しい`ordered_*`は**報酬を与えたイベント**であって歩数の
置換ではありません。同時フレームでの両足着地は、報酬上の順序を捏造せず加点
しません。成功判定は従来の実測`landing_sequence`等を使います。

## 7. 評価とbest選択

従来の基本歩行条件・生action差分RMS≤0.25・同一脚連続割合≤0.25等は維持し、
v4ではさらに以下を品質条件に追加しました。

- 実移動距離が指令積分距離の90〜110%（0.02 m/s・12秒・現ランプでは約198〜242 mm）。
- 平均絶対速度誤差 ≤0.012 m/s。
- LPF後目標角の1方策周期差分RMSの**関節別RMSの平均** ≤0.0125 rad。

これらは新しい試行目標で、達成可能性を学習で実証した値ではありません。
細かいサーボ目標が滑らかでも、生actionが振動していれば不合格です。
歩行としての条件を満たした候補でのみ、速度追従・順序・指令・姿勢の品質を比較
してbestを選びます。総報酬や前進距離だけでは選びません。

`target_delta_rms_rad_mean`は実関節の振れ幅ではありません。
`target_delta_global_rms_rad`は全関節二乗平均をまとめてから平方根を取る別値です。
比較試験との連続性のため、進級判定には前者を使います。

## 8. 診断ログ

CSVに生action、可動域制約後の目標、slew後の目標、LPF後の目標、遅延後の目標、
実角・実角速度・トルクを収録します。`policy_input_00`〜`60`はそのactionに使った
観測です（reset行は初期観測）。足底の世界座標と着地イベントも追加しています。

JSONには`target_lowpass_time_constant_s`、指令距離比、距離誤差、連続着地割合、
`ordered_*`累積値、終了時の実MuJoCo接触対を収録。接触対の名前と力は代理衝突
形状の値であり、実物のケースの接触を保証しません。通常の自己接触終了判定は
50 Hzのままです。1 ms全接触履歴の保存ではありません。

```bash
python audit_lp40.py
tensorboard --logdir runs --host 127.0.0.1 --port 6006
```

`audit_lp40.py`は人工状態での報酬関数テストです。物理歩行・学習結果ではありません。

## 9. 互換性

旧checkpointはLPFなしで読み込まれ、旧v1〜v3報酬のまま再生・再開されます。
旧フォルダーへ上書きインストールせず、v4を別フォルダーで使用してください。
新LPF設定は`interface.json`にも保存します。暗黙の制御条件変更は拒否します。

`walk_lp40.json`は`transfer.allow_target_lowpass_change=true`で、`--init-from`時
に限ってLPF差分を許可します。モデル・関節順・actionスケール・slew・観測等の
他の不一致を無視するフラグではありません。変更は`transfer.json`に記録します。

診断だけで旧方策へLPFを付けて評価する場合は、明示的なオプションが必要です。

```bash
python evaluate.py \
  --checkpoint ../stackchan_r5a_rl_v3/runs/walk_refine/best \
  --config configs/walk_lp40_baseline.json --allow-target-lowpass-change \
  --commands 0.02 --episodes 5 --seed 20000 \
  --out outputs/lp40_integration_baseline.json
```

このbaseline設定は**v3報酬＋LPF40 ms**で、以前のprobeと制御・目的を揃えるもの。
新学習用`walk_lp40.json`とは報酬が違います。v3との重みは同じでも、フィルター
の有無で閉ループ挙動が変わるので、同一挙動を保証する「互換性」ではありません。
実行時ライブラリーの差による再現差にも注意してください。

## 10. 未検証の範囲

今回の配布環境ではMuJoCo/SB3依存の取得に失敗し、v4の物理実行・本学習・GUI・
ユーザー方策の閉ループ再現は未実行です。単体テスト、実際の保存重みのPyTorch
テンソルレベルでの転送試験、フィルターの独立参照実装との一致を、それらと区別
して記録しています。詳細は `TEST_REPORT_ja.md` と `validation/` を参照。
実機転送、電源・熱・ホーン・配線・CAD連続干渉、走行は対象外です。
