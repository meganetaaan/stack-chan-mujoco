
### LOGIC入力保護の端子接続候補

`schematics/power/logic_input_branch_candidate_v1/branch.json` にTPS26601RHFRの全端子、抵抗とバイパス接続先を具体化。RTN/EPとGNDは別ネットで、逆接保護を維持する。24端子とNC一覧を資料照合済み。製作・主回路統合は未完。RILIM=120kΩは推奨上限そのもので、正の部品公差を許容できないことを追加阻害要因として記録。抵抗選定、起動、放電、電池保護の未成立は残り、Issueを閉じない。
