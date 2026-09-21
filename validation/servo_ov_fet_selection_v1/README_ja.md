# 過電圧遮断FETの選定比較

[ADI LTC4365 Rev.B](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4365.pdf)
はVIN=VOUT=5V、IGATE=-1µAでGATE−VOUT最小3V。
したがって「チャージポンプあり」を根拠に4.5Vまたは10V駆動時の抵抗を採用しない。
背中合わせFETの実ソース電圧と、5V以外での駆動余裕も別途確認する。

初期比較の[TI CSD17577Q3A](https://www.ti.com/lit/ds/symlink/csd17577q3a.pdf)は
オン抵抗が4.5V／10V条件で規定され、今回の3V駆動での最大値を使えないため見送る。
しきい値電圧は大電流を流すときの低抵抗保証ではない。

[Vishay SiSS80DN-T1-GE3](https://www.vishay.com/docs/77684/siss80dn.pdf)を候補にする。
2.5V駆動で最大3mΩ、VDS20V、VGS+12/−8V、PowerPAK1212-8S。
左右各2個の背中合わせ構成、計4個。熱設計と遮断過渡は未適合。

25°C抵抗を使う単純比較では、1脚のモデル上限4.917Aで
2×3mΩによる降下29.502mV、損失145.061mW（2個合計）。
高温・ゲート電圧・実電流の保証を含む最悪値ではなく、全配電の合格でもない。
モデル上限は`validation/model_dc_envelope_v2/`の条件付き理想回路値。

次の終了条件：実配線で両FETのVGS範囲を求め、その範囲・温度での抵抗と損失、
ゲート電荷・遮断時間・SOA・寄生インダクタンスに対する耐量を同じ部品で照合する。
温度の典型曲線やゲート電荷の典型値を保証最大へ読み替えない。
VDS20Vという値だけで3S側の故障・リンギングに適合したとしない。
手はんだの適否を含むメーカー実装指示と基板の放熱条件も製作条件へ含める。

選定状態は`schematics/power/servo_ovp_candidate.json`。製造BOMへの確定は保留。
