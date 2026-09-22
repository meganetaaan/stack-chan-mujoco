# 共通M2ナット16点のメーカー概算重量

ヨー支持8点と電源モジュール支持8点は、選定資料上どちらもBossard1088211（BN109、M2、鋼、亜鉛めっき）。16点を同一品番として照合した。

[メーカー重量計算器](https://website-assets.bossard.com/Weight-Calculator/Weight-Calculator-en.html)の六角ナット・鋼・二面幅4 mm・呼び径2 mm・高さ1.6 mmでは、概算0.150375 g/個、16個で2.405998 g。公開計算モジュールを直接実行した値と、保存した再現計算を1e-12 kg/100個以内で照合した。表示単位はkg/100個で、個当たりkgではない。

これは品番1088211の公称/保証重量ではない。高さのカタログ上限を使っても、計算器の形状・材質係数・面取り/ねじ/めっき条件が概略のため、質量上限にもできない。メーカー自身も初期概算としている。確定台帳のnullは維持し、未知を解消した件数に数えない。今後の影響比較に使える参考値としてのみ保存する。鋼種・強度区分の表記からナット耐力や締付け許容を推定しない。

再現：メーカー公開モジュールをローカルへ取得し、次を実行する。元JavaScriptは再配布せず、URLとハッシュをreport.jsonへ保存。

```sh
.venv-engineering/bin/python software/sim/structural/screen_bossard_nut_mass.py --calculator-js /path/to/data-weight-hexagon.js
```

一次資料：
- [BN109製品群](https://www.bossard.com/ch-en/eshop/hex-nuts/hex-nuts-0-8d/p/109/)
- [計算データと関数](https://website-assets.bossard.com/Assets/js/data-weight-hexagon.js)
- [入力・100個単位の表示処理](https://website-assets.bossard.com/Assets/js/weight-hexagonnuts.js)

残る30部品の確定質量、部品内部の重心/慣性、全身入力は未完。製作HOLD。
