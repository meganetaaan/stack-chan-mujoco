# EDA移行用の中間接続データ

`manual_rearm.xml` はKiCadの中間XMLネットリストにあるcomponents/nets構造へ、現行の型番候補と接続を出力したもの。46部品、27ネット、接続端子147点。未接続12端子はreport.jsonへ分離した。出力XMLを読み戻し、全型番・全接続が元の組立と一致することを確認した。

これは `.kicad_sch` 回路図や配線済み基板ではない。基板エディターへの直接インポート可能性も未確認。KiCad CLIがこの環境にないため、アプリでの読込やERCを実施済みとはしない。フットプリント欄は空欄とし、端子番号・ランド寸法の照合なしにパッケージ名だけで自動割当しない。

用途は、次のEDA回路図作成で端子・部品の転記を照合する基準と、XML後処理への入力。起動監視・外部停止・主電力経路の未設計を埋めるものではない。

形式参照：[KiCad公式・中間ネットリスト](https://docs.kicad.org/9.0/en/eeschema/eeschema.html)。再現：`python3 software/sim/circuits/export_manual_rearm_xml.py --out /tmp/manual-rearm-xml-check`（未作成の出力先）。型番BOMの参照ハッシュが現行設計と異なる場合は停止する。
