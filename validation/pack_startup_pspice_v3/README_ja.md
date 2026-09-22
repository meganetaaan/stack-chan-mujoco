# 現行インターフェース負荷を反映したPSpice入力

**生成のみ。未実行、起動・保護は未合格。**

196部品v4の制御枝に対応する部分負荷を[予算対応表](../controller_probe_load_v1/README_ja.md)から読み、9 V/12.6 Vの入力を生成。3.3 Vで12.129356 mAとなる等価抵抗を置き、追加100 nF×2も明示した。初期低電圧では抵抗電流が下がるため、一定電流やMCUの起動電流を再現するものではない。部品の起動順序も含まない。

```
python3 software/sim/circuits/reconcile_controller_probe_load.py
python3 software/sim/circuits/export_pack_startup_pspice.py --efuse-zip /path/to/tps26600.zip --ldo-zip /path/to/tps70933.zip --include-current-interfaces
```

モデルはmanifest.json記載のTI配布元から取得し、展開したLIBをデッキと同じ場所に配置する。モデル自体は再配布しない。PSpice実行環境は未確認。既存ngspiceで暗号化モデルを実行できたとは扱わない。

全機ではなく制御枝の互換性・起動確認用。電池PCM、前段保護、全負荷、温度・公差、リセット動作は含まない。旧v1/v2を保持し、現行の部分負荷用入力はv3を参照する。
