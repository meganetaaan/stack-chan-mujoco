# 直列保護案の低電圧分圧接続

revAに左右24.9kΩ／10kΩの分圧を追加し、UV入力を未接続ポートから内部ノードへ変更した。計20部品。抵抗品番は未選定で、総合±1%は設計配分。

[LT4363 Rev.C](https://www.analog.com/media/en/technical-documentation/data-sheets/4363fb.pdf)の立上り閾値と入力電流を使う比較では、電源換算の起動閾値4.242〜4.663V。5Vはこの比較上限を上回る。ただし表の標準VCC条件は12Vで、実際の4〜5Vへの適用確認を残す。

ヒステリシス12mVは典型値しかない。これを使った立下り比較は4.201〜4.620Vだが、4Vより前に必ず遮断する保証とはしない。立上りの上下限から立下りの保証を作らない。変換器最低電圧・瞬時低下、抵抗温度/実装変化、停止ドライバ、逆流・回生などは未確認であり、通電・製造承認は保留。

再現：`.venv-engineering/bin/python software/sim/circuits/add_series_clamp_uv.py --out /tmp/series-uv-review`。
