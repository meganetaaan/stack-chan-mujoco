# 電源配置の個別ソリッド干渉検査

## 判定

統合配置revAの8群について、群をまたぐ28組を385組のソリッド対に展開した。
全対で交差体積は0。したがって従来の公称非干渉という配置判断は維持する。
形状・寸法・判定しきい値は変更していない。

この再検査は、Tab5近傍部品の照合でcompound全体への差集合が意図しない結果を
返したために実施した。重なりを含む組立を融合済み形状とみなさず計算する。
`comparison`は旧結果と新結果、`solid_pairs`は各個別判定を保存する。
入力ハッシュ不一致では停止し、別版のCADを混ぜて判定しない。

対象は群間のみ。ヨー組立内部のねじ接触・締結、全身運動、配線・UBEC固定具・
保護基板・公差・たわみ・放熱・実ベルト留め具の成立を証明しない。
接触距離0の意図した着座を、可動部に必要な隙間として合格扱いしない。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_packaging_solid_pairs.py --report board/mechanical/prototype/power_packaging_revA/report.json --out /tmp/power-packaging-solid-recheck
```

出力先は未作成ディレクトリを使う。元の統合STEPを作り直す必要はない。
今後配置を変更した際は、新しい統合配置レポートに対してこの検査を行う。
