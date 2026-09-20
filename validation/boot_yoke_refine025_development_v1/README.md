# 0.25 mmへの局所接触細分化：接触圧未収束

同じ形状・荷重・材料・係数で両部品を0.25 mmへ細分化。計算完了・合反力・めり込み基準は合格。最大接触圧4.335233 MPaは0.35 mmから11.3724%変化し、収束基準10%に不合格。変位変化はブーツ2.468%、ヨーク1.195%で5%以内。

細分化により圧力最大値は下がっているが、繰返し収束条件を満たしていない。単に小さい値を採用せず、要素・接触面分割の影響も見直す必要がある。局所切断、アンカー、材料・予圧・全身荷重などの制限は継続し、締結強度・製造承認なし。

## 保存と再現

大きいDAT/FRDはgzipで保存し、compression.jsonに圧縮前SHAとサイズを記録。圧縮後に全バイト一致を確認した。評価器はcontact.dat.gzを直接読み、既存0.35 mmケースで非圧縮結果との完全一致も確認済み。

engineering環境とLD_LIBRARY_PATHを設定し、mesh_boot_nut_patch.pyとmesh_local_yoke_contact.pyへ --mesh-mm 0.25 --out <新規先>を指定。probe_boot_yoke_contact.pyへ --mesh-mm 0.25 --boot-mesh-dir <ブーツ先> --yoke-mesh-dir <ヨーク先> --out <新規接触先>を渡す。evaluate_boot_yoke_contact.py --source <接触先>で判定。compare_boot_contact_refinement.py --source <plan.jsonとcontactを持つ親>で比較する。

圧縮データの再評価は本フォルダのcontactを--sourceに指定する。FRDの可視化時は別の作業ディレクトリへ展開する。過去の不合格証跡を保持した。
