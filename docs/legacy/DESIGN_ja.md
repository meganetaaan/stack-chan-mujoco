# 実装仕様

## 対象モデルと座標

`assets/r5a/scene.xml` はR5のA案からコピーした元ファイルです。元ZIPと各assetのSHA-256を `SOURCE_MANIFEST.json` に記録しています。モデルの差し替えは学習済みpolicyとのI/Oチェックで検出します。B案への自動切替はありません。

座標は +Xが前（画面側）、+Yが左、+Zが上です。`base` の原点はボディ下部であり、床から頭頂までの全高やCOM高さではありません。homeのbase zは約0.08458 mで、評価高さはここを基準にします。

`home` キーフレームを使います。全関節ゼロは有効な初期姿勢ではありません。表示用と学習用で同じ物理量を使い、学習用では `vis_*` という、質量0・衝突無効の描画専用geomだけを外します。

## 制御ブロック

```text
61次元観測
  → PPO MLP actor（128,128 / Tanh、50 Hz）
  → 10次元action [-1,1]
  → home + 関節ごとの角度オフセット
  → 関節目標範囲・外向き開脚ガード
  → 目標角度のslew制限（2 rad/s）
  → 元仕様の指令遅延（10 ms）
  → PD（1 kHz）
  → 元上限と回転速度に応じたトルク制限
  → gear=1のMuJoCo motor（data.ctrl はN·m）
  → freejointを持つ本体と接触シミュレーション
```

PDは `tau_raw = kp * (q_delayed_target - q) - kd * qd` です。元設定のkp=3 N·m/rad、kd=0.065 N·m·s/radを使います。目標角度をMuJoCoのmotorに直接代入することはしません。

| 関節（左右共通） | サーボ種 | 元シミュレーション上限 | action=±1の角度オフセット |
|---|---|---:|---:|
| 股roll | XC330-M288-T | ±0.45 N·m | ±0.14 rad |
| 股pitch | XL330-M288-T | ±0.26 N·m | ±0.35 rad |
| 膝 | XC330-M288-T | ±0.45 N·m | ±0.45 rad |
| 足首pitch | XL330-M288-T | ±0.26 N·m | ±0.35 rad |
| 足首roll | XL330-M288-T | ±0.26 N·m | ±0.14 rad |

上表は本モデルの設定であり、メーカーの連続定格ではありません。トルクと速度が同符号の力行側では無負荷速度へ近づくにつれて出力を減らします。逆符号の制動側は元トルク上限以内に保ちます。これは単純化した近似で、実モーターの電圧・電流・温度依存性の同定結果ではありません。MicroDuckのBAMパラメーターは使っていません。XMLにある摩擦・dampingを再度外付けして二重計算しない構成です。

観測前処理は固定物理スケールです。`VecNormalize` を使わないので、学習時・評価時の統計ファイル取り違えがありません。ただしモデル・意味・スケールが同一であることを `interface.json` で要求します。

## 観測 61次元

配列の範囲はPythonの `[start:stop]` です。

| 範囲 | 内容 | スケーリング |
|---|---|---|
| 0:3 | body座標の重力方向 | 単位ベクトル |
| 3:6 | baseの並進速度 | 初期heading座標、m/s ×5 |
| 6:9 | body角速度 | body座標、rad/s ×0.25 |
| 9:19 | homeからの関節角差 | actionの角度スケールで除算 |
| 19:29 | 関節角速度 | rad/s ×0.1 |
| 29:39 | 直前のaction | [-1,1] |
| 39:49 | slew後の関節目標−home | actionの角度スケールで除算 |
| 49:52 | 速度指令vx,vy,wz | ×[5,5,0.5]。現版は前進vxだけ使用 |
| 52:53 | base高さ誤差 | m /0.05 |
| 53:55 | 目標位置からのXYずれ | 初期heading座標、m /0.1 |
| 55:57 | heading誤差 | sin,cos |
| 57:59 | 左右の実接触フラグ | 0/1 |
| 59:61 | 歩容位相 | sin,cos。停止時は両方0 |

最後に全要素を±10にclipし、float32で返します。絶対yaw・絶対XY位置をそのまま入力せず、エピソード開始時を基準にします。四元数の規約はMuJoCoのwxyzです。姿勢の重力投影、body角速度、速度指令の座標系を混同しません。

速度・高さ・接触などはシミュレーターの真値を含みます。実機向けには推定器か観測仕様の再設計が必要です。

## 報酬と成功判定を分離

立位では直立、home付近の高さ、低い速度、位置維持、両足支持を報酬にします。歩行では前進指令への追従、向き、姿勢を評価し、左右交互の接触位相と6 mm程度の足上げへ弱い誘導を与えます。停止指令には離床・着地報酬を与えません。

過大な関節速度、角速度、トルク、機械的パワー、action変化、接地点の水平速度、飽和、不要な飛行を罰します。滑りは足先siteの速度だけでなく、足の角速度と接触点の位置を用いて接触点速度を近似します。

継続的な報酬は「1秒あたりの値 × 方策dt」で加算します。着地のイベント報酬と転倒罰則はdtを掛けません。時間制限は `truncated=True`、転倒・異常は `terminated=True` とし、学習時の価値のブートストラップを区別します。報酬の具体的重みは `config.py` と `configs/walk.json` です。

### 立位の合格基準（初期設定）

10秒完走、非足底床接触なし、自己接触なし、base高さがhomeの80%以上、傾き最大15°以下、開始位置からの水平ずれ最大35 mm以下、最初の0.5秒を除いた両足支持率80%以上です。

### 歩行の合格基準（初期設定）

12秒完走、共通の接触・高さ条件、傾き最大25°以下、横ずれ50 mm以下、headingずれ20°以下、前進速度誤差平均0.03 m/s以下、指令積分距離の50%以上かつ25 mm以上の実前進を要求します。左右それぞれ2回以上の有効着地と、着地系列で3回以上の左右交代、飛行割合15%以下も要求します。

有効着地は、いったん実接地した足が0.08秒以上離床し、2 mm以上浮き、離床中の半分以上を反対足が支えたものとします。初期落下、チャタリング、ずり歩き、両足を浮かせるだけで着地数を稼ぐ経路を抑えるための定義です。運動の自然さ・エネルギー・実機実現性を保証する定義ではありません。

成功判定には方策周期50 Hzの観測を使います。これは実接触に基づく評価ですが、サブミリ秒の全接触イベントを検出する連続検証ではありません。サーボのピークトルクと二乗平均は1 kHzの内部ループから集計します。

## 終了条件

角度35°超の転倒、base高さ逸脱、足底以外と床の接触、閾値を超える自己接触、関節限界の超過、過速度、外向き開脚の探索ガード超過、非有限状態、MuJoCoの数値警告／自動リセットを検出したらterminatedにします。終端には正の報酬を付けず転倒罰則だけを返します。

時間制限完走は必ずしも成功ではありません。例えば、傾き20°で全時間持ちこたえても立位成功基準15°を超えるので不合格です。大きな報酬や `best/` 保存を「立てた」「歩けた」の代わりにしません。

## 再現性と保存

Python側のseed、Gymnasiumのreset seed、SB3のseedを設定します。学習用seed、学習途中の重み選択用seed、最終評価用seedを分けます。異なるOS・BLAS・バージョン・プロセス数を跨ぐビット単位の一致は保証しません。

チェックポイントは一時ディレクトリに書き終えてから置換し、ファイル更新の例外時には元のディレクトリへ戻します。電源断を含むあらゆる障害に対するトランザクション保証ではありません。中途半端なフォルダーを誤って読み込まないよう、`READY` と全必須ファイルの存在を確認します。

`--resume` はSB3のweightsとoptimizerを再利用します。`--init-from` はactor/criticのweightsだけをコピーし、optimizerを新規にします。後者で立位→歩行のタスクを変えられますが、I/O契約は変えられません。

ログには `config.json`, `interface.json`, 実行環境バージョン、各評価、Monitor CSV、エピソード終了理由、必要に応じて関節角・指令・トルクの時系列を保存します。ユーザー側で成功した環境の `python -m pip freeze` を別途保存するとバージョンも固定できます。配布時のrequirementsは実行検証済みの固定版ではありません。

## 設定を追加する方法

例えば、立位の初期傾きを少し増やす設定は `configs/stand_tilt.json` を次の内容で作成します。

```json
{
  "extends": "stand.json",
  "env": {
    "reset_tilt_deg": 3.0
  }
}
```

```bash
python train.py --config configs/stand_tilt.json \
  --init-from runs/stand/best --run-dir runs/stand_tilt
```

JSONの未知キー、継承の循環、batch_sizeと環境数の不整合を検出します。相対の `extends` は設定ファイルの所在から解決し、モデルパスはプロジェクトのルートから解決します。保存時のconfigは継承を展開した完全な値になります。

## API照合元

以下は実装に使用した公式APIの参照先であり、このロボットの歩行を検証する資料ではありません。

- MuJoCo Python（MjModel/MjData、passive viewer）: `https://mujoco.readthedocs.io/en/stable/python.html`
- MuJoCo API（jacobian、contact force等）: `https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html`
- SB3 PPO（CPU、MLP、学習・保存・再読込み）: `https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html`
- SB3 Custom Environment: `https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html`
- SB3 Vectorized Environments: `https://stable-baselines3.readthedocs.io/en/master/guide/vec_envs.html`
- SB3 Monitor 2.6.0: `https://stable-baselines3.readthedocs.io/en/v2.6.0/common/monitor.html`
- Gymnasium Time Limits: `https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/`
