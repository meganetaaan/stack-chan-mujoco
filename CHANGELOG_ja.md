# v3.0.0 変更一覧

- Stage 1.5設定 `configs/walk_refine.json` を追加。既存の `walk` / Stage 1〜3設定は変更しません。
- `quality.py`：1 kHzのpitch/load/touchdown計測、50 Hzのaction/target error、4秒の前進着地バランス。
- `env.py`：読み取り専用のsubstep telemetryを追加。観測/サーボ/物理設定は維持。
- `rewards.py`：v3専用にpitch、二階差分、着地荷重、接近速度、偏り、連打のコスト。
- `walk_events.py`：既存判定を維持し、イベントの左右識別を追加。
- `evaluation.py`：独立したquality gate、失敗条件、歩行を前提とするquality選択。
- `training.py`：actor/log_std保持・critic再初期化、開始時評価とinitial/best保存、品質ログ。
- `evaluate.py`：同一interfaceでの明示config評価、1epごとのログ/部分保存、seed記録。
- `diagnose_gait.py`：JSONの失敗条件診断と、同一条件による前後比較。
- `play.py`：閉じたviewerの同期回避とlock。GLXドライバー修正ではありません。
- `benchmark.py --config`、品質条件を確認するcheck_stage、refineまでのsmoke経路を追加。
- Stage 2/3用に整形目的を保持する `walk_step2_smooth.json` / `walk_step3_smooth.json` を別名で追加。
- v3 unit tests、実MuJoCo/SB3用テスト、実行記録と日本語手順。

モデル・PD・出力のスケールを変えるパッチではありません。新規学習にはv2のwalk_step1/bestを `--init-from` で指定します。v2の `--resume` はv2の報酬を維持します。

---

# v2.0.0 変更一覧

## 変更したもの

- `config.py`：旧設定の補完、新旧歩行目的のバージョン管理、転送設定、進級時の複数指令評価。
- `rewards.py`：正の指令で静止中の速度報酬をゼロにする相対速度項、前進記録・除荷・実離床・着地・交互切替・停滞項。姿勢や動作の罰則を調整。
- `walk_events.py`（新規）：接地確認、支持を伴う離床、前進着地、同じ足の連打対策、イベント不成立の理由。
- `env.py`：上記を報酬と評価へ接続。CSV/JSON診断の追加。接触力のraw観測やサーボ・自由な胴体の物理計算は維持。
- `transfer.py`（新規）：actorだけの転送、criticの新規初期化を保持、探索分散の明示リセット。
- `training.py`：転送処理、歩行を優先するbest選択、速度別評価と左右の実歩数をログ化。
- `evaluation.py`：指令別の成績、進捗による順位、挙動分類。未学習の人工集計を物理実行済みとしない。
- `checkpoints.py`：旧bundleを新フィールド付きで読み込むが、旧報酬を無断でv2へ変えない。
- `play.py`, `evaluate.py`：前進着地と挙動分類を出力。
- `configs/walk_step1/2/3.json`（新規）：0.02固定→0.02〜0.04→停止＋0.02〜0.06。
- `configs/walk.json`：Stage 1を指す。旧設定は `walk_legacy.json` に保存。
- `check_stage.py`（新規）：別seed評価の進級目安を検査。時間経過だけで次の段階へ移さない。
- `audit_rewards.py`（新規）：人工状態に対する旧・新報酬の比較。物理テストとは区別。
- 追加の回帰・実行テスト、更新したREADME・設計メモ・検証記録。

## 変更していないもの

A案のMJCF/全asset、関節数、質量・慣性、衝突形状、サーボの上限、観測61次元とaction10次元の順序・スケール、50 Hz方策・1 kHz物理/PD、外向き股ロールの探索ガード。架空の支持力やルートの強制移動は追加していません。

## 再学習時の注意

旧 `--resume` は旧報酬での再開です。v2を適用するには `--config configs/walk_step1.json --init-from <旧stand/best>` を使い、新しいrun-dirへ保存します。v2で保存した結果の再開は通常どおり `--resume` です。既存の学習結果を上書きするパッチ適用スクリプトは含めていません。
