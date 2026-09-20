# モノレポへの移行と再現

対象リポジトリは `meganetaaan/stack-chan-walk`。以前のルート直下のPythonスクリプトは
`software/sim/mujoco/` に移した。既存スクリプトの相対パスは、このディレクトリを基準にする。

| 旧配置 | 新配置 |
|---|---|
| `*.py`, `stackchan_rl/`, `tests/` | `software/sim/mujoco/` 配下 |
| `assets/`, `configs/`, `policies/` | `software/sim/mujoco/` 配下 |
| `design/` | `board/mechanical/design/` |
| `validation/` | ルートに保持（凍結済み記録） |
| `requirements*.txt` | `software/sim/mujoco/`（学習等の追加用途） |

`software/sim/mujoco/design` と `validation` は、新しい実体への相対シンボリックリンク。
これは既存のCAD生成・検証ツールの相対参照を保つ互換入口で、内容の複製ではない。
現在の再現対象はLinux/WSLで、チェックアウトにシンボリックリンクのサポートが必要。
凍結モデル・履歴のバイト列は `migration_manifest.json` で4,176ファイルを照合する。
将来の製作仕様を修正する際も、過去の試験に用いたモデルを上書きしない。

## クリーン環境

リポジトリのルートで実行する。検証環境はPython 3.14、MuJoCo 3.13。
GPU、既存CAD生成物、学習済みPython環境は左右旋回の再現に不要。

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r software/sim/requirements-runtime.lock
.venv/bin/python software/sim/run.py verify-migration
.venv/bin/python software/sim/run.py baseline --out outputs/prototype-baseline
```

`baseline`は左右の有限角度試験を再実行し、1 ms接触記録から着地数を再計算する。
各方向6歩、90度±1度、胴体も静止する時刻が3秒未満で、その後1秒以上維持することを確認。
WASD、速度制御、横移動のテストも実行し、失敗は終了コード1とレポートに残す。
出力先は新規パスを指定する。`--skip-teleop`は診断用で、全体合格にはならない。

## 任意の既存スクリプト

```sh
.venv/bin/python software/sim/run.py script teleop_yaw.py --fps 15
.venv/bin/python software/sim/run.py test
```

`script`の相対パス引数と生成物は `software/sim/mujoco/` 基準。
GUIにはGLFW/OpenGLの表示環境が必要。WSLで必要なら `GALLIUM_DRIVER=d3d12` を指定する。
既存ドキュメントの `python probe_...` 等は、最初に `cd software/sim/mujoco` して実行する。
学習用依存とCadQueryは別環境とし、このEPICの動作再現に混在させない。

## 解析結果の共通形式

MuJoCo・回路・構造・SIL・アクチュエータの各解析は、出力フォルダ内の `result.json` を索引とする。
`software/sim/integration/result_bundle.py` が共通の生成・検査を行う。

- `schema_version`, `domain`: フォーマットの版と解析種別。
- `commit`, `runtime`: コードの版とPython・ライブラリの実行環境。
- `commands`: 作業ディレクトリと実際に実行した引数列。
- `inputs`: リポジトリ相対パスとSHA256。実行中の未コミットコードも個別ハッシュで記録。
- `parameters`: 名前、値、単位、出典と `assumed/datasheet/measured/derived` の区別。
- `gates`: 事前に定めた判定基準と真偽値。`passed`は全条件の論理積。
- `artifacts`: 出力フォルダ相対パスとSHA256。
- `limitations`: 省略・近似・未検証事項。

解析固有の波形・メッシュ・状態列は別ファイルにし、索引から参照する。
回路・構造解析そのものの実装はEPIC #5・#6の範囲であり、ここでは形式のみ共有する。
