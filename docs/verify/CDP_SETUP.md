# CDP 驗證環境啟動方式（Chrome DevTools Protocol, port 9222）

> **用途**：`docs/verify/cdp_*.py` 這批驗證／量測腳本都以 CDP 連 `http://127.0.0.1:9222`
> （`fetch /json/new?about:blank` 開分頁 → WebSocket `Input.dispatchMouseEvent` /
> `Emulation.setDeviceMetricsOverride` / `Runtime.evaluate`）。**跑腳本前必須先有這個瀏覽器**。
>
> **最後更新**：2026-10-09（首頁 BC 動態模組 `#bc-bg-footer` 自頁尾移到最上方當第一個 hero、
> GUNTE hero 下移 → `cdp_verify_footer_scroller.py` 追加 J11–J15：第一 section ＝ `.hero.bc-bg-hero`、
> 載入即在首屏（`rect.top` 0）、`computed margin-top` 0px、DOM 順序在 `.bc-gunte-hero` 之前、
> 且全頁已無 `footer` 元素；同日稍後追加 J16–J19：置頂 hero 去掉頁尾感（`index.html` extra_css 覆寫
> `.grid.is-footer{border-top:0 none}` ＋ `#bc-bg-footer`/`.footer{background:transparent}`）——
> J16 分隔線已移除且 `padding-top` 未動、J17 黑底已透明（由頁面底色 `bg_4.jpg` 穿透）、
> J18 覆寫錨點＝`SECTION.hero.bc-bg-hero` 只命中首頁、J19 `goto /about/` 反向守門（真頁尾仍保有
> `1px solid` 分隔線 ＋ `#0e0e0e` 黑底）；該檔項目數 **111 → 116 → 120**。
> 另新增 `cdp_shot_index_hero_viewport.py`＝新 hero 的 3 斷點視窗截圖（含捲到 GUNTE hero 的第二張））
>
> 沿革：2026-10-06 配合圖片斷言復原（行動／平板恢復顯示圖片）時確認，347 → 355。
>       2026-10-08 `cdp_verify_top_art.py` 隨 `.top_art` 模組自首頁移至 `/about/`、
>       改連 `http://localhost:8081/about/`，並追加 3 項「位置」斷言——模組須緊接
>       `.bc-fujiya-photo` 之後、後接既有 `.ftco-section-blank`；腳本項目數 355 → 367。
>       2026-10-09 `cdp_verify_footer_scroller.py` 的跨頁基準自首頁 `/`（已改用 `#bc-bg-footer`）
>       改指向 `/coffee_menu/`（唯一仍渲染靜態 `.ftco-footer` 的頁面），並新增 J 系列驗首頁保真。

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
python3 docs/verify/cdp_verify_top_art.py          # 關於頁 /about/ 的 .top_art 模組（367 項）
python3 docs/verify/cdp_verify_floating_cart.py    # 浮動購物車（5 斷點 × 4 頁，25 項）
python3 docs/verify/cdp_verify_footer_scroller.py  # 首頁 BC 動態 hero ＋ /coffee_menu/ 頁尾跑馬燈（3 斷點，120 項）
python3 docs/verify/cdp_shot_index_hero_viewport.py # 首頁新 hero 外觀截圖（3 斷點 × 2 張；只截圖＋印幾何，無斷言）
```

- 腳本會自己 `PUT /json/new?about:blank` 開一個分頁、跑完 `Page.close`；**不會**動到 9222 那個
  `about:blank` 常駐分頁。
- 需要 DJANGO 站台同時在跑（本機 `python3 manage.py runserver 8081`）。
- ⚠️ **改過 `templates/**` 之後要重啟站台再跑腳本**：Django 4.1+ 的 `TEMPLATES` 預設使用
  `cached.Loader`，長時間執行的 `runserver`（尤其 `--noreload`）會把舊的編譯結果留在記憶體，
  `curl` 會看到舊 HTML，驗證腳本量到的也是舊 DOM（現象＝改了 template 卻「怎麼跑都一樣」）。
  重啟方式：`pkill -f 'manage.py runserver 8081'` 後重新啟動（或對任一 `.py` 存檔觸發 autoreload）。
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
