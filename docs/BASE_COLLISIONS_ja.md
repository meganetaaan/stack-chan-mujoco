# 固定クレードル・電装予約の衝突形状追加

歩行評価中のモデルを変更せず、`assets/r6_base_collisions` に別候補を作成した。
固定クレードル左右各9箱と、電池・降圧器・通信基板・配線締結予約の各1箱、計22形状を追加。
質量・慣性・関節・アクチュエータ・表示CADは変更していない。外形と脚長も維持する。

CADの差集合で6部品それぞれの未被覆体積は0 mm³。
クレードルは中央開口と下側の逃げを残し、角丸を外包する。
余分な体積は左右各11.032 mm³、基板などの予約は各約3.4–4.3 mm³。
電池の箱予約は完全一致するが、実物の端子や固定具を含むモデルではない。

コンパイル後も質量・慣性中心・主慣性、関節原点・軸・範囲、摩擦・減衰、
アクチュエータのトルク範囲・ギアが元モデルと一致した。
形状数は561から583。接触判定を追加した結果の動力学は別途評価が必要。
URDFの衝突形状は今回も更新していない。

方角観測版の固定条件00について、保存した5,476姿勢を新しい形状で照合し、
追加形状の侵入は検出しなかった。これは20 msごとの**姿勢再生**であり、
新モデルでの動力学再実行や1 msごとの無衝突を証明しない。

陽性対照として、左股ピッチ0.95 radの静止姿勢では追加クレードルと左膝モータの
侵入2.370 mmを検出した。同じ姿勢でCADにも19.635 mm³の交差があり、実形状の干渉を確認した。
この姿勢には他の部品干渉もあるため、「旧モデルがこの姿勢全体を見逃した」とは主張しない。

## 再現

まず `docs/REAR_BRIDGE_ja.md` の元CAD候補を生成する。

```bash
.venv-cad/bin/python add_base_reservation_collisions.py \
  --design outputs/design_r6_rear_bridge8_collision --out outputs/design_r6_base_collisions
python audit_added_collision_states.py --design outputs/design_r6_base_collisions \
  --trial outputs/r6_heading_acceptance/fixed/trial_00 --out outputs/base_collision_pose_audit.json
.venv-cad/bin/python check_design_clearance.py --design outputs/design_r6_base_collisions \
  --trajectory-terminal-csv validation/base_collisions/positive_pose.csv \
  --out outputs/base_collision_positive_cad.json
```

陽性対照のCAD検査は交差を検出するため終了コード1が期待値。
結果と入力・コードのハッシュは `validation/base_collisions` に保存する。
この候補の合格歩行はまだ確認していない。元モデルの成績は流用しない。

電池の固定具は別途 `design/battery_mount_concept.json` に未製作の設計案を保存した。
既存内部レールへ取り付けるトレーと中央の保持バンドを想定し、外形・脚長・足形状は維持する。
これはまだCAD生成・干渉検証前の案であり、今回のモデルや質量には反映していない。
