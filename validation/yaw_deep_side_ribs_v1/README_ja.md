# 側面リブを深くする補強候補

既存断面をCADで確認すると、左右の側面リブは各5 mm厚（左支持のY8..13および39..44 mm）。この幅を維持し、X-30..10、Z70..88 mmの直方体を既存リブに一体化して前側の断面を深くした。板ポケット内への追加は行わない。

両側で単一有効ソリッド、外形不変、現行固定組立への追加干渉なし。サーボメーカーCADのケース・コネクタとの追加材料の最小距離は3 mm。配線予約通路の隙間1.3 mmを保持。片側追加体積3024 mm³、仮に密度1.27 g/cm³なら左右合計7.681 gの追加。実造形質量は未確定。

`validation/yaw_deep_side_ribs_motion_v1` はヨーカプラとロール支持部を含め、ヨー±15°を1°刻みで検査。新候補との公称最小距離9.057 mm、角度サンプル間の見落とし上限0.274 mmと既存公差・変形配分0.8 mm控除後7.983 mm。対象は支持部とこの可動部の組のみで、全身・配線・工具を保証しない。変形配分の成立は別途必要。

形状検査通過は製造承認ではない。保存荷重による変形比較は `validation/yaw_deep_side_ribs_fe_v1` に分離。現在のrevBへは未統合。造形方向、根元フィレット、実材料強度・疲労・締結予圧、工具と組立順序、最新質量の荷重更新は未確認。

再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_yaw_deep_side_ribs.py --out validation/yaw_deep_side_ribs_reproduce
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_clearance.py --out validation/yaw_deep_side_ribs_motion_reproduce --step-deg 1 --include-cradle --joint-limits --support-dir validation/yaw_deep_side_ribs_reproduce
```

出力先は未使用のものを指定する。`ribbed_connection` が新候補、`original` は旧MuJoCo参照形状の検査であり現行revBとの比較ではない。
