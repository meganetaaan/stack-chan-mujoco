# KiCad 接続確認用回路図（製作不可）

revI の46部品・159端子を編集可能な KiCad 回路図へ移行した。
KiCad 7.0.11 自身の XML 出力を照合し、選定型番46件、接続147端子、
独立した明示的未接続12端子が assembly/BOM と一致した。
PDF は同じ回路図を KiCad で出力した閲覧用資料。

全端子は汎用 passive シンボルであり、電気的 ERC を完了した図ではない。
フットプリント未割当、機能別配置未整理。シーケンサー、保護回路、
電源容量の未解決事項は残る。この移行によって #6/#24 は完了しない。

## 再現

リポジトリルートで実行。生成先は新しいディレクトリを指定する。

```sh
python3 software/sim/circuits/export_manual_rearm_schematic.py --out /tmp/rearm-native-new
kicad-cli sch export netlist --format kicadxml -o /tmp/rearm-readback.xml /tmp/rearm-native-new/manual_rearm.kicad_sch
kicad-cli sch export pdf -o /tmp/rearm-native-new/manual_rearm.pdf /tmp/rearm-native-new/manual_rearm.kicad_sch
python3 software/sim/circuits/verify_manual_rearm_kicad.py --netlist /tmp/rearm-readback.xml --schematic /tmp/rearm-native-new/manual_rearm.kicad_sch --out /tmp/rearm-native-new/report.json
```

検証環境は Ubuntu パッケージの KiCad 7.0.11+dfsg-1build4。
実行環境は一時ディレクトリへ展開し、リポジトリへバイナリは格納していない。
XML の日時・パスによるバイト差は許容するが、部品値・全端子の接続・NC は完全一致を要求する。
report のハッシュは今回使用した入力を識別するもの。

次に必要なのは端子電気属性と実部品シンボルの確認、未完成機能の設計、
電源状態ごとの成立確認である。基板製作や通電の許可資料ではない。
