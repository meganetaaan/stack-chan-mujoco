# CAD再生成と機構候補

`r5a_source/` は提供されたR5-AのCAD・モデル生成ソースを未改変で収録したものです。
`SOURCE_MANIFEST.json` に各ファイルのSHA-256を保存しています。
元の脚設計を再生成するため、内部にR4という名称が残っています。
元ソースの制御・plannerは未検証の低速参照であり、0.10 m/s実機歩行用の制御ではありません。

## 再現環境

CADはシミュレーション用環境から分離します。検査した環境はLinux、Python 3.12.3、
CadQuery 2.8.0 / OCCT 7.9.3.1.1です。依存バージョンは `requirements-cad.lock.txt` に固定しました。
これはpip freeze形式で、パッケージバイナリのハッシュ固定ではありません。

```bash
uv venv --python 3.12 .venv-cad
uv pip install --python .venv-cad/bin/python -r design/requirements-cad.lock.txt
.venv-cad/bin/python build_design.py --out outputs/design_r5a_rebuild
python validation/verify_design_rebuild.py --rebuild outputs/design_r5a_rebuild \
  --out validation/goal_baseline/cad_rebuild.json
```

最後のコマンドはMuJoCo導入済みの環境で実行します。生成先が既にある場合、
生成スクリプトは拒否します。別名の出力先を指定してください。

STEPアセンブリ・試作用STEP/STLは生成先の `cad/`、メッシュ・MJCF・URDF・慣性は
`models/`、部品表は `hardware/parts.csv`、再読込み検査は `reports/exports.json` です。
2026-09-19の再生成では元マニフェストの42資産が全てバイト単位で一致し、
MuJoCoで nq=17、nv=16、nu=10 としてコンパイルできました。
製作公差、締結強度、実機歩行が検証されたことは意味しません。

## 股間隔の候補選定

```bash
.venv-cad/bin/python screen_hip_spacing.py \
  --out validation/goal_baseline/hip_spacing_study.json
.venv-cad/bin/python build_design.py --hip-half-spacing-mm 22 \
  --out outputs/design_r6_hip22
.venv-cad/bin/python check_design_clearance.py --design outputs/design_r6_hip22 \
  --out validation/goal_baseline/r6_hip22_clearance.json
```

最初の検査は**左右脚間だけ**を対象にしたB-rep交差です。元の半間隔19 mmでは
6.5°で干渉が再現し、22 / 25 / 28 mmでは検査した0 / 6 / 6.5 / 10 / 16°で
左右脚間の体積干渉がありませんでした。連続掃引や全関節範囲の保証ではありません。
広げすぎによる横方向の重心移動・必要トルク増を避ける検討の出発点として22 mmを選びます。

候補生成は脚の関節原点、固定クレードル、胴体取付レールを同じ量だけ移動し、
既存のサンプル掃引由来の底面開口も平行移動します。CADから質量・慣性を再計算します。
Tab5と胴体外寸、5軸×2脚、リンク長、足の形状、サーボ選定はこの候補では元設計を使います。
候補の `robot.json` とMJCFはR6実験用IDになり、旧方策のモデル一致検査を通りません。
旧モデルを上書きしたり、既存方策の成功結果を候補へ引き継いだりしないでください。

最後のコマンドは同一リンク・隣接部品を除外せず、胴体も含めて5姿勢を検査します。
生成した22 mm候補では33機械部品の全組合せについて、5姿勢とも0.01 mm³を超える
体積干渉はありませんでした。質量計算値は0.825567 kg、MuJoCoで17/16/10次元として
コンパイルできました。記録は `validation/goal_baseline/r6_hip22_clearance.json` です。
意図した接合面の接触は体積交差でないため除外されます。実ねじ・配線・変形・公差は未検査です。
なお開口は元のサンプル集合の平行移動に限られ、新しい歩容全体の必要開口を保証しません。
MuJoCoの簡略衝突形状も候補について追加検証が必要です。
