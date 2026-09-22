# 左右PGを含む手動再始動回路の部品BOM

revJの54部品を、既存の抵抗・コンデンサ選定表と照合して型番別に集計した。
左右へ複製した部品はorigin_referenceで元の選定を参照し、実際の左右参照番号で数量を数える。
全54部品に候補型番が対応する。未選定0は、この部分回路の型番欄が埋まったという意味で、
適合・調達・製造リリースではない。

主電力経路、回生回路、起動状態回路、独立停止、UV/OV監視はこのBOMに含まれない。
旧revIの46部品BOMと重ねて合算しない。

```sh
.venv-engineering/bin/python software/sim/circuits/build_manual_rearm_bom.py --assembly schematics/power/manual_rearm_revJ/assembly.json --out /tmp/rearm-bom-revJ
```

引数省略時の旧46部品BOMも再生成し、保存済みv4のCSVとバイト一致を確認した。
