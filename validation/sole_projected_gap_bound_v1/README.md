# 接触積分点間の隙間監査

最初に `sole_projected_gap_audit_v1` で頂点・辺中点を評価し、積分点最大食込み3.74808e-6 mmより大きい4.71041e-6 mmを外周頂点で確認した。

さらに初期平面上のmaster/slave三角形の交差多角形を作成した。P1変位の鉛直投影隙間は各交差領域内で一次関数になるため、頂点で最小となる。685交差領域を評価し、同じ最大食込み4.71041e-6 mmを得た。各slave三角形の面積を交差領域が覆う誤差は最大1.54e-13で、事前1e-8以内。既存の数値食込み上限0.01 mmも満たす。

これは初期座標・鉛直法線・小変位・P1三角形面のモデルに限定した隙間評価。CAD曲面と平面近似の差、有限回転・横すべり・接触圧収束・実接合強度の証明ではない。ペナルティ法なので微小な貫通は残り、ゼロ貫通を主張しない。浮動小数点のクリッピングであり、区間演算による厳密証明でもない。

縁落とし面の根元近傍における微小な接触領域を、現在の3点積分が十分に積分できるかは別途検証する。元の圧力非収束を解消した扱いにはしない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/audit_projected_contact_gap.py --out outputs/sole_gap_samples
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/bound_projected_contact_gap.py --out outputs/sole_gap_bound
```

入力は保存済み `sole_projected_contact_probe_v1/fields.npz` と `sole_extended_contact_mesh_v1`。最初の多角形監査はJSON保存時にnumpy.bool_の直列化で失敗した。Python boolへ変換後に再実行した結果をcompletedへ保存し、元の事前planも残した。依存ライブラリshapelyが利用できなかったため、凸三角形の半平面クリッピングを実装した。
