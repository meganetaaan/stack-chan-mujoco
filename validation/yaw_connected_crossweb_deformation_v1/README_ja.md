# 前端横板案：保存荷重の変形比較を通過

事前planの通り、同じ保存荷重、E=1120MPa・ν=0.35、後端理想固定を用いた。レール面のボンド支持や荷重低減を追加していない。3mmメッシュで0.2mm以下なら2mmを一度実行し、両者0.2mm以下かつ相対差10%以下を要求した。

結果は3mmで0.192068116mm、2mmで0.196593827mm。相対差約2.36%で比較条件を通過。2mmでは147333自由度・27361要素、自由自由度残差3.86e−11N、外力仕事2.264988239Nmm、ひずみエネルギー1.132494119Nmm。数値釣合いも通過した。局所応力最大値の収束は合格根拠にしていない。

結論は「この保存荷重・仮定材料・理想固定での変形比較を通過」だけ。0.2mmまでの残りは約0.003406mmと小さい。材料、実締結、初期隙間、全荷重による変動を吸収する保証余裕ではない。#18や製作可の判定には不足する。

事前に決めた2メッシュで停止。次は横板を含む組立経路と動作干渉、全荷重包絡、実材料条件の確認を進める。正式currentは据置き。比較を通すための基準変更は行っていない。

再現:
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/screen_yaw_deep_ribs.py --step validation/yaw_connected_crossweb_v1/left_yaw_fixed_support.step --out /tmp/stackchan-crossweb-fe
```

荷重の出典と入力ハッシュはplan.json、詳細結果はreport.json。メッシュは再生成可能な生成物として公開対象から除外した。
