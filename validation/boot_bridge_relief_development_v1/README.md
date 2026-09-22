# ブーツ上側横桟逃がし候補：不合格

足首ロール座標の x=[−21.3,−10.7], y=[−32,32], z=[15,45] mm に局所開口を設けた。左右とも有効な単一ソリッドで、除去体積は約430.948 mm³。z≤10 mmの下部形状は体積比較の数値精度内で維持した。外形寸法や脚長は拡大していない。

最新フレームに対する±0.34 rad連続区間の判定を試みたが、左+0.34 / 右−0.34 radで隙間0.906500256 mmの反例を得て停止した。事前基準1.1 mmに不合格。全範囲の最小値を証明した結果ではない。上側横桟近傍の開口だけでは不足し、別の接近位置を特定する必要がある。

開口端の丸み、剛性・強度、製造性、全構成部品との干渉は未検証。この候補を製造用設計として採用しない。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/relieve_boot_bridge.py --out outputs/reproduce_boot_relief
.venv-engineering/bin/python software/sim/structural/certify_native_yoke_gimbal.py --gimbal-dir validation/native_yoke_gimbal_wider_relief_v1/cad --moving-dir outputs/reproduce_boot_relief --moving-part boot_shell --out outputs/reproduce_boot_clearance
```

出力先は未作成ディレクトリを使用する。判定失敗はreport.json内に記録され、プロセス終了コードのみでは合否を判断しない。スナップショットは結果取得後に説明文だけ修正しており、判定計算は同一。
