# P2150R保護付き電池の公称配置

メーカー最大径/長さの円柱を旧電池中心[29,0,80]mm、軸Y方向へ置き、統合ヨーv4固定52部品とTab5を個別照合した。

- 53形状との体積重複0。
- 最小公称距離6.600000mm。
- 保護付き電池外形のみ。接点・保持具・配線・取り出し空間・公差・変形は含まない。
- 質量70gはメーカー記載重量で最大保証ではない。MuJoCo質量や正式トレイへの反映は未実施。

再現（リポジトリルート、CadQuery環境）：

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_direct_cell_package.py --spec validation/direct_cell_p2150r_v1/cell_candidate.json --out /tmp/p2150r-package-recheck
```

出力先は未作成のディレクトリを指定する。成立する配置を探す走査は行わず、既存中心での1回の検査を終了条件とした。外形を大きく変えずに比較できることの局所証拠であり、組立・保持・電源性能の合格ではない。
