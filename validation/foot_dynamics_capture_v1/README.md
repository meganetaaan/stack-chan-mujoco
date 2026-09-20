# 足部動力学の同時刻記録

左旋回7秒、7000時刻の接触位置・接触座標系・生の接触力/トルク、足首ロールボディのcvel/cacc/cinert/cfrc_int/cfrc_ext・姿勢・質量・基準COMを保存。47340接触レコード。mj_rnePostConstraintを呼ぶ既存joint_wrenchesの直後に取得している。

元EPIC4左旋回trace.npzの全配列と完全一致した（capture_audit.json）。記録追加による軌道・荷重の変更なし。問題のサンプル2446は2.447秒、両足合わせて3接触。

生のMuJoCo空間ベクトルは座標・原点・作用方向を解釈してから使用する。接触力の合計と慣性・重力・関節反力の釣合いはまだ未評価。足首ボディ以外の子孫に分離された接触形状は現抽出の対象外であり、モデル階層を確認する必要がある。最新CAD質量は未反映。

```sh
OPENBLAS_NUM_THREADS=1 .venv-engineering/bin/python software/sim/actuator/run_probe.py --foot-loads --out outputs/foot_capture_repro
```

foot_loads.jsonl.gzは時刻ごとのJSONをgzip圧縮したもの。強度合格・実機性能の証跡ではなく、境界条件を修正する入力データ。
