# #5・#6 最新候補と製作判断の入口

2026-09-22更新。**製作HOLD。#5・#6および#17〜#24の完了は未証明。**
この一覧は製造リリースではなく、分散した候補と適用限界をまとめるもの。
過去の解析が新しい形状・部品へ自動適用されるとは扱わない。

## 要求と設計選択

ユーザー要求は現行の外形・脚長を基本にしたTab5・12軸機、ABS/PETG/TPUを使える3Dプリント、通常・最悪条件・適用する異常時の成立。電池選定は設計側へ委任されている。
部品の保証条件と設計上の仮定は各資料に残す。PETG優先、LB-020、左右別レギュレーター、インサート、立上り容量100 nFは設計候補でありユーザー指定ではない。
[製作条件](BUILD_CONSTRAINTS_ja.md)を参照。材料一般の代表値を造形品の許容値に読み替えない。

## 機構

| 対象 | 現在の参照先 | 確認範囲と残件 |
|---|---|---|
| 胴体 | [115部品候補](../../../../validation/serviceable_torso_v3/README_ja.md) | 新規関連1,899組を検査。Tab5簡略モデル対ねじ4件は未解決。全脚動作・配線・新制御基板・公差・変形は含まない |
| Tab5枠の造形前形状 | [座ぐり付き枠](../../../../validation/tab5_frame_print_v1/README_ja.md) | 単一ソリッドと圧入後近似への整合を確認。造形方向、下穴補正、保持能力は未確定 |
| Tab5締結 | [ねじ候補と座ぐり](../../../../validation/tab5_frame_screws_v2/README_ja.md) | 公称侵入4.3 mm。雌ねじの使用可能深さ、底付き余裕、掛かり、締付条件が未確認 |
| ヨー支持 | [現行入口revC](../../../../board/mechanical/prototype/yaw_support_candidate/current.json) | 52部品候補。旧revB解析を新形状の強度証明にしない |
| 足部 | [現行入口revE](../../../../board/mechanical/prototype/foot_candidate/current.json) | 材料・締結・工具・全慣性・変形込み隙間が未完 |
| 電源取付 | [現行入口revB](../../../../board/mechanical/prototype/power_mount_candidate/current.json) | 43部品、公称穴形状の候補。保持強度と工程公差は未証明 |
| 質量 | [115部品の対応表](../../../../validation/current_torso_mass_v2/README_ja.md) | 数値78件、材料密度未割当15件、部品質量未定22件。旧割当を分離。全身mass/COM/inertiaは未確定 |

[115部品版の抜取り検査](../../../../validation/insert_carrier_removal_v2/README_ja.md)では、側面4ねじを除去後、移動10部品・固定101部品の前方40 mm経路に公称干渉フラグなし。配線・工具・公差・変形・保持能力は未確認。旧111部品版の結果とは区別する。
[胴体造形7部品の工程対応](../../../../validation/torso_print_conditions_v1/README_ja.md)では金属座金16点（加工品8・市販品8）を分離し、既存PETG比較条件と未確定工程を明示。先にTab5締結条件・造形工程・全荷重経路を決め、保持、座面、根元の変形と干渉に必要な評価を行う。局所最大応力の収束だけで完了にしない。

[旧負荷と最新質量の適用性確認](../../../../validation/current_load_mass_basis_v1/README_ja.md)：旧base 523 gに対し、現候補の既知部分＋均質PETG比較は672 g。集計範囲は異なり保証重量差ではないが、旧±5%感度試験を現構成の合格根拠にできない。全機統合後に負荷を再生成する。

[最新CADの部分慣性](../../../../validation/current_torso_inertia_v1/README_ja.md)は85点の比較値を集計し、未割当30点を拒否する検査を追加。内部均質分布の仮定で、全身入力は未完。[座標照合](../../../../validation/current_torso_frame_v1/README_ja.md)ではmm→m後に既存baseローカル座標と一致。world初期位置は差し引かず、未割当のためXML更新は保留。

## 電源

優先比較候補は保護内蔵ROBOTIS LB-020とPololu D42V110F5×2。
[電池比較](PROTECTED_PACK_COMPARISON_ja.md)の通り、容量×C値はPCMの遮断条件ではない。
指定充電器を含む仕様適合、PCMの遮断・復帰・逆流条件、配線損失、全負荷予算は未確定。

| 対象 | 現在の参照先 | 適用限界 |
|---|---|---|
| 新電池の統合入口 | [194部品接続候補](../../../../schematics/power/protected_pack_system_candidate_v3/README_ja.md) | 制御枝/主許可/補助許可/クリア駆動を接続。4信号境界と全過渡・保護協調は未完。未動作 |
| 旧全系統 | [250部品接続候補](../../../../schematics/power/system_power_integration_candidate_v1/README_ja.md) | 生セル側BQ保護を含む旧構成。未選定部品あり。LB-020採用済み完成回路ではない |
| 保護内蔵電池への移行 | [移行監査](../../../../validation/protected_pack_transition_v1/README_ja.md) | 旧電池回路の削除だけでは給電・起動許可・監視が成立しない |
| 新しい制御電源枝 | [41部品候補](../../../../schematics/power/pack_control_ramp_candidate_v1/README_ja.md) | 191部品案へ接続候補として統合。既知部分負荷と仮定による充電比較で、突入電流上限や起動合格ではない |
| メーカー過渡モデル | [PSpiceプローブv2](../../../../validation/pack_startup_pspice_v2/README_ja.md) | 主許可出力の追加負荷を反映。9/12.6 Vの回路を出力済み、未実行。対応環境と波形が必要。温度・MCU起動等のモデル限界あり |

[主起動許可の3部品接続候補](../../../../schematics/power/pack_main_allow_interface_candidate_v1/README_ja.md)では、SYS無給電時のHCS11直結を避け、受信側給電バッファを選定。191部品案へ接続候補として統合したが、電源遷移と信号余裕は未検証。

250部品と41部品を合算したBOMを購入用にしない。次の設計作業は全負荷予算と制御・停止境界の接続、メーカー条件との照合、対応環境での起動・保護検証。未選定回路を実測待ちとして処理しない。

## 完了条件と後続実測

当初条件は[Issue照合の保存記録](ISSUE_STATUS_ja.md)とそこにリンクする本文スナップショットを保持し、基準を下げない。
設計・解析の残件は#17〜#24に残す。実測事項は#48/#49で追跡するが、実機製作・実測とEPIC #7以降の実装は今回の対象外。
各候補のREADMEに再現方法・結果・限界があり、[変更履歴](CURRENT_CANDIDATES_ja.md)には失敗案も残す。
完成を主張するには、最新の統合構成に対して当初の強度・動作余裕・通常/最悪/異常給電の証跡が必要。現時点でクローズ対象はない。
