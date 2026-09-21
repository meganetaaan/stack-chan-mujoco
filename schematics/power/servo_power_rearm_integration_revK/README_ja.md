# 小容量バイパス部品の統合

既存選定表 manual_rearm_capacitors.json とメーカー資料を照合し、未反映の17箇所に GRM31C5C1H104JA01L を反映。既存PG回路の4個と合わせて21個となる。94部品・308ピンの接続は変更していない。candidate_bom.csvはこの統合候補の全参照番号を含み、未確定行もそのまま残す。購入・製造用の確定BOMではない。

出典：https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM31C5C1H104JA01-01A.pdf （2026-06-30、2〜3ページ）。100 nF、初期±5%、50 V、C0G、1206。通常3.6 Vまでの比較は電圧定格内。初期容量下限95 nFは全条件の実効容量保証ではなく、100 nF以上の最小容量要求を満たすとの主張でもない。

再現：

```sh
python3 software/sim/circuits/integrate_monitor_bypass.py --out /tmp/monitor-bypass-integration
```

検査条件は対象17参照がLOGIC3V3またはSTOP_AUX3V3とGND間の100 nF用途であること。配線・部品数の同一性と、大容量入力/出力コンデンサおよびゲートコンデンサが無変更であることを確認した。

1206の配置面積・接地経路・高周波インピーダンスはPCB設計で確認が必要。大容量品の実効容量・ESR・レギュレータ安定性、全電源過渡・故障試験は未確認。これらを小容量部品の選定で完了扱いにはしない。

## 出力容量の要求出典訂正

C_STOP_OUTの公称4.7 µFと実効2.2 µFの設計目標は維持。TI資料8.1.1が3.3 V出力に示す安定範囲は実効1.5〜47 µF、ESR 0〜0.2 Ωであり、旧文の「2.2 µF以上がTI要求」は誤りだった。要求文のみ訂正し、値・接続・型番未選定状態は変更しない。詳細と部品系列候補は `schematics/power/stop_output_capacitor_requirements.json`。
