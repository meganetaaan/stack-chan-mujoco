# 新規ヨークとフレームの統合検査

別々に検証した標準ホーン用足ヨークと実ケース対応フレームを組み合わせると、後側の耳と下側横桟に左右各84.319 mm³の重なりがあった。ロール座標系の干渉範囲はx[-29,-27]、y[-9,9]、z[-8.8,-6.4] mm。意図した接触ではないため不成立として記録する。

下側横桟の中央30.9 mmを開放する候補を生成した。左右側板は上側横桟で連結された単一有効ソリッドを保持し、体積は各177.984 mm³減少。中立でヨークとの重なり0、距離3.3 mmとなった。メーカー15部品との中立干渉もヨーク・フレームとも0.01 mm³以下。

しかしロール角−0.34～＋0.34 rad、0.02 rad刻み35姿勢×左右のヨーク対フレーム検査では、最小距離0.792502 mmとなり、事前の1.1 mm基準を満たさなかった。中立姿勢の改善を全可動域成立と解釈しない。ブーツとの約0.606 mmの隙間不足も未解決。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/open_lower_gimbal_bridge.py --out outputs/gimbal_open_lower_repeat
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/check_native_yoke_assembly.py \
 --gimbal-dir outputs/gimbal_open_lower_repeat --out outputs/gimbal_open_lower_assembly_repeat
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/sweep_native_yoke_gimbal.py \
 --gimbal-dir outputs/gimbal_open_lower_repeat --out outputs/native_yoke_gimbal_sweep_repeat
```

下側の横連結を除いたため剛性・応力の再評価が必要。ケース固定ねじ、支持荷重経路、連続掃引、公差・変形も未検証。関節限界や凍結モデルは変更しない。
