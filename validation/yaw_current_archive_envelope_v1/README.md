# 最新支持部候補と保存荷重全体の比較

## 結論

ねじ逃げ付き横リブ候補は引き続き未成立。旧形状で選んだ荷重1例だけを改善の判断に使うと、現在形状により厳しい荷重を見落とす。
38ケース・266,000時刻を六つの単位荷重応答から上界評価し、各ケースの変位上界最大時刻を直接重ね合わせた。右側荷重・3.020秒の変位 **0.220130 mm** は従来比較荷重の同じ3 mmメッシュ結果 **0.199283 mm** より10.46%大きく、既存の暫定変位配分0.2 mmを超える。

- 全時刻に対する三角不等式の上界は0.319457 mm。これは実際の最大変位ではない。
- 0.220130 mmも全時刻の厳密最大ではなく、選んだ38時刻の最大であり、全時刻最大の下界。
- 旧比較荷重の重ね合わせは既存直接解析と相対差1.45e-15以内で一致。各単位解析の力・モーメント、残差、エネルギーを検査した。
- 旧比較荷重では別途2 mmメッシュでも0.203709 mmで不合格。今回の新しい荷重での細分化は行わない。まず形状・荷重経路の判断を変える根拠を得ることを終了条件とした。

## 評価範囲

最新候補STEP、Z89の荷重面、理想的な後部固定、仮定E=1120 MPa・ν=0.35の線形等方解析。右荷重を対称変換して左形状に適用した。実際の積層材料、締結接触、座屈、疲労を保証しない。応力上界は参考値であり、旧スクリプトの5.6 MPaを認証済み材料許容値として使わない。変位判定を通すための基準変更はない。

保存荷重には最新CADの質量変更が未反映で、実機動作全体の保証ではない。次の候補比較には少なくとも従来荷重と今回の荷重を含め、最終候補では現行質量に更新した支持・旋回・停止の荷重集合を検証する。#5の強度・締結・座屈・動作干渉の完了条件を置き換えない。

## 再現

リポジトリルートで、未使用の出力ディレクトリを指定する。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --current-shelf --step validation/yaw_crossweb_screw_relief_v1/left_yaw_fixed_support.step --out /tmp/yaw-archive-reproduction
.venv-engineering/bin/python software/sim/structural/compare_yaw_archive_envelope.py --envelope /tmp/yaw-archive-reproduction --comparison-plan validation/yaw_shelf_compliance_v1/plan.json --direct-report validation/yaw_crossweb_screw_relief_deformation_v1/report.json
```

入力SHAはplan.json、単位応答の釣合いはunit_0〜5.json、ケース別結果はreport.json、直接解との比較はcomparison.json。大きな再生成可能メッシュ・単位応答配列・時系列上界配列はGit追跡対象外。
