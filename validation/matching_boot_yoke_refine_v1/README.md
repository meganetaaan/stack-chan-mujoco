# 一致接触メッシュの細分化

0.5→0.35 mmでBOOT変位4.2123%、YOKE変位0.18094%、最大接触圧6.57776%の変化。事前固定の変位5%・圧力10%基準に合格。圧力2.014830 MPa、BOOT変位0.00262240 mm、YOKE変位0.00502249 mm。

これは仮の締付力20 N、切り出し形状、等方弾性材の数値感度確認。内部応力、安全率、実締付条件、歩行荷重、全体境界条件は未評価であり、Issue #18の強度成立は未証明。

## 再現

リポジトリルートから実行。最初に本フォルダのplan.jsonを新しい出力フォルダへコピーする。モデル・ソルバーは既存エンジニアリング環境を使用。

```sh
mkdir outputs/matching_refine_repro
cp validation/matching_boot_yoke_refine_v1/plan.json outputs/matching_refine_repro/plan.json
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_boot_yoke.py --mesh-mm 0.35 --out outputs/matching_refine_repro/mesh
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.35 --boot-mesh-dir outputs/matching_refine_repro/mesh/boot --yoke-mesh-dir outputs/matching_refine_repro/mesh/yoke --out outputs/matching_refine_repro/contact
.venv-engineering/bin/python software/sim/structural/evaluate_boot_yoke_contact.py --source outputs/matching_refine_repro/contact
.venv-engineering/bin/python software/sim/structural/compare_boot_contact_refinement.py --source outputs/matching_refine_repro
```

大きなDAT/FRDはgzipで可逆圧縮し、元ファイルのSHA256をcompression.jsonに保存。次段階では応力出力・評価を加え、実荷重と締結モデルへ接続する。
