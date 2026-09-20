# 回路シミュレーション

電源・保護回路解析（EPIC #6）の配置先。入力負荷はアクチュエータ解析から渡す。
結果は `../integration/result_bundle.py` の共通形式で保存し、推定値/実測値を区別する。
このディレクトリの存在は回路解析完了を意味しない。

開発中の電源系は[結合試行](../../../docs/prototype/engineering/COUPLED_POWER_ja.md)を参照。補助電源と再起動は[起動順序](../../../docs/prototype/engineering/AUX_SEQUENCE_ja.md)、回生側は[ゲート保持](../../../docs/prototype/engineering/STARTUP_HOLD_ja.md)に記録している。いずれも行動モデルを含む開発段階で、EPIC #6完了や製造承認を意味しない。
