# 出力コンデンサ動的モデルの適用範囲

Murata HSPICEライブラリ26.06（提供ページ更新2026-08-27）を取得し、対象GRM31CR71H475KA12のモデルが含まれることを確認した。モデル生成日は2026-06-02。ヘッダの範囲は100 Hz〜6 GHz、−55〜125°C、DC 0〜50 V、小信号。大信号起動波形や部品ばらつきの保証モデルとは扱わない。

提供ページ：https://www.murata.com/tool/data/librarydata/library-hspice
アーカイブ：https://www.murata.com/-/media/webrenewal/tool/library/hspice/download/murata-lib-hspice-d-mlcc-2606.ashx?cvid=20260827010000000000&la=en-us

該当モデルはHSPICE暗号化形式。この環境のPATHにHSPICEはなく、実行結果は得ていない。復号や他形式への推測変換は行わない。モデルは製品特性確認・回路シミュレーション用に提供され、無保証かつ無断再配布不可。公開リポジトリにはモデル本体を保存せず、ハッシュと確認手順を保存した。

再現は提供ページの条件を確認して取得したアーカイブを指定する：

```sh
python3 software/sim/circuits/inspect_stop_cap_model.py --archive /path/to/download.zip --out /tmp/stop-cap-model-scope
```

この検査はモデル収録とヘッダ確認のみ。Ceff・ESR・安定性の試験ではない。公称仕様からの追加計算は終了し、候補を残す。今後このモデルを使う条件は、対応シミュレータが利用でき、他候補との採否判断に小信号特性が必要な場合に限る。取得できたことやシミュレーション一致を保証限界の代用にはしない。

次の電源設計は、停止電源の負荷合計・発熱と入力保護の成立条件を確認する。コンデンサ未確認事項を理由に、それらの机上設計まで止めない。
