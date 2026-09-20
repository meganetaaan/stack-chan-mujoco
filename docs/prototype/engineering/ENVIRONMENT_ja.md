# 機構・電源解析環境

Ubuntu 24.04 amd64、Python 3.12で確認。システムへのrootインストールは不要。下記はリポジトリルートで実行する。

```sh
python3.12 -m venv .venv-engineering
.venv-engineering/bin/pip install -r software/sim/engineering/requirements.lock.txt
python3 software/sim/engineering/bootstrap_tools.py
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
.venv-engineering/bin/python software/sim/engineering/check_environment.py --out outputs/engineering_check
.venv-engineering/bin/python software/sim/structural/extract_load_cases.py --out outputs/structural_loads
```

OS依存パッケージは名前・版・SHA256を `debian_packages.json` に固定する。Ubuntuの該当版の配布元が必要。ngspice 42、CalculiX 2.21、CadQuery 2.8.0、Gmsh 4.15.2を使用する。`.tools` と仮想環境はGitへ保存しない。

`check_environment.py` はCAD立方体の体積・体積メッシュと、1 kΩ/1 µFのRC回路のステップ応答を既知解と比較する。ロボットの強度・電源の合否試験ではない。
`extract_load_cases.py` は前EPICの片脚34条件と全身左右2条件から、関節ごとの最大力・モーメント・軸トルクの発生時刻を取り出す。全軸の同時刻ベクトルを保存し、荷重をCADへ適用する前に姿勢と座標を変換する必要がある。
