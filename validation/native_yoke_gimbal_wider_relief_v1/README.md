# 足首下側横桟の追加切欠き候補

従来候補の最小隙間は左右とも0.792501574 mm。左−0.34 radの最近点はロール座標でヨーク(-27,-12.752865,-9.064289)、フレーム(-27,-13.5,-8.8) mm。右は鏡像。下側横桟の残存端部が接近箇所だった。

切欠き幅を30.9から32.1 mmへ拡大し、各側0.6 mm追加除去した。両側とも有効な単一ソリッド、中立隙間3.3 mm。±0.34 radを0.02 rad刻みで検査した70姿勢の最小隙間は1.192719433 mm、重なりなし。試験前の基準1.1 mmをこの離散的な部品対検査では満たした。

これは連続軌道の証明でも製造承認でもない。ブーツと上側横桟の隙間不足、実サーボケースとの余裕、締結部品、たわみ、切欠き後の強度は未解決。全機構の合格を意味しない。

## 再現

リポジトリルートで engineering 環境を使用する。出力先は未作成のディレクトリを指定する。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/open_lower_gimbal_bridge.py --out outputs/reproduce_wider_gimbal
.venv-engineering/bin/python software/sim/structural/sweep_native_yoke_gimbal.py --gimbal-dir outputs/reproduce_wider_gimbal --out outputs/reproduce_wider_sweep
```

使用スクリプトのスナップショットと入力SHAは同梱。original_nearestは変更前の不合格位置を保存する。
