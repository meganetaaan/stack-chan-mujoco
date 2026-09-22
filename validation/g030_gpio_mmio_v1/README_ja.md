# STM32G030 GPIO MMIOアダプター

既存の初期化・出力制御へ渡せる実レジスタ読書きコールバックを追加した。GPIO A/B/Cのみ、必要なレジスタだけを許可する。IDR/ODRは読出し専用、BSRRは書込み専用として扱い、範囲外・予約領域・非整列指定はアクセスせずソフトウェア異常を記憶する。

出典は[ST公式CMSISヘッダの固定コミット](https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-g0/f576c24e123edf3332988ecd49512c0f35f85186/Include/stm32g030xx.h)。GPIO基点0x50000000、ポート間隔0x400、レジスタ配置を確認し、取得ファイルのSHAと根拠をmanufacturer_register_map.jsonに保存した。HAL/CMSISのソース本文は複製していない。

## 検査

実アダプターをLinux上でコンパイルし、実コードが使うアドレスに匿名RAMを割り当てて検査。既存領域を上書きしないMAP_FIXED_NOREPLACEを使い、割当てできない環境では合格にしない。

- A/B/Cの読出し24通り、書込み21通りを照合。
- 書込みでは4096バイトの領域全体を比較し、対象以外を変えていないことを確認。
- 不正指定595件で読出し0/書込みなし、異常記憶がその後の正常アクセスでも消えないことを確認。
- Cortex-M0+向けオブジェクト生成に成功。
- 共通ヘッダへのIDR追加後、既存初期化100パターン/失敗2ケースと出力制御2048組を再確認。

匿名RAMはBSRRのGPIO動作や実端子を模擬しない。実レジスタの動作、入力の正当性、電気的タイミングをこの結果で保証しない。

## 呼出し条件

GPIOクロック、RTC/LSEによるPC14/15所有、PA9/10再割当て、同一端子へ結合された別GPIO、起動コード/ゼロ初期化は呼出し側の責任で、ボードへの統合は未完了。既存g030_gpio_init.hの前提を満たしてから使用する。

呼出し側は各シーケンス処理の前後でpower_g030_mmio_ok()を確認し、失敗をpower_runtime.io_faultへ記憶する必要がある。異常後も停止用のベストエフォート書込みを可能にするため、正常なレジスタ指定は受け付ける。異常記憶を無視して給電許可を出してよいという意味ではない。

IDRは生の端子値であり、未完成の受信回路・電源有効性・非同期故障捕捉を代替しない。独立したハードウェア遮断が依然必要。書込み可能な完成ファームウェア、製造リリース、#24完了ではない。

再現（リポジトリルート、未作成出力先）：

```sh
.venv-engineering/bin/python software/sim/circuits/check_g030_gpio_mmio.py --out /tmp/g030-mmio-recheck
.venv-engineering/bin/python software/sim/circuits/check_g030_gpio_init.py --out /tmp/g030-init-recheck
.venv-engineering/bin/python software/sim/circuits/check_g030_gpio_outputs.py --out /tmp/g030-output-recheck
```
