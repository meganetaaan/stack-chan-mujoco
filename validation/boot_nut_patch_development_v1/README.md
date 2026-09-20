# ナット実接触範囲のメッシュ分割

左後部ナット座の局所モデルに4×4 mmの角ナット面を刻み、実際の穴を除いたnut_bearing面を定義した。体積は変更せず、接触面CAD面積11.845243716 mm²を確認。3メッシュの面積誤差はそれぞれ約0.225%で事前基準1%以内。pad_bottom面も物理グループとして保存した。

従来のナット空間底面全体への荷重拡張を外し、実接触面へ荷重または接触条件を与える準備である。これは表面分割とメッシュ品質の検査で、まだ接触・離間を解いていない。構造合格や製造承認ではない。

初回はメッシュ生成後のJSON保存でnumpy.bool型を処理できず停止。明示的なbool変換を加えて新規出力先へ再実行し、正常終了を確認した。初回の生成物を成功証跡として扱っていない。

## 再現

```sh
export LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu"
.venv-engineering/bin/python software/sim/structural/mesh_boot_nut_patch.py --out outputs/reproduce_boot_nut_patch
```

未作成出力先を指定。局所モデルはvalidation/boot_nut_seat_fe_development_v1/local_seat.stepを使用。全メッシュ、事前条件、面積・体積保存の結果を保存した。
