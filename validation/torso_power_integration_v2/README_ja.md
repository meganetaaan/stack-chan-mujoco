# 胴体統合v2：調整用通し穴を反映

ヨー支持部revCと電源取付候補revBを統合した100部品の公称組立。
電源候補の参照先は`board/mechanical/prototype/power_mount_candidate/current.json`。
部品の数え方と除外範囲はv1と同じ。旧後部板は置換し、ヨー後部締結16点を保持する。

異なる部分組立間の検査は包絡箱で2686組を除外し、近接40組、体積重複16組。
16組はいずれもモジュール包絡とねじ・スペーサーの組合せである。
そのハードウェアと配置はv1から不変なので、共通メーカーSTEPで重複なしとした
`validation/torso_module_contacts_v1`の限定的な照合は適用できる。
5V版専用適合や公差を含む保証へは拡張しない。

`revision_check.json`で100部品を名前・体積対応のうえB-rep差分比較。
98部品は双方向の形状差分が許容数値誤差未満。
左右ブラケットは各18.107512mm³の除去のみで、新規材料なし。
したがって固定した公称姿勢の外部剛体隙間を悪化させる変更ではない。
材料除去で低下し得る強度、座面、変形はこの論理で引き継げない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/integrate_torso_power.py
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_torso_revision.py
```

製造条件は電源取付候補READMEの表で管理する。全身の脚・足、ハーネス、
最新電源保護基板はまだこの100部品に含まれない。全身強度・干渉合格ではない。
製作リリースfalseを維持する。
