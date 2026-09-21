# v7機構と3S候補配置を結んだ質量台帳

yaw_v7_inertial_ledger_v1の旧2S電池予約・変換器予約・トレイを除き、
既存3S電池候補と左右UBEC、revBトレイの配置へ置換した。
除去・追加した各項を保存し、部品ごとの再合算と差分結果が一致することを確認。
同一座標で原点慣性を合算し、小計の重心慣性が正定値であることも確認した。

電源置換の増分25.933 g。密度割当済み固定項の小計445.287 g。
支持部等の11密度項、ねじ・ナット、配線・保護回路等を含む全身重量ではない。
残る係数と金属・座金・旧機器の項も明示的に引き継ぐ。

電池はTA-45C-850-3S1P-XT30の公表76 g、左右UBECは比較資料の各36 g。
内部質量分布はCAD一様分布、トレイは既存PETG候補の典型密度という仮定。
UBECの実注文型番・5V版の同定、保護構成の成立は未完了で、部品の採用確定ではない。
1S電池案との比較は別管理で、この台帳へ重ねて加算しない。

全項を同じbody座標に変換してモデルへ入れる工程は未実施。
基準を満たすために未配賦の質量をゼロとしたり、旧25 g枠で代替したりしない。
製造リリース、電源適合、全身動作の証明には使わない。

再現：
```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/replace_payload_inertial_ledger.py --base validation/yaw_v7_inertial_ledger_v1/report.json --out /tmp/yaw-v7-payload-ledger
```
