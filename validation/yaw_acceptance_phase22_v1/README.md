# 22%候補の正式評価

開発20条件の総合20/20と状態記録の再評価を確認してから、候補を凍結して正式40試行を開始した。実行中であり、正式達成はまだ確認していない。

`candidate/snapshot.json` はモデル・参照・制御・実行エンジン・物理設定・評価条件・依存環境の凍結記録。制御・実行ソースはコミット `9563fa8` のもの。`candidate/run_claim.json` はこの候補で正式試験を開始した記録であり、成功の証拠ではない。

実行コマンド：

```sh
python run_yaw_acceptance.py --snapshot validation/yaw_acceptance_phase22_v1/candidate/snapshot.json --out outputs/yaw_acceptance_phase22_v1 --workers 10
```

固定シード217000〜217019、ランダム化シード218000〜218019を、同じ205秒・24区間で全て評価する。固定20/20、ランダム18/20以上の総合合格を必要とする。シードの置換・失敗の再試行は行わない。完了後に全状態、失敗を含む結果、再生動画をここへ整理する。
