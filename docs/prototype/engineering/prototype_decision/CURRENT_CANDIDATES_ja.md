# 現在の比較候補と製作判定

現時点で通電試作を許可する完成構成はない。次の資料は候補の所在で、全てを合算した製造BOMではない。

| 対象 | 現在参照する比較案 | 主な未完了事項 |
|---|---|---|
| 足部 | board/mechanical/prototype/foot_candidate/revC | 材料・ワッシャ実品・締付け・強度・公差 |
| 電池と変換器 | schematics/power/rc_supply_candidate.json | 出力過渡、セル保護、取付け、給電保護 |
| 変換器の代替 | schematics/power/pol_module_screen.json | 電圧窓が未成立。UBECへ追加する部品ではない |
| 既存2段保護案 | schematics/power/servo_ovp_candidate.json | OVP分圧、過渡、回生、故障記憶 |
| 保護の統合代替 | schematics/power/integrated_servo_protection_screen.json | 2段保護と排他的な比較。型番動作・故障復帰・遮断保証 |
| 手動再始動＋左右PG | schematics/power/manual_rearm_revJ/assembly.json | 電圧監視、起動状態回路、両側給電駆動、電源遷移 |

revJのPG受信部はrevIの単一受信部を置換する。抵抗はR15を含め19個、
局所コンデンサは17個。candidate_bom.csvの抵抗セット18個は別掲R15を除いた数。
足部revBでは旧足裏スペーサー2個を除去し、ワッシャ形状2個で置換。
ヨー取付板側の旧スペーサー8個とは区別する。

これらの数量修正は部品適合や製作許可ではない。任意の代替候補を混ぜて
質量・電圧降下・熱を合算しない。構成確定後に全体の質量と回路を更新する。

足部revCは外装固定ねじ8本と封入ナット8個を組立CADへ追加。revBの7部品/足は締結品を網羅していなかった。片足15部品の静的公称交差は0だが、完全な足部慣性・工具接近・締結強度は未確認。

訂正: 外装ねじ先端の天井干渉判定は既存穴を無視した誤判定だった。`validation/boot_tip_relief_v1`で元CADの8箇所を検査し、軸上の交差0を確認。逃げ追加案は不採用。径方向公差と有効ねじかかりは未確認。

外装ねじ穴: `validation/boot_bore_clearance_v1`で16箇所の通過穴径2.3 mmを確認。既存の印刷面誤差仮定では通過を保証できない。大径化は頭受け面積を減らすため、2.3 mm仕上げ後加工を優先比較するが、封入ナットを傷つけない工具・加工深さ・公差の設計が必要。
