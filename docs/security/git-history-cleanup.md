# Git 歷史機密清理 + 金鑰輪換指引

> 2026-09-06 安全掃描發現：`init` commit（2026-02-14）曾包含
> `keys/alipay_private_key.pem`、`keys/alipay_public_key.pem`、
> `betweencoffee_delivery/keys/private.key`、`public.key`。
> 2026-08-01 `46fb0d3a` 才從 git 移除。**Repo 為公開** → 此期間歷史人人可讀。

## ⚠️ 步驟 0：先確認（最重要）
在支付寶開放平台確認目前商戶金鑰是否為 8/1「金鑰輪換」後的新鑰。
**沒有十足把握就直接再輪換一次**（後台重產生 + 更新本機 `keys/` + 重新上傳公鑰），不要賭。

## 步驟 1：清除 git 歷史中的金鑰 blob
```bash
pip install git-filter-repo
git filter-repo --path keys/ --path betweencoffee_delivery/keys/ --invert-paths
git remote add origin https://github.com/pythonkei/betweencoffee_delivery_enhance.git
git push --force --all
git push --force --tags
```
> 注意：`filter-repo` 會改寫所有 commit hash；如有其他 clone/合作者需重新 clone。
> 執行前先備份：`git clone --mirror . repo-backup.git`

## 步驟 2：確認殘留為零
```bash
git rev-list --all --count            # hash 已全改寫
git log --all --oneline -- keys/      # 應無輸出
git ls-tree -r HEAD --name-only | grep -iE 'pem|key|secret'   # 應無輸出
```

## 步驟 3：repo 改 private（建議）
GitHub → Settings → Danger Zone → Change repository visibility → Private。
Render 用私人 repo 佈署不受影響。

## 長期防護
- 機密永不進 repo（`.env`、`keys/`、`*.pem` 已在 `.gitignore`，保持）
- API key 只放環境變數/密碼管理器；**每季 rotation**
- Anthropic / GitHub Console 設用量上限與告警、啟用 2FA
- 不把 key 貼進任何 prompt、issue、截圖
- 只安裝官方/知名 MCP 套件，安裝前檢查實際套件名與參數
