# 補強ヨー支持部の全記録荷重評価

背面壁8 mm、取付座半径6 mm、リブ厚5 mmの候補を対象に、EPIC #4から保存した266,000組時刻のヨー荷重を評価する。
以前の全荷重評価と同じ材料仮定（E=1,120 MPa、ν=0.35）、取付座4面の理想固定、変位0.2 mm・応力5.6 MPaの基準を用いる。
入力形状は `validation/yaw_back_reinforcement_development_v1/yaw_back_reinforced_v2/left_yaw_fixed_support.step`。

## 全時刻を覆う上限

まず[単位応答の三角不等式](YAW_LOAD_BOUNDS_DEVELOPMENT_ja.md)により全記録荷重の上限を算出する。
この上限が基準を超える場合は、荷重空間を分割して上限を絞る。
各荷重群の成分ごとの最小・最大の中点を中心荷重cとし、全節点・全積分点で中心荷重の応答を重ね合わせで求める。
任意の群内記録荷重wについて、応答ノルムは次で抑えられる。

`応答上限 = 中心荷重の最大応答 + max(群内のw) Σ |w_i − c_i| × 単位応答iの最大値`

変位ノルム、最大絶対主応力（対称テンソルのスペクトルノルム）、von Mises応力について別々に適用する。
中心が実際の記録荷重である必要はないが、線形弾性であることが前提。
上限を満たさない群は応答係数で重み付けした荷重幅が最大の軸に沿って二分する。
全ての記録時刻がちょうど一つの終端群に所属することを検査し、群ごとに包含数・荷重範囲・中心・応答上限を保存する。
単一時刻まで分割しても基準を超える場合は不合格として記録する。

この処理は時刻の間引きや、代表時刻だけによる合格判定ではない。ただし記録時刻間の運動や、記録にない負荷は含まれない。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --step validation/yaw_back_reinforcement_development_v1/yaw_back_reinforced_v2/left_yaw_fixed_support.step --out outputs/yaw_reinforced_bounds_new
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/certify_yaw_load_clusters.py --bounds outputs/yaw_reinforced_bounds_new --out outputs/yaw_reinforced_clusters_new
```

## 評価範囲

初回全荷重評価は3 mmメッシュ。以前に実施した一荷重のメッシュ収束を、全荷重の収束に読み替えない。
右支持部は鏡映対称を仮定する。実際の背面構造、締結接触、異方性、座屈、疲労、クリープは引き続き未検証。
追加質量を反映した負荷再計算と全身干渉も必要であり、今回の評価だけでIssue #17・#18をクローズしない。

## 結果

|評価|変位上限 mm|最大絶対主応力上限 MPa|判定対象|
|---|---:|---:|---:|
|3 mmメッシュ・単純上限|0.196694|3.99171|266,000組時刻|
|2 mmメッシュ・単純上限|0.1999993|3.81822|266,000組時刻|
|2 mmメッシュ・中心荷重による上限|0.1839395|3.81822|266,000組時刻|

2 mmの単純上限は0.2 mmに極めて近いため、計算上の余裕を確認する追加評価として基準を5%厳しくし、変位0.19 mm、応力5.32 MPaを実行前に設定した。
元の基準を緩めたものではない。中心荷重の評価が必要だった4荷重群を含め、計38群がこの追加基準を満たした。
今回の実荷重では群の二分まで進む必要はなかった。各荷重群の所属ラベルにより266,000組全ての包含を確認した。
von Mises応力上限は3.11250 MPa。

単純変位上限の3→2 mmの差は約1.68%、応力上限の差は約4.35%。これは上限指標の比較であり、全負荷の全節点・全積分点の場が収束した証明ではない。
基準内を確認したのは両メッシュの線形解析モデルである。実接合、材料・質量の仮定、形状変更後の負荷は未検証のまま。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/bound_yaw_loads.py --mesh-mm 2 --step validation/yaw_back_reinforcement_development_v1/yaw_back_reinforced_v2/left_yaw_fixed_support.step --out outputs/yaw_reinforced_bounds_2mm_new
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/certify_yaw_load_clusters.py --bounds outputs/yaw_reinforced_bounds_2mm_new --out outputs/yaw_reinforced_clusters_2mm_new --reserve-fraction .05
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/check_load_certificate.py --out outputs/load_certificate_check_new
```

最後のコマンドは既知の相殺例と不合格例による算法確認。変位、主応力、von Mises応力の相殺、重複荷重を含む二分、全所属、実際に基準を超える単一荷重の不合格判定を確認する。
この確認用の不合格荷重は意図した結果であり、ロボットの解析失敗ではない。
全記録は `validation/reinforced_all_loads_development_v1/`。締結工具の未達は [REINFORCED_FASTENERS_ja.md](REINFORCED_FASTENERS_ja.md)を参照。
