# ねじ逃げ付き横板の変形：2mmメッシュで未達

既存0.2mm枠、保存荷重、E1120MPa、ν0.35、後端理想固定を維持。3mmで基準内なら2mmを一度追加する事前手順に従った。

3mm: 最大変位0.199282690mm、80655自由度。
2mm: 最大変位0.203708665mm、147819自由度、27383要素。
相対差約2.22%は10%以内だが、2mm結果が0.2mmを超えるため比較条件は未達。3mmだけを採用して合格とはしない。

2mmの自由自由度残差3.66e−11N、外力仕事2.360287442Nmm、ひずみエネルギー1.180143721Nmm。数値釣合いを確認。局所応力の収束を目的に追加細分化しない。

結論: ねじ逃げ前の比較合格は、ねじ逃げ後へ引き継げない。現在案は新規静止干渉を解消したが、変形枠は未達。閾値や弾性率を結果に合わせて変更しない。実材料・締結・最新全荷重の確認も未完であり、製作へ進める状態ではない。

再現:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_yaw_deep_ribs.py --step validation/yaw_crossweb_screw_relief_v1/left_yaw_fixed_support.step --out /tmp/stackchan-crossweb-relief-fe
```

2メッシュで終了。次の検討では全組合せ検査で残ったねじ受け板の12組の重なりの性質も確認し、成立していない締結を理想固定で置換したまま量産/製作判定しない。
