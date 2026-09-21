# 接触ソルバーの解析解チェック

`unilateral_contact.solve`へ実形状で使用していたactive-set計算を共通化。初期隙間にも対応する。別実装だけを試験するのではなく、実形状の診断と同じ関数へ解析解のある問題を入力した。

地盤ばねk、荷重F、接触面積A、ペナルティp、初期隙間g0に対し、非接触ならu=F/k、接触ならu=(F−p A g0)/(k+p A)。圧力は接触時−p(g0+u)、非接触時ゼロ。これを用いて圧縮と離間の混在、初期隙間が閉じない状態、初期隙間が閉じた状態を比較した。さらに平均変位ゼロの2物体へ±Pを与えるケースで、変位±P/(2pA)、圧力P/A、拘束乗数ゼロを確認した。

事前許容誤差1e-10。4ケースすべて一致。離間ケースでは初期接触集合から1点または2点が外れ、2反復で収束。式の符号、初期隙間項、非接触で引張を伝えないこと、平均拘束との連立を確認できた。

実形状0.5 mm最適化モデルも再実行し、保存済みの全フィールドと比較した。最大差0。共通化で結果が変わっていないことをregression.jsonに保存した。

これは代数的な接触コアの検証。有限要素組立、曲面接触、節点面積による圧力近似、有限回転、材料、実接合の強度は検証しない。座面外周圧力のメッシュ非収束は未解決。既存Issueを閉じる根拠ではない。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/check_contact_analytic.py --out outputs/contact_analytic_repro
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/structural/probe_sparse_sole_contact.py --mesh-dir validation/sole_optimized_mesh_v1/mesh --mesh-mm 0.5 --out outputs/contact_shared_repro
```

2つ目のfields.npzの全キーを `validation/sole_optimized_mesh_v1/analysis/fields.npz` と比較し、絶対差最大1e-10以内を確認する。失敗した計算の収束フラグは維持し、反復上限を成功扱いしない。
