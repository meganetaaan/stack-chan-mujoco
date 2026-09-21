# 上面補強を含む統合比較v6

v5の52部品から左右支持部だけを置換し、残り50部品の記録を保持。
変更差分はv5に対する値であり、旧revBとの差分へ二重加算しない。
全1326組の静的比較で、revB比の新規体積干渉フラグ0。
旧来のねじ包絡等の重複は記録として残り、締結成立を意味しない。

固定姿勢・部品順・体積・重心を照合した比較組立であり、動作全域、工具、
全公差、最新電池とTab5、実接触・締結の検証は未完了。
密度未割当ての幾何モーメントを保存。ナットは回転包絡で実質量ではない。
正式版ポインタは変更しない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/integrate_yaw_upper_shelf.py --out /tmp/yaw-v6
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_yaw_integrated_overlap.py --candidate /tmp/yaw-v6 --all-pairs
```
