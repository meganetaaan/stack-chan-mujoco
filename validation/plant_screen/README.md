# 参照歩容のモデル変動試験（強化学習評価ではない）

仮定した範囲から seed 20260919 で事前生成した20条件を、同一の参照歩容で実行した。
全20条件で100秒以内に10 mへ到達したが、00・03・14は停止時に自己衝突した。
停止まで含む成功は **17/20**。`summary.json` に失敗も含めた結果を保存する。
範囲は実機同定値ではない。IMUノイズ・飽和保護が未実装のため新RL受入基準に数えない。

最後の一歩で足をそろえ、両脚支持への移行を0.3秒に延ばした `probe_stopping_gait.py` を
失敗した3条件に適用すると、3条件とも109.5秒まで自己接触・足裏以外の床接触なし。
これは選択した3条件の再試験であり、新制御器での20/20を示すものではない。

`case_XX` は元の20条件、`aligned_stop_XX` は変更後の3条件。
`trajectory.csv.gz` は実MuJoCoで記録したCSVの可逆圧縮。
`original_reference.json.gz` / `aligned_reference.json.gz` はIK参照（実状態ではない）。
全ケースで共通の参照を重複保存しない。`commands.json` は元試験の実行コマンド。

停止変更の再現例（モデル構築は docs/REAR_BRIDGE_ja.md）:

```bash
.venv-dynamics/bin/python probe_stopping_gait.py \
  --design outputs/design_r6_rear_bridge8_collision --speed .1 --step-period .27 \
  --height-offset-mm -2 --com-forward-offset-mm -3 --com-inset-mm 24 \
  --static-compensation --slew 6 --steps 400 \
  --plant-variation design/plant_variations/case_00.json --out outputs/reproduce_aligned00
```

`aligned_stop_00_finish_cad.json` は変更後00の108.5秒以降の保存姿勢についてのCAD照合。
保存姿勢の検査であり、連続時間の干渉や実機強度の保証ではない。
