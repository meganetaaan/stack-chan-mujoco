# 補強支持部の締結・工具アクセス検査

背面壁を8 mmにした支持部について、M3ねじ8本、座金16枚、ナット8個、後方六角レンチ・前方ナットドライバーの包絡を出力した。
ねじの候補系列は [Bossard BN 3](https://www.bossard.com/us-en/eshop/screws-and-bolts-with-internal-drive/hex-socket-head-cap-screws-fully-threaded/p/3/)（ISO 4762、鋼8.8、全ねじ）。
個別の注文番号・全公差を確定したBOMではない。頭径5.5 mm、頭高3 mm、座金外径7 mm・厚0.5 mm、ナット包絡径6.4 mm・厚2.4 mmは呼び形状。
ナットは外接円筒としてモデル化し、ねじ山の噛合いは干渉検査に含めない。

## 結果

M3×20 mmでは積層13.9 mmに対して先端が6.1 mm余り、左右各1本の先端が現在のDC-DCコンバータ予約形状と約8.17 mm³重なる。
M3×16 mmへ変更すると、呼びの余りねじ長2.1 mm（4.2ピッチ）を残し、この2か所の交差は解消した。
ただし積層公差、先端面取り、不完全ねじ、締付け保持は未評価。最終部品選定時に有効ねじ掛かりを再計算する。
電源部品の形状が今後変わるため、現在の予約形状との確認だけで最終搭載を承認しない。

どちらのねじ長でも、外径8 mm・長さ25 mmと仮定したナットドライバーの進入包絡は、組立済みのヨーモーター・カップリング・コンバータと計10か所で交差する。
支持部のリブにも接するため、公差分0.4 mmと必要隙間0.5 mmを満たしていない。モーターを後から組むだけではリブ側の問題は解消しない。
工具進入条件の見直し、取付穴位置やリブ形状の変更、またはナット保持構造を設計してから組立性を再評価する。
後方六角レンチ包絡には今回の対象部品との交差は見つからなかったが、全脚・配線は含まない。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_reinforced_fasteners.py --out outputs/reinforced_fasteners_20_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_reinforced_fasteners.py --out outputs/reinforced_fasteners_16_new --bolt-length-mm 16
```

干渉判定は交差体積0.01 mm³超。工具は必要隙間0.5 mmに加え、双方の公差合計0.4 mmを差し引く。
計画、呼び寸法CSV、全包絡STEP、交差する部品と体積を保存する。組立手順・製造可能性の完了判定は保留。
