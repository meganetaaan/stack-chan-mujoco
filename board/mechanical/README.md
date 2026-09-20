# 機構CADと製作仕様

- `design/`: 既存CAD生成ソース・設計入力。履歴資料としてバイト単位で保持。
- `prototype/`: 製作候補のBOM・12軸仕様・座標・制限。凍結r9とは別に管理する。
- MuJoCoで使用する生成済みメッシュ/MJCF: `software/sim/mujoco/assets/`。
- 既存CAD再生成の入口: `software/sim/mujoco/build_design.py` 等。
  CADツールはシミュレーターの出力規約を共用するため、現段階では同ディレクトリから実行する。

構造の変更・構造解析はEPIC #5で扱う。EPIC #3・#4で製造承認は行わない。
