# ヨー支持部の工具アクセスを確保する取付穴配置

前候補では、ナット用工具が支持部リブに接し、モーターを後から取り付けるだけでは必要隙間を確保できなかった。
取付穴の左右位置を中心から±9 mmから±7 mmへ変更する。各穴は2 mm内側へ移動し、穴列間隔は18 mmから14 mmになる。
高さ方向は中心z=70 mmから±12 mmのまま。取付座も穴と同時に移動し、背面カバーは元の穴なしCADから新しい穴位置で生成する。

支持部の外側境界箱・脚長・体積・仮定質量は前候補と同じ。ねじはM3×16 mmを使用する呼び形状で、積層13.9 mm、余りねじ長2.1 mm。
設定は `board/mechanical/engineering/yaw_inset_fasteners.json`。全公差・注文番号・締付け条件を確定した製造BOMではない。

## 工程を区別した評価

組立済み状態では、ナットドライバーとヨーモーター・カップリング・コンバータとの10か所の交差が残る。
一方、次の6部品を取り付ける前の工程では、対象のねじ・座金・ナット・工具の交差と工具隙間不足は検出されなかった。

- 左右のヨーモーターケース
- 左右のヨーカップリング
- DC-DCコンバータ
- TTLインターフェース

この6部品は、解析から理由なく除外した部品ではなく、後工程で取り付ける予定の部品として計画と結果に明記した。
残した部品は支持部、穴あけ後の背面カバー、胴体、Tab5、電池予約形状、電池トレイ。

仮の工程順は、支持部を背面カバーへ締結し、工具を抜いてから上記6部品を取り付ける。
支持部ナットの再締結・交換には逆順の分解が必要になる。実際のモーター取付工具と挿入経路、最終的な胴体への組付け、配線、治具はまだ検証していない。
「静止姿勢でのこの工程の工具進入包絡が成立」と「ロボット全体が組み立てられる」を区別する。

## 締結と強度

新しい穴配置で全266,000組時刻のボルト群を再計算した。
ボルト相当応力上限8.3309 MPa（基準290 MPa）、樹脂面圧0.6263 MPa（仮定基準5.6 MPa）でスクリーニング基準内。
群の基準面を取付座の背面x=-62.2 mmとし、こじり倍率2、等剛性ボルト群、樹脂有効厚8 mmを仮定する。これは締付け保持や接触の証明ではない。

支持部本体は穴位置変更後の形状で、以前不合格だった同一荷重を4・3・2 mmのメッシュで再解析する。
既存の全荷重上限0.184 mmは旧穴配置の結果であり、この変更案へ流用しない。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/reinforce_yaw_back.py --out outputs/yaw_inset_mount_new --rib-thickness-mm 5 --pattern-half-width-mm 7
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_reinforced_fasteners.py --out outputs/inset_fasteners_complete_new --bolt-length-mm 16 --support-dir outputs/yaw_inset_mount_new --pattern-half-width-mm 7
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_reinforced_fasteners.py --out outputs/inset_fasteners_staged_new --bolt-length-mm 16 --support-dir outputs/yaw_inset_mount_new --pattern-half-width-mm 7 --stage before_yaw_and_power
.venv-engineering/bin/python software/sim/structural/check_bolt_group.py --config board/mechanical/engineering/yaw_inset_fasteners.json --out outputs/inset_bolt_group_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/screen_yaw_back.py --step outputs/yaw_inset_mount_new/left_yaw_fixed_support.step --out outputs/yaw_inset_strength_new
```

干渉基準、工具寸法、未検証部品の制限は [REINFORCED_FASTENERS_ja.md](REINFORCED_FASTENERS_ja.md)を引き継ぐ。

## 代表荷重と工具隙間の結果

最終2 mmメッシュで、変位0.16107 mm、最大絶対主応力3.91341 MPa、von Mises応力3.01228 MPa。
最後の2メッシュの差は変位約2.72%、最大絶対主応力約5.52%で、同じ事前基準を満たした。
工具と対象部品の最小距離は1.8 mm（胴体との隙間）。公差合計0.4 mmを差し引いた残余は1.4 mmで、必要な0.5 mmを上回る。
この値は工程で残した部品群の結果である。後工程の部品を取り付けた状態で工具が通るという意味ではない。

## 穴位置変更後の全記録荷重

変更後の形状について、3 mm・2 mmの両メッシュで6単位応答を計算し、全266,000組時刻を再評価した。
荷重群の中心応答と残差上限を使い、元の基準を5%厳しくした変位0.19 mm・応力5.32 MPa以下を確認した。

|メッシュ|荷重群による変位上限 mm|最大絶対主応力上限 MPa|包含時刻数|
|---|---:|---:|---:|
|3 mm|0.189306|4.850986|266,000|
|2 mm|0.180852|4.361972|266,000|

2 mmでは50群に分けて全記録を包含した。3 mmと2 mmで群分割が異なるため、この表の変位上限の差をメッシュ収束や剛性改善の指標には使わない。
代表荷重の実変位は旧穴配置0.14978 mmに対し新配置0.16107 mmと増えている。上限が小さくなったのは上限評価の分割が細かくなったためで、支持部が硬くなったという意味ではない。
単純な応力上限のメッシュ間差は約10.08%であり、全荷重の応力場の収束確認は未完了。両メッシュで応力基準内を包含したことと区別する。

六つの荷重で剛性行列を共用するよう解析器を変更した。同一メッシュの保存済み独立解と、変位・応力・荷重・反力を比較し、全6条件で相対差6×10⁻¹²未満を確認した。
計算対象・拘束・材料・判定基準はこの最適化で変更していない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_shared_factorization.py --reference validation/reinforced_all_loads_development_v1/yaw_reinforced_bounds_v1 --out outputs/shared_factor_check_new
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --mesh-mm 2 --step outputs/yaw_inset_mount_new/left_yaw_fixed_support.step --out outputs/inset_all_bounds_2mm_new
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/certify_yaw_load_clusters.py --bounds outputs/inset_all_bounds_2mm_new --out outputs/inset_all_clusters_2mm_new --reserve-fraction .05
```

3 mm評価は `--mesh-mm 3` と別の出力先で再現する。
証跡は `validation/inset_yaw_assembly_development_v1/`。実行時の `outputs/` 参照は同証跡内の同名ディレクトリに対応する。
実接合・保持・全組立手順・配線・追加質量を反映した負荷の確認が残っており、Issueは未完了。
