# CDP 驗證環境啟動方式（Chrome DevTools Protocol, port 9222）

> **用途**：`docs/verify/cdp_*.py` 這批驗證／量測腳本都以 CDP 連 `http://127.0.0.1:9222`
> （`fetch /json/new?about:blank` 開分頁 → WebSocket `Input.dispatchMouseEvent` /
> `Emulation.setDeviceMetricsOverride` / `Runtime.evaluate`）。**跑腳本前必須先有這個瀏覽器**。
>
> **最後更新**：2026-10-15 稍後（**首頁照片格 `#bc-clock-photos` 的桌機（≥992px）咖啡照片縮小 ＋
> 名稱／highlight 字級放大 —— 1440 時 280×400、字級 20/16px**；使用者指示「桌機的咖啡照片太大、
> 名稱與 highlight 太小」）：四處宣告全部落在 `templates/betweencoffee_delivery/index.html` 的
> extra_css，**未動任何 .css／.js ⇒ 無版號變更**：① `.footer-logo-list` 高 `480vw/ratio` →
> `400vw/ratio` ② `--bc-hand-img-w` `336vw/ratio` → `280vw/ratio`（＝400 ÷ 1.4286，仍精確整除）
> ③ `.bc-series-caption-name` 16 → 20px ④ `.bc-series-caption-highlight` 12 → 16px
> （⇒ `--bc-hero-caption-h` 49.59 → 60.39）。逐斷點照片尺寸：1905 = 370.41×529.14、1440 = 280×400、
> 1280 = 248.88×355.53、992 = 192.88×275.53；列高（＝cell 高）：1905 684.59 → 589.55、
> 1440 529.59 → 460.39、1280 476.25 → 415.94、992 380.25 → 335.94。**`.footer-logo-cell` 頂端／
> `#bc-bg-footer`／`.grid.is-footer` 的文件座標全程 Δ0（實測）**，列變矮 ⇒ 下方內容等量上移、
> 頁面總高 @1440 3936 → 3867；時鐘數字／`{ }` 隨列高置中**上移 34.6px**，天氣格 ↔ `{` 間距
> 136.8 → 102.2px（≥992px 各斷點 1905 = 154.0／1280 = 84.4／992 = 52.3px，皆遠大於 0），
> 連帶上一輪的已知代價「左鄰居咖啡與 `{` 重疊約 22px」縮到約 13px（像素級量測 @1440 本就是 0px、
> 992 由 7 → 3px、照片×山大黃球 @1440 由 723 → 381px）；**≤991px（991／768／390）逐值不變**
> （cell 寬高／list 高／caption 高／row 高／cell 內距／docHeight／字級 13-10／天氣↔`{` 間距全等於
> 改動前）。驗證：`cdp_verify_hero_coffee_photos.py` **193/193**（EXPECT 四列改為新值、`exp_img_w()`
> 336→280）＋回歸 `cdp_verify_hero_weather.py` **208/208**（F4 `4.80`→`4.00`×w/14.4、F5 `exp_cap`
> 60.39、F7 字級 20/16）／`cdp_verify_clock_braces.py` **112/112**／`cdp_verify_bg_footer.py` PASS／
> `cdp_verify_footer_scroller.py` **127/127**／`cdp_verify_clock_clash.py` **48 PASS / 2 FAIL**（2 條為
> 1440 的瞬態殘留 1578px、與改動前基準同值 ⇒ 既有環境抖動；明顯遮蔽 ≥2000px = 0 組）＋
> `manage.py check` 0 issue；截圖 `_verify_clock_photos_{1905,1440,1280,992,991,390}_{before,after}.png`
> （`before` 由 CDP 注入上一輪舊值即時產生）。**僅本機：已提交 `373f3bfd`（7 檔／142 insertions／60 deletions）、未 push、未部署**（正式站仍為 `ec8fcadb`）。
> 原：2026-10-15（**首頁照片格 `#bc-clock-photos` 的桌機（≥992px）咖啡照片放大 —— 1440 時
> 336×480**；使用者指示「桌機的咖啡照片放大到 1440 時 336×480，與 GUNTE hero 視覺同級」）：
> 三處宣告全部落在 `templates/betweencoffee_delivery/index.html` 的 extra_css，**未動任何 .css／.js
> ⇒ 無版號變更**：① `.bc-bg-hero … .footer-logo-cell` 於 `@media (min-width:992px)` 內
> `padding-top／padding-bottom: 0`（原 `u-40 + 14px`／`u-40`；這段留白「吸收」進照片區 ⇒ 照片頂緣
> 上移到時鐘列頂端）② `.footer-logo-list` 高 `276vw/ratio` → `480vw/ratio` ③ `--bc-hand-img-w`
> `193vw/ratio` → `336vw/ratio`（＝480 ÷ 1.4286）。⚠ **①的 media query 必須排在「+14px」那條規則
> 之後**：兩者特異度相同（1,2,0）⇒ CSS 以來源順序決勝，寫在前面會被蓋掉（第一版實測 padding-top 仍是
> 66.92／54／49.56px 而非 0，padding-bottom 因來源檔只有 (1,1,0) 故已生效）。逐斷點照片尺寸：
> 1905 = 444.5×635.0、1440 = 336.0×480.0、1280 = 298.7×426.7、992 = 231.5×330.7；**≤991px
> （991／768／390）逐值不變**（cell 寬高／list 高／caption 高／row 高／cell 內距／docHeight 全等於
> 改動前）。列高 @1440 419.6 → 529.6（+110）：`.footer-logo-cell` 頂端、`#bc-bg-footer`、
> `.grid.is-footer` 的**文件座標完全不動（實測 Δ0）**，只有列向下長、下方內容（`.footer-socials` 等）
> 等量下移、頁面總高 +110（3826 → 3936）；時鐘數字／`{ }` 隨列高置中 ⇒ 下移 55px（代價：左鄰居咖啡
> 「不透明內容 bbox」上緣與 `{` 在 x 85–107 帶內重疊約 22px，改動前該處留 +24px；截圖
> `_verify_clock_photos_1440_after.png` 目視 `{` 完整可讀、白線稿尖端距字緣約 10px、不互相遮蔽）。
> 驗證：`cdp_verify_hero_coffee_photos.py` **193/193**（E 段新增 **E7**「≥992px cell 內距 = 0／
> ≤991px = u-24 + 14px / u-24」與 **E8**「照片寬 ＝ 照片區高 ÷ 1.4286」×5 斷點；基準表改為
> `BEFORE`（≤991px 用）＋`AFTER`（≥992px 用）合成的 `EXPECT`；`exp_img_w()` 的 193→336）＋回歸
> `cdp_verify_hero_weather.py`／`cdp_verify_bg_footer.py`／`cdp_verify_clock_braces.py`／
> `cdp_verify_footer_scroller.py` ＋ `manage.py check` 0 issue；截圖
> `_verify_clock_photos_{1905,1440,1280,992,991,390}_{before,after}.png`（`after` 為現況、`before`
> 由 CDP 注入舊值產生對照）。**已隨本輪批次提交 `aaf7c2aa`（16 檔／1985 insertions／713 deletions）、
> 未 push、未部署**（正式站仍為 `ec8fcadb`）。
> 原：2026-10-14 稍後（第二次）（**首頁照片格 `#bc-clock-photos` 的環形照片列改為「與 hero
> 同一顆大圓」＝整頁扇形** —— 使用者指正「展示咖啡動畫不是 footer-logo-list-wrap，區域太小了，
> 動畫展示是使用整個頁面的。參考 hero_hand」。① `--circle-radius` 由縮小版（`227vw/14.4`／
> `86.5vw/3.93`）改回 **100vw**（與 hero 同值）⇒ 25° 步進下左右鄰居落在 ±0.4226R ≈ ±42vw、扇形
> 橫跨整個頁面寬（±50° 以後落在畫面外）；② `--bc-hand-img-w` 改取「既有照片區高 ÷ 咖啡照實際比例
> 1.4286（840×1200）」＝ `193vw/14.4`（≤991px `126vw/3.93`）⇒ current 那張上下剛好貼齊照片區、
> 不壓文字列；③ 照片格／照片區的 `overflow: clip` 移除（唯一的裁切框＝`#bc-bg-footer{overflow:hidden}`，
> 與 hero 由 `.bc-gunte-hero{overflow:hidden}` 裁切同義）；④ **必須修的隱形裁切**：
> `.footer-logo-cell` 的 `data-reveal="clip-down"` 會被 GSAP 在揭示後留下 `clip-path: inset(0%)`
> （＝永久把內容框在格子內）→ 側邊鄰居整張被切掉（rect 存在、圖片已載入，但 `elementFromPoint`
> 命中的是 `#bc-clock`）⇒ `bc-bg-footer.js` 的 clip 揭示改為「揭示跑完即釋放內含
> `[data-bc-hand-ring]` 容器的 clip-path」（`/about/` 沒有該標記 ⇒ 進場與裁切行為完全不變）；
> ⑤ 照片格 7 張 `<img>` 由 `loading="lazy"` 改 eager（環上多數落在畫面外，lazy 會讓輪到置中的那張
> 空窗；這 7 張與 hero 同 src、已在快取）。
> 驗證：`cdp_verify_hero_coffee_photos.py` 擴充為 **179 項**（A 結構（含 overflow 與 eager）／B 與 hero
> 同源／C 索引同步（含 radius＝100vw）／D1 半徑＝100vw、D6 可見 2–3 張且必為 current±1、D8 鄰居在
> ±0.4226R 且落在頁面兩緣、D9 不壓文字列、D10 無水平溢出、D11 揭示後無殘留 clip-path／E 零回歸／
> F 圖片 HTTP／G `/about/` 反向守門／H 互動），且 **量測前先捲到照片格讓揭示真的跑完**（不捲就驗不到
> D11 那條路）；另回歸 `cdp_verify_hero_weather.py`／`cdp_verify_bg_footer.py`／
> `cdp_verify_clock_braces.py`／`cdp_verify_footer_scroller.py`。版號：`bc-hand-ring.css` →
> `20261014b`、`bc-bg-footer.js` → `20261014b`（index ＋ about）。
> 原：2026-10-14 稍後（**首頁照片格 `#bc-clock-photos` 改為 GUNTE hero 的「環形照片列」
> 縮小版** —— 使用者指示「改用 hero 的 `hero_hand` 環形模組 ＋ 旋轉動畫、半徑縮進格子裡、
> 超出裁切、由 hero 的 Splide index 驅動」。新增共用模組 `static/css/bc-hand-ring.css` ＋
> `static/js/bc-hand-ring.js`（`BC_HAND_RING.register(root, caption?)` / `goAll(i)` / `index()`；
> 唯一索引來源＝hero 的 Splide，`register()` 會讓晚註冊者會合 ⇒ 載入順序無關、沒有輪詢或事件橋接），
> hero 的 `updateSlideStates()` 改呼叫 `goAll()`（原 `rotateHeroHand()` 內容移入模組）；
> 照片格 markup 改為 7 × `.hero_hand_item`（與 `#hero_hand_list` 同源）＋ 一組 7 筆
> 「名稱/highlight」（只有 `-current` 顯示；`bc-bg-footer.js` 只負責註冊）；
> 照片格幾何（半徑/照片寬/圓心）在 `index.html` extra_css 逐斷點覆寫（本版為縮小版）、
> `.footer-logo-cell` 與 `.footer-logo-list` 加 `overflow: clip`（本版已移除）。
> 首頁不再有 5 秒輪播（`window.__footerLogoInterval` 首頁為 null；`/about/` 的 deco 輪播不變）。
> `cdp_verify_hero_coffee_photos.py` 當時為 **158/158**；`cdp_verify_hero_weather.py` 的 F 段改驗環形
> ＋單一文字。版號：`bc-gunte-hero.css`／`bc-gunte-hero.js` → `20261014a`、`bc-bg-footer.js` →
> `20261014a`（index ＋ about）；`static/css/bc-hand-ring.css`／`static/js/bc-hand-ring.js` →
> `20261014a`（首次）。）
> 原：2026-10-14（首頁 hero `#bc-clock` 加入 about 頁的天氣/時鐘元件（在左側 `{` 之上、
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
python3 docs/verify/cdp_verify_clock_clash.py      # 照片列 vs { }／數字／山大黃球的「像素級遮蔽」（prod/clobber/clash 三階段；1440/1280/992/991/768/390）
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

## 像素級遮蔽（clash）量測：cdp_verify_clock_clash.py

2026-10-15 新增。量的是「**不同元素的可見像素是否落在同一點**」——`cdp_verify_clock_braces.py` 的 E1
是 rect 兩兩不重疊；但桌機照片放大（1440 時 336×480）後，環形照片列（`#bc-clock-hand-list`）本來就會
離開 `.footer-logo-cell`（`bc-bg-footer.js` 的 `releaseRingClip` 設計：揭示跑完即釋放裁切框）
⇒ **rect 重疊是設計必然、不是 bug**，所以要看像素。三階段：`prod`（生產未被干擾 ＋ 探針零副作用）、
`clobber`（重現舊探針的破壞性還原 ＋ 安全法對照）、`clash`（六斷點遮蔽表，整體 ＋ 逐張照片＝current 與左右鄰居）。

量法：把某一層用「只插一條 `!important` 的 stylesheet 規則」隱藏（`visibility:hidden` 不影響 layout）
→ 與基準截圖相減 = 該層真正畫到的像素遮罩；兩層遮罩的交集 = 兩層互相遮蔽的像素數。

⚠ **四個都踩過、而且都不會報錯的坑**（任何一支做「隱藏圖層再相減」的探針都適用）：

1. **絕不可用 `element.style.visibility=''` 當「還原」**：`[data-reveal]` 的可見性 ＝ CSS
   `#bc-bg-footer [data-reveal]{visibility:hidden}`（`static/css/bc-bg-footer.css:73`）＋
   `bc-bg-footer.js:267` 於 `whenFontsReady` 寫入的 inline `visibility:visible`。設成 `''` 是
   **刪掉 inline 宣告、不是還原** ⇒ 退回 CSS 的 hidden ⇒ `.footer-logo-cell` 內整個環形照片列
   （visibility 繼承）永久隱形 ⇒ 之後所有像素差 = 0（實測：照片貢獻像素 54047 → 0）。
   正解＝加一條 stylesheet 規則、還原＝清空該規則內容，永不碰 inline style。
2. **揭示必須先真的跑完**：不捲到照片格 ⇒ `data-reveal="clip-down"` 永不觸發；本機 rAF 被節流 ⇒
   1.2s 的揭示實測要 16–36s ⇒ 必須 `SPEED_GSAP_JS`（`timeScale(100)`）＋輪詢 `clip-path == 'none'`。
   少這步會量到「揭示前」的狀態（幾乎全被 clip 裁掉）＝假的 0。
3. **凍結用 `finish()`、不要用 `pause()`**：`pause()` 把 `CSSTransition` 凍在半途，之後插入 `<style>`
   觸發 style recalc 時被丟棄的 transition 會直接跳到終值 ⇒ 基準圖與之後每張圖都差一塊「會動的區域」
   ⇒ 每個圖層遮罩都含同一塊假區域、兩兩交集全變成同一個 bbox（實測 992/768 的環形列 `scale` 過渡，
   假遮蔽 2000–3500 px）。只有無限次動畫（品牌 `noise_animation`）才用 `pause()`（`finish()` 會丟
   `InvalidStateError`）。
4. **每個 viewport 都要驗「還原殘留 = 0 px」**（`Sess.layer()` 回傳 `resid`）：殘留 ≠ 0 代表量測期間
   有東西在動 ⇒ 該 viewport 數字不可信，直接判 FAIL。這條就是第 3、5 點的守門
   （沒有它，假數據會靜靜地變成「24 組嚴重遮蔽」）。
5. **要停掉會改 DOM 文字的計時器**：`bc-bg-footer.js:36` 的 `__footerTimeInterval` 每秒 tick，
   每分鐘把 `[data-footer-time]` 的「分」進位 ⇒ 基準圖與之後每張圖差那一小塊數字區域
   （實測殘留 177 px @390、647 px @1280、1452–1958 px @992；而且**每一個圖層的遮罩都含那塊**
   ⇒ 假的「照片×數字 1081 px 遮蔽」、`bbox` 還全部一模一樣）。計時器只寫文字、不影響任何幾何
   ⇒ 量測前 `clearInterval` 即可（本腳本也順手清 `__footerLogoInterval`）。未具名的計時器
   （如 `bc-weather.js:219` 的 1 秒時鐘）則交給第 4 條守門。

本腳本對第 4 條的處理方式：某個 viewport 只要出現非 0 殘留，就**整輪重測**（最多 2 次；重試時第一輪
不計分）—— 因為同一輪的所有遮罩必須共用同一張基準圖，交集才有意義；只重測單層會讓交集變成
「不同基準的遮罩互比」。重測仍失敗才判 FAIL（寧可誠實說「這個 viewport 不可信」）。

本腳本跑完（含例外路徑）一定用 HTTP `/json/close/<id>` 關掉自己開的分頁 —— 殘留分頁會讓 compositor
不再為新分頁產 frame（本輪就因為早期版本在 `except` 時漏關、累積 3 個殘留分頁，讓「偶發瞬態」變成
「每次重測都失敗」的常態；清掉殘留分頁後即恢復）。

實測結果（2026-10-15，`P1 6/0 ＋ P2 8/0 ＋ P4 36/0`＝**總計 50 PASS / 0 FAIL**，耗時 159s；六斷點
1440/1280/992/991/768/390，每個 viewport 的「還原殘留」皆 0 px；6 個 viewport 中有 1 個觸發一次
自動重測後通過）：**明顯遮蔽（互相遮蔽 ≥2000 px）0 組**；「照片 × 數字」六斷點**全部 0 px**；
「照片 × `{ }`」最多 83 px（991；其餘 44 / 27 / 7 / 0 / 0）；唯一持續出現的是 **山大黃球 × 照片
723–777 px（1440，佔黃球可見像素 2.6–2.7%，bbox 約 80×50＝黃球圓形上方那支塗鴉的尖端與右鄰居
杯身相接；1280 僅 42 px）**。⇒ 照片放大後並沒有遮蔽時鐘的 `{ }`／數字，唯一可考慮微調的是
黃球塗鴉與右鄰居照片那一條細邊。

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
