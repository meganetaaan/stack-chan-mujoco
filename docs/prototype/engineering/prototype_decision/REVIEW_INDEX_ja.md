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

統合回路候補は保護内蔵ROBOTIS LB-020とPololu D42V110F5×2。PTH240/241への置換は後述の詳細比較段階で、未統合。
[電池比較](PROTECTED_PACK_COMPARISON_ja.md)の通り、容量×C値はPCMの遮断条件ではない。
指定充電器を含む仕様適合、PCMの遮断・復帰・逆流条件、配線損失、全負荷予算は未確定。

| 対象 | 現在の参照先 | 適用限界 |
|---|---|---|
| 新電池の統合入口 | [209部品接続候補](../../../../schematics/power/protected_pack_system_candidate_v7/README_ja.md) | Tab5許可も接続。明示未接続は電池低電圧警告。検出/通信・全予算・過渡・保護協調は未完。未動作 |
| 旧全系統 | [250部品接続候補](../../../../schematics/power/system_power_integration_candidate_v1/README_ja.md) | 生セル側BQ保護を含む旧構成。未選定部品あり。LB-020採用済み完成回路ではない |
| 保護内蔵電池への移行 | [移行監査](../../../../validation/protected_pack_transition_v1/README_ja.md) | 旧電池回路の削除だけでは給電・起動許可・監視が成立しない |
| 新しい制御電源枝 | [41部品候補](../../../../schematics/power/pack_control_ramp_candidate_v1/README_ja.md) | 191部品案へ接続候補として統合。既知部分負荷と仮定による充電比較で、突入電流上限や起動合格ではない |
| メーカー過渡モデル | [PSpiceプローブv3](../../../../validation/pack_startup_pspice_v3/README_ja.md) | v4の制御側追加負荷を反映。9/12.6 Vの回路を出力済み、未実行。メーカー模型の実行には対応環境が必要。#22は根拠付き近似も可。温度・MCU起動等のモデル限界あり |

[主起動許可の3部品接続候補](../../../../schematics/power/pack_main_allow_interface_candidate_v1/README_ja.md)では、SYS無給電時のHCS11直結を避け、受信側給電バッファを選定。191部品案へ接続候補として統合したが、電源遷移と信号余裕は未検証。

250部品と41部品を合算したBOMを購入用にしない。次の設計作業は全負荷予算と制御・停止境界の接続、メーカー条件との照合、対応環境での起動・保護検証。未選定回路を実測待ちとして処理しない。

## 完了条件と後続実測

当初条件は[Issue照合の保存記録](ISSUE_STATUS_ja.md)とそこにリンクする本文スナップショットを保持し、基準を下げない。
設計・解析の残件は#17〜#24に残す。実測事項は#48/#49で追跡するが、実機製作・実測とEPIC #7以降の実装は今回の対象外。
各候補のREADMEに再現方法・結果・限界があり、[変更履歴](CURRENT_CANDIDATES_ja.md)には失敗案も残す。
完成を主張するには、最新の統合構成に対して当初の強度・動作余裕・通常/最悪/異常給電の証跡が必要。現時点でクローズ対象はない。

[クリア入力速度の再評価](../../../../validation/sequence_clear_input_v1/README_ja.md)：旧194部品の10 kΩ直接入力は代表容量だけでも21.798 ns/Vとなり10 ns/V条件を超える比較結果。196部品では74LVC1G17GVを追加。旧入力の詳細化は終了し、新段の出力・電源遷移・予算の確認へ進む。回路成立は未証明。

[起動負荷の現候補への照合](../../../../validation/controller_probe_load_v1/README_ja.md)：補助許可・クリア回路を含む部分比較値12.129 mA、公称CTRL容量10.3 µF。[PSpice v3](../../../../validation/pack_startup_pspice_v3/README_ja.md)へ反映済みだが未実行。全電流上限・起動成立を示さない。

[左右監視から停止への接続](../../../../validation/source_window_reset_connection_v1/README_ja.md)：以前は未消費だった監視出力を既存RAIL_HEALTH_Nへ接続。監視ノードの電気条件と遮断時間は未確認。変換器ALLOWをSYSリセットへ従属させると起動循環になるため、その接続は禁止する設計判断。

[左右変換器の起動許可](../../../../validation/regulator_request_connection_v1/README_ja.md)：PA5/PA6→シュミット→CTRL許可ラッチとのANDを接続。SYSリセットから独立。追加抵抗比較負荷3.876 mA・容量400 nFは旧起動プローブに未反映。ENAしきい値、部分給電、全予算は未完。

[統合監視ノードの静的比較](../../../../validation/health_node_static_v1/README_ja.md)：単独出力の比較負荷0.418 mA。R9は10 kΩを維持して品番TNPW060310K0BEEAを割当。表記条件とのLow/High余裕を確認したが、全温度・電源遷移の合格ではない。

[当初完了条件と残件の再照合](../../../../validation/prototype_remaining_scope_v1/README_ja.md)：#22は根拠付き近似を許容し、PSpice必須ではない。現204部品には品番／値未確定20点。主遮断ゲートRC・電流制限・過電圧、Tab5枝、全電力予算の確定を優先する。

[外付けゲートRCの代替判断](../../../../validation/integrated_reverse_alternative_v1/README_ja.md)：TPS25948の片脚1個置換は温度範囲抵抗による比較で29〜34 mV不足し不採用。現ゲート駆動の不足仕様はRC仮置きで解消しない。保護群分割・変換器精度・駆動保証のいずれかを先に判断する。

[精度改善と保護分割の比較](../../../../validation/precision_module_comparison_v1/README_ja.md)：次の詳細候補はPTH08T240W×2＋TPS25948系。未割当降下の比較余裕41〜46 mVで、Pololu維持・保護分割の9〜12 mVより大きい。未統合であり、周辺容量・停止入力・14 V入力上限・熱・CADが未確認。

[PTH入力容量候補と出力安定性条件](../../../../schematics/power/pth_input_cap_candidate_v1/README_ja.md)：EEUFR1C471を入力側各1個の候補に選定。5 V時の必要リップル条件を700 mArmsへ修正。出力は全容量バンクの最低ESR条件が未確認で、PTH採用確定は保留。

[出力安定性の設計／実測境界](output_stability/DECISION_ja.md)：PTH08T241Wを低ESR対応の比較候補に追加。局所実効容量と全負荷範囲は設計残件。E0-S/E1-S手順を#49へ引き継ぐが未実施で、親Issueは未完。

[PTH停止インターフェース候補](../../../../schematics/power/pth_inhibit_candidate_v1/README_ja.md)：左右12部品の接続を具体化。無給電ALLOW漏れの比較で初案100 kΩを退け、解除側4.7 kΩへ変更。BSS138のメーカー差、起動競争、温度・漏れの適用性は未解決。全体v6未置換、#24未完。

[最新胴体の工具と組立順](../../../../validation/current_face_tool_access_v1/README_ja.md)：Wera 05118068001の公称包絡で1,404組を検査。装着中のTab5固定ねじ操作は殻・後部プレートに干渉するため不採用。単体顔ユニットでは最小隙間1.011 mm、側面ねじの工具・抜取りも交差フラグなし。単体でTab5を締結する順序を採用。ねじ深さ・締付・配線・支持・公差は未完。

[現枠の座面積・強度評価入力](../../../../validation/current_carrier_bearing_v1/README_ja.md)：接触面12か所をCADから抽出。側面ねじ頭の殻側座面14.679 mm²、枠パッド25.918 mm²で、同じ合力なら殻側平均面圧は約1.77倍。予圧・材料許容は未設定。殻座面の圧縮/曲げ/クリープ、保持・離間・相対変位を解析量に明記し、旧1.256 Nや7 MPaを現構成の合格基準に転用しない。

[Tab5起動要求の接続](../../../../validation/tab5_request_connection_v1/README_ja.md)：PA7→シュミット→CTRL許可とのAND→既存SHDNを接続。状態契約640組と既存8イベントを照合。追加抵抗負荷比較0.704 mA・容量200 nF。停止入力のGND電位差、検出器・通信・全電源動作は未確認。
