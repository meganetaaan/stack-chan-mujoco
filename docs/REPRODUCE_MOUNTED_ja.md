# 固定具込み構成の再現

対象は `assets/r6_mounted_battery`、`policies/r6_mounted_seed20260924`、
`validation/r6_mounted_seed20260924`。固定20/20・ランダム化18/20はこの組合せの結果。
電源・実機同定は未実施で、製作リリースではない。

## 環境と取得

公開リポジトリの `codex/tab5-10m-redesign` ブランチを取得し、リポジトリ直下で実行する。

```sh
git clone --depth 1 --branch codex/tab5-10m-redesign https://github.com/meganetaaan/stack-chan-mujoco.git
cd stack-chan-mujoco
```

実行環境の記録は `policies/r6_mounted_seed20260924/runtime.json`。
RL側はPython 3.14.7、MuJoCo 3.13.0、NumPy 2.5.3、Gymnasium 1.3.0、
Stable-Baselines3 2.9.0、PyTorch 2.14.0でCPU実行。
直接依存の指定は `design/requirements-r6-rl.txt`。CAD側はPython 3.12.3、
CadQuery 2.8.0、`design/requirements-cad.lock.txt` を使用する。環境を分ける。
以下の `python` はRL環境、`.venv-cad/bin/python` はCAD環境を指す。
動画にはffmpegと使用可能なMuJoCoレンダリングバックエンドが必要。
学習結果の数値はOS・CPU・ライブラリに依存し得るため、受入結果の再評価には公開方策を使う。

## 公開結果の整合性検査

```sh
python verify_r6_release.py --checkpoint policies/r6_mounted_seed20260924 \
  --evaluation validation/r6_mounted_seed20260924 \
  --seed-plan configs/r6/mounted_evaluation_seeds.json \
  --out outputs/mounted_release_audit.json
```

モデル47ファイル、方策・設定・シード計画のハッシュ、全40試行の状態・時刻、
シードから再生成した実現パラメータ、合否条件の一致を検査する。
これは新しい歩行計算ではなく、保存結果の整合性検査。

## 同じ方策で歩行を再実行

```sh
python run_planned_r6_evaluation.py --checkpoint policies/r6_mounted_seed20260924 \
  --seed-plan configs/r6/mounted_evaluation_seeds.json --out outputs/mounted_reproduction
python verify_r6_release.py --checkpoint policies/r6_mounted_seed20260924 \
  --evaluation outputs/mounted_reproduction --seed-plan configs/r6/mounted_evaluation_seeds.json \
  --out outputs/mounted_reproduction_audit.json
```

固定117000–117019、ランダム化118000–118019、各20試行。
1試行109.5秒の全状態を保存し、失敗も集計する。既存出力先は再使用しない。
同じシードの再実行は再現性の確認であり、新しい独立した受入バッチには数えない。

```sh
MUJOCO_GL=egl python replay_residual.py --batch outputs/mounted_reproduction/fixed \
  --trial trial_00 --out outputs/mounted_reproduction_fixed00.mp4
```

動画は実際の保存状態だけを使う。実行時間・フレーム数・ハッシュは同名JSON。
EGLが利用できない環境では、MuJoCoが利用可能な描画環境を別途用意する。

## CADからモデルを再生成

```sh
.venv-cad/bin/python reproduce_mounted_design.py --out outputs/mounted_fresh_design
```

元CAD、脚内部の逃げ・横梁、ジンバルの衝突形状、固定クレードル等の衝突形状、
トレー・ベルト・締結具、固定具込み慣性とMJCFを順に生成する。
既存の作業用CADや未追跡STEPを入力にしない。
組立は `outputs/mounted_fresh_design/mount/assembly.step`、
モデルは `outputs/mounted_fresh_design/model/models/scene.xml`。
生成経路のログは `regeneration.json` と `step_*.log`。
公開モデルを上書きせず、差分を確認する。

## 学習を再実行

```sh
python train_mounted_residual.py --checkpoint policies/r6_steering_seed20260923 \
  --out runs/mounted_retraining --seed 20260924
```

公開親方策を初期値に32,768ステップのPPOを実行する。新規オプティマイザを使用。
ゼロからの歩容発見ではなく、参照歩容に対する学習済み残差の転移学習。
再学習した方策の性能は、その方策を評価するまで未確認。
設計仮定と保護条件は [受入条件](GOAL_PROTOCOL_ja.md)、
実機への移行条件は [実機受入手順](HARDWARE_PROTOCOL_ja.md) を参照する。

## 実施した再現性確認

追跡ファイルだけのコミット `06765dd` のアーカイブと、`662b5d9` の再生成エントリを別ディレクトリへ展開して確認した。既存のRL/CAD実行環境を使用し、OSや依存パッケージの新規導入試験は行っていない。

- 作業用 `outputs/`・`runs/` を持ち込まず、公開一式の統合監査に合格。
- 元CADから5段階で再生成し、入力由来のパス等を含む生成記録2ファイルを除いた、公開モデルの全比較対象ファイルがバイト一致。MuJoCoの質量・慣性・関節・接触形状・メッシュ・アクチュエータ配列も一致。
- 公開方策で固定seed117000を109.5秒再実行し、状態NPZとレポートがバイト一致。配列内の全状態・行動・観測・最終サブステップトルクも一致。

証拠は `validation/r6_mounted_seed20260924/reproducibility`。同一環境・同一シードによる1試行の再現であり、未知環境でのビット一致や独立した40試行の追加成功を主張しない。
