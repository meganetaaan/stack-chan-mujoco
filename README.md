# stack-chan MuJoCo RL

10 m・平均0.10 m/s・実機18/20試行を目指す再設計を開始しました。
[再設計台帳](docs/REDESIGN_ja.md)と[受入試験手順](docs/GOAL_PROTOCOL_ja.md)を参照してください。
この実機目標は未達成です。

MuJoCo と Stable-Baselines3（PPO）を使い、ｽﾀｯｸﾁｬﾝ R5-A の立位・歩行制御を検証するプロジェクトです。

現在の実装は v4 です。40 ms の目標角ローパスフィルターを制御経路へ組み込み、歩容と 0.02 m/s の速度追従を調整しています。詳しいセットアップ、学習・評価方法、既知の制限は [日本語ドキュメント](README_ja.md) を参照してください。

## 現在の状態

- 観測 61 次元、action 10 次元の PPO 方策
- v3 の学習済み actor から v4 制御条件への転送に対応
- オフライン回帰テスト 48 件と依存環境を使う runtime テストを収録
- v4 の歩行改善・収束は未実証

実行済み検査の範囲は [TEST_REPORT_ja.md](TEST_REPORT_ja.md)、変更点は [CHANGELOG_ja.md](CHANGELOG_ja.md) に記録しています。学習済み方策と `runs/`、`outputs/` はリポジトリに含めていません。
