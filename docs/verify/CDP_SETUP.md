# CDP 驗證環境啟動方式（Chrome DevTools Protocol, port 9222）

> **用途**：`docs/verify/cdp_*.py` 這批驗證／量測腳本都以 CDP 連 `http://127.0.0.1:9222`
> （`fetch /json/new?about:blank` 開分頁 → WebSocket `Input.dispatchMouseEvent` /
> `Emulation.setDeviceMetricsOverride` / `Runtime.evaluate`）。**跑腳本前必須先有這個瀏覽器**。
>
> **最後更新**：2026-10-06（配合 `cdp_verify_top_art.py` 的圖片斷言復原——行動／平板恢復顯示圖片——時確認；腳本項目數 347 → 355）

## ⚠️ 本機踩雷：不要用 snap 版 chromium

`/snap/bin/chromium`（Chromium 154 snap）**即使指定了不同的 `--user-data-dir` 也會把新啟動
轉給使用者正在用的那個實例**，只會印出：

```
Opening in existing browser session.
```

→ 除錯埠**不會**開起來（`curl http://127.0.0.1:9222/json/version` 連線被拒），而且不會有任何
錯誤訊息。**必須另找非 snap 的 Chromium 執行檔**。

本機可用的替代品＝**Playwright 內附的 chromium**（非 snap、可直接背景常駐）：

```
/home/kei/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome
```

（路徑可用 `find ~/.cache/ms-playwright -maxdepth 3 -type f -name chrome` 重新確認；
`chromium-1234` 之後可能隨 Playwright 更新而變號。）

## 啟動指令（在專案根目錄執行）

```bash
mkdir -p /tmp/bc_cdp_profile
setsid nohup env DISPLAY=:0 \
  /home/kei/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/bc_cdp_profile \
  --no-first-run --no-default-browser-check \
  --disable-gpu --disable-dev-shm-usage \
  about:blank > /tmp/chromium_cdp.log 2>&1 < /dev/null &
disown
```

要點：

- **`setsid … & disown` ＋ `< /dev/null` 是必要的**：直接 `nohup … &` 在本工具的非互動 shell 內
  會隨 shell 結束被一起收掉（現象＝啟動後 `ps` 找不到、log 空白）。
- **`--user-data-dir` 要用獨立路徑**，否則會與使用者的瀏覽器互相搶 profile。
- `DISPLAY=:0` 為 headful（與既有 335／347／355 項驗證的環境一致，避免 headless 造成幾何差異）；
  `--disable-dev-shm-usage` 避免 `/dev/shm` 過小造成當掉。
- 連線檢查：

```bash
curl -s --max-time 5 http://127.0.0.1:9222/json/version
# → {"Browser":"Chrome/151.0.7922.34", …, "webSocketDebuggerUrl":"ws://127.0.0.1:9222/devtools/browser/…"}
```

## 執行驗證

```bash
python3 docs/verify/cdp_verify_top_art.py          # 首頁 .top_art 模組（355 項）
python3 docs/verify/cdp_verify_floating_cart.py    # 浮動購物車（5 斷點 × 4 頁，25 項）
```

- 腳本會自己 `PUT /json/new?about:blank` 開一個分頁、跑完 `Page.close`；**不會**動到 9222 那個
  `about:blank` 常駐分頁。
- 需要 DJANGO 站台同時在跑（本機 `python3 manage.py runserver 8081`）。
- 單次執行約 1～2 分鐘（4 個 viewport × 逐頁量測）；輸出量大，建議導到檔案再 grep：

```bash
setsid nohup python3 docs/verify/cdp_verify_top_art.py > /tmp/verify_top_art.log 2>&1 < /dev/null &
sleep 60; grep -c PASS /tmp/verify_top_art.log; grep FAIL /tmp/verify_top_art.log
```

## 關閉

```bash
pkill -f 'remote-debugging-por[t]=9222'   # 注意：[t] 括號技巧
pgrep -af 'debugging-por[t]=9222'         # 應為空
ss -ltn | grep -c 9222                    # 應為 0
```

- ⚠️ **不要寫成 `pkill -f 'remote-debugging-port=9222'`**：下這道指令的 shell，其命令列本身就含
  這個字串 → pkill 會**連自己的 shell 一起殺掉**（現象＝指令回報 `Command terminated by signal
  SIGTERM`、後面的檢查全部沒跑到）。用 `por[t]` 讓字面字串不等於自己（regex 才匹配）。
- 只會殺掉帶此旗標的驗證用實例，**不影響使用者自己的瀏覽器**；Django（8081）與此無關、不會被動到。
- 關閉後 `curl http://127.0.0.1:9222/json/version` 應連線被拒（若還要再跑腳本，重新執行上面
  的啟動指令即可）。
