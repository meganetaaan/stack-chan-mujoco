# 左右変換器の起動許可接続

## 設計判断

SYSの電圧監視・RESETに依存せず、先に起動するCTRL側から左右変換器を起動する。STM32G030F6P6のTSSOP20ピン12 PA5を左、13 PA6を右へ割り当てた。各要求は10 kΩでLowを既定とし、74LVC1G17GVで波形整形後、SN74LVC1G08DBVRで既存CTRL_LATCH_PERMITとANDをとる。通常有効電源下では要求と許可の両方がHighの場合のみENAドライバーがHighになる。

10 kΩで開放端子が変化する信号を通常CMOS入力へ直接入れない。前段の入力速度制限がない部品を使用する。ただし整形段出力・許可ラッチ出力の速度／負荷とAND入力の適合は未確認。ウォッチドッグによる既存許可ラッチ解除経路を使用し、SYS側の手動再ARM・電圧監視は引き続き下流サーボ給電を制御する。

## 接続と計算

新規10部品で204部品となる。MCUの未使用2端子以外の旧部品ピン接続は保持。左右REGULATOR_ALLOWを接続し、明示的な未接続ポートはTAB5_START_ALLOWとPACK_UV_WARN_Nの2つ。ただしポート数は完成度や他の未完インターフェースの不存在を示さない。

ENAは既存100 Ω直列・2.21 kΩプルダウンを維持。[Pololu製品資料](https://www.pololu.com/product/5671)のENA/ENBそれぞれのVINへの1 MΩと相互10 kΩを含めて公称DC計算。表はreport.jsonに保存。メーカーの保証されたENAしきい値は得られていないため、算出電圧を起動・停止合格へ読み替えない。ENB/PFMは既存どおり開放。

追加CTRL抵抗負荷は3.6 V・外付け抵抗±1%という工学的比較で両側計3.876 mA。新規バイパス容量400 nF。IC静的・動的消費、端子漏れ、内部抵抗公差などを含む総最大値ではない。従来の12.129 mA起動プローブはこの追加を含まず、現候補の起動確認には使えない。

一次資料: [ST DS12991 Rev6 Table12](https://www.st.com/resource/en/datasheet/stm32g030f6.pdf)、[TI SN74LVC1G08 RevAA](https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf)、[Nexperia 74LVC1G17 Rev16.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G17.pdf)。これは部品選定・接続の根拠であり全回路保証ではない。

## 評価終了条件と残件

次の評価はENAの電圧条件、CTRL/モジュールの部分給電時の注入、GPIOリセット状態、論理出力の負荷と速度、全電流予算を確定すること。メーカー保証がないモジュール特性は未確認のまま残し、仮定波形の追加だけで合格にしない。起動シーケンスの実装は対象外で、要求Low初期化・明示ARM・電圧資格確認後のサーボ再ARMという契約のみ示す。

再現: `python3 software/sim/circuits/connect_regulator_requests.py`。電源遷移は未実行、製作HOLD、Issue未完。
