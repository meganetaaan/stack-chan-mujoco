# 現行ヨー組立と部品表の照合

current.jsonが指すrevBを標準入力とし、52部品を10行の部品表へ一度ずつ対応した。参照元CADのSHA-256も照合する。後部ワッシャーはSCW-YAW-REAR-WASHER-01 revA加工案へ更新し、調達・製造承認とは区別した。

初回検査は旧足部スペーサーの数量条件で失敗した。足部revEのクランプワッシャーへの変更を反映し、SCW-SOLE-SPACER-01の足部割当てを2から0、全体数量を8へ整理した。失敗記録をinitial_failure.txtへ保存。その他の共有部品数量は変更していない。

現行52部品の数量対応は合格。旧revAを明示指定すると後部ワッシャーと部品表の不一致で失敗することも確認し、old_revision_rejection.txtへ保存した。形状の強度・製造可否・全ロボットの調達網羅性を証明する検査ではない。

再現（未存在の出力先）：

```sh
.venv-engineering/bin/python software/sim/structural/audit_yaw_bom_coverage.py --out /tmp/yaw-bom-review
```
