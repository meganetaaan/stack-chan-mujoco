# 基板上の手動許可ボタン候補

B3U-1000P（SPST-NO）と3 kΩプルアップ、非反転Schmitt受信74LVC1G17GVを候補とする。生信号は解除確認AND入力へ、MAX6816出力は従来のデバウンス経路へ渡す。ボタン押下を電力停止入力として使う設計ではない。

目的は接点の電流仕様を満たしつつ生信号を読める構成の選定。終了条件はメーカー仕様での定常電流比較と、未保護の境界の明示。新しい遅延や接点劣化モデルを仮定した掃引はしない。

[MAX6816](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX6816-MAX6818.pdf)の内蔵32〜100 kΩだけでは、公称電源範囲で接点電流は約32〜106 µA。[B3U資料](https://components.omron.com/us-en/system/files/2023-01/datasheet_pdf/A162-E1.pdf)は10 µA／1 Vを参考最小負荷とするが、今回は定格1〜50 mA・3〜12 Vを比較に使う。総合±1%の3 kΩ追加で、初期接触抵抗と受信漏れを含む接点電流は約1.089〜1.249 mA。電源電圧も定格範囲に入る。3 kΩはCodexの設計選択であり、合格基準を変更したものではない。

B3Uの初期接触抵抗≤0.1 Ω、バウンス≤5 msを参照。電流比較は寿命末期や押下機構の保証ではない。ボタン上面高さは1.6 mm（資料表）、1.2 mmは本体部寸法なので混同しない。正確なフットプリント、押し棒の過押し防止と基板支持は未設計。

[74LVC1G17](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)は入力速度制限のないSchmitt受信候補。ただしBUTTON_RAWへ分岐すると、MAX6816単体の±25 V入力・ESD定格を回路全体の仕様にはできない。今回は同一基板のボタン用候補とし、外部配線コネクタを設けない。保護と基板配置が未確認なのでrevHへ無条件に統合せず、未完事項を残す。ユーザー要求を縮小したのではなく、未指定だったボタンの配置案である。

`python3 software/sim/circuits/check_local_enable_button.py --out /tmp/local-enable-button-review`で再現（新規出力先）。16端点の定常計算のみであり、回路全体の合格ではない。仕様は`schematics/power/local_enable_button_candidate.json`。
