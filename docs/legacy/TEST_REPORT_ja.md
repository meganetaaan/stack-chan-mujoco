# 配布時の検証記録

## 結論

**コードを実装し、40件の物理エンジンを使わないテストを実行して合格しました。実MuJoCo・Gymnasium・SB3の9件は未実行です。立位・歩行を学習した結果はありません。**

作成環境はPython 3.13.5、NumPy 2.3.5、PyTorch 2.10.0+cpuです。`pip install` が名前解決エラーで失敗し、MuJoCo、Gymnasium、Stable Baselines3をインストールできませんでした。これはユーザーのWSL2でインストールできないという意味ではありません。

## 実行したもの

| 検査 | 結果 |
|---|---|
| 全Pythonファイルの構文コンパイル | 成功 |
| オフラインunit tests | 40件実行、40件合格 |
| 元A案ファイルとのSHA-256照合 | 一致 |
| XMLとJSONのモデル名、10関節・motor対応 | 一致 |
| 明示慣性からの総質量 | 0.8260386996 kg |
| 原点・単位・homeの独立したXML順運動学 | テスト合格 |
| 61次元観測の仕様、立位と歩行のI/O同一性 | テスト合格 |
| action範囲、目標slew、10 ms遅延、トルクと速度制限 | 数値関数のテスト合格 |
| 接触系列からの歩数判定 | 初期落下・滑り・チャタリング・同時跳躍の除外テスト合格 |
| 報酬・成功判定 | 時間刻み、終端罰則、高報酬と成功の分離などのテスト合格 |
| チェックポイントのファイル構成と置換処理 | 仮の保存器を用いたI/Oテスト合格。実SB3保存ではない |
| `check_env.py` の実行試行 | 依存不足を検出し `NOT_RUN_MISSING_DEPENDENCIES` を記録 |
| `smoke_test.py --subproc` の実行試行 | 最初のpreflightで停止。PPOもsubprocess学習も未到達 |

## 未実行のもの

実MuJoCoによるMJCFコンパイル、接触計算、Gymnasium/SB3のruntime checker、実PPO更新、実SB3保存・読込み、並列プロセス学習、立位・歩行の成功率、GUI/動画描画、実学習policyのTorchScript書出し、実機動作は未実行です。

`python -m unittest discover -s tests -v` は配布時に49件を発見し、40件合格・9件skippedを返しました。`OK (skipped=9)` を「49件動作確認済み」とは扱いません。

実行依存が揃ったWSLで `python check_env.py` → unit tests → `python smoke_test.py --subproc` を実行すると、対応する実テストへ進みます。問題がある場合はエラーにして止まります。テストを省略したり物理をスタブに差し替えたりして成功に見せる処理はありません。

## 記録ファイル

- `validation/unit_tests.json`, `validation/unit_tests.log`: 実テスト件数、合否、skip理由と環境
- `validation/preflight.json`, `validation/preflight.log`: 依存チェックで停止した実行記録
- `validation/runtime_smoke_attempt/`: 最初の段階で停止した接続テストのログ
- `validation/dependency_install_attempt.log`: 実際のpipエラー
- `assets/r5a/SOURCE_MANIFEST.json`: 元A案とコピーしたファイルのハッシュ

`validation/run_tests.py` を実行すると、ローカル環境でunit test記録を更新できます。元モデルの物理上の仮定・未検証事項は `docs/R5_source_report.md`、今回の制御・観測・評価仕様は `docs/DESIGN_ja.md` を参照してください。
