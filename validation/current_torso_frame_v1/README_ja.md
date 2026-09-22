# 現胴体CADからMuJoCo base座標への対応

**座標単位をmm→mへ換算した後の回転は単位行列、平行移動は0。** 現在の配置規約では、CAD原点が凍結r9モデルのbaseローカル原点に対応する。baseの初期world位置(-0.012127,-0.00000745,0.084582) mを部品重心から差し引かない。

根拠は、凍結XMLのbase直下vis_Tab5が位置0・姿勢指定なしでTab5.stlを0.001倍して使うこと。STLとXMLの保存ハッシュを検査し、現115部品CADのTab5と三軸の最小/最大座標を照合した。最大差1.4e-17 m。XML衝突箱の中心(0.058,0,0.088) mと半寸法(0.006,0.064,0.040) mとも一致した。明示された配置規約の確認であり、対称な外形だけから未知の姿勢を推定したものではない。

前回の部分重心/重心慣性をこの座標へ対応付け、MJCF fullinertiaの並びIxx,Iyy,Izz,Ixy,Ixz,Iyzをレビュー用に出力した。原点慣性から重心慣性への平行軸項の逆変換も照合。原点慣性をそのままinertial要素へ渡さない。

**完成モデルへの出力は不可のまま。** 30点のCAD部品質量とCAD外の部品、内部分布が未確定で、部分値をbase全体の代わりに設定しない。XML未変更。今回の座標確認は実組立の位置精度、各可動リンクの座標、強度・動作合格を保証しない。

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_current_torso_frame.py
```
