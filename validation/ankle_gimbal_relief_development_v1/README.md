# 足首フレームの逃げ形状候補

脚長・軸位置・外接寸法を増やさず、下側横桟を前へ0.8 mm・上へ1.2 mm移動し、上側後端をz=16.4 mmまで切り下げた。下側横桟は2.4 mm厚を維持。最終形状は左右とも単一有効ソリッド。ブーツCADは変更しない。

局所11姿勢（0、±0.24/0.28/0.30/0.32/0.34 rad）のフレーム対最小隙間:

|候補|最小隙間 mm|結果|
|---|---:|---|
|v1|0.0394|上端の逃げ範囲不足、最接近が隣接縁へ移動|
|v2|0.3000|旧横桟の一部が残り、隙間不足|
|v3|0.5397|下端改善、上端の逃げ深さ不足|
|v4|0.9065|フレーム対のみ離散姿勢の0.9 mm基準を満たす|

v4でも足ヨーク対モータ軸包絡体は0.88459 mmのままで、全体基準は不成立。さらにフレーム対の0.9065 mmは公差0.4 mmを差し引くと0.5065 mmしか残らず、弾性変形・角度間の掃引余裕は未計上。可動域拡大、強度成立、製造承認を意味しない。

旧横桟を十分除去できなかったv2を含め、形状・生成器・失敗結果を保存した。v1～v3の生成器は各cad/generator.py、v4はsource_snapshot/relieve_ankle_gimbal.py。旧版生成器を実行する際は元のsoftware/sim/structural配置へ戻す隔離作業ツリーを用いる（リポジトリ位置解決がその配置に依存する）。

v4再現:

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/relieve_ankle_gimbal.py --out outputs/ankle_gimbal_relief_repeat
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" \
 .venv-engineering/bin/python software/sim/structural/screen_ankle_roll_cad.py \
 --gimbal-dir outputs/ankle_gimbal_relief_repeat --out outputs/ankle_roll_relief_repeat
```

残課題: 軸・軸受・締結の実構成、変更フレームとモータの固定側部品間確認、変更後強度・座屈、全姿勢の連続掃引と変形余裕、CAD・質量・衝突モデルの更新。ソフトの関節限界は変更していない。
