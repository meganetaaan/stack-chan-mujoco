# 足部の一致接触メッシュ診断

BOOTとYOKEを同時に分割し、接触面480三角形を一致させた後、部品ごとに節点を分離した。接着拘束ではない。元STEPの体積と荷重面積を検査した。

0.5 mm、20 N、ペナルティ1e6 N/mm³で最大接触圧2.156692 MPa。別々に生成した同サイズのメッシュでは5.524037 MPa。変位変化は1%未満。内部要素も変わるため接触面だけの効果とは断定しない。単一サイズであり収束・実接合強度は未確認。微小な負圧も出力のまま保存する。

## 再現

リポジトリルートでエンジニアリング環境を使用する。出力先は未作成の場所を指定する。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_boot_yoke.py --out outputs/matching_repro_mesh
.venv-engineering/bin/python software/sim/structural/probe_boot_yoke_contact.py --mesh-mm 0.5 --boot-mesh-dir outputs/matching_repro_mesh/boot --yoke-mesh-dir outputs/matching_repro_mesh/yoke --out outputs/matching_repro_contact
.venv-engineering/bin/python software/sim/structural/evaluate_boot_yoke_contact.py --source outputs/matching_repro_contact
```

DAT/FRDは必要に応じgzipで可逆圧縮。元データのハッシュはcompression.jsonに記録。次は一致メッシュでサイズを変更し、変位5%・最大圧力10%の既存収束基準を検証する。
