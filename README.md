# stack-chan MuJoCo RL

現行の胴体・脚長・足形状とTab5の顔を維持した、R6の残差強化学習を進めています。
現段階の受入条件は、0.10 m/s指令で10 m連続歩行を固定条件20/20、ランダム化条件18/20。
実機10 m・18/20は電源構成と実機同定後の次段階です。**最新評価は固定20/20、ランダム化14/20で、受入は未達成**です。

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
