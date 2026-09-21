# 要求ごとのタイマー完了確認

前回追加した完了条件を状態付きの観測モデルへ反映した。要求開始時はRESET_TIMERへ入り、RESET_LOW_VALIDをLowにする。タイマーDONEのLowを観測してからQUALIFYへ進み、健全電源と両CLR Lowの観測中だけRESET_LOW_VALIDをHighにできる。DONE High、ARMED Low、ENABLE_PERMISSION Lowが揃って初めて解除可能とする。

古い組合せ論理の判定は、すべての入力が成立して見えると前回のDONE Highも受け入れる。新モデルでは、Highが残る要求開始、正常な新規完了、連続要求、電源健全性喪失、CLR観測の中断、ラッチ出力が非同時に消える場合の6系列を確認した。観測中断や健全性喪失後も再びDONE Lowからやり直す。ラッチ出力をモデル側で瞬時に消去する処理は入れていない。

これは観測順序の検査であり、実装するクロックや同期回路の設計ではない。入力グリッチ、メタステーブル、観測しきい値、MR伝搬、実端子配線、CLR解除後の回復時間の保証は残る。実回路へ未統合であり、通電許可に使わない。

再現：`python3 software/sim/circuits/check_clear_timer_freshness.py --out /tmp/clear-timer-freshness-check`（未作成の出力先）。追加の仮定時間を置いた波形掃引は行わない。次の設計対象はこの順序を実現する観測・再初期化回路である。
