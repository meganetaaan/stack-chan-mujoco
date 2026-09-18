# R5-A v3 制御切り分け試験（再学習なし）

既存のwalk_refine/bestを固定し、元の制御と、速度制限の後へ追加したローパス（40/80 ms）を同じ条件で比較します。
**物理比較はこの配布環境では未実行です。改善する保証はありません。** 数値単体試験8件に合格しました。
元のソース・モデル・チェックポイントは変更しません。追加の学習ライブラリーはありません。

## 実行

v3のフォルダーにこのZIPをコピーして、現在の仮想環境で実行します。

```bash
cd ~/stack-chan-mujoco/stackchan_r5a_rl_v3
unzip walk_refine_probe.zip
python walk_refine_probe/test_control_probe.py -v
python walk_refine_probe/compare_control.py \
  --checkpoint runs/walk_refine/best \
  --episodes 5 \
  --command 0.02 \
  --out outputs/control_probe
```

3条件×5試行のheadless評価だけです。PPOの更新・再学習はしません。WSLgやOpenGLも使いません。
フォルダーが既にある場合は上書きせず停止します。再実行には別の`--out`を指定してください。
対象ソースのハッシュも照合します。不一致を無視して実行するオプションはありません。

`outputs/control_probe/comparison.json`が最終比較です。各条件のフォルダーにCSV・方策入力NPZ・エピソードJSONを保存します。
中断時の`partial.json`は完了結果ではありません。

## 比較の読み方

まずbaselineが従来どおりに動くことを確認します。物理モデル、方策、seed 20000〜20004は3条件とも同じです。
40/80 msはフィルターの時定数で、policy周期ではありません。方策は50 Hzのまま、フィルターは1 kHzで更新します。

比較対象は実際の前進距離、左右の有効着地、胴体ピッチRMS、目標角の差分、終了理由です。
フィルターで滑らかになっても、足が止まる・転倒が増える場合は改善とは扱いません。
raw actionの品質合格基準は変更しません。raw actionが振動したままなら`quality/action_smoothness`は引き続き不合格です。

この試験では実効的な制御ダイナミクスを意図的に変更します。元方策との学習再開互換性や実機安全性を認定するものではありません。
結果を保存して自動で方策を上書きしたり、フィルターを製品コードへ採用したりはしません。

## 自己接触ログ

終了時に、実MuJoCoの接触対・力・距離を`terminal_self_contact_pairs`に保存します。
元CSVから幾何学的に推定した候補と、実エンジンで検出された相手が一致するかを確認するためです。
この診断値は既存の50 Hz終了判定の時点です。全1 kHz履歴の完全な接触列ではありません。
