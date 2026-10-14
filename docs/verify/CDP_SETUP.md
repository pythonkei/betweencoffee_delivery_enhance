# CDP 驗證環境啟動方式（Chrome DevTools Protocol, port 9222）

> **用途**：`docs/verify/cdp_*.py` 這批驗證／量測腳本都以 CDP 連 `http://127.0.0.1:9222`
> （`fetch /json/new?about:blank` 開分頁 → WebSocket `Input.dispatchMouseEvent` /
> `Emulation.setDeviceMetricsOverride` / `Runtime.evaluate`）。**跑腳本前必須先有這個瀏覽器**。
>
> **最後更新**：2026-10-14（首頁 hero `#bc-clock` 加入 about 頁的天氣/時鐘元件（在左側 `{` 之上、
> +30%，`--wc-scale:1.3`）＋ 照片列每張照片下方加「名稱 + highlight」。新增本清單第一支腳本
> `cdp_verify_hero_weather.py`（**208 項**：A 結構／B 幾何（與 7 個時鐘子項 0 重疊、在 `{` 之上、
> 欄位與改動前逐值相同）／C `--wc-scale` 與 ×1.3 逐值／D 內容填充／E 首頁 navbar 那顆仍隱藏且未縮放／
> F 照片列文字（name＝img alt、highlight 品牌金、照片高度不變）／G `/about/` 反向守門）；
> 另改寫 3 支既有腳本的過時斷言 → **cdp_verify_clock_braces.py 112/112**（E1 可見子項 7→8，
> index 多出天氣那一格；about 仍 7）、**cdp_verify_hero_coffee_photos.py 128/128**
> （D5 改驗 `<a>` display:flex、D7 改驗「img 橫向撐滿 `<a>`、高度 = `<a>` 高 − 文字高」，
> 新增 D9–D11 文字斷言）、**cdp_verify_floating_cart.py 25/25**（`bc-weather.js` 的載入斷言由
> 「非 about 不載入」改為「index 需載入、非 about/index 不載入」）；`cdp_verify_bg_footer.py` 與
> `cdp_verify_footer_scroller.py`（127 項）回歸全過。驗證跑法：`bash` 先啟動本清單的 CDP 指令，
> 再 `timeout 240 python3 docs/verify/cdp_verify_hero_weather.py`（約 50 秒／7 斷點）。）
>
> **前次（2026-10-13）**：首頁順序再反轉 —— GUNTE hero 回到「第一眼看到的第一屏」、BC 動態 hero
> `#bc-bg-footer` 下移到它之後；`index.html` 的 `.bc-reviews-section` 加 `hidden` →
> `cdp_verify_footer_scroller.py` 的 J11–J14 改寫：第一個「可見」section ＝ `.hero.bc-gunte-hero`、
> DOM 第一個 section ＝ `.bc-reviews-section`（`display:none`）、`.bc-gunte-hero` 在文件順序上在
> `.bc-bg-hero` 之前、載入時 GUNTE hero `rect.top` 0（`scrollY` 0、無 100px 空隙）且 `#bc-bg-footer`
> 接在其後（不重疊）、兩塊 hero `computed margin-top` 皆 0px；同日另追加 K1–K4：GUNTE hero 環形字
> markup 修正（非法的 `<hidden text>…</text>` → `<text class="bc-ring-hide">`，只有 BUTTER KING 顯示，
> 由 `bc-gunte-hero.css` 的 `display:none` 隱藏）；同日稍後追加 K5–K7：環形字尺寸改由 viewBox 單位表達
> （`font-size: 24px → calc(24px * 540 / 432)`＝30、`stroke-width: 1.5 → calc(1.5 * 540 / 432)`＝1.875、
> 手機 2 → 2.5）＋ Splide **`start: 3 → 1`**（⚠ Splide 的 `start` 是 0-based 索引：實測 `start: 2`
> 置中的是 `aria-label="3 of 7"`＝第 3 張「果香浅煎」、環形字仍被 `.bc-ring-hide` 隱藏 →
> `start: 1` 才是 DOM 第 2 張 BUTTER KING）＝載入當下就看得見環形字；
> 該檔項目數 **120 → 124 → 127**（PASS 127 / FAIL 0）。
> 前次（2026-10-09）：BC 動態模組置頂當第一個 hero（J11–J15：第一 section ＝ `.hero.bc-bg-hero`、
> 載入即在首屏、`margin-top` 0px、DOM 順序在 `.bc-gunte-hero` 之前、全頁已無 `footer` 元素）；
> 同日稍後追加 J16–J19：置頂 hero 去掉頁尾感（`index.html` extra_css 覆寫
> `.grid.is-footer{border-top:0 none}` ＋ `#bc-bg-footer`/`.footer{background:transparent}`）——
> J16 分隔線已移除且 `padding-top` 未動、J17 黑底已透明（由頁面底色 `bg_4.jpg` 穿透）、
> J18 覆寫錨點＝`SECTION.hero.bc-bg-hero` 只命中首頁、J19 `goto /about/` 反向守門（真頁尾仍保有
> `1px solid` 分隔線 ＋ `#0e0e0e` 黑底）；項目數 111 → 116 → 120。
> 另新增 `cdp_shot_index_hero_viewport.py`＝新 hero 的 3 斷點視窗截圖（含捲到 GUNTE hero 的第二張））
>
> 沿革：2026-10-06 配合圖片斷言復原（行動／平板恢復顯示圖片）時確認，347 → 355。
>       2026-10-08 `cdp_verify_top_art.py` 隨 `.top_art` 模組自首頁移至 `/about/`、
>       改連 `http://localhost:8081/about/`，並追加 3 項「位置」斷言——模組須緊接
>       `.bc-fujiya-photo` 之後、後接既有 `.ftco-section-blank`；腳本項目數 355 → 367。
>       2026-10-09 `cdp_verify_footer_scroller.py` 的跨頁基準自首頁 `/`（已改用 `#bc-bg-footer`）
>       改指向 `/coffee_menu/`（唯一仍渲染靜態 `.ftco-footer` 的頁面），並新增 J 系列驗首頁保真。
>       2026-10-13 首頁順序反轉（GUNTE hero 回第一屏、BC 動態 hero 下移）→ 該檔 J11–J14 改寫、
>       新增 K1–K4（GUNTE 環形字 markup 修正），項目數 120 → 124。
>       2026-10-13 稍後追加 K5–K7（環形字尺寸 ×1.25：改以 viewBox 單位 `calc(24px*540/432)`＝30、
>       描邊同步 1.875；Splide `start 3 → 1` 讓載入當下置中的是 BUTTER KING；K7 量測分三段 ——
>       逼 frame 前先記下載入時那張、用 `Page.captureScreenshot` 逼 frame 讓 CSS transition 前進、
>       收尾補 `Page.close`），項目數 124 → 127。

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
python3 docs/verify/cdp_verify_hero_weather.py     # 首頁 hero #bc-clock 的天氣/時鐘元件（{ 之上、+30%）＋照片列名稱/highlight（7 斷點 × A–F ＋ /about/ 反向守門 G，208 項）
python3 docs/verify/cdp_verify_top_art.py          # 關於頁 /about/ 的 .top_art 模組（367 項）
python3 docs/verify/cdp_verify_floating_cart.py    # 浮動購物車（5 斷點 × 4 頁，25 項）
python3 docs/verify/cdp_verify_footer_scroller.py  # 首頁 hero 順序（GUNTE 第一屏）＋ 環形字尺寸／載入可見性（K1–K7）＋ /coffee_menu/ 頁尾跑馬燈（3 斷點，127 項）
python3 docs/verify/cdp_shot_index_hero_viewport.py # 首頁新 hero 外觀截圖（3 斷點 × 2 張；只截圖＋印幾何：ttlFont/ttlStroke、loadIndex/loadAriaLabel/loadRevealed、activeSlideIndex，無斷言）
```

- ⚠️ **CSS transition 在本機 CDP「不會自己前進」→ 量「淡入後」的值必須逼 frame**：headful
  （`DISPLAY=:0`）實測 `el.getAnimations()` 的 CSSTransition 會停在 `playState='running'` 但
  `startTime=null`／`currentTime=0` 的 pending 狀態 → computed opacity 一直是過渡起點，等 15 秒也不動。
  解法＝用 `Page.captureScreenshot`（`{"format":"jpeg","quality":10}`、結果丟棄）逼出 frame，
  transition 才會前進（實測 0 → 0.30 → 1）：`cdp_verify_footer_scroller.py` 的 K7 與
  `cdp_shot_index_hero_viewport.py` 都這樣做。
  ⚠ 逼 frame 同時會讓 `setInterval`／Splide autoplay 真的走動 → 「載入時」的狀態必須在逼 frame
  **之前**先記下（本輪做法：`window.__bcHeroLoadIndex`，斷言讀 `*_at_load` 欄位）。
- ⚠️ **`Page.captureScreenshot` 可能卡死整支腳本**（等不到 frame，無回應）→ 一定要用
  `asyncio.wait_for` 包逾時（本輪 3 秒）；且每個 `cdp_*.py` 跑完要 `Page.close` 自己開的分頁 ——
  否則每跑一次留一個分頁，殘留多個背景分頁時 compositor 不再為本分頁產 frame（實測殘留 5 個時踩到）。

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
