# stack-chan MuJoCo RL

**高速旋回 r9:** MuJoCoで左右90°（停止誤差±1°以内）を6歩・約2.76秒で完了。名目条件と重量・摩擦の単独変動を含む10条件を検証済み。[再現手順・設計変更・結果](docs/FAST_TURN_RUN_ja.md)／[記録動画](validation/fast_turn_v1/left_turn.mp4)。既存r8とは別モデルです。

**WASDで操作:** `python teleop_yaw.py` — W/Sで前進・後退、A/Dで旋回、キーを離すかSpaceで停止。[操作手順](docs/TELEOP_ja.md)

現在はTab5の顔と胴体・脚長・足形状を保ち、前進・後退・左右旋回・停止とその切替を検証しています。股関節ヨーを含む12軸のr8候補について、205秒・24区間の正式評価で固定20/20・ランダム化18/20の総合通過を確認しました。全40試行の状態記録からの再評価も一致しています。設計データ、制御・評価ソフト、全40試行の状態記録、成功・不合格の再生動画を公開しています。

[動作・切替の目標と基準](docs/MANEUVER_GOAL_ja.md)、[正式評価手順](docs/YAW_ACCEPTANCE_RUN_ja.md)、[凍結候補と正式評価記録](validation/yaw_acceptance_phase22_v1/README.md)、[開発20条件の結果と実状態動画](validation/yaw_backward_phase22_development_v1/README.md)を参照してください。実機検証は電源・パラメータ同定後、起き上がりは対象外です。

以下のR6の成績は従来の前進専用評価であり、新しい動作・切替の合格率には転用しません。

現行の胴体・脚長・足形状とTab5の顔を維持した、R6の残差強化学習を進めています。
現段階の受入条件は、0.10 m/s指令で10 m連続歩行を固定条件20/20、ランダム化条件18/20。
実機10 m・18/20は電源構成と実機同定後の次段階です。**固定具込みの仮定モデルで固定20/20、ランダム化18/20を達成**しました。電源・製作・実機の検証は未完了です。結果は `validation/r6_mounted_seed20260924`、方策は `policies/r6_mounted_seed20260924`、モデルは `assets/r6_mounted_battery`。ランダム化の関節制限逸脱1件・自己衝突1件も保存しています。

[学習と再現手順](docs/R6_RL_ja.md)、[受入条件](docs/GOAL_PROTOCOL_ja.md)、
[機構](docs/REAR_BRIDGE_ja.md)、[電源・電池](docs/POWER_ja.md)を参照してください。
初回の学習済み方策は `policies/r6_residual_seed20260920`、凍結モデルは `assets/r6_rear_bridge8_collision`。
以下は併存する旧R5-A環境の説明です。

MuJoCo と Stable-Baselines3（PPO）を使い、ｽﾀｯｸﾁｬﾝ R5-A の立位・歩行制御を検証するプロジェクトです。

現在の実装は v4 です。40 ms の目標角ローパスフィルターを制御経路へ組み込み、歩容と 0.02 m/s の速度追従を調整しています。詳しいセットアップ、学習・評価方法、既知の制限は [日本語ドキュメント](README_ja.md) を参照してください。

## 現在の状態

- 観測 61 次元、action 10 次元の PPO 方策
- v3 の学習済み actor から v4 制御条件への転送に対応
- オフライン回帰テスト 48 件と依存環境を使う runtime テストを収録
- v4 の歩行改善・収束は未実証

実行済み検査の範囲は [TEST_REPORT_ja.md](TEST_REPORT_ja.md)、変更点は [CHANGELOG_ja.md](CHANGELOG_ja.md) に記録しています。旧R5-A方策と作業用の `runs/`、`outputs/` はリポジトリに含めていません。R6方策は上記の公開ディレクトリへ整理しています。
