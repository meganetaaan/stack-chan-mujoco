# 外付けナットの中立組立空間

外付けナット・10 mmねじ・半径4 mm/上向き20 mmの工具予約空間を、既存のメーカーX330 STEP全構成部品と足首ジンバルに照合した。配置変換はcheck_native_yoke_assembly.pyと同一。メーカーCADと部品マッピングのハッシュ一致・部品数を先に確認。

左右とも全組合せで公称隙間1.1 mm以上、重複0。最小隙間7.4 mm。これは中立姿勢の組立空間で、サーボを取り外さずに組立できる可能性を支持する。ただし工具は実品ではなく予約包絡であり、把持・締付け回転・下側工具経路の完了証拠ではない。

基準1.1 mmは既存の公称隙間スクリーニング（残余0.5＋仮定公差0.4＋仮定変位0.2）を引き継いだ値。実機変位/公差の保証ではない。歩行/停止の全姿勢、ハーネス、変形、ねじ緩み、締付け保持は未検証。#19全体の合格へ拡張しない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_external_nut_servo.py --out outputs/external_nut_servo_clearance_new
```

次は実工具を選び、アクセス包絡の差と締付け手順を確認する。中立空間が十分なため、同じ条件の追加CADサンプルは増やさない。
