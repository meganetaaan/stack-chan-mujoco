# 対応PSpice環境用の起動プローブ

111部品候補の電源枝からTPS26601とTPS709の接続、抵抗6本とバイパス4個を生成。`startup.cir` は未実行で、回路の合格証拠ではない。物理パッケージ番号とSPICEモデル端子順は異なるため、取得したモデルのヘッダ順へ明示変換した。

モデル取得先:
- https://www.ti.com/lit/zip/slvmby3 （TPS26601_TRANS.LIB、暗号化PSpice版）
- https://www.ti.com/lit/zip/sbvm571 （TPS70933_TRANS.LIB、非暗号化版）

取得したLIBを同じ作業ディレクトリに置き、対応PSpice環境で実行する。モデルのハッシュは `logic_vendor_model_probe_v1/report.json` 参照。モデル本体は公開リポジトリへ複製していない。

```sh
.venv-engineering/bin/python software/sim/circuits/export_logic_pspice_probe.py
```

このプローブでは12.6V/100µsの理想入力、165Ω負荷、27.975µFの理想出力容量を使う。実際の全ロジック、シーケンサ、容量のESR・温度は含まない。まず解析が10ms終端まで到達し、電圧/電流波形を出力できることが終了条件。出力3.3V付近への到達だけで保護や最悪条件を合格にしない。合格基準や実部品値を変更して計算を通さない。

TINA代替経路も確認した。 https://www.ti.com/lit/zip/slvmby4 のLIBは先頭にEncrypted Libraryを持つため、ngspiceへの直接移植は不可。ハッシュと限定した環境探索結果をtina_review.jsonに保存。対応ソフトがこの機械のどこにも存在しないとまでは断定しない。

回路条件を保持したGear2解法の追加試行は別ログに保存する。実行環境の問題と実回路の未成立を混同しない。この経路が未実行でも、メカやデータシートに基づく設計判断は継続可能。

Gear2は55秒の実行上限で終了コード124となった。起動波形の完走は確認できず、改善成立とはしない。回路条件は先行プローブと同じで、変更は `.options method=gear maxord=2` のみ。追加の数値解法探索はここで止める。
