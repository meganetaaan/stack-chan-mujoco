# 手動再始動revJのKiCad接続図

54部品182端子を出力し、KiCad 7.0.11で読み戻したネットリストについて
全型番、168接続端子、14明示NCが一致した。2本のPG配線はinterconnectsを
導通ネットへ統合して出力。単に別名ラベルを置いて未接続にする扱いを修正した。
部品増加に合わせてA1用紙へ変更。

汎用passive端子の接続移行図で、電気種別を使ったERC・フットプリント・製造図ではない。
起動回路や主電力経路は依然未完成。図面読戻しを保護の成立と解釈しない。

```sh
.venv-engineering/bin/python software/sim/circuits/export_manual_rearm_schematic.py --assembly schematics/power/manual_rearm_revJ/assembly.json --bom validation/manual_rearm_bom_v5/bom.csv --out /tmp/rearm-J
kicad-cli sch export netlist --format kicadxml -o /tmp/rearm-J/readback.xml /tmp/rearm-J/manual_rearm.kicad_sch
.venv-engineering/bin/python software/sim/circuits/verify_manual_rearm_kicad.py --assembly schematics/power/manual_rearm_revJ/assembly.json --bom validation/manual_rearm_bom_v5/bom.csv --schematic /tmp/rearm-J/manual_rearm.kicad_sch --netlist /tmp/rearm-J/readback.xml --out /tmp/rearm-J/report.json
```
