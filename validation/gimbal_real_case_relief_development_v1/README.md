# 実ケースに対する上側横桟の逃げ

上側横桟をz=14..16.4から14.9..17.3 mmへ移動した。厚さ2.4 mm・幅・体積を保持し、左右とも単一有効ソリッド。実ケースへ削り込んだ薄肉ポケットではない。

メーカーの全15部品に対する中立検査では、足ヨーク・変更フレームとも体積干渉0.01 mm³超はゼロ。変更前の中間ケース55.524 mm³・後ケース17.612 mm³との重なりを解消した。最小ケース隙間は0.4 mmであり、公差・変形・取付支持を含む完成条件ではない。

一方、ブーツと変更フレームの局所11姿勢検査で、±0.34 rad端の最小隙間は0.60636 mm。以前の0.90650 mmから減少し、0.9 mmの離散姿勢基準を満たさない。体積干渉はなかったが、隙間不足として保存する。

boot_screenは従来チェック器によるもので、ブーツ対フレームの評価に限って本候補に対応する。同ファイルの旧足ヨーク・簡略モータ対の結果を新規実ホーン組立の評価に流用しない。native_neutralが実ケースおよび新規ヨークの検査であり、そちらは中立姿勢のみ。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/raise_gimbal_bridge.py --out outputs/gimbal_raised_bridge_repeat
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/check_native_yoke_assembly.py \
 --gimbal-dir outputs/gimbal_raised_bridge_repeat --out outputs/gimbal_raised_assembly_repeat
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/screen_ankle_roll_cad.py \
 --gimbal-dir outputs/gimbal_raised_bridge_repeat --out outputs/gimbal_raised_boot_repeat
```

ケース固定ねじ・取付面・支持剛性、ブーツ開口、連続掃引と公差・変形を合わせた検証が残る。機構全体の合格・可動域拡張・製造承認とはしない。
