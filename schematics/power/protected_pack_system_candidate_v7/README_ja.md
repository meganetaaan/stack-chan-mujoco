# Tab5起動許可を接続した209部品候補

v6の204部品にTab5要求のシュミットバッファ、許可AND、プルダウン、バイパス容量2個を追加した。制御マイコンPA7から既存Tab5枝のSHDNへ接続する。現時点ではPololuを含む統合候補であり、PTH比較案への置換ではない。

[接続・静的比較・状態契約・残件・再現](../../../validation/tab5_request_connection_v1/README_ja.md)。部品表は[bom.csv](bom.csv)、端子表は[connections.csv](connections.csv)、値と入力来歴は[assembly.json](assembly.json)。

明示した未接続ポートはPACK_UV_WARN_N。これ以外の未設計機能がないという意味ではなく、Tab5の電源OFF確認・準備完了・終了応答等は検出/通信手段が未実装。Tab5枝の電流制限・DVDTも未確定。全電力・過渡・異常・熱の検証は未完、製作リリース不可。
