# Tab5対枠ねじと頭部座ぐり候補

NBK SLH-M3-8を4本配置するため、枠に直径6 mm、X46.3〜48.3 mmの座ぐりを追加。頭部座面を48→48.3 mmへ移した。枠から154.193 mm³を除去し、単一の有効ソリッドを維持。外形・脚長は変更しない。

[NBKメーカー寸法](https://www.nbk1560.com/products/specialscrew/nedzicom/spacesaving/SLH/SLH-M3/SLH-M3-8/)：M3×0.5、首下8 mm、頭径5.5 mm、高さ2 mm、六角二面幅2 mm、公称質量0.62 g/本。4本で2.48 g。表の最大締付けトルクを樹脂/Tab5の組立トルクへ転記しない。

初案v1は頭部が枠へ干渉したため不採用。v2はTab5以外の既存部品との公称体積干渉なし。頭部から固定殻まで0.3 mmを確保したが、公差や変形を引いた余裕ではない。座ぐり径6 mmと位置は設計仮定。

Tab5公称背面X52に対し先端X56.3で、侵入量4.3 mm。**有効雌ねじ深さ、底付き余裕、ねじ/枠の公差、必要掛かり長さは未確定。M3×8の購入/組付け承認ではない。** メーカー図面のM3*10は10mm深さの意味にしない。メーカーSTLからねじ強度・有効深さを推測しない。

簡略Tab5モデルとねじは各10.579 mm³交差する。簡略穴R1.45とM3外径の相違を含み、実ねじの干渉とも適合とも判定できない。Tab5内部への接触も未検証。

座面には残厚3.7 mmの公称パッドが残るが、薄肉外周・座面圧・締付け保持・熱圧入インサート保持・工具経路は別途判断する。枠は圧入後表示用近似で、現時点のcarrier_installed_approximation.stepを造形データとして使わない。造形用枠・全体アセンブリ・質量台帳の正式指し先は未更新。製作HOLD、#17/#19/#20未完。

再現：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_tab5_frame_screws.py
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_tab5_frame_screws_v2.py
```
