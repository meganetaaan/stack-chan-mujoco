# 外面固定時の内部メッシュと変形エネルギー

plan.jsonのcases順に元の粗い内部、内部目標0.125 mm、0.08 mmを比較する。各メッシュのファイル名は共通の全体サイズ0.5 mmであるため、結果のmesh_mmだけでは内部サイズを識別できない。rowsは各ケースのboss、spacerの順で出力する。

全要素の弾性エネルギーを体積積分し、保存された最終接触力・外力・拘束力と変位の仕事を独立に照合する。許容差1e-6 Nmmは実行前にplan.jsonへ保存。エネルギー差は診断値であり、応力10%・変位5%の収束基準を置き換えない。

解析結果が全ケース揃った後、リポジトリルートで実行する。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_rounded_elastic_energy.py --source validation/sole_spacer_interior_energy_v1
```

既定の従来3ケースでも変更後のスクリプトを実行し、既存report.jsonと同一の結果を確認した。新しい内部細分化のreport.json生成までは本比較は未完了。
