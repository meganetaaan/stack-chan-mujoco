# 足裏保持突起の前側位置修正

前側突起をx=24から18 mmへ移動、後側x=-16 mmを維持。ヨーク穴も追従。足裏外形・接地面高さは維持。左右とも有効な単一ソリッドで、下方挿入5姿勢・横移動5姿勢におけるヨーク/ブーツとの重複はなし。

前案のx=8/6 mm移動時のブーツ干渉を解消した。ただし有限姿勢だけの検査で、連続経路、公差、サーボ/フレーム/配線、工具アクセスの証明ではない。滑り戻り防止ロックはまだないため保持完了とは扱わない。

次は取り外し可能な固定ねじなどで移動を拘束し、その固定部・傘部・ヨーク断面の強度、保持後の遊びを評価する。穴追加を含むヨーク全体解析も必要。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/build_sole_retention.py --front-x-mm 18 --out outputs/retention18_repro
.venv-engineering/bin/python software/sim/structural/build_keyhole_sole_retention.py --retention-dir outputs/retention18_repro --out outputs/keyhole18_repro
```

実際の候補組合せはretention内のsole_TPUとkeyhole内のfoot_yoke。retention内のfoot_yokeは加工途中形状。現候補は製造リリース前。
