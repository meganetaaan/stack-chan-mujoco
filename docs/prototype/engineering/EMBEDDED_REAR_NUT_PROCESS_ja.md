# 造形途中に金具を挿入する背面接合候補

次の接触解析では、側方に開いたナットポケットを閉じた形状にし、造形途中に座金・角ナットを配置する候補を使用する。四隅の位置y=±57 mm、z=8/120 mmと外形は維持する。金具の交換性は低下し、ねじ損傷時には胴体交換が必要となる可能性がある。

## 部品と形状

角ナットは既存候補の[Accu HFSN-M3-A4 DIN562](https://www.accu.co.uk/flat-square-nuts/21333-HFSN-M3-A4)。内側座金を[Accu HRDW-M3-A4 DIN433](https://www.accu.co.uk/metric-flat-washers/404911-HRDW-M3-A4)へ変更する。公表寸法は外径6.0 mm（+0/−0.3）、内径3.2 mm（+0.18/−0）、厚さ0.5 mm（±0.05）。ナット幅は5.5 mm（+0/−0.4）、厚さ1.8 mm（+0/−0.4）。材質表記のみからねじ耐力を確定しない。

閉じたポケットは幅6.6 mm、奥行き2.9 mm、x=-56.2〜-53.3 mm。座金の支持面を実形状のx=-56.2 mmに合わせ、CAD上で接触距離ゼロ・体積交差なしを確認した。以前の側方挿入候補には、座金支持面を0.1 mm深く削る形状が含まれていたため、この候補ではそれを引き継がない。

胴体各面±0.2 mmと部品の公表公差を用いた最小総すきまは、座金幅方向0.20 mm、ナット幅方向0.70 mm、座金とナットを合わせた奥行き方向0.15 mm。いずれも事前基準0.10 mmを満たす。座金径の縮小により支持面積が減るため、座面圧は新しい接触モデルで再評価する。

## 工程のCAD検査

胴体の背面を造形面とし、元座標+Xへ積層する。出力STEPのプリンター座標は128×128 mmの平面、造形高さ126.2 mm。均一な層高0.2 mmを仮定し、高さ8.8 mm（元座標x=-53.4 mm、44層相当）の、ポケット屋根を作る前で停止する。実際にはスライサー上で屋根の開始層を確認して停止位置を設定する。

停止時点までのCAD形状を切り出し、座金→角ナットの順で+X側から着座位置まで動かす全範囲を検査した。4箇所とも体積交差0.01 mm³超はなく、座金の着座も確認した。金具が完全に着座した前提では、支持面と金具厚さの最悪組合せでも上端x=-53.65 mmとなり、停止面より0.25 mm低い。事前基準0.20 mmを満たす。

屋根の造形を再開する前に、金具の着座・向き・同軸位置を確認し、仮置き工具をすべて取り除く。ポケット内の金具は浮動するため、後工程のねじ掛かり・位置合わせは別途確認する。

## 判定範囲

CADによる工程形状・挿入・高さ積上げの予備基準に合格。実機プリンターの対応、G-code、ノズル以外のヘッド形状、ブリッジ・熱・密着・再開品質を検証した結果ではない。座金・ナットのねじ強度、締付け・予圧、保持壁・胴体ボス・背面板の接触と強度も未完了。製造リリースやEPIC完了とはしない。

## 再現

```sh
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/build_captive_rear_nuts.py --out outputs/embedded_nuts_new --slot-width-mm 6.6 --loading-mode embedded
LD_LIBRARY_PATH="$PWD/.tools/root/usr/lib/x86_64-linux-gnu" .venv-engineering/bin/python software/sim/structural/check_embedded_nut_process.py --candidate outputs/embedded_nuts_new --out outputs/embedded_process_new
```

現在の解析対象を`board/mechanical/engineering/rear_connection_candidate.json`に記録する。証跡は`validation/jig_stiffness_embedded_development_v1`。旧y=±59 mmの理想固定解析、側方ポケットの強度結果を流用しない。
