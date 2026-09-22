# 丸み候補の局所細分化メッシュ

前回curved_meshは接触面約53万三角形まで増えた一方、頭部座面の1%面積基準を満たさなかった。今回、曲率分割を32から16、円周最小分割を32から64へ変更し、境界の細かいサイズを面内部へ延長する設定を無効化。形状、荷重面、1%基準は変更しない。

結果: 最大面積誤差は丸み面0.421422%、頭部座面0.271739%。接触面の一致を含め既存メッシュ判定を達成。接触三角形は片側2,010個。形状面積の確認であり、応力・接触圧の収束を証明しない。境界付近の要素品質と応力収束は接触解析で別途確認する。

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_matching_sole_spacer.py --curvature-points 16 --circle-points 64 --no-boundary-extension --spacer-step validation/sole_rounded_edge_candidate_v1/cad/spacer.step --contact-extensions --optimize-tets --fixed-anchor-points --mesh-mm 0.5 --out outputs/sole_rounded_local_mesh
```

既定設定は従来通り。新設定は明示的に指定。丸みR0.05の製造公差・材料・締結条件は依然候補段階。
