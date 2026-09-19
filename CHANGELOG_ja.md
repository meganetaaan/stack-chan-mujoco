# v4変更履歴

## この版の対象

A案・10軸・0.02 m/s。v3の `walk_refine/best` から40 ms LPF条件へ転送して再学習。
歩行高速化、機構変更、サーボ強化、実機デプロイは含みません。

## 実装

- **actuation / env:** probeと同じpost-slew LPFを正式経路に導入。初期化・遅延・
  最終速度ガードを保持。tau=0はv3と同じコード経路。
- **config / spec / checkpoints:** LPF設定保存、旧interface保持、限定的・明示的な
  actor転送。旧resume/playを新制御へ黙って切り替えない。
- **train / evaluate / play:** 同じenvを利用。初期方策の新条件評価と保存を継続。
  診断用の旧方策評価に `--allow-target-lowpass-change` を追加。
- **rewards:** 前進報酬を指令距離でcapし係数を縮小。速度超過、生action一階/二階
  差分を強化。同じ足の連続着地の前進ボーナスを削除し、実際の着地順を使用。
- **target_metrics / env:** raw・bounded・slew・filtered・delayed・実角を別記録。
  そのactionで実際に使用した観測61値、足底座標、終了時接触対を追加。
- **quality / evaluation:** 従来条件を維持し、距離追従・速度誤差・目標差分を追加。
  滑らかな静止や速度超過でbestを獲得しにくい選択・診断へ変更。
- **diagnose_gait / check_stage:** 指令距離へ減速した改善を「前進量の悪化」にしない。
  v4進級は総合成功率と全試行の自己接触/非足底接触の双方を確認。
- **configs:** `walk_lp40_baseline`（旧目的＋LPF）、`walk_lp40`（v4学習）、
  `lp40_smoke`（接続確認）の3設定を追加。
- **tests:** 新規48件のオフライン回帰、8件の依存ありruntimeテストを追加。
  元のv3試験を削除していません。

## 意図的に残した制限

LPF前のslew状態・遅延キュー全体をactorの観測へ足していません。観測は完全な
Markov状態ではありません。着地判定・終了判定は50 Hz、ピッチ/荷重計測は1 kHz。
実形状でなく既存MJCFの衝突代理形状です。自己接触を無効化していません。
新しい係数・品質しきい値は初回の試行値です。歩行改善の実証はまだありません。

検査結果は `TEST_REPORT_ja.md`。v3以前の変更履歴は `docs/legacy/v3/`。
