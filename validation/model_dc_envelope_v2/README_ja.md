# DCモデル包絡の再現性修正

v1では記録との照合結果を生成後に追記していたため、掲載コマンドだけでは
report.json全体を再生成できなかった。v2では左右旋回の照合を生成器へ統合した。
関節数・機種数はjoints.jsonから取得し、電流列と軸名を対応付ける。
合計だけでなく、各軸の正負の電流包絡を全保存時刻で検査する。
入力データと軸定義のハッシュを結果に保存する。

結果は片脚4.917A、全身9.834Aで変更なし。物理的保証への拡張は行っていない。
式と限界の説明は../model_dc_envelope_v1/README_ja.mdを参照。

リポジトリルートで実行（NumPyが必要）：
```
.venv-engineering/bin/python software/sim/circuits/derive_model_dc_envelope.py --out NEW_DIRECTORY
```

旧v1は履歴として保持する。v2生成器は左右対称構成を前提とし、
機種数が左右非対称になった場合は停止して個別包絡の実装を要求する。
