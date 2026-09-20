# ヨー軸偏心・ホーンフランジの修正候補

`assets/r8_yaw_offset_flange_v1` はメーカー図面の7.5 mm偏心を反映した別候補。既存の合格済み資産や評価閾値を更新していない。正式受入シードも未使用。

## 機構変更

- ヨー関節位置を保ち、ケース長手をロボットX方向へ配置。ケース34×20×23 mm、回転ホーン直径16×3 mmを別形状にした。背面アイドラーは搭載しない。
- 回転側に直径16×厚さ2 mmのフランジを追加。PCD12 mmに4つの直径2.2 mmクリアランス穴を設けた。これは提案する印刷部品の穴径であり、メーカーの直径1.6 mmタッピング穴とは異なる。
- 最初のフランジ案ではトレー支持部と最大0.6 mm重複した。支持部の経路を広げ、円形フランジとの公称半径方向隙間を0.8 mm以上にした。初案のソース・不合格監査も保存。
- 胴体・Tab5・足の衝突形状、脚の関節位置・軸・可動範囲を従来候補と比較するテストが通過。足首XC仕様も維持。
- 総質量0.935436144 kg。ヨーモーターは各18 gをケース・ホーンの代理体積比で配分する近似。メーカー慣性行列は基準点が未確認のため適用していない。新しいねじの詳細BOMは未確定で、従来のケーブル・締結品概算を残している。

## 干渉検査の範囲

初期姿勢で左右ヨー角を各19点、±0.09 radで掃引した361組では、ヨー取付部の食い込みはゼロ。初期姿勢の食い込みもゼロ。ただし左右脚を内向きにする端部6組では脚・足同士が干渉する。関節範囲の直積全体を安全な姿勢集合とは扱わない。動作中の自己衝突検査を省略していない。

修正ケースと、元CADから再構成した固定部品・生成したトレー／支持部の体積交差はゼロ。対象部品一覧は `yaw_offset_flange_fixed_cad_v2_repro.json` に保存した。追加のバッテリー締結付属品すべてを覆うCAD検査ではない。補助的に同一base内の全衝突代理形状との距離も調べ、ケースの負距離がないことを確認した（`fixed_proxy_distances.json`）。表示専用形状は対象外。離散MuJoCo検査は連続CAD掃引の証明でもない。

ケース固定ねじ・背面側支持・ホーンねじ長さと頭部隙間・工具アクセス・支持強度は未確定。現在の支持棚は概念形状で、製作リリースではない。

## 開発試験

修正した質量・慣性を使って参照と静的トルク補償を再生成。旧版の状態記録を新モデルの成績へ流用していない。

32秒の固定条件310501とランダム条件310613はいずれも転倒・自己衝突・関節逸脱・保護停止なしで完走し、先頭5区間の全運動指標と移動区間の着地数を満たした。有効着地は固定33/33回、ランダム33/22回。32秒には旋回区間が含まれず、全205秒の合格とは異なる。

205秒固定条件は物理異常なく完走し、有効着地292/292回、全移動区間の着地要件を満たした。ただし10_forward、12_forward、21_arc_left、22_arc_rightの横速度RMSEは0.030255、0.030624、0.031032、0.031324 m/sで閾値0.030を超え、全体は不合格。

205秒試験の結果は `summary.json` と `yaw_offset_flange_trial205_v2/report.json` を参照。正式固定20/20・ランダム18/20の達成は主張しない。

関連16ユニットテストが通過。`video32.mp4` は32秒固定試験の実MuJoCo積分状態を50 fpsで再生したもの。8秒の抽出画像を確認済み。

## 再現

既存のCAD環境とMuJoCo環境を使用。各出力先は未使用パスにする。

```sh
python build_yaw_dynamics_candidate.py --cad-design outputs/design_r6_base_collisions --manufacturer-yaw-layout --out outputs/new_offset_base
python upgrade_candidate_ankles.py --cad-design outputs/design_r6_base_collisions --design outputs/new_offset_base --out outputs/new_offset_xc
python audit_yaw_fixed_cad.py --cad-design outputs/design_r6_base_collisions --design outputs/new_offset_xc --out outputs/new_fixed_cad.json
python audit_yaw_layout.py --design outputs/new_offset_xc --out outputs/new_yaw_grid.json
python generate_yaw_maneuver_reference.py --cad-design outputs/design_r6_base_collisions --design outputs/new_offset_xc --out outputs/new_offset_ref --duration 205 --shift-fraction .25 --steady-inset-mm 25.9 --period .32 --forward-period .30
python probe_yaw_dynamics_candidate.py --design outputs/new_offset_xc --reference outputs/new_offset_ref/reference.json.gz --protocol configs/maneuver/acceptance_v1.json --out outputs/new_offset_trial --duration 205 --static-torque-scale 1 --yaw-kp 6 --yaw-kd .13
MUJOCO_GL=egl python replay_yaw_candidate.py --trial outputs/new_offset_trial --design outputs/new_offset_xc --out outputs/new_offset.mp4
```

最初の3コマンドはCadQuery環境、以降はMuJoCo環境。32秒比較では生成・実行の両方に `--duration 32` を指定し、ランダム試験は実行へ `--randomize --seed 310613` を追加する。

各reportのoutputsパスは実行時の履歴。参照・試行はこのフォルダの同名ディレクトリ、モデルは上記assetsへ同一物理ファイルを収録。ソーススナップショットとSHA-256を保存する。メーカー資料本体は再配布せず、既存の取得スクリプトと出典を利用する。
