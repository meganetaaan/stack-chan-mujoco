# v4 設計の変更範囲

v4の実行仕様・コマンド・評価条件は `../README_ja.md` が入口です。
本書はv3からの変更箇所と、判断に必要な境界を整理します。

## 制御の一本化

`StackChanEnv` が `make_servo_bank` を呼ぶため、学習ワーカー・評価・GUI再生・
動画出力が同一の制御を使います。`target_lowpass_time_constant_s=0` は元の
`ServoBank` をそのまま返します。正の値は `PostSlewLowPassBank` を使用します。

LPFは1 kHzで更新し、速度制限の後段・元の通信遅延の前段に置きます。
`filtered_target_offset`は実際に遅延キューへ渡す値です。前段のslewとLPFの状態を
別に保持し、reset時に再初期化します。60次元台への観測拡張は行っていません。
前段状態、遅延キュー、イベントの履歴が完全には観測されない制限は残ります。

## 報酬と評価の分離

v4前進報酬は、新しい最大到達位置の増分を現在の速度指令×方策周期で上限制限。
上限を越えた分を将来に繰り越さないため、急に進んで停止する行動へ貯金を与えません。
速度追従の項と別に速度超過を抑制します。これは停止/過速という人工状態での
報酬の性質を調整したもので、PPOが目的の歩容を必ず獲得する証明ではありません。

`OrderedStepCredit` は実測された直前の有効着地を基準に報酬を決めます。
報酬を付けなかった着地も履歴を更新するため、報酬用cooldownで抑制された
イベントを飛ばして架空の左右交互を作りません。同時着地には順序を割り当てません。
元の歩数・着地順序は別に保持し、qualityや成功判定を通すために書き換えません。

生のaction差分と、LPF後の目標差分を別集計します。実関節の変位や角速度とは別量です。
新しい品質条件とbest選択では、動かない方策を滑らかさだけで優先しません。
速度超過の改善で移動距離が減ることは想定内で、指令積分距離との誤差で比較します。

## 保存・移行

LPF設定と実装種類をinterfaceへ追加します。tau=0の旧interfaceは変更しません。
旧checkpointのresume/playは厳密なinterface一致が必要です。
`--init-from`だけ、設定で明示許可したLPF差分を限定的に認めます。
評価の制御変更にも専用フラグが必要です。モデル、関節順、可動域、home、
actionスケール、slew、観測の違いを、この移行許可で無視することはできません。

転送したactor/log_stdを保存して新条件で初期評価を行い、その後にPPO更新します。
criticとoptimizerは新しくします。旧runやユーザーの元重みを上書きしません。

## 変更していないもの

A案の43 asset、サーボ仕様、MJCFの衝突代理形状・接触フィルター・慣性・質量、
トルク/速度上限、PDゲイン、10 ms遅延、関節ガード、歩数検出の高さ/時間しきい値。
胴体の固定、補助外力、ルート姿勢の強制移動は追加していません。
元の機構・実機に関する未検証事項は `R5_source_report.md` を参照してください。

## ソースとAPI参照

- 直接の改修元: v3のPython一式。差分は `../validation/changes_from_v3.patch`。
- LPFの独立参照: 比較試験用probe。数値回帰用の凍結コピーを `../tests/` に収録。
- ユーザーの `comparison.json`: LP40の採用根拠。v4の学習結果ではありません。
- SB3 PPO: https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
- SB3 Gymnasium environment: https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html
- MuJoCo Python: https://mujoco.readthedocs.io/en/stable/python.html

元の61次元I/Oとv3設計は `legacy/v3/DESIGN_ja.md` に保存しています。
旧スタンド/歩行の設定例 `resolved_stand_config.json` / `resolved_walk_config.json` は
従来版の参照用です。v4用は `resolved_walk_lp40_config.json` と `interface_lp40.example.json`。
