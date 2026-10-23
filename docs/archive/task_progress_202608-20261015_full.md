# 今日任務總覽 (2026-10-15)

## 55. 首頁照片格桌機（≥992px）咖啡照片縮小 ＋ 名稱／highlight 字級放大 —— 1440 時 280×400 ＋ 20/16px ☕ — ✅ 2026-10-15 稍後

### 需求（使用者指示）
「桌機的咖啡照片太大、名稱與 highlight 太小」→ 選定 **Option A**：只動桌機（≥992px），照片區高
`480vw/ratio` → `400vw/ratio`（@1440 = 480 → 400px）、照片寬同步 `336vw/ratio` → `280vw/ratio`
（＝400 ÷ 1.4286，仍精確整除）、名稱 `16px` → `20px`、highlight `12px` → `16px`
（⇒ `--bc-hero-caption-h` 49.59 → 60.39）；≤991px 完全不動（#54 的「cell 內距歸零」維持）。

### 先量再改（CDP 量測；`/tmp/bc_probe_photos.py`、`/tmp/bc_gap_shot.py`）
| 項目 @1440 | 改動前（＝#54 放大後） | 改動後 |
|---|---|---|
| `.footer-logo-list`（照片區）高 | 480.00px | **400.00px** |
| current 照片 | 336×480 | **280×400** |
| 名稱／highlight 字級 | 16／12px | **20／16px** |
| 文字區（`--bc-hero-caption-h`） | 49.59px | **60.39px** |
| 時鐘列（＝cell）高 | 529.59px | **460.39px**（−69.2） |
| `.footer-logo-cell` 頂端／`#bc-bg-footer` | — | **文件座標 Δ0（完全不動）** |
| 頁面總高 | 3936px | **3867px**（−69；下方內容等量上移） |
| 天氣格 ↔ `{` 間距 | 136.83px | 102.23px（`{` 隨列高置中上移 34.6px） |

### 改動（四條宣告，全部在 `templates/betweencoffee_delivery/index.html` 的 extra_css）
1. `@media (min-width: 992px)` 內 `.footer-logo-list` 高 `480vw/ratio` → `400vw/ratio`。
2. `#bc-clock-photos .hero_hand` 的 `--bc-hand-img-w` `336vw/ratio` → `280vw/ratio`。
3. `.footer-logo-caption .bc-series-caption-name` 字級 `16px` → `20px`。
4. `.footer-logo-caption .bc-series-caption-highlight` 字級 `12px` → `16px`；
   `--bc-hero-caption-h` 同步改為 `calc(8px + 20px * 1.3 + 4px + 16px * 1.4)`（＝60.40，實測 60.39）。
- **未動任何 `.css`／`.js` ⇒ 無版號變更、無新檔**；`--circle-radius` 仍為 100vw（與 hero 同值）。
- 文字放大後的單行檢查：最窄桌機斷點 992 的文字區可用寬 190px，最長 highlight（16px）文字寬
  152.6px、名稱（20px）134.2px，皆單行未折行（行高 22.4／26）。

### 驗證（實測）
- `docs/verify/cdp_verify_hero_coffee_photos.py` **193/193 PASS**（EXPECT 表 1905/1440/1280/992 四列
  改為 589.55／529.16／60.39、460.39／400.00／60.39、415.94／355.55／60.39、335.94／275.55／60.39；
  `exp_img_w()` 336 → 280）；`cdp_verify_hero_weather.py` **208/208**（F4 `4.80` → `4.00` × w/14.4、
  F5 `exp_cap` → 60.39、F7 字級 → 20/16）。
- 回歸：`cdp_verify_clock_braces.py` **112/112**、`cdp_verify_bg_footer.py` PASS、
  `cdp_verify_footer_scroller.py` **127/127**、`python3 manage.py check` **0 issue**。
- `cdp_verify_clock_clash.py` **48 PASS / 2 FAIL**（耗時 247s）：2 條 FAIL 都是 1440 的「瞬態殘留
  1578px」（改動前基準同樣出現 1 條、值一模一樣 ⇒ 既有環境抖動、非本次改動引起；腳本本身已自動
  重測 2 次）。**明顯遮蔽（≥2000px）六斷點 0 組**；照片×`{ }`：1440 **0px**（不變）、992 7 → **3px**、
  ≤991px 逐值不變（991 = 83／768 = 44／390 = 27）；照片×黃球 @1440 **723 → 381px**（縮小後更好）。
- ≤991px 逐值不變（`/tmp/bc_probe_photos.py` 991/768/390：cell 寬高／照片區／文字區／列高／
  docHeight 全等於改動前）。
- 截圖 `_verify_clock_photos_{1905,1440,1280,992,991,390}_{before,after}.png`（`after` ＝現況；
  `before` 由 CDP 注入上一輪（照片放大）的舊值即時產生對照，不改檔案）。目視 @1440：中杯
  280×400、名稱 20px、highlight 16px 皆清楚可讀，`{` 完整、與左鄰居咖啡分離。
- **僅本機改動：未 push、未部署**（正式站仍為 `ec8fcadb`）。


## 54. 首頁照片格 `#bc-clock-photos` 桌機（≥992px）咖啡照片放大 —— 1440 時 336×480 ☕ — ✅ 2026-10-15

> ⚠ **同日稍後已被 #55 取代**：使用者改口「桌機的照片太大、名稱與 highlight 太小」⇒ 照片縮回
> 400vw/ratio（@1440 = 280×400）、字級放大為 20/16px。本節保留為完整沿革（三處宣告與量測方式相同）。

### 需求（使用者指示）
「桌機的咖啡照片放大到 1440 時 336×480，與 GUNTE hero 視覺同級」→ 選定 **Option C**：只動桌機
（≥992px），把 `.footer-logo-cell` 的上下內距吸收進照片區、照片區高 `276vw/ratio` → `480vw/ratio`，
照片寬同步 `193vw/ratio` → `336vw/ratio`（＝照片區高 ÷ 1.4286）；≤991px 完全不動。

### 先量再改（CDP 量測；`/tmp/bc_measure.py`、`/tmp/bc_gap.py`、`/tmp/bc_shot.py`）
| 項目 @1440 | 改動前 | 改動後 |
|---|---|---|
| `.footer-logo-cell` 內距（上／下） | 54.0 / 40.0px（`u-40 + 14px` / `u-40`） | **0 / 0px** |
| `.footer-logo-list`（照片區）高 | 276px | **480px** |
| current 照片 | 193×276 | **336×480** |
| 時鐘列（＝cell）高 | 419.59px | 529.59px（+110） |
| `.footer-logo-cell` 頂端／`#bc-bg-footer`／`.grid.is-footer` | — | **文件座標 Δ0（完全不動）** |
| 頁面總高 | 3826px | 3936px（+110；下方內容等量下移） |

### 改動（只有三條宣告，全部在 `templates/betweencoffee_delivery/index.html` 的 extra_css）
1. `@media (min-width: 992px)` 內 `.bc-bg-hero … .footer-logo-cell` → `padding-top/padding-bottom: 0`
   （原 `u-40 + 14px` / `u-40`；留白吸收進照片區 ⇒ 照片頂緣上移到時鐘列頂端）。
2. 同 media query 內 `.footer-logo-list` 高 `276vw/ratio` → `480vw/ratio`（原本的全斷點宣告改為
   只在 ≥992px；≤991px 仍走原本的 `180vw/ratio`）。
3. `#bc-clock-photos .hero_hand` 的 `--bc-hand-img-w` `193vw/ratio` → `336vw/ratio`（≤991px 的
   `126vw/ratio` 未動）。
- **未動任何 `.css`／`.js` 檔 ⇒ 無版號變更、無新檔**；`--circle-radius` 仍為 100vw（與 hero 同值）。

### 踩雷（已寫入原始碼註解）
①的 media query **必須排在「`+14px`」那條規則之後**：兩者特異度相同 (1,2,0)，CSS 以來源順序決勝。
第一版寫在檔案前面 ⇒ 實測 `padding-top` 仍是 66.92／54／49.56px（`padding-bottom` 因來源檔只
(1,1,0) 故已生效）→ 移到該規則之後才得到 0px／0px。

### 驗證（實測）
- `docs/verify/cdp_verify_hero_coffee_photos.py` **193/193 PASS**（E 段新增 **E7**「≥992px cell 內距 = 0
  ／≤991px = u-24 + 14px / u-24」與 **E8**「照片區高 ÷ current 照片寬 = 1.4286」×5 斷點；基準表改為
  `BEFORE`（≤991px 用）＋`AFTER`（≥992px 用）合成的 `EXPECT`；`exp_img_w()` 193→336）。
- `cdp_verify_hero_weather.py` **208/208**（F4 期望值同步改為 `4.80 * w / 14.4`；初次回歸 205/208 的
  3 條 FAIL 正是這條刻意改動的舊期望）、`cdp_verify_bg_footer.py` **40/40**、
  `cdp_verify_clock_braces.py` **112/112**、`cdp_verify_footer_scroller.py` **127/127**、
  `manage.py check` **0 issue**。
- 截圖 `_verify_clock_photos_{1905,1440,1280,992,991,390}_{before,after}.png`（`after` ＝現況；
  `before` 由 CDP 注入舊值即時產生對照）。
- 逐斷點照片尺寸：1905 = 444.5×635.0、**1440 = 336.0×480.0**、1280 = 298.7×426.7、
  992 = 231.5×330.7；≤991px（991／768／390）逐值不變。
- 副作用（已知、可視覺接受）：時鐘數字／`{ }` 隨列高置中 ⇒ 下移 55px，左鄰居咖啡的「不透明內容
  bbox」上緣與 `{` 在 x 85–107 帶內重疊約 22px（改動前該處留 +24px）；截圖目視 `{` 完整可讀、
  白線稿尖端距字緣約 10px。要更寬鬆只能改照片尺寸（半徑須維持 100vw＝與 hero 同值）。
- **僅本機改動：尚未提交、未 push、未部署**（正式站仍為 `ec8fcadb`）。

## 53. 首頁照片格＝「與 hero 同一顆大圓」的整頁扇形（#52 修正）🎠 — ✅ 2026-10-14 稍後

### 需求（使用者指正）
「展示咖啡動畫不是 footer-logo-list-wrap，區域太小了，動畫展示是使用整個頁面的。參考 hero_hand」
→ #52 做成「縮小版圓弧、半徑縮進格子、超出由 `overflow:clip` 裁掉」，扇形只有 ~200px 寬（實測 1440：
三張照片擠在 288px 的格子內）＝與需求相反。本輪改為與 hero 逐值相同的**整頁扇形**。

### 先量再改（CDP 量測；`/tmp/bc_ring_page.py`、`/tmp/bc_cellpage.py`、`/tmp/bc_clipwhy.py`）
| 項目 | hero（`.bc-gunte-hero .hero_hand`） | 照片格（改前 #52） | 照片格（本輪） |
|---|---|---|---|
| `--circle-radius` | 100vw（模組預設值） | `227vw/14.4`（@1440＝227px） | **100vw** |
| 可見張數 | 3（current ＋ 左右鄰居） | 3（全擠在格子內） | 3（橫跨整頁） |
| current 中心 | 頁面中心 x=713 | 照片格中心 | 照片格中心＝頁面中心 |
| 鄰居中心 `dx` | ±0.4226R（＝±608px） | ±96px | ±608px（頁面 7%／92%） |
| 鄰居 `dy` | +135px | +21px | +135px |
| 照片寬 | 231px（`420px × --bc-gunte-scale`） | 121px | **193px**（＝照片區高 276 ÷ 1.4286） |

### 改動
1. `templates/betweencoffee_delivery/index.html`（extra_css 的 B1）
   - `--circle-radius: 100vw`（與 hero 同值）⇒ 25° 步進下鄰居落在 ±0.4226R、扇形橫跨整頁。
   - `--bc-hand-img-w: calc(193vw / var(--ratio))`（≤991px `126vw / 3.93`）＝「既有照片區高 ÷ 咖啡照
     實際比例 1.4286（840×1200）」⇒ current 上下剛好貼齊照片區、不壓文字列（**不改任何版面高度**；
     E 段量測逐值不變）。
   - 移除 `.footer-logo-cell`／`.footer-logo-list` 的 `overflow: clip`；唯一裁切框＝
     `#bc-bg-footer{overflow:hidden}`（與 hero 由 `.bc-gunte-hero{overflow:hidden}` 裁切同義）。
2. `static/js/bc-bg-footer.js`：clip 揭示新增 `releaseRingClip(els)`（`onComplete` 釋放「內含
   `[data-bc-hand-ring]`」容器的 `clip-path`）。
   **為什麼非修不可**：GSAP 的 `data-reveal="clip-down"` 揭示跑完會把 `clip-path: inset(0%)` 留在
   `.footer-logo-cell` 上＝永久框住格子（inset rect 之外全部不可見）⇒ 側邊鄰居整張被切掉（rect 存在、
   `img.complete` 為 true，但 `elementFromPoint` 命中的是 `#bc-clock`）。`/about/` 沒有
   `[data-bc-hand-ring]` ⇒ 該分支不命中，deco 釘牌／天氣元件的進場與裁切完全不變。
3. `templates/betweencoffee_delivery/partials/bc_hero.html`：7 張 `<img>` 的 `loading="lazy"` → eager
   （環上 7 張只有 2–3 張在畫面內，lazy 會讓「輪到置中」的那張還沒載入＝空窗；這 7 張與 hero 同 src、
   已在快取）。
4. 版號：`bc-hand-ring.css` → `20261014b`（檔頭註解更新）、`bc-bg-footer.js` → `20261014b`
   （index ＋ about）。

### 驗證
- `docs/verify/cdp_verify_hero_coffee_photos.py` **183/183 PASS**（原 158 項；改寫/新增：A7 改驗
  照片格＋照片區 `overflow:visible` 與 `#bc-bg-footer:hidden`、A8 eager、C5 `radius == 100vw`、
  D1 半徑＝100vw、D6 可見 2–3 張且必為 current±1（循環）、D7 img 寬＝照片區高÷1.4286、D8 鄰居在
  ±0.4226R 且落在頁面兩緣且 rect 已離開照片格、D9 7 張都不與文字列相交、D10 無水平溢出、
  **D11 揭示後照片格無殘留 clip-path**）。
  - ⚠ 量測前必須先**捲到照片格**：該 cell 在首屏之外，不捲則 `data-reveal` 永不觸發 —— D11 那條路
    就是這樣藏起來的（這也是本輪才發現的驗證盲點）。
  - ⚠ 本機 CDP 的 rAF 被節流（GSAP `lagSmoothing` 每 tick 只推進 33ms）⇒ 1.2s 的揭示實測要 16–36 秒；
    腳本以 `gsap.globalTimeline.timeScale(100)` ＋輪詢到釋放處理（真瀏覽器不需此招）。
- 回歸：`cdp_verify_hero_weather.py` **208/208**、`cdp_verify_bg_footer.py`、`cdp_verify_clock_braces.py`、
  `cdp_verify_footer_scroller.py` 全過；`python manage.py check` 0 issue。
- 視覺（CDP 截圖 1440／991／390）：current 置中放大、左右鄰居落在頁面兩緣（角度越大越往外側被頁面裁切），
  與時鐘數字（`{ 22 : 36 }`）僅極小擦邊（咖啡照四周是透明留白）。


## 52. 首頁照片列與 GUNTE hero 環形字「同步換格」🔗 — ✅ 2026-10-14

### 需求（使用者指示）
首頁 hero 的環形字（GUNTE Splide）與其下方的咖啡照列（`#bc-clock-photos`，7 格）必須**同步換格**。

### 問題定位（先量再改）
- **照片列**：`static/js/bc-bg-footer.js` 的 `initFooterLogo`（:40 起）以 `setInterval(next, 5000)` 自主輪播
  （`cur` / `setActive` / `next`），與 hero 完全無關 → 兩條 5 秒時脈遲早漂移。
- **hero**：`static/js/bc-gunte-hero.js` 的 `splideHero`（`autoplay:true, interval:5000, start:1`）
  是**區域變數**、不對外開放；`updateSlideStates()`（:79）是 `'mounted'` / `'move'` 的**唯一匯流點**
  （圓環 `rotateHeroHand(index*-25)`、`#hero_nav` 的 `-current`、`state-active/prev/next`）。
- **載入順序不可依賴**：Splide ＋ `bc-gunte-hero.js` 是 body 內**非 defer**（index.html:990/991）、
  `bc-bg-footer.js` 是 **defer**（index.html:1007）→ 兩者都掛 `DOMContentLoaded`，且 defer 執行當下
  `readyState` 已是 `'interactive'`（⇒ footer **同步 boot**、hero 的 listener 反而晚一輪），
  換瀏覽器／快取情境可能相反 ⇒ 必須設計成**雙向會合**（誰先就緒誰把對方拉過來）。
- **Splide 4.1.3 原始碼確認**（`static/library/splide-4.1.3/dist/js/splide.min.js`）：
  ① Autoplay 在核心內，`pauseOnHover` 是 bind **root** 的 `mouseenter mouseleave`、
  `pauseOnFocus` 是 bind root 的 `focusin focusout`；② `Move.go` 為 `M(r)`（setIndex）**先於**
  `emit('move')` ⇒ 在 `'move'` 事件內讀 `splideHero.index` 已是**新值**（同步、無時序陷阱）；
  ③ `go()` 在 `state.is([animating, dragging]) && waitForTransition` 時會被**忽略**（驗證腳本 H3 因此有重試）。

### 實作（5 檔；純前端 ＋ 模板 ＋ 驗證腳本，無 migration）
1. **`static/js/bc-bg-footer.js`（+41 / −3）**：新增 `heroDriven` 旗標、`stop()`（清 `window.__footerLogoInterval`
   —— **名稱不可改**，`docs/verify/*.py` 以此停錶求量測確定性）、`start()` 在 `heroDriven` 時直接 `return`
   （不再起第二個 5 秒計時器）；對外開放
   `window.__bcClockPhotos = {count, index(), go(i), stop(), isHeroDriven()}`（`go` 以 `((i % n) + n) % n`
   收斂，負數／超界皆安全）；boot 尾端若 `window.__bcHeroSlideIndex` 已是 number → `stop()` ＋ `go(該值)`
   （hero 先執行時由本檔自己收斂），否則照舊 `start()`。`wrap` 點擊維持 `next(); start();`
   （接管後 `start()` no-op ⇒ 照片列暫時領先一格，hero 下次換張自動回正）。
2. **`static/js/bc-gunte-hero.js`（+18）**：新增 `syncClockPhotos()` ——
   `window.__bcHeroSlideIndex = splideHero.index` 對外發佈，並對**已存在**的 `window.__bcClockPhotos`
   呼叫 `stop()`（冪等）＋ `go(index)`；呼叫點在 `updateSlideStates()` 尾端 ⇒ 涵蓋 `'mounted'`
   （載入＝`start:1`）與每次 `'move'`（含 5 秒 autoplay、`#hero_nav` 點擊）。
3. **`templates/betweencoffee_delivery/index.html`**：`bc-gunte-hero.js ?v=20261013a → ?v=20261014a`（:991）、
   `bc-bg-footer.js ?v=20261008a → ?v=20261014a`（:1007）＋兩處機制註解（WhiteNoise `MAX_AGE` 1 年 ⇒ 必須升版）。
4. **`templates/betweencoffee_delivery/about.html`**：`bc-bg-footer.js` 同升 `?v=20261014a` ＋註解
   （本頁無 hero ⇒ 不呼叫 `stop()`、仍維持原有 5 秒自主輪播＝**零回歸**）。
5. **`templates/betweencoffee_delivery/partials/bc_hero.html`**：照片列註解改寫（原句「bc-bg-footer.js 的
   5 秒自動輪播不受影響」已過時）＋**移除 :102 的孤兒 ` -->`**（先前 symlink-append 事故殘留、只在 HEAD）。
6. **`docs/verify/cdp_verify_hero_coffee_photos.py`（128 → 144 項）**：`MEASURE_JS` 增「四方來源」原子讀值；
   新增 `HERO_SYNC_JS` / `HERO_NAV_CLICK_JS` / `HERO_APLAY_JS`；D1 改寫；新增 H1/H2（載入後接管狀態＋四方一致）、
   H3（hero 換張傳播）、H4a/H4b（autoplay 5 秒同步，僅首輪）、G5/G6（`/about/` 未被接管的反向守門）；
   docstring 增「改動背景 2026-10-14」與 H 段說明；`main()` 加 `wait_sync()` 收斂輪詢、viewport 迴圈改
   `enumerate`（H4 只在第一個 viewport 跑）。

### 驗證（CDP，4 斷點 1280/991/768/390 ＋ `/about/`）
- **`cdp_verify_hero_coffee_photos.py` 144/144、FAIL 0**：D1「顯示格 == hero index（=1）」；
  H2 四方同格（顯示格 / `__bcClockPhotos.index()` / `__bcHeroSlideIndex` / 環形字角度÷−25 / `#hero_nav` `-current`）；
  H3 點 `#hero_nav` 第 k=3 顆 → **1 次嘗試**即四方收斂到 3；H4a autoplay 3 → 4、H4b 換張後 hero/照片列/環形字/nav
  全 = 4 且 `__footerLogoInterval == null`。
- **回歸全過**：`cdp_verify_bg_footer.py`（各斷點幾何 ＋ `/about/` 點擊輪播序列 `0→1→2→3→4→0`，exit 0）、
  `cdp_verify_hero_weather.py` **208/208**、`cdp_verify_clock_braces.py` **112/112**、
  `cdp_verify_footer_scroller.py` **127/127**、`cdp_shot_index_hero_viewport.py`（exit 0；3 斷點
  `loadIndex=1`／`loadAriaLabel="2 of 7"`／`loadButterKing=true`／`loadRevealed=true` 皆不變）；
  `python3 manage.py check` → 0 issues。
- 截圖：`_verify_hero_coffee_photos_{desktop,pad991,tablet,mobile}.png`（重跑覆蓋）。

### 已知取捨（非缺陷）
- hero mount 前的數十毫秒照片列先顯示 index 0，mount 後立即校正為 1（同一幀批次、肉眼不可見）。
- 點照片列**空白處**（`wrap` 非 `<a>` 區域）＝手動覆寫：只推照片列一格，hero 下次換張自動回正；
  點**照片本身**會導覽到 `/coffee/<id>/`（不影響同步）。
- hero autoplay 受 `pauseOnHover` / `pauseOnFocus` 影響（滑鼠移入 hero 或聚焦 hero 內按鈕時暫停）
  → 照片列也一起停（＝同步行為；`/about/` 無 hero，維持 5 秒自主輪播）。

### 未動的檔
`bc-bg-footer.css`、`bc_bg_footer.html`（about 來源，仍 5 格 deco）、`bc-gunte-hero.css`、
`bc_hero.html` 的 markup（只改註解）、其餘模板與後端（無 migration、可逆：不升版即回舊行為）。

## 51. 首頁順序反轉（GUNTE hero 回第一屏）＋ GUNTE 環形字 markup 修正 ＋ 環形字尺寸 ×1.25／載入即見 🎨 — ✅ 2026-10-13

### 需求（使用者指示）
1. 首頁最上方改回 **GUNTE hero（第一眼看到的第一屏、與 navbar 之間零空隙）**；
   抹茉／BC 動態 hero（`<section class="hero bc-bg-hero">`，內含 `#bc-bg-footer`）下移到它之後。
2. **GUNTE hero 的環形字（曲線標題 `<text>`）markup 修正**：使用者把 6 張不顯示的環形字
   開啟標籤手寫成不存在的 `<hidden text>`（而且用 `</text>` 收尾、開／閉不成對）
   → 改為合法 markup，只留第 2 張（BUTTER KING）顯示。

### 定位（先量再改）
- 舊版順序（10-09、已提交於 `c5016e29`）：`.bc-bg-hero`（第 1 個 section）→ …；
  GUNTE hero 在其後。10-13 反轉為：①`hidden` 的 `.bc-reviews-section` ②`.bc-gunte-hero`
  ③`.ftco-section-blank-small` ④`.bc-bg-hero`。
- **100px margin 來源**：`bc-components.css:4438`
  `.bc-page-content > section:first-of-type:not(.home-slider){margin-top:100px}` —— **只命中 first-of-type**。
  10-13 的 first-of-type 是 `hidden` 的 `.bc-reviews-section`（不渲染、量不到），GUNTE hero 為第 2 個
  section → 該 100px 不會命中；且 `bc-gunte-hero.css:611`
  `.bc-page-content > section.bc-gunte-hero.hero{margin-top:0 !important}` 是 **class 規則、不依賴序位**
  ⇒ **不需要新增桌面 margin-top 覆寫**（實測兩塊 hero computed 皆 `0px`：CDP J14）。

### 實作（4 檔）
- **`templates/betweencoffee_delivery/index.html`**
  - 順序＝上述 ①②③④；檔頭新增 10-13 註解（新順序、margin 來源、extra_css 那條 `first-of-type.bc-bg-hero`
    已成保險條），10-09 舊註解保留為「歷史段」；`.bc-reviews-section` 的 provenance 註解同步改寫；
    移除搬移處殘留的空行。
  - 環形字：6 個 `<hidden text>` → `<text class="bc-ring-hide">`（開／閉成對）；BUTTER KING 那張維持
    `<text>`（文案＝使用者原編輯「BUTTER KING 極致豐厚焦糖黃油定番。放大」）。
  - 版號：`bc-gunte-hero.css ?v=20261008e → ?v=20261013a`（WhiteNoise MAX_AGE=1 年，必須升版）。
- **`static/css/bc-gunte-hero.css`**：新增 `.bc-gunte-hero .hero_slide_item_ttl text.bc-ring-hide{display:none}`
  （＋註解：`.bc-ring-hide` 是「不顯示」的修飾 class；只隱藏 `<text>`，同一個 SVG 的 `<path>` 不動）。
- **`docs/verify/cdp_verify_footer_scroller.py`**：J11–J14 改寫為新順序語意（第一個「可見」section＝
  `.bc-gunte-hero`、DOM 第一個 section＝`hidden` 的 reviews 段、GUNTE 在 `.bc-bg-hero` 之前、載入幾何、
  兩塊 hero margin-top 0），新增 **K1–K4**（環形字 markup 合法性／可見性）；J15–J19 不變。
- **`docs/verify/cdp_shot_index_hero_viewport.py`**：舊旗標 `gunteBeforeBg`（語意與命名不符）→
  正確的 `bgAfterGunte` ＋ 追加 `firstVisibleSec`；第二張截圖由「捲到 GUNTE hero」改為「捲到 BC hero」。
- **`docs/verify/CDP_SETUP.md`**：最後更新改 2026-10-13、項目數 120 → 124、沿革補一筆。

### 驗證（本機 8081 ＋ CDP 9222；改模板後重啟站台再跑）
- `python3 docs/verify/cdp_verify_footer_scroller.py` → **124 項、PASS 124 / FAIL 0**（原 120 ＋ K1–K4）。
- 幾何（載入未捲動）：desktop 1280×800 → GUNTE hero `top=0`、`h=694`、`margin-top=0px`；
  BC hero `top=774`（＝694 GUNTE ＋ 80 `.ftco-section-blank-small` 留白，接在其後、不重疊）、`margin-top=0px`；
  tablet 768×1024 → GUNTE `0/829`、BC `885`；mobile 390×844 → GUNTE `0/721`、BC `777`。
- 環形字：`getElementsByTagName('hidden')` ＝ **0**；`.hero_slide_item_ttl` SVG 7 個、各 1 個 `<text>`（成對）；
  `text.bc-ring-hide` 6 個且 computed `display:none` 6 個；唯一可見者＝BUTTER KING 那張（K1–K4 PASS）。
- 回歸：H 系列（`/coffee_menu/` ftco 頁尾保真）、I 系列（reduced-motion）、J16–J19（分隔線／黑底／
  作用域／about 反向守門）**全數 PASS**；`python3 manage.py check` **0 issues**。
- 視覺：`_verify_index_hero_top_{desktop,tablet,mobile}.png`（第一屏＝GUNTE hero）＋
  `_verify_index_hero_bg_{desktop,tablet,mobile}.png`（捲到 BC hero，證明它在 GUNTE hero 之後）。

### 追加（2026-10-13 稍後：使用者「尺寸改動」＋「載入時就要看得到環形字」）
- **環形字尺寸 ×1.25**（`static/css/bc-gunte-hero.css`）：`.hero_slide_item_ttl text` 的
  `font-size: 24px → calc(24px * 540 / 432)`（＝30 viewBox 單位）、
  `stroke-width: 1.5 → calc(1.5 * 540 / 432)`（＝1.875）；手機（`max-width:767px`）覆寫
  `2 → calc(2 * 540 / 432)`（＝2.5）。
  [為什麼是 540/432] `<text>` 位於 `<svg viewBox="0 0 540 540">` 內、整個 SVG 已隨 `--bc-item-w`
  縮放 → 實際渲染字級 ＝ viewBox 字級 × 框寬/540；要把「432px 參考圖寬下的 24px」等值換算成
  viewBox 單位 ＝ 24 × 540/432 ＝ 30（渲染 30 × 框寬/540 ＝ 24 × 框寬/432）。
  **不可**寫成 `calc(var(--bc-item-k) * 24)`：會與 SVG 自身縮放重複相乘（短視窗桌機縮到 9.1px、
  手機 7.0px，比同層 cap 10px 還小）—— 這才是「尺寸跑掉」的寫法。
- **載入即見環形字**（`static/js/bc-gunte-hero.js`）：Splide `start: 3 → 1`。
  ⚠ **Splide 的 `start` 是 0-based 索引**（不是「第幾張」）—— CDP 實測 `start: 2` 置中的是
  `aria-label="3 of 7"`＝第 3 張「果香浅煎」（環形字被 `.bc-ring-hide` 隱藏）、`start: 3` 是第 4 張、
  `start: 0` 是第 1 張 BLACK BLEND（同樣被隱藏）→ **`start: 1` ＝ DOM 第 2 張（`aria-label="2 of 7"`）
  ＝ BUTTER KING**，載入當下就看得見環形字（中間曾一度改成 `start: 2`，實測為第 3 張、環形字仍被隱藏，
  已於本輪修正為 `1`）。
- **`docs/verify/cdp_verify_footer_scroller.py`**：新增 K5–K7 ——
  K5 環形字 computed `font-size` ＝ 30px 且 `stroke-width` ＝ 1.875px
  （⚠ Chromium 對 SVG 幾何屬性（stroke-width）的 computed style 會保留 `calc()` 字面 → 回傳
  `"calc(1.875px)"`，斷言比對剝除外層 `calc()` 後的值，原始字串另存 `ttl_stroke_width_raw` 一起印出）；
  K6 環形字 SVG 框寬 ＝ 投影片圖片寬（新增實測欄位 `ttl_item_img_w`，避免硬寫 432）且渲染字級 ＝
  `round(24 × 框寬/432, 2)`；
  K7 載入時置中的是 BUTTER KING（`active_slide_index == 1`、`active_slide_aria_label == "2 of 7"`）
  且其環形字 `opacity == 1` 且未被 `.bc-ring-hide` 隱藏。
  K7 的量測方式（三段，都是實測踩到假 FAIL 後才改成這樣）：
  ① **不用 `goto()` 等 readyState complete**（會多等 1.2 秒；暖機狀態下 Splide autoplay
    （interval 5000ms）已先換張，實測 shot 腳本原本的固定 sleep 5s 就記成 index 4）→ 改為
    `Page.navigate` 後立刻以 0.1s 間隔輪詢 `.state-active`，一出現就把「載入時置中的那張」
    記到 `window.__bcHeroLoadIndex`（斷言讀 `*_at_load` 欄位；之後 autoplay 換張都不影響）。
  ② **必須逼 frame**：本機 CDP（headful，但 compositor 不一定產 frame）下 CSS transition 會停在
    pending —— `el.getAnimations()` 實測 `CSSTransition opacity delay=1500 dur=500`、`playState='running'`
    但 `startTime=null`／`currentTime=0`，computed opacity 一直停在過渡起點 `0`（`.hero_slide` 與
    環形字都是），等 15 秒也不會動；用 `Page.captureScreenshot` 逼 frame 後實測 0 → 0.30 → 1
    （約 1 秒）。截圖呼叫包 3 秒 `asyncio.wait_for`（殘留多個背景分頁時曾整支腳本卡死）。
  ③ 收尾補 `Page.close`：原腳本沒有關分頁 → 每跑一次留一個（實測殘留 5 個頁面時 compositor
    不再為本分頁產 frame，就是②卡死的成因）；補上後跑完只剩常駐的 `about:blank`。
- **`docs/verify/cdp_shot_index_hero_viewport.py`**：追加 `loadIndex`／`loadAriaLabel`／`loadButterKing`／
  `loadRevealed`（載入時置中那張；逼 frame 前先記錄，`loadRevealed` ＝ 逼 frame 後其環形字確實到過
  opacity 1）＋ `activeSlideIndex`／`activeAriaLabel`／`activeTtlOpacity`／`ttlStrokeRaw`（讀值當下，
  僅診斷），並更新檔頭說明（start 3 → 1、逼 frame 的原因）。
- **`templates/betweencoffee_delivery/index.html`**：兩處註解同步（`start 3 → **1**`＋ 環形字字級
  換算說明），版號沿用 `bc-gunte-hero.css ?v=20261013b`／`bc-gunte-hero.js ?v=20261013a`
  （10-13 內容已涵蓋本輪，未再升版）。

### 驗證（追加，2026-10-13 稍後；已重啟 8081 再跑）
- `python3 docs/verify/cdp_verify_footer_scroller.py` → **127 項、PASS 127 / FAIL 0**（124 ＋ K5–K7）；
  連跑 3 次結果一致（含修正量測方式後的最終版）。
- K5 `font=30px stroke=1.875px raw=calc(1.875px)`；K6 `box=297 img=297 rendered=16.5 期望=16.5`；
  K7 `atLoad[butter=True index=1 aria=2 of 7 opacity=1 textDisplay=block]`（＋`[hero] 載入時置中`
  先記到 `{"index":1,"aria_label":"2 of 7","is_butter_king":true}`）。
- 跨斷點（`cdp_shot_index_hero_viewport.py`，載入未捲動）：desktop／tablet／mobile 皆
  `loadIndex=1`、`loadAriaLabel="2 of 7"`、`loadButterKing=true`、`loadRevealed=true`（環形字真的到過
  opacity 1）、`activeTtlOpacity=1`；`ttlBoxW=297 / 315.03 / 266`、
  `ttlRenderedFont=**16.5 / 17.5 / 14.78**`（改動前 24px 固定值換算為 13.2 / 14.0 / 11.8 → 三斷點一致 ×1.25）。
- 截圖：`_verify_index_hero_top_{desktop,tablet,mobile}.png`（載入第一屏，環形字可見）。
- 環境副作用修好：`cdp_verify_footer_scroller.py` 收尾補 `Page.close`（原本每跑一次留一個分頁，
  殘留 5 個時 compositor 不再為本分頁產 frame → 逼 frame 的截圖會卡死整支腳本）。

### 待確認（本輪未動，等使用者指示）
- `.bc-reviews-section` 現為 `hidden`（使用者 10-13 自己的編輯）→ 首頁不顯示該反向跑馬燈。
  若應改為「移到 GUNTE hero 之後顯示」或「整段刪除」，需再調 markup 並同步 J11 斷言。
- （已於 10-13 稍後處理者：載入時圈圈字不可見 → `start: 3` → `1`；圈圈字固定 24px 不等比 →
  改為 viewBox 單位 `calc(24px*540/432)`。GUNTE hero 的 carousel／cap／en 標籤尺寸仍未動。）

### 回復點
- `docs/verify/patches/index_hero_20261013.patch`（本輪 worktree vs `HEAD` 的完整 diff、
  共 6 檔：`index.html`／`bc-gunte-hero.css`／**`bc-gunte-hero.js`**（上一版漏收，本輪補上）／
  `cdp_verify_footer_scroller.py`／`cdp_shot_index_hero_viewport.py`／`CDP_SETUP.md`；
  `git apply -R` 可還原，已 `git apply --check -R` 驗過）。
  ※ `task_progress.md` 被 `.gitignore` 的 `/*.md` 排除（本地記憶檔），不在 patch 內。）
- 快照：`templates/betweencoffee_delivery/backup/index.html.20261013`（10-13 19:05 的 worktree 版本、
  早於本輪編輯；本輪的實際差異一律以 patch 為準）。
- 本機 8081 站台與 9222 CDP 瀏覽器為本輪驗證啟動（收工可 `pkill -f 'manage.py runserver 127.0.0.1:808[1]'`
  ／`pkill -f 'remote-debugging-por[t]=9222'`）。



# 今日任務總覽 (2026-10-12)

## 50. 手機／平板時鐘 `{ }` 恢復顯示 ＋ bc_hero／bc_bg_footer 的 `w-node-*` 語意化命名 🕐 — ✅ 2026-10-12

### 需求
1. 「在手機和平板電腦端，在時鐘中，此符號 `{` `}` 消失」。
2. 「`bc_hero.html`，重新命名這種 `w-node-_xxxxx` 等 CSS 名稱，使用相關組件屬性名稱命名」。

### 定位（先量再改，非猜測）
- **`{ }` 成因**：兩者沿用 Webflow 原生 `h1.is-desktop` → 於 `@media (max-width:991px)` 被
  `#bc-bg-footer .is-desktop{display:none}` 隱藏；該斷點時鐘列只有 6 欄且已被 `15 : 照片 : 19`
  佔滿，`}` 的 `grid-area:1/8/2/9` 在 6 欄格中還會產生**隱式欄**。
- **照片尺寸守門**：照片欄佔比 2/6 = 3/9 → 以 **9 欄**重排可讓照片尺寸逐值不變
  （768px 220px、390px 111px 實測與改前相同）。

### 實作
- `partials/bc_hero.html`、`partials/bc_bg_footer.html`：`{` `}` 改 `.h1.bc-clock-brace`
  （移除 `is-desktop`）＋語意 id；8 個時鐘 id 語意化；`w-node-*` 全數改名
  （`bc-clock` 系列／`bc-heading-*`／`bc-footer-*` 等），共 33 個選擇器。
- `static/css/bc-bg-footer.css`：≤991px `.footer-time{grid-template-columns:repeat(9,minmax(0,1fr))}`
  ⇒ `{ 15 : 照片(跨 3 欄) : 19 }`；數字改各欄置中。
  ⚠ **`minmax(0,1fr)` 必要**：純 `1fr` 會被數字的 min-content 撐大欄位、照片被壓到 196px。
- **三檔同步**（同一組 id 由 index 的 `bc_hero.html` 與 about 的 `bc_bg_footer.html` 共用；
  只改一檔會讓 hero 失去 grid 定位）。
- 版號：`bc-bg-footer.css ?v=20261009a → 20261012a`（`index.html` / `about.html`）。

### 驗證（本機 8081 ＋ CDP 9222，改後重啟 server 以避開 cached.Loader）
- 新增 `docs/verify/cdp_verify_clock_braces.py`（112 項）→ **112 PASS / 0 FAIL**。
- 回歸 `docs/verify/cdp_verify_hero_coffee_photos.py` → **116 / 116 PASS**。
- ⚠ **踩雷**：兩支腳本**並行**執行會互搶 dev server → 出現 C1／F2／F3 偽 FAIL
  （顯示中那格 `img.complete=false`、點擊導覽未發生）。**序列執行即全綠**，非真實回歸。
- CSS 結構平衡（去註解與字串後 `{` `}` diff = 0）；`manage.py check` **0 issues**。
- **原始需求複驗（咖啡詳情頁氣泡）**：`/coffee/10/`（1905px）實測三顆 `.staff-comment` 氣泡
  **皆在咖啡杯不透明區之外**（距杯緣 18 / 31.8 / 47px，落在去背透明留白區），
  照片框 516×458、照片 358×458、左右留白各 79px。DB 僅 Butter King（id=10）有氣泡文字
  （`mr` / `tl` / `tr`），其餘 7 款留空 → 依設計不顯示。

### 遺留（未提交）
- worktree ≠ `origin/main`（`git rev-list --left-right --count origin/main...HEAD` = `0 0`，
  即本地 HEAD 尚停在已部署的 `458e1780`）。
- 未提交內容含 **10-12（時鐘＋改名）** 與 **10-09 遺留**（`index.html` GUNTE hero 段下移、
  `bc_hero.html` h1 首字大寫、「Perfect／to Go」加 `hidden`）→ 因 `index.html`／`bc_hero.html`
  同時含兩批，無法以檔案為單位分割提交。
- 本機 8081 server 已重啟（驗證用 9222 CDP 瀏覽器已關閉）。
- ⚠ 本節為 10-12 當時記錄：上述「未提交」內容已於後續提交（`6e29b447`／`ec8fcadb`／`0dc72714`），
  10-13 只剩任務 51 的變更留在 worktree。


## 49. 部署：2026-10-09 批次推上正式站 ＋ 生產驗證 ＋ 記憶文件同步 🚀 — ✅ 2026-10-12

### 需求
- 使用者授權以 API 觸發 Render 部署（`autoDeploy=no`），把累積未上線的 10 月批次（`c5016e29`＋`458e1780`）推上正式站，並驗證＋回寫記憶文件。

### 執行（純上線，無程式碼變更）
- **觸發**：以 `RENDER_API_KEY` 呼叫 Render API `POST /v1/services/{id}/deploys`（service `srv-d8jce6rtqb8s73897t4g`／singapore／free）。
- **部署**：deploy **`dep-db67vu2jnfac73cp8tcg`** → status `live`、trigger `api`、部署 commit **`458e1780`**、建置 14:36→14:39（+08:00）。
  同日稍早的 `dep-db677p142hec73b62qb0`（commit `dc118b78`）已被本次取代並 deactivated。
- **migration**：部署時自動套用 0074~0080（首頁商品圖更名／Sunshine 首頁圖 v2／咖啡詳情頁圖修正／咖啡商品圖全面換新／選項組新增「烘焙」「茶種」）。

### 生產驗證（正式站 `https://betweencoffee-delivery-enhance-v1.onrender.com`）
- `/` → **HTTP 200**（90,949 bytes）：hero 下緣 7 張咖啡照齊全（`class="img contain"` ×7／`href="/coffee/N/"`）、`bc-bg-footer.css?v=20261009a` 生效。
- `/about/` → **HTTP 200**：動態 footer／logo 釘牌／`.scroller-box` 跑馬燈皆在。
- 啟動日誌僅 **`django_site` 重複鍵告警**（benign、非阻斷）＋ Celery 同步降級訊息。

### 記憶文件同步
- `.clinerules/.clinerules`：新增「目前上線版本」行（L82）＋ 近期任務（2026-10-12 部署）區塊；把 2 處遺留 `[!] 待部署` 翻為 `[x] 已上線（2026-10-12）`。
- `04_SYSTEM_STATE.md`：新增部署 blockquote、狀態表「部署（Render）」列改 ✅、近期變更新增一筆。
- `05_PRIORITY_TASKS.md`：新增部署 blockquote、把兩處 `⚠️ 待部署` 敘述改為「已部署上線」。
- `bc-context`：狀態 echo 改為已上線（L82／L103／L129／L161）。

### 遺留（未提交、未部署，正式站 ≠ worktree）
- `templates/betweencoffee_delivery/index.html`（312 行 diff）：GUNTE hero 段由 line 111 下移至 line 343（reviews 段由 264 上移至 line 109；hunk `@@ -109,155 +108,0 @@` → `@@ -495,0 +341,157 @@`，淨 +2 行）。
- `templates/betweencoffee_delivery/partials/bc_hero.html`（8 行 diff）：三處 `<h1>` 首字母大寫（`Beans`／`Roasted`／`Daily`）＋「Perfect / to Go」標題組加 `hidden`（`#w-node-_7dac5ba3-75b3-d297-693a-71a77bf5e06c-032bc8db`）。
- 另有本任務產生的記憶文件改動（`.clinerules`／`04`／`05`／`bc-context`／`task_progress.md`）尚未提交。

## 48. 首頁置頂 hero 去掉「頁尾感」：移除頂部 1px 分隔線 ＋ 自帶黑底 🎨 — ✅ 2026-10-09

### 需求
- 使用者指示：「把 #bc-bg-footer hero 最上面的邊框線和黑色背景拿掉」。

### 定位（CDP 實測，先量再改）
- **線** = `static/css/bc-bg-footer.css:113` `#bc-bg-footer .grid.is-footer{border-top:calc(.25vw/14.4)solid
  rgba(255,255,255,.08)}`（源自 Webflow 頁尾「與上方內容分隔」設計）→ 在 1280×800 實測繪出
  **y=14、x=14–1250、rgb(32,32,32) 的 1px 線**（頁面底色 rgb(14,14,14)；`grid.left=14`、寬 1237 ⇒ **不是滿版**）；
  同列 x=1265–1279 的亮帶是瀏覽器卷軸、非頁面元素（已排除）。
- **黑底** = 兩層：`bc-bg-footer.css:42` `#bc-bg-footer{background-color:var(--_colors---background--bg)}`
  與 `:129` `#bc-bg-footer .footer{同}`，**皆為 #0e0e0e**（`--_colors---background--bg:#0e0e0e` 由檔內品牌覆寫提供）。
- **拿掉黑底後會露出什麼？**（改前先用 `Runtime.evaluate` 注入 `transparent` 做實驗，不動檔案）
  `body`／`html`／`.bc-page-content`／`.bc-bg-hero` 的 computed 底色皆為 `rgba(0,0,0,0)`，
  真正來源是 `static/css/style-bootstrap.css:3118` 起的 `body` 規則 —— 先 `background:#151111`，
  但**同規則後一行** `background:url(../images/bg_4.jpg) no-repeat fixed;background-size:cover`
  的 shorthand 把純色覆蓋掉 ⇒ `body` 實際是**固定不滾動的深色背景照片**（computed background-color = transparent）。
  逐段捲動取樣確認該照片在首頁其餘區塊（`.feed--video`／`ftco-section-blank-*` 一帶，scrollY 1600／3200）
  本來就可見（(12,12,12)／(10,8,11)／(13,12,17)）⇒ **移除黑底＝與頁面其餘區塊一致**，非引入新視覺。

### 實作（只動 1 檔、只覆寫首頁）
- **`templates/betweencoffee_delivery/index.html`**：於 `extra_css` 的 `<style>`（緊接既有
  `.bc-page-content > section:first-of-type.bc-bg-hero{margin-top:0 !important}` 之後）新增三條頁面級覆寫
  （含 18 行成因／特異度／範圍註解）：
  - `.bc-bg-hero #bc-bg-footer{background-color:transparent}`
  - `.bc-bg-hero #bc-bg-footer .footer{background-color:transparent}`
  - `.bc-bg-hero #bc-bg-footer .grid.is-footer{border-top:0 none}`
- **為何不直接改 `bc-bg-footer.css`**：about 頁的 `#bc-bg-footer` 是**真頁尾**（父層為 `BODY`），
  需保留分隔線與黑底；改共用檔會誤傷。
- **特異度**：加上 `.bc-bg-hero` 後為 (1,1,0)／(1,2,0)／(1,3,0)，皆高於原始 `#bc-bg-footer …`；
  且 `border-top` 全檔**只在 :113 宣告一次**（≤991px 媒體查詢只改 `padding-top`、未重新宣告邊框）
  ⇒ 全斷點生效、**不需 `!important`**、不必逐斷點鏡射。
- **零位移**：`.grid.is-footer` 的 `padding-top`（桌面 `calc(120vw/14.4)`=106.667px、≤991px 72px）**刻意不動**。
- **未動**：`bc-bg-footer.css`／`bc-bg-footer.js`／`partials/bc_hero.html`／about 來源 partial。

### 驗證
- **同頁 A/B 隔離測試**（把覆寫還原成原始值再重新套用，消除「不同次載入 lazy 圖/動畫狀態不同」的干擾）：
  唯一差異 = 該 1px 邊框 —— hero 1449.36→**1448.36**px、GUNTE hero `top` 1449→**1448**、
  `.h1` top 122→**121**、時鐘 top 614→**613**；其餘（`gunte_h` 693.5、`grid top` 14、`padding-top` 106.667px）
  **完全不變**；覆寫可重複套用**無殘留**（A vs C 全等）。
- `docs/verify/cdp_verify_footer_scroller.py` 追加 **J16–J19** ⇒ **合計 116 → 120 項、PASS 120 / FAIL 0**：
  J16 `.grid.is-footer` computed `border-top-width 0px` / `style none` 且 `padding-top` 仍為 106.667px（非 0）；
  J17 `#bc-bg-footer` 與 `.footer` computed 底色皆 `rgba(0,0,0,0)`；
  J18 首頁 `#bc-bg-footer` 父層 ＝ `SECTION.hero.bc-bg-hero`（覆寫錨點、只命中首頁）；
  J19 同腳本 `goto /about/` **反向守門**：真頁尾仍為 `1px solid rgba(255,255,255,.08)` ＋
  `footer/root` 底色 `rgb(14,14,14)` ＋ 父層 `BODY`。
- 回歸：`docs/verify/cdp_verify_bg_footer.py`（about 頁）**0 FAIL**、`python3 manage.py check` **0 issue**。
- 視覺：`docs/verify/cdp_shot_index_hero_viewport.py` 重跑 3 斷點 ⇒ 幾何 desktop 1448／GUNTE top 1448（零空隙）、
  tablet 2171／2171、mobile 1098／1098（皆＝原基準 −1px）；新截圖 `_verify_index_hero_top_{desktop,tablet,mobile}.png`
  逐張以 PIL 掃描 y<40 確認**已無跨 >40% 寬度的亮線**，白字標題／時鐘／右上購物車／「Order」藥丸／頭像／
  金色徽章全部正常。改前對照留存為 `_verify_index_hero_top_BEFORE_FIX_desktop.png`（`/_verify_*.png` 已 gitignore）。
- ⚠️ 同前次：改模板後**必須重啟站台**再跑 CDP（cached template loader）。
  `pkill` 不可寫成 `pkill -f 'manage.py runserver 8081'`（下指令的 shell 命令列含同樣字串 → 自殺）；
  用 `pkill -f 'manage.py runserver 127.0.0.1:808[1]'`。

### 回復點
- 回復＝刪掉 `index.html` `extra_css` 內那三條 `.bc-bg-hero #bc-bg-footer …` 覆寫即可（其餘皆未動）。




## 47. 首頁 BC 動態 hero（#bc-bg-footer）由頁尾移到最上方 🕐 — ✅ 2026-10-09

### 需求
- 使用者指示：「把頁尾那個動態模組移到首頁最上面當 hero，原本（GUNTE）的 hero 往下」。

### 實作（新 partial 1 ＋ index.html 1）
- **新 `templates/betweencoffee_delivery/partials/bc_hero.html`**：`partials/bc_bg_footer.html` 的 hero 變體，
  與 footer 版逐字相同，只差 ①最外層 `<footer class="footer">` → `<div class="footer">`（收尾同理）②檔頭註解。
  保留 `id="bc-bg-footer"`：`bc-bg-footer.css` 的 **135 條**選擇器全以此 id 為前綴、`bc-bg-footer.js` 以
  `getElementById('bc-bg-footer')` 綁定 ⇒ 與 about 頁共用同一份 CSS/JS、**零樣式改動**（index／about 是不同頁，同 id 不衝突）。
- **改標籤是本次最關鍵的踩雷點**：`static/js/bc-yama-header.js:24` 用 `document.querySelector('footer')`
  （＝DOM 第一個 `<footer>`）當「footer 交會」觀察目標；置頂模組若仍是 `<footer>`，頁面一載入它就在視口內
  ⇒ IntersectionObserver 立刻回呼：`.tax-nav` 被移除 `init`（右下「Order」圓球淡入失效）、`header-bot` 加 `is-hide`
  （浮動購物車鈕被藏）。改成 `<div>` 後 `querySelector('footer')` 為 `null`、交會邏輯自然 no-op。
  CSS 只用 `.footer` **類別**選取、與標籤無關 ⇒ 外觀零變化（已由 J15 ＋ 截圖確認）。
- **`index.html` 五處**：①`{% include '.../bc_hero.html' %}` 包在 `<section class="hero bc-bg-hero">`，放在
  `bc-page-content` 最前（原 GUNTE hero 之前，含三段式檔頭註解）②GUNTE hero 整段（原 90–239 行）原封不動下移
  ③`block bcc_footer` 刻意覆寫為空（不重複渲染同一模組；也刻意不回退 base 的 `.ftco-footer`，否則兩套 footer 視覺並存）
  ④extra_css 新增 `.bc-page-content > section:first-of-type.bc-bg-hero{margin-top:0 !important}`
  （蓋掉 `bc-components.css` 首 section 的 100px／768→72px／576→60px 預留，比照既有 `.feed` 寫法，一次全斷點生效）
  ⑤既有註解同步（BC 動態 footer 那段的「頁尾 → 首頁 hero」說明）。
- **未動的檔**：`bc-bg-footer.css`、`bc-bg-footer.js`、`bc-gunte-hero.css`、`bc_bg_footer.html`（about 來源）、
  `bc-components.css`。兩個 hero 之間零空隙（GUNTE hero 的 `margin-top:0` 是 **class 規則**、不依賴 first-of-type 序位）；
  `.hero` 這個類別在全庫沒有裸規則（唯一一條同時要求 `.bc-gunte-hero`）。

### 驗證
- `docs/verify/cdp_verify_footer_scroller.py` 追加 **J11–J15**：**合計 116 項、PASS 116 / FAIL 0**（原 111 項全保留）。
  J11 首 section ＝ `.hero.bc-bg-hero` 且內含 `#bc-bg-footer`；J12 文件順序在 `.bc-gunte-hero` 之前；
  J13 載入時 `#bc-bg-footer` 已在首屏（`rect.top=0`、`innerH=800`）；J14 `margin-top=0px`；
  J15 `querySelectorAll('footer').length==0`（yama 交會 no-op 的 DOM 保證）。
- 實測幾何（載入、未捲動）：desktop 1280×800 → BC hero 高 1449、GUNTE hero `top=1449`（**零空隙**）；
  tablet 768×1024 → 2172／2172；mobile 390×844 → 1099／1099；首頁 `.bc-page-content > section` 共 11、`#bc-bg-footer` 僅 1 個。
- 回歸：`docs/verify/cdp_verify_bg_footer.py`（about 頁 41 項 ＋ 輪播點擊順序 1→2→3→4→0）**PASS / FAIL 0**、
  `python3 manage.py check` 0 issue。
- 新增 `docs/verify/cdp_shot_index_hero_viewport.py`（3 斷點 × 2 張視窗截圖，只截圖＋印幾何、無斷言）：
  `_verify_index_hero_top_{desktop,tablet,mobile}.png`（hero 在最上方）、
  `_verify_index_hero_gunte_{desktop,tablet,mobile}.png`（捲到 GUNTE hero）。桌面版截圖可見右下「Order」圓球＋
  浮動購物車鈕**開站即在**（＝footer 交會邏輯未被誤觸的視覺證據）。
- ⚠️ 本機 `DEBUG=False` ＋ `runserver --noreload` 使用 cached template loader ⇒ 改模板後**必須重啟站台**再跑 CDP。

### 備份／回復點
- 改前備份：`templates/betweencoffee_delivery/backup/index.html.20261009`（`backup/` 已 gitignore）。
- 改前 commit：`dc118b78`。回復頁尾版＝把 `block bcc_footer` 內容換回 `{% include '.../bc_bg_footer.html' %}`、
  刪掉最上方 `<section class="hero bc-bg-hero">`、GUNTE hero 移回原位。



## 46. 收尾：10 月批次推送 GitHub ＋ 記憶文件三處同步 🚀 — ✅ 2026-10-08

### 需求
- 使用者指示：「① 更新目前狀態及全部對話已完成任務到 memory bank, clinerule and bc-content ② 推送目前狀態 github」。

### 執行
- **文件同步（4 處）**：
  - `betweencoffee_memory_bank/04_SYSTEM_STATE.md`：新增「收尾」摘要行；系統狀態摘要表補「部署（Render）」「版本控制」兩列；近期變更補 6 筆
    （10-08 收尾、about 頁 BC 動態 footer 收尾＋移植、10-06 選項組 0079／0080、購物車選項標籤化、`.top_art` 圖片恢復、CDP 驗證基礎建設）。
  - `betweencoffee_memory_bank/05_PRIORITY_TASKS.md`：新增「收尾」摘要行；待部署清單補 about 動態 footer／`.top_art`／購物車標籤化／CDP 腳本；近期優先補 5 筆。
  - `.clinerules/.clinerules`：新增「## 近期任務（2026-10-02 ~ 10-08）」整節（任務樹 ＋ 關鍵實作細節 ＋ CDP 驗證教訓）；
    「部署方式」更正為 `autoDeploy` 已關閉（2026-10-06 起，service `srv-d8jce6rtqb8s73897t4g`）；「色彩」規範註明第二主題色已無元件引用；
    舊「待部署」註記更新為 migration 0070~0080 且已 push。
  - 根目錄 `bc-context`（上下文摘要腳本）：更新「系統狀態／最新改動」兩行 ＋ 新增 `│   2026-10-02~08 ✅` 條目（原本停在 2026-09-23；`bash -n` 通過）。
- **GitHub 推送**：10 月 worktree 全部改動（migration 0079／0080、about 動態 footer、`.top_art`、購物車標籤化、index 主題色、圖片資產與 `docs/verify/` 腳本等）
  一次提交並 push `origin/main`（commit **`18a14070`**，72 檔）；**排除本機驗證截圖 `_verify_*`**（歷來皆不入庫，另新增 `.gitignore` 規則）。
- **未改任何程式碼、未觸發部署**（Render `autoDeploy=no` → 需 dashboard 手動 Manual Deploy）。
- 附註：`index.html:508-509` 的 `search_img01.png`／`search_img02.png` static fallback 指向的實體檔已在先前清理中刪除（正常由 `BeanItem` pk 7／6 供圖）。


## 45. index.html「第二主題色 → 第一主題色」🎨 — ✅ 2026-10-08

### 需求
- 使用者指示：「index.html 目前第二主題色改為第一主題色」（使用者確認＝圓球＋圓點＋浮動購物車圓圈三處都改）。
- 名詞定義（查證）：**第一主題色＝品牌金 `#c49b63`**（`bc-components.css :root` 的 `--bc-gold`，`style-bootstrap.css` 的
  `--primary`／`--brand-primary` 同值）；**第二主題色＝`#FCFF4B`／rgb(252,255,75)**（`--bc-theme2`，2026-09-21 使用者指定）。
- 盤點（CDP 逐元素掃描 `/`，含 `::before/::after`）：首頁真正渲染第二主題色的只有 2 類元素 ——
  ① yama 圓球 `.bc-yama .tax-nav a`（≥769、174px）② hero 圓點 `.bc-gunte-hero #hero_nav > li > button::before`（7 顆）；
  另 `.bc-floating-cart-badge` 為全站元件（購物車空時 `display:none`，仍在 DOM）。順帶清掉 index 上最後一個用法：
  `.bc-yama-discount`（-5 積分，僅登入後 ≤768 近黑球上可見）。

### 實作（3 檔 CSS ＋ 3 處版號）
- `static/css/bc-yama-header.css`：`:root` 的 `--bc-yama-circle` `var(--bc-theme2, #fcff4b)` → **`var(--bc-gold, #c49b63)`**
  （**僅 ≥769 生效**；≤768 球底色是硬編碼近黑 `#131211`，本次刻意不動）；`.bc-yama-discount` 同步 `var(--bc-theme2, #fcff4b)`
  → **`var(--bc-gold, #c49b63)`**（＝還原 2026-09-21 前的原值；≤768 金字對近黑底 7.27:1、≥769 由檔尾 media 覆寫 `#1b1b1b`
  對品牌金 6.74:1，皆 AA 內文）。同檔檔尾註解補 ③ 說明。
- `static/css/bc-gunte-hero.css`：`.hero_nav > li > button::before` 背景 `var(--bc-theme2)` → **`var(--bc-gold, #c49b63)`**
  （`.‑current` 仍白 32px、hover 只變寬不變色、`:active` 仍白）。
- `static/css/bc-components.css`：`.bc-floating-cart-badge` 背景 `var(--bc-theme2)` → **`var(--bc-gold)`**（全站；深字 `#0e0e0e`
  對品牌金 7.5:1，維持不變）；`:root` 的 `--bc-theme2` 註解更新為「2026-10-08 起全站已無元件引用」（**定義保留**，日後要用直接 `var()` 取用）。
- 版號：`templates/.../base.html` bc-components `?v=20260921m → ?v=20261008e`；`index.html` bc-yama-header
  `?v=20260925c → ?v=20261008e`、bc-gunte-hero `?v=20260921b → ?v=20261008e`（WhiteNoise `MAX_AGE=1 年`）。
- ⚠️ 本機 `DEBUG=False` + `runserver --noreload` 使用 **cached template loader** ⇒ **改模板必須重啟 runserver** 才生效（本次踩到）。
- 純顏色變更：**幾何、動畫、z-index、事件全未動**（圓球 174/150px、圓點 16/32px 與 13/24px、ORDER NOW 文字環、hover 白球皆不變）。

### 驗證
- 新增 `docs/verify/cdp_verify_theme_color_index.py`（CDP）：**合計 100 項、PASS 100 / FAIL 0**。
  A 版號／B 圓球（≥769 品牌金、≤768 維持近黑）／**B0 `.tax-nav` opacity==1**（圓球可見）／**B4 圓球實際截圖像素**（品牌金 2250、1688 點）／
  C 圓點（6 金 + 1 白，依斷點 32px／24px；另 **C0/C4 CSSOM 靜態規則檢查**：基底 `var(--bc-gold, #c49b63)`、`.‑current` 白/32px）／
  D badge（品牌金＋深字）／G 對比／**E1 首頁 computed 掃描 0 筆第二主題色**／**F1 CSSOM 掃描「除 `:root` 定義外不得再引用 `var(--bc-theme2)`」**
  （⇒ 連登入後才出現的 `-5` 也涵蓋）／H `/about/`、`/coffee_menu/` 的 badge 與殘留。
- 既有回歸：`docs/verify/cdp_verify_floating_cart.py`（5 斷點 × 5 頁）**全部通過**；`python3 manage.py check` 0 issue。
- 截圖：`_verify_theme_gold_1440.png`／`_verify_theme_gold_390.png`／`_verify_theme_gold_ball_zoom.png`（圓球品牌金、深字可讀、
  ORDER NOW 環保留）／`_verify_theme_gold_dots_1440.png`（6 金 + 1 白）；改前對照 `_verify_theme_theme2_1440.png`／`_verify_theme_theme2_390.png`（萊姆）。
- **兩個量測陷阱**（已寫入腳本註解與防線，避免日後誤判）：
  ① hero 為**自動輪播**且圓點 active 有 **0.3s 過渡** ⇒ 過渡起始瞬間取樣會把「白 32px」誤判成「品牌金 16px」
  （實測抓到 `rgb(215,187,149)` / `21.1px` 的中間值）→ 腳本先注入 `*{transition:none}` 凍結過渡，另加 C0/C4 靜態檢查。
  ② Chrome 對**被遮蔽／背景分頁會暫停動畫** ⇒ 圓球淡入（`.init` 0.6s）可能凍結在 `opacity:0`
  （造成截圖上圓球「不見了」的假缺陷）→ 新增 B0（opacity==1）與 B4（實際像素）兩項。
- 另註：CDP `Page.setCacheDisabled` **單獨無效**（仍會用瀏覽器快取）→ 需 `Network.enable` + `Network.setCacheDisabled`；
  本次 A/B 期間即因此量到舊 CSS（已於腳本中同時設定兩者）。



## 44. about footer 換上 index 跑馬燈 ＋ 修掉平板/行動「越欄 2000px」缺陷 🎏 — ✅ 2026-10-08

### 需求
- about footer 的 email CTA（`.footer-mail-inner`）改為與 index footer 逐字相同的 `.scroller-box` 跑馬燈（樣式/JS 全部複用）。
- 完成後發現：平板/行動跑馬燈量到 ~2000px、橫貫整個 footer 並壓到右側裝飾字，只因 `#bc-bg-footer{overflow:hidden}` 裁掉才沒出現水平捲軸。

### 診斷（CDP 量測 ＋ 逐一注入候選修法比對）
- ≤991px 時 `.foooter-mail` 帶 Webflow 原樣 `grid-area:5/1/6/4; justify-self:start` ⇒ grid item 走 shrink-to-fit；
  其 max-content 由跑馬燈決定：main.js 設 `data-animated=true` 後 `.scroller__inner{flex-wrap:nowrap}`、2 個 li 各 1108px
  （`.tag-list li{width:1108px}`）＋ `.scroller{max-width:2000px}` ⇒ item 量到 2000px。
- 實測：平板 768（欄寬僅 341px）item 2000px、行動 390（欄寬 173px）item 2000px；桌機 ≥992px 因 `justify-self:auto`
  本來就拉伸到欄寬（298/336px）⇒ **只有 ≤991px 壞**，故 desktop 看不出問題。
- 候選修法實測：`min-width:0` 無效、`justify-self:stretch` 被 ID 特異度（2,1,0）既有規則蓋掉、
  `.scroller{max-width:100%}` 反而放大到 2745px、**只有 `width:100%` 把 item 拉回欄寬（平板 341／行動 173）**。

### 實作（只動 2 檔）
- `static/css/bc-bg-footer.css`：新增 `#bc-bg-footer .foooter-mail{min-width:0;width:100%;}`（附成因/修法註解；
  `min-width:0` 用來擋 `min-width:auto` 以 min-content(2000px) 反過來把格子撐開）。
- `templates/betweencoffee_delivery/about.html`：`bc-bg-footer.css ?v=20261008c → ?v=20261008d`。
- 動畫與 li 尺寸完全不受影響：inner 仍 4435（≥768）／2745（<768）、`animation: scroll 60s linear`、li 1108px ／ ≤767.98px 685px。

### 驗證
- `docs/verify/cdp_verify_footer_scroller.py`：**合計 101 項、PASS 101 / FAIL 0**（原 93 項 ＋ 新增 F5/F6 每斷點 2 項 ＋ I5/I6）。
- 新增檢查：F5「`.foooter-mail` 未撐破所屬 grid」、F6「`.foooter-mail` 寬 <= viewport 寬」（每斷點各 1 組）＋
  I5/I6（prefers-reduced-motion 無動畫狀態）；**舊版只驗 `scroller <= mail`，兩邊同步被撐大時照樣 PASS ⇒ 抓不到此缺陷**。
- 反測（把 `width:100%` 暫時還原成 `width:auto` 後重跑）：**合計 101 項、PASS 95 / FAIL 6**，
  錯誤訊息即缺陷本體 `grid scrollW 2000 vs clientW 690`（平板 768）、`2000 vs 343`（行動 390）⇒ 新防線確實有效。
- 修後量測：桌機 1280 grid 1237/1237、mail 298；平板 768 grid 690/690、mail 334；行動 390 grid 343/343、mail 166；
  reduced-motion 390 亦 343/343、166；截圖 `_verify_footer_scroller_{desktop,tablet,mobile}.png` 可見跑馬燈僅在自己欄位內捲動、
  不再與「roasted daily」交疊。


## 43. 首頁 bc-reviews 跑馬燈全端放大 15%（方案 C：CSS 變數倍率）🔍 — ✅ 2026-10-07

### 需求
- 首頁 `bc-reviews-section`（feed 下方反向跑馬燈）整區放大 15%；about 頁同一模組維持原樣。

### 實作（方案 C：CSS 變數倍率；只動 2 個檔案）
- **`static/css/bc-reviews.css`**：所有尺寸值改為 `calc(原基準px * var(--rv-scale, 1))`（base＋`@media 768`＋`@media 480` 三段）；新增 `.bc-reviews-section--lg { --rv-scale: 1.15; }`。
- **`templates/betweencoffee_delivery/index.html`**：首頁 section 加 `bc-reviews-section--lg` class；版號 `bc-reviews.css ?v=20260906a → ?v=20261007a`。
- 預設 `--rv-scale:1` ⇒ about 頁（未加 `--lg`）像素等值（fallback）；倍率經 CSS 變數繼承，改倍率只動一行。
- **JS 零改動**：`bc-reviews.js` 速度 `duration = half/80`（half＝`scrollWidth/2`）隨內容 ×1.15 自動等長 ⇒ 線性速度維持 ~80px/s。

### 驗證（全 PASS）
- 新增 `docs/verify/verify_reviews_scale.py`（CDP）：首頁 @1280/768/390 全部尺寸 == 該斷點基準×1.15、`--rv-scale=1.15`、無水平溢出、跑馬燈 moving＋`repeat:-1` tween=1；about @1280/390 全部尺寸 == 原基準、`--rv-scale` fallback 1、section 無 `--lg` → **PASS 110 / FAIL 0 ✅**。
- `python3 manage.py check` → 0 issue；CSS 大括號 37/37 平衡。

### 涉及檔案
- `static/css/bc-reviews.css`、`templates/betweencoffee_delivery/index.html`、`docs/verify/verify_reviews_scale.py`（新增）


## 42. 咖啡自訂選項組新增「茶種」（tea_type）🍵 — ✅ 2026-10-06

### 需求
- 咖啡選項新增一組「茶種」，值為 `1 碧螺春`／`2 白芽奇蘭`（與 §41「烘焙」同一模式）。
- 需在咖啡詳情頁前端渲染、在 Django Admin 放入自訂選項組並支援顯示排序。

### 實作（機制全資料驅動；功能面 3 個檔案＋1 個前端遺漏修正）
- **定義**：`eshop/models/option_definitions.py` 的 `OPTION_GROUPS` 末追加 1 組——`key="tea_type"`／`label="茶種"`／`icon="emoji_food_beverage"`／`choices=[("1","碧螺春"),("2","白芽奇蘭")]`／`default="1"`（⇒ 咖啡 17 組 → **18 組**；同步更新該檔「咖啡 18 組 + 豆 3 組」註解）。
- **模型**：`eshop/models/shop_items.py` 的 `CoffeeItem` 追加 `option_tea_type`（`BooleanField(default=False)`＝**每款咖啡由 Admin 決定是否啟用**；未啟用者詳情頁完全不渲染 ⇒ 舊資料零影響）與 `option_order_tea_type`（`PositiveIntegerField(default=0)` 排序）。
- **Migration**：`eshop/migrations/0080_coffeeitem_option_order_tea_type_and_more.py`（`AddField` ×2，deps＝0079）。
- **附帶修正（前輪遺漏）**：`static/js/bc-slideout-cart.js` 咖啡分支原用硬編碼 `labelMap`（缺 `roast_level`／`tea_type` ⇒ 滑出購物車會把原始 key 顯示給客人）→ 改為與豆端一致「API `extra_options_labels`／`extra_options_icons` 優先、`labelMap` 僅作後備（並補齊 18 組）」；`templates/betweencoffee_delivery/base.html` 版號 `?v=20260921g` → **`?v=20261006a`**。
- **零改動即生效的既有機制**：Admin 合併欄位（`OptionGroupsConfigFormMixin.save()` 泛型 `option_<key>` setattr；`CoffeeItemAdmin.fieldsets` 只有 `option_groups_config`，故新組自動出現）／詳情頁 `Coffee.get`（依 `option_<key>` 過濾＋`option_order_<key>` 排序）／模板 `coffee.html`（泛型 `group.*` 迴圈）／`cart/views.py`（泛型收集 `option_<key>` 進 `extra_options`）／`OrderModel.translate_option`、`get_order_display_items`（`ALL_OPTION_GROUPS` 查表＋圖示）。
- **註解同步**：`eshop/admin.py`（17 組 → 18 組，2 處）、`option_definitions.py`（咖啡 18 組 + 豆 3 組）。

### 驗證（全 PASS）
- `python3 manage.py makemigrations eshop` → `0080_coffeeitem_option_order_tea_type_and_more`；`migrate eshop` → OK；`python3 manage.py check` → **0 issue**；`makemigrations --check` → **No changes detected**。
- **新增** `docs/verify/verify_coffee_tea_type_option.py`（27 項，可重複執行、跑完自動復原）：定義層（label/icon/default/choices、18 組 key 唯一、`get_option_label`／`get_option_value_label`／`translate_option`、不在 `BEAN_OPTION_GROUPS`）／Admin（Widget 解析、Form 儲存寫回 `option_tea_type`＋`option_order_tea_type`、合併欄位有 checkbox＋排序數字、無分離欄位）／前台（未啟用不渲染、啟用渲染「茶種 :」＋碧螺春/白芽奇蘭＋default `1` active＋hidden value `1`、`option_order_tea_type=1` 時排最前）／購物車（`extra_options["tea_type"]="2"`、cart key `coffee_1_tea_type_2`、`CartItem.options_json` 同步）／訂單（`extra_options_cn`＝白芽奇蘭、`options_display` 含「茶種: 白芽奇蘭」）／舊訂單相容 → **全部通過 ✅**
- `docs/verify/verify_all_options.py`（17→18 組）：PICK／EXPECT_CN／DEFAULTS 加 `tea_type`，B 段暫時啟用＋E 段復原、E 段新增茶種定義與 Admin 專項 → **全部通過 ✅**
- `docs/verify/verify_group_order.py`（標籤改動態 `{len(KEYS)}`）→ **全部通過 ✅**；`docs/verify/verify_bean_group_order.py`（Coffee Admin 仍 18 組）→ **50/50 通過 ✅**
- `docs/verify/verify_coffee_roast_option.py`：原硬編碼「roast_level 為最後一組（17 組）」因追加茶種而失效 → 改為與位置無關的「18 組、key 唯一、roast_level 在定義中」→ **全部通過 ✅**
- **滑出購物車**（`bc-slideout-cart.js`）：以**真實原始碼＋真實 API payload**（`/cart/count/`）做 node 單元驗證 **6/6**（輸出含「茶種: 白芽奇蘭」「烘焙: 中烘」、不再外洩 `tea_type:`／`roast_level:`、圖示正確）＋ **Playwright 瀏覽器 E2E**（`/coffee/1/` 點「白芽奇蘭」→加入購物車→開滑出購物車＝`emoji_food_beverage 茶種: 白芽奇蘭`）→ **全部通過 ✅**（驗證後已還原 #1 的暫時啟用）。
- 註：5 支驗證腳本**必須循序執行**（共用 DB、暫時啟用→復原，並行會互相污染）。

### 未動 / 觀察
- `CoffeeItem #9 果香浅煎 option_roast_level=True` 為**使用者本人於 2026-10-06 06:29–06:30 在 Admin 親自啟用**（`django_admin_log` 有兩筆 user 58 紀錄），屬人工設定，**未更動**。



### 需求
- 咖啡選項新增一組「烘焙」，值為 `1 浅烘`／`2 中烘`。

### 實作（機制全資料驅動，只動 3 個檔案）
- **定義**：`eshop/models/option_definitions.py` 的 `OPTION_GROUPS` 末追加 1 組——`key="roast_level"`／`label="烘焙"`／`icon="local_fire_department"`／`choices=[("1","浅烘"),("2","中烘")]`／`default="1"`（⇒ 咖啡 16 組 → **17 組**；同步更新該檔「咖啡 17 組 + 豆 3 組」註解）。
- **模型**：`eshop/models/shop_items.py` 的 `CoffeeItem` 追加 `option_roast_level`（`BooleanField(default=False)`＝**每款咖啡由 Admin 決定是否啟用**；未啟用者詳情頁完全不渲染 ⇒ 舊資料零影響）與 `option_order_roast_level`（`PositiveIntegerField(default=0)` 排序）。
- **Migration**：`eshop/migrations/0079_coffeeitem_option_order_roast_level_and_more.py`（`AddField` ×2，deps＝0078）。
- **零改動即生效的既有機制**：Admin 合併欄位（`OptionGroupsConfigFormMixin.save()` 泛型 `option_<key>` setattr；`CoffeeItemAdmin.fieldsets` 只有 `option_groups_config`，故新組自動出現）／詳情頁 `Coffee.get`（依 `option_<key>` 過濾＋`option_order_<key>` 排序）／模板 `coffee.html`（泛型 `group.*` 迴圈）／`cart/views.py`（泛型收集 `option_<key>` 進 `extra_options`）／`OrderModel.translate_option`、`get_order_display_items`（`ALL_OPTION_GROUPS` 查表＋圖示）。
- **語意隔離**：`BeanItem.roast_level` 為咖啡豆「烘焙水平刻度」（light/…）欄位，與本組 `"1"/"2"` 不同域；`BEAN_OPTION_GROUPS` 自 0073 起無 roast 組 ⇒ `ALL_OPTION_GROUPS` key 不重疊（程式碼內已註明：豆端未來若要開同名組須先換 key）。

### 驗證
- `python3 manage.py makemigrations eshop` → `0079_coffeeitem_option_order_roast_level_and_more`；`migrate eshop` → OK；`python3 manage.py check` → **0 issue**。
- **新增** `docs/verify/verify_coffee_roast_option.py`（27 項，可重複執行、跑完自動復原）：定義層（label/icon/default/choices、17 組 key 唯一、`get_option_label`／`get_option_value_label`／`translate_option`、不在 `BEAN_OPTION_GROUPS`）／Admin（Widget 解析、Form 儲存寫回 `option_roast_level`＋`option_order_roast_level`、合併欄位有 checkbox＋排序數字、無分離欄位）／前台（未啟用不渲染、啟用渲染「烘焙 :」＋浅烘中烘＋default `1` active＋hidden value `1`、`option_order_roast_level=1` 時排最前）／購物車（`extra_options["roast_level"]`、cart key 含 `roast_level_2`、`CartItem.options_json` 同步）／訂單（`extra_options_cn`＝中烘、`options_display` 含「烘焙: 中烘」）／舊訂單相容 → **全部通過 ✅**。
- `docs/verify/verify_all_options.py`（16→17 組）：取樣咖啡改為「PICK 中啟用最多組」動態取樣，未啟用組改驗「不渲染」⇒ 對 Admin 調整具韌性 → **全部通過 ✅**
- `docs/verify/verify_group_order.py`（16→17）：排序測試於開頭暫時啟用所需的 4 組、結束復原 → **全部通過 ✅**
- `docs/verify/verify_bean_group_order.py`（16→17）：購物車取樣改為明確取 `type=="bean"` 那筆（`Cart.sync_with_database` 會把登入帳號殘留的 `CartItem` 併入而取到別的商品）→ **50/50 通過 ✅**

### 涉及檔案
- `eshop/models/option_definitions.py`（新增 `roast_level` 組＋註解）
- `eshop/models/shop_items.py`（`CoffeeItem` 新增 2 欄位）
- `eshop/migrations/0079_coffeeitem_option_order_roast_level_and_more.py`（新增）
- `eshop/admin.py`（僅註解：16 組 → 17 組）
- `docs/verify/verify_coffee_roast_option.py`（新增）、`verify_all_options.py`、`verify_group_order.py`、`verify_bean_group_order.py`
- ⚠ **待部署：migration 0079**（Render `autoDeploy=no`，需手動 Manual Deploy）

## 40. sake-shirakiku product-mv 整合 + ramen REAL/reviews 整合 + 平板照片放大置中 🍜 🍶 — ✅ 2026-09-01

### 需求
- ① 整合 ramenclub.jp c-sec-product-real「3 つのリアル」+ hakujuji waffle `.reviews` 水平跑馬燈至 about 頁；② 平板端 bc-ramen-product 照片放大 + 與頁面中心對齊；③ 整合 sake-shirakiku.jp/products/vibran 的 `<section id="shopify-section-template--16830511972551__main" class="shopify-section product-mv">`（完整複製 UI/動畫、置於 `.boxBottomLine` 下方），載入額外字型。

### 實作
- **reviews 跑馬燈**：`bc-reviews.js` 原 body 尾同步執行（GSAP defer 未載入 → 提早 return）→ 改 `DOMContentLoaded` 內檢查 gsap；區塊包 `section.bc-reviews-section` 移至 row-animation 下方、capabilities 前；dot 垂直居中（`.reviewsMark__box` inline-flex align-items:center height:25px）。
- **ramen REAL**：行動端（≤680px）`.c-real-txt > .r` `margin-top: calc(-29.07vw - 30px)` 重疊照片 25%；**+ 符號位移修復**（`.c-real-txt .r` 後代選擇器誤傷 `.ui-btn-more > .r` → 改子選擇器）；**平板照片放大 + 置中**（768-1279px）：width 48vw、left 26vw、top `calc(50vh - 27.8vw)` → 照片中心 = 頁面中心。
- **product-mv 整合**：新 `section.bc-sake-mv` 包住原站結構（4 staff-comment 氣泡 + 產品照片 vibran.jpg）；**rem 基準轉換** `--sake-rem`（≤767 26.67vw / 768-1099 80.527px / 1100-1365 7.32vw / ≥1366 100px，Xrem→calc(X*var(--sake-rem))）；**Bootstrap `.p-1~p-4` padding 衝突修復**（padding:0 !important）；黑底文字 `color:#111`；載入 **YakuHanJP** 字型（jsdelivr CDN）；`bc-sake-mv.js` 複製原站 mvStaff（3 秒亂序切換 is-show）；**氣泡超出 mv 修復**（staff margin-top `calc(2.5 * var(--sake-rem))`，先 overflow:clip 會裁動畫氣泡）；img-load loaded clip-path 進場動畫。

### 驗證（Playwright 實測）
- 1280px 桌面與原站逐項對照：product-mv 1280×1280、p-1~p-4 位置/尺寸全一致（128/407.6 147×161、320/468.5 201×180、768/407.6 201×180、1088/451.7 164×147）；文字 #111、字距 .02em、圖章 staff01~04、pattern SVG 正確。
- 平板 834（--sake-rem 80.527px）/ 行動端 375（26.67vw、staff absolute、overflow hidden）換算全正確。
- 動畫：is-show 輪播切換正常、img-load 進場、氣泡動畫完整不裁切不超出 mv（pixel 分析 + rect 量測）。
- scoped：`.staff-comment` 僅存在 .bc-sake-mv（4 個），不影響其他 section；console 無新增錯誤。

### 涉及檔案
- `templates/betweencoffee_delivery/about.html`
- `static/css/bc-ramen-product.css`（?v=20260828z）、`static/css/bc-reviews.css`（?v=20260828c）、`static/css/bc-sake-mv.css`（?v=20260831e）
- `static/js/bc-reviews.js`（?v=20260828b）、`static/js/bc-sake-mv.js`（?v=20260831a）
- `static/images/sake-mv/`（vibran.jpg + blowing-pattern01~03.svg + staff01~04.png）、`static/images/ramen/`

### 40b. fujiya-peko.co.jp/cakebrand #photo_area 鎖定頁面整合 — ✅ 2026-09-01
### 需求
- 整合 https://www.fujiya-peko.co.jp/cakebrand/ 的 `#photo_area` 鎖定頁面部分（photo_slide_item1/2/3 + photo_line1/2/3 + 標語 copy）與相關動畫至 about 頁；新 section 包住 + 置於 `.boxBottomLine` 下方；UI/動畫與原站完全一致、不添加額外 UI/css。

### 實作
- **HTML**：新 `section.bc-fujiya-photo` 包住原站 `#photo_area`（完整複製：`#photo_ttl` 三組標語 copy 逐字 span + mark.svg + `#photo_slide` 三照片 picture/picture.b + sp source + `photo_line1/2/3`），置於 `.boxBottomLine`（topConcept）結束後、ftco-section-blank 前；圖片路徑改 `{% static %}`。
- **2026-09-01 追加（.mark → .bc-other-members）**：photo_area 三個 copy 的 `.mark`（mark.svg）內容更改為 `.bc-other-members` 動畫——完整複製 topConcept 元件（「【 他にもいます！】」span + other-members-svg 手繪圓形），SVG mask/clipPath id 加後綴 `_FP` 避免與 topConcept 衝突。**2026-09-01 五次修訂（使用者最終行為定義）**：① **文字 z-index 置圓形正中央**（span z-index:2 疊 svg z-index:0 上，flex 居中）；② **只顯示 1 次**（一份置 title 層）；③ **跟隨第一組文字（copy1）**——向下捲 copy1 顯示（showPhoto(1)）時顯示並播放動畫、**每次重新進入重播**（remove .show → reflow → add .show 重啟 scale/畫線）；copy1→2→3 全程常駐（showPhoto/closePhoto 2/3 不影響 bc-other-members）；向上回捲到第一組文字消失（closePhoto(1)）時一起 `.hide` 消失；再次往下捲動重新觸發。修正：早期 hide 綁定 closePhoto(所有 n)/photo_area 段落造成 copy2 顯示或回捲時提早/不消失。
- **CSS**（新 `bc-fujiya-photo.css`）：複刻原站 screen.css 4 斷點（≥1921 px 大版 / 1360-1921 px 小版 / 768-1359 vw 版 / ≤767 SP 600vh）+ cmn.css `txt_up_slide`；黑底 #0e0e0e + 白字 #fff 適配；SP `.copy` `transform:none` 覆蓋 PC translateX。
- **JS**（新 `bc-fujiya-photo.js`）：複製原站 script.min.js photo_area——Waypoint ×6（offset `.79*(windowH−copyH)` / `10%`）+ GSAP ScrollTrigger ×3（mask scrub）+ resize；**時序修正**：body 尾同步 script 早於 head defer GSAP → DOMContentLoaded 後 `boot()` 檢查。
- **資源**：`static/images/fujiya-photo/`（photo1~3.jpg 2720×1200 + _b/_sp/_b_sp + mark.svg + sv_shape_pc/sp.svg）。

### 驗證（Chrome DevTools 實測）
- 桌面 1920（1360-1921 斷點 txt 24px/mark 64px/slideH 927/copy left 193px）；平板 834（vw 版 txt 14.72px/mark 39px/700vh/pc mask）；行動端 375（600vh/photo_line 30vh/sp 圖 750×1040/slideH 471/copy left 0）。
- 滾動全程：photo_line1/2/3 各階段 copy 切換 + item.open + mask-position 0px + mask-size 185%（SP 300%）+ 逐字 y:0 + mark 滑入；逆滾 closePhoto 反向正常；sticky 鎖定 rectTop 0；console 無新增錯誤。

### 涉及檔案
- `templates/betweencoffee_delivery/about.html`
- `static/css/bc-fujiya-photo.css`（?v=20260901k）、`static/js/bc-fujiya-photo.js`（?v=20260901h）
- `static/images/fujiya-photo/`（photo1~3.jpg + _b/_sp/_b_sp + mark.svg + sv_shape_pc/sp.svg）


## 39. Timber Wharf 全域應用 + weekday 徽章 + SERIES 資料庫驅動（咖啡/咖啡豆）🌍 — ✅ 2026-08-27

### 需求
- ① 「他にもいます！」動畫文字縮小 + 加【 】符號；② 整合 yokohama-timberwharf event/1125 的 `.weekday` 徽章（香港真實星期、與日期水平對齊）；③ weekday 稍微加大；④ Timber Wharf 元件**應用於全域**（所有頁面右上角）；⑤ 右側虛線應位於底層（不疊 weather）；⑥ bc-series-caption 照片與文字水平居中；⑦ bc-series-caption-highlight 稍微減小；⑧ bc-series-list 照片改**資料庫咖啡**（id 1-4、7、8 主圖）；⑨ 修復照片 2（Sunshine 圖檔被刪）；⑩ 複製一組咖啡豆 **BEANS 括號滑桿**（BeanItem 照片/名稱/highlight）。

### 實作
- **① 他にもいます！**：字體 16/20/26 → **13/16/21**（約 -20%）；文字改 **【 他にもいます！】**（about.html `.bc-other-members` span + bc-series.css）。
- **② weekday 徽章**：nav.html date 內加 `<span class="weekday">`；inline script + bc-weather.js `fillDate` 填入香港真實星期（`getDay()` → Sun..Sat）；CSS 膠囊徽章（`border-radius:100px`、白 12% 背景、9px——黑底適配原站 `#0000001a`）；桌面/平板 inline 與日期水平對齊（`vertical-align:middle`）、移動端（≤767.98）block 換行下方（原站 .mb 行為、空間不足）。
- **③ weekday 加大**：桌面 9→**10px**、移動端 8→**9px**（padding 同步）；weekday 變寬使 weather 容器 80→84px → c-attract 對齊位移 -11→**-9px**。
- **④ 全域應用**：nav.html 移除 `{% if url_name=='about' %}` 條件；base.html head 加 bc-weather.css、scripts 加 bc-weather.js；about.html 移除重複引用。全站右上角顯示（index/coffee_menu 驗證）。
- **⑤ 虛線 z-index**：`#borders` **9999→2**（navbar 3 > 虛線 2 > 內容 1）——weather 顯示於虛線之上，虛線位於底層。
- **⑥ caption 水平居中**：`.bc-series-caption` 加 `text-align:center`（名稱/highlight 與照片水平居中）。
- **⑦ highlight 減小**：16/13/11px（原 18/15/12）。
- **⑧ 咖啡照片資料庫驅動**：About view 加 `series_coffees`（CoffeeItem id 1,2,3,4,7,8；id 5、6 已刪）；about.html 兩組 SERIES 滑桿改 `{% for coffee %}` 迴圈，圖片**統一 `coffee.image.url`**（主圖；先前誤用 image_index 首頁圖已修正）、名稱/highlight 資料庫驅動。
- **⑨ 照片 2 修復**：Sunshine 主圖 `coffee_08_B0g2qHs.png` 工作區被刪（404）→ `git checkout` 從 HEAD 恢復（861KB）。
- **⑩ 咖啡豆 BEANS 滑桿**：複製括號滑桿 `<section class="bc-series-hero bc-series-bracket show">`，標題 BEANS + 副標題「咖啡豆，專屬風味」；`{% for bean in series_beans %}`（BeanItem id 1,2,3,6,7,8）照片/名稱/highlight；SVG id C 後綴（leafFlowRevealMaskC/leafFlowClipC）；bc-series.js 自動支援（多組 hero 拖動/pager/snap）。

### 驗證（Playwright/CDP 實測）
- weekday：桌面/平板 Thu 與日期水平對齊（中心 Y 一致）、移動端 block 換行；全站（index/coffee_menu）顯示香港真實星期。
- 全域：weather 在 index/coffee_menu 顯示、虛線對齊各斷點（1280=1214、375=342）、無溢出。
- 虛線：weather 中心點 elementFromPoint 最頂層為 weather 內容（非虛線）、z-index 2 < navbar 3。
- SERIES：caption 名稱中心 = 照片中心（1280/1024/375 全居中）；highlight 16/13/11px；咖啡照片（coffee_01_2/coffee_08_B0g2qHs/coffee_03_1/coffee_02_WIBSw91 + id7/8 主圖）HTTP 200 載入。
- BEANS 滑桿：6 種豆（Kenya/Rwanda/Kingsman/Brazil/Sumatra/Colombia）+ highlight + bean 圖；pager 左移 0→-420、右移 -420→0；SVG id 無衝突；show class 觸發。
- `manage.py check` 0 issues、node --check OK。

### 涉及檔案
- `betweencoffee_delivery/views.py`、`templates/betweencoffee_delivery/about.html`、`templates/betweencoffee_delivery/base.html`、`templates/layouts/nav.html`
- `static/css/bc-weather.css`、`static/css/bc-attract.css`、`static/css/bc-series.css`、`static/js/bc-weather.js`
- `media/coffee_images/coffee_08_B0g2qHs.png`（git 恢復）


## 38. yokohama-timberwharf weather 天氣/時鐘元件整合 to about 頁右上角 🌤️ — ✅ 2026-08-26~27

### 需求
- 將 https://yokohama-timberwharf.com/ 的 `<div class="weather -font_en">`（天氣/溫度/日期元件）整合到 about 頁右上角；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。
- **後續追加需求**：① 新增時鐘（動畫順序 **時鐘→天氣→溫度**）；② 修復初始狀態異常（溫度先顯示跳動/重疊日期/日期跳動）；③ 位置與 c-attract（點線）中心點對齊；④ 隱藏年份（顯示邏輯不變）+ 日期字體增大；⑤ 導航列「｛ Between ｝」增大；⑥ 天氣改為**香港葵涌**；⑦ 移除底部邊框線；⑧ 修復載入「--:--」閃現與時間日期不同步。

### 原站機制分析（yokohama-timberwharf.com）
- **HTML**：`<div class="weather -font_en">` = `.view`（`.icon` + `.temperature` 重疊裁切窗 **80×40 overflow:hidden**）+ `.date`（month/day/year）+ `.border`。
- **CSS**（style.css `header .main .weather` 系列）：flex column 高 80px；`.view>*` absolute `inset:0;margin:auto` 重疊置中；icon/溫度透過 **GSAP x 位移在 80px 窗口內滑動切換**；`.-font_en` 600 weight `SaansSemiBold,Helvetica Neue`；`.-color_white` 變體 `filter:brightness(0) invert(1)` 反白圖示。
- **JS**（main.js）：XMLHttpRequest → OpenWeatherMap `q=Yokohama&units=metric&lang=ja`；`weather[0].icon` 對映 7 個 `header_weather_*.svg`（建立 img width=80 height=40 + alt）；日期/溫度填充；**每 5 秒 icon↔溫度滑動切換**（duration .8、easeInOut、rAF 計時）。

### 實作
- **資源**（7 個）：`static/images/header_weather_sunny/partlycloudy/cloudy/rainy/snowy/foggy.svg` 下載自原站（80×40、`#242322`）；**⚠️ thunderstorm 原站自身 404**（JS 有引用但檔案不存在、Wayback 無存檔）→ 依原站風格（rainy 雲朵 + 閃電）補建。
- **nav.html**（僅 about 頁 `{% if request.resolver_match.url_name == 'about' %}` 條件顯示，其他頁面零影響）：container 內（toggler 後）加入 weather 結構；**時鐘** `.clock` 加入 view 內（動畫首位）；**inline script 立即同步填入時鐘+日期**（DOM 解析時執行，早於外部腳本）。
- **static/css/bc-weather.css**（新建）：原站 weather 樣式完整複製 scoped 至 `#ftco-navbar .weather`；黑底 `-color_white` 反白；**CSS 初始定位**（clock x:0 / icon·temp x:80，CSS 生效即時鐘顯示）；**c-attract 對齊 transform**（4 斷點 -11/-21/+8/+12px 中心對齊右側虛線）；時鐘樣式 28/24px；日期 12px + `.year{display:none}`；`.border{display:none}`。
- **static/js/bc-weather.js**（新建）：原站邏輯還原（XHR/icon 對映/日期溫度/alt）；時鐘 `updateClock` 每秒刷新 HH:MM；**3 元素循環動畫狀態機**（ORDER = clock/icon/temperature，每 5 秒當前滑出左側、下一個右側滑入、上上個悄悄回右側待命）；**初始定位立即執行（不等 API）+ startLoop 延至 API 回應後**；API 改 `q=Kwai Chung`（**香港葵涌**，coord 22.3633,114.125）。
- **bc-components.css**：navbar-brand「｛ Between ｝」各斷點 **+4px**（40/34/28/24）。

### 修復歷程（重要）
- **① 初始狀態異常**：`setupAnimation` 原只在 API 回應後執行 → 回應前三元素無 transform 疊在 view 中央（溫度 23°C 蓋住時鐘/icon）→ 溫度先顯示再跳動。修復：**CSS 初始 transform** + JS `setInitialPositions()` init 立即執行 + `startLoop()` 延後（icon 有圖才開始循環）。
- **② `.value` selector 撞名**：時鐘加入後 DOM 有兩個 `.value`，`fillDate` 的 `querySelector('.value')` 誤選時鐘 → 溫度從未更新（顯示 HTML 初始 23）。修復：精確 `.temperature .value`/`.temperature .unit`。
- **③ c-attract 對齊**：weather 水平中心對齊 `#borders` 右側虛線中心（= Order 按鈕視覺中心）；位移量 = weather centerX − 虛線 centerX，各斷點不同（虛線 right 65/36/32px + weather 寬 80/60px）：≥992 左移 11、768-991.98 左移 21、576-767.98 右移 8、≤575.98 右移 12。用 transform（不影響 flex 佈局）。
- **④ 「--:--」閃現 + 時間日期不同步**：時鐘 HTML 佔位 `--:--` 在外部 JS 前顯示；日期原在 API 回應後才填（原站邏輯）→ 時間先、日期後。修復：inline script 立即**同步填入時鐘 + 日期**（日期用本地 `new Date()`，不依賴 API）。

### 驗證（Playwright/CDP 實測）
- **桌面 1280**：weather 右上角且**中心對齊虛線（1214=1214）**；時鐘即時（16:56 等）；葵涌天氣 30°C + cloudy；日期「Aug, 27」（year 隱藏）；**動畫 5 秒完整循環**（時鐘→icon→溫度→時鐘，5 點取樣）；無溢出、無 JS 錯誤。
- **響應式**：768/600/375 三斷點 weather 中心 = 虛線中心（702/563/342 全對齊）、60×30、year 隱藏、無水平溢出。
- **navbar logo**：40/34/28/24px 四斷點、與 weather/漢堡選單無重疊、index 頁正常（112px navbar）。
- **CSS-only 降級**：清除 JS transform 後 CSS 初始定位仍正確（時鐘顯示）。`manage.py check` 0 issues、node --check OK。

### 涉及檔案
- `templates/layouts/nav.html`、`templates/betweencoffee_delivery/about.html`、`templates/betweencoffee_delivery/base.html`
- `static/css/bc-weather.css`（新）、`static/js/bc-weather.js`（新）、`static/css/bc-components.css`
- `static/images/header_weather_*.svg` ×7（新）


## 37. sukima capabilities-gallery 整合 to about 頁 🎞️ — ✅ 2026-08-25

### 需求
- 將 https://sukima.tokyo.jp/ 的 `.capabilities-gallery` 整合到 about 頁（建立新 section）；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。
- **整合決策**：黑底適配（沿用先例）；動畫範圍用「進入視口→通過視口」vh 範圍（避免原站 150vh 過長跟不上——who 整合經驗）；分段比例與原站相同。

### 原站機制分析
- **結構**（12595 字符）：`.capabilities-gallery flx` = `cgi-left`（團隊照片）+ `cgi-right`（團隊照片）+ `capabilities-anim-char`（**36 幀** `anim-frame` picture，桌面 `/animations/wwcd/N.webp` + 行動 `sp/N.webp`）+ `surprise-anim-svg`（手繪閃電，`reveal-brush` dasharray 300/offset 305）。
- **CSS**（index.css）：gallery `position:relative;flex;gap:18/34/46;max-width:606/880;padding:30/60/80`；cgi-left/right 初始 `translate3d(10/-9px)`（≥834 18/-17、≥1920 23/-24）；anim-char `absolute;top:22.8%;left:44.6%;width:26%;aspect-ratio:.5678;z-index:3`；anim-frame `absolute 填滿;visibility:hidden`（frame-1 visible）；surprise `absolute;top:6px;right:6px;width:41/61/81px;translate(100%,-100%)`。
- **JS setupCapabilitiesAnimation**（scroll scrub）：前段 0-30% cgi 歸位 + y 微移（-10/10）；中段 30-80% 36 幀切換（visibility）；後段 80-100% reveal-brush 305→0；反向重置。

### 實作
- **資源**（74 個）：`static/images/capabilities-left.webp`（99KB）、`capabilities-right.webp`（80KB）、`static/animations/wwcd/1~36.webp` + `wwcd/sp/1~36.webp`（桌面/行動各 36 幀）下載自原站。
- **about.html**（版號 bc-capabilities.js ?v=20260825b）：row-animation 後、topConcept 前插入 `<section class="capabilities bc-capabilities"><div class="capabilities-gallery flx">…</div></section>`（完整複製 36 幀；**移除 srcset**（候選 URL 無法本地化，用單圖 src 視覺相同）；SVG id 加 2 後綴 `animatedRevealMask2`/`mainClip2`）。
- **static/css/bc-capabilities.css**（新建）：原站樣式 scoped 到 `.bc-capabilities` + 響應式 + 黑底（padding 96px 0 區塊間距）。
- **static/js/bc-capabilities.js**（新建）：原生 scroll + rAF 重現 scrub——範圍 `(vh-rect.top)/(h+vh)`、分段 30/50/20；**⚠️ 修正：p≥0.8 保證最後一幀**（原 if(p>=a&&p<=S) 在瞬間滾動跳過中段時 frame 停 frame-1）。

### 驗證（全 PASS，playwright-core 實測）
- **CDP 22/22**：36 幀、cgi 初始位移 18/-17px、左右圖 src、surprise 61px、reveal-brush 305、id 無重複、前段 cgi 歸位（x 18→9）、中段 frame-18 切換 + cgi x=0、後段 brush 152、最終 brush 0 + frame-36、反向重置 frame-1 + brush 305、響應式無溢出、無 JS 錯誤。
- who + row + capabilities 共存 9/9 PASS；`manage.py check` 0 issues。

### 後續微調（2026-08-25 使用者反饋）
- **① 照片分離修復**：`.capabilities-gallery` 原站 class 含 `flx`（display:flex），本地未載入 → 兩圖垂直堆疊分離（left y2715/right y3855）、anim-char 錯位。修復：CSS gallery 加 `display:flex`（兩圖並排、動畫居中、gallery 高 2400→658px）。版號 bc-capabilities.css ?v=20260825b。
- **② 照片錯開修復**：scroll 中段 cgi y 微移（left -10/right +10）使照片錯開 20px（本地 vh 範圍下明顯；原站 150vh 範圍同位置僅 -2px 不明顯）。修復：移除 cgi y 微移（僅 x 歸位，照片始終頂部對齊）。版號 ?v=20260825c。
- **③ 速度/時機調整（多輪）**：cgi 歸位前段 32%→50%（太慢）→35%→32%；後重寫分段：cgi 延後開始 0.10→0.20→0.30→加快回 0.10、frame 加快 25%→15%→11%→12%；brush 段 0.66-1→0.44-1。版號 ?v=20260825d-j。
- **④ 「！」動畫消失修復**：surprise「！」SVG 本身與原站一致（mask+2 fill path），但 brush 段 0.44-1 太長（56% 滾動慢慢畫），使用者滾到 capabilities 頂部時「！」幾乎未顯示（mask 遮住）→ 縮短 brush 段 **0.44-0.60** 快速畫線完成（galTop -75 完成，接近原站 -152）。版號 ?v=20260825k。
- **最終版號**：bc-capabilities.js ?v=20260825k、bc-capabilities.css ?v=20260825b；CDP 22/22 + 共存 9/9 全 PASS。


## 36. sukima content-block-title 思考氣泡手繪畫線動畫整合（Who we are 右側）💭 — ✅ 2026-08-25

### 需求
- 將 https://sukima.tokyo.jp/ 的 `.content-block-title` 內 SVG 手繪圓圈（思考氣泡 culture-kangaeteiru-svg）整合到 about 頁「Who we are」文字右側；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。

### 原站機制分析
- **結構**：Culture section `<h3 class="content-block-title">考えていること <svg width="60" height="78" class="culture-kangaeteiru-svg">`——mask `thoughtBubbleRevealMask` + 白線 tracer `thought-bubble-reveal-tracer`（dasharray 500/offset 500）+ clipPath + `#BFFF00` 思考氣泡（g opacity .75，4 個 path）。
- **CSS**（index.css）：`.culture-kangaeteiru-svg{position:absolute;top:8px;right:0;transform:translate3d(100%,-100%,0);width:42px;height:auto}`（≥834→top 22/width 60；≥1920→top 41/right -6/width 80）；`.content-block.show .thought-bubble-reveal-tracer{animation:animSvgStrokeTo 2s ease-in-out forwards}` + `@keyframes animSvgStrokeTo{to{stroke-dashoffset:0}}`。
- **觸發**：IO 監測 `.content-block`（threshold 1）加 `.show`（once）。原站實測（CDP）：SVG absolute 顯示在標題**右側偏上**（title x680/w175，svg x855/y267）。

### 實作
- **about.html**（版號 bc-who.css ?v=20260825d）：who 標題 `<h2 class="section-title__text">` 內「Who we are」後插入完整 SVG（3381 字符）；mask/clipPath id 加 **2 後綴**（`thoughtBubbleRevealMask2`/`thoughtBubbleClip2`）防衝突。
- **static/css/bc-who.css**：追加 scoped 樣式 `.bc-who-section .culture-kangaeteiru-svg`（原站定位 + 響應式 42/60/80px）+ `.bc-who-section.show .thought-bubble-reveal-tracer` 動畫 + `@keyframes animSvgStrokeTo`。
- **無新 JS**：沿用 who section 既有 `.show` 觸發（bc-who.js IO 進視口加 .show），CSS 以 `.bc-who-section.show` 觸發 SVG 畫線。

### 驗證（全 PASS，playwright-core 實測）
- **CDP 18/18**：SVG 在 Who we are 標題內、tracer/mask/clip 存在、id 無重複、**SVG 在標題右側（title 右緣=svg.x）且偏上（svg.y < title.y）**、position absolute、寬度 60px（≥834）、who .show 觸發後 tracer `animName=animSvgStrokeTo` + 2s + `dashOffset=0`（畫線完成）、響應式 42/60/80px 無溢出、無 JS 錯誤。
- who + row + 新 SVG 共存 9/9 PASS（who 字元亮起、row scrub 正常）；`manage.py check` 0 issues。


## 35. sukima row-animation video scrub 整合 to about 頁 🎞️ — ✅ 2026-08-25

### 需求
- 將 https://sukima.tokyo.jp/ 的 `.row-animation`（video scroll scrub 動畫）整合到 about 頁（建立新 section）；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。
- **顏色決策（使用者確認）**：融入本地黑底（原站白底 var(--color-white)）；hard-light 混合保留。

### 原站機制分析
- **結構**：who section 後、capabilities 前 `<div class="row-animation"><video muted playsinline class="row-animation__video"><source src="/animations/row-animation.mp4" type="video/mp4"></video></div>`。
- **CSS**：`.row-animation{background:var(--color-white);font-size:0;display:flex;justify-content:center;align-items:center;position:relative;overflow:hidden;height:96px}`（≥1024→160px、≥1920→200px）；`.row-animation__video{height:100%;width:auto;mix-blend-mode:hard-light}`。
- **動畫**：videoScrubber（GSAP ScrollTrigger）——start `top 90%`（頂部對齊視口 90%）→ end `bottom 25%`、scrub 0.2 平滑、30fps 節流；`video.currentTime = 進度 × duration`（10.25s，可前進/後退）；preload。

### 實作
- **資源**：`static/animations/row-animation.mp4`（452KB）下載自原站；**moov atom 由檔案末尾移至前面**（ftyp→moov→mdat，修正 488 個 stco chunk offsets，純 python 腳本）——改善各環境 seek。
- **about.html**（版號 ?v=20260825c）：who section 後、topConcept 前插入 `<section class="row-animation bc-row-animation">`（含 video + source static）；extra_css/js 載入 bc-row-animation.css/js。
- **static/css/bc-row-animation.css**（新建）：原站樣式 scoped 到 `.bc-row-animation`；背景 `var(--bc-bg)` 黑底適配；高度 96/160/200px 響應式。
- **static/js/bc-row-animation.js**（新建）：原生 scroll + rAF 重現 videoScrubber——progress `(0.9vh-rect.top)/(0.65vh+h)`、scrub 平滑 0.2/幀、30fps 節流、video.currentTime 跟隨滾動可前進/後退。
  - **⚠️ 關鍵適配**：Django dev server **不支援 Range 請求**（Range 回 200 非 206）+ mp4 moov 在尾部 → video seek（currentTime）失敗（readyState=4 仍無法設 currentTime）→ 改用 **fetch → Blob → objectURL** 載入（記憶體中 seek 可靠，所有環境通用；fetch 失敗 fallback 直接 source）。

### 驗證（全 PASS，playwright-core 實測）
- **CDP 18/18**：row-animation 存在、高度 160px（1280≥1024）/96（375-768）/200（1920）、全寬 flex、overflow hidden、video height:100% + hard-light、muted、source 正確、duration 10.25s、**scrub：progress 0.5→currentTime 5.11s、progress 1→10.23s、回滾→0.02s**、響應式無溢出、無 JS 錯誤。
- `manage.py check` 0 issues；既有 WS 403/`ws-fallback` 404 與本次無關。


## 34. sukima who section（.section.who #who）整合 to about 頁 🎬 — ✅ 2026-08-25

### 需求
- 將 https://sukima.tokyo.jp/ 的 `<section class="section who" id="who">` 整合到 about 頁（建立新 section）；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。
- **顏色決策（使用者確認）**：融入本地黑底（白字），SVG 高亮 #BFFF00 保留；非原站淺灰底黑字。

### 原站機制分析
- **結構**：`who-content-sticky`（flex column center）→ `section-title`（kicker 括號 `(sukimaって何の会社？)` + 「Who we are」h2）→ `who-content-text`（93 個 `wwa-anim-char` 逐字 + `sukima-anim-wwa`（s/u/k/i/m/a + who-circle-svg 手繪圓圈）+ `wwa-visual-01/02`（img wwa-01/02.png）+ `video-anim-wwa`（映/像 + who-arrow-svg 手繪箭頭）+ `wwa-visual-03`（video wwa.mp4））。
- **動畫**：GSAP ScrollTrigger **scrub**（滾動跟隨）——元素間隔 0.5s、char 0.3s、spacer 2s、visual/img/video 3s、circle 1s（提前 1s）、arrow 1s；circle dashoffset 800→**377**、arrow 300→0、char opacity .5→1、img/video scale 0→1、video scale 完成後 play。
- **響應式**：base / ≥704 / ≥834 / ≥1920（content-text 24/34/50px、spacer 75/90/140px、visual-01 58/90/144px、visual-03 54/76/126px、circle 102/158/203px、arrow 114/146/188px、kicker margin-left 87/173/262px）。
- **區塊間距**：原站 section padding `0 80px`（≤1080→40、≤834→20）+ wrapper gap 96px。

### 實作
- **about.html**（版號 ?v=20260825c）：第二組 SERIES 滑桿後、topConcept 前插入 `<section class="section who bc-who-section" id="who">`；日文文字原文完整複製；SVG mask/clipPath id 加 **2 後綴**（`animatedRevealMaskWwaCircle2`/`mainClipWwaCircle2`/`arm-arrowwwa2`/`mcarrowwwa2`）避免與 summary 區塊既有 `arm-arrowwwa`/`mcarrowwwa` 衝突。
- **static/css/bc-who.css**（新建）：完整複製原站樣式，全部 scoped 到 `.bc-who-section`；文字白色、SVG #BFFF00 保留；響應式目標寬度用 CSS 變數 `--who-spacer-w/--who-visual01-w/--who-visual03-w`（JS 讀取）；⚠️ **sukima-anim-wwa 必須是 inline**（非 inline-block），否則 bbox 高度變 line-height 61.2 使圓圈 top:73% 定位偏移（原站實測 inline 高 34）。
- **static/js/bc-who.js**（新建）：原生 scroll + rAF 重現原站 **ScrollTrigger scrub**——依原站時間軸參數為每元素計算進度直接設定屬性（opacity/width/scale/stroke-dashoffset），同元素重複出現（sukima 字母、video-anim-wwa 內字元）用 Map 後者覆蓋（對應 GSAP overwrite）；video 在 scale 完成後 play；kicker 括號用 IO 加 .show 觸發 CSS transition（原站一次性行為）。未引入 GSAP。
  - **⚠️ scrub 範圍修正（2026-08-25 使用者回報「看不到動畫」）**：原站 start/end 公式（top bottom-=35% → bottom+=20% bottom）在較矮區塊下 denom 僅 ~60px（h-0.55vh），用戶滾 200px 即跳過全部動畫 → 改為 `progress=(vh-rect.top)/(h+vh)`（section 進入視口到完全通過，~1300px），逐字亮起全程可感知（每 40px 亮 2-3 字）。
  - **⚠️ scrub 完成點修正（2026-08-25 使用者回報「滾到頂部文字仍未完成亮起 + 看不到 wwa.mp4」）**：`(h+vh)` 範圍讓動畫在 section 完全離開視口（rect.top=-h）才完成，who 頂部對齊視口頂（rect.top=0）時僅 59% → 改為 `progress=(vh-rect.top)/vh`（who 頂部到視口頂即完成全部 93 字/圓圈/箭頭/video）；video delay 在 timeline 93% 處，原公式下永遠不出現（scale 0 隱藏）→ 新公式下滾到 who 頂部附近淡入播放（76×55px、1.08s）。
  - **⚠️ 縮排動畫修正（2026-08-25 使用者回報「字元向左縮排動畫沒有了」）**：spacer 在 timeline 前 2s（4.3% 進度 = 35px 滾動）瞬間展開，用戶看不到 → ① 加入 **GSAP scrub 平滑**（原站 scrub:0.3，每幀向目標進度逼近 0.12，動畫滯後於滾動）；② spacer dur 依使用者回饋逐步加大 **2s→10s→20s→32s→40s→46s**（=totalDur，縮排展開跨越 who 進入到滾完的整個 800px；每步 80px 僅展開 ~16px）→ 慢速滾動實測：spacer 12→28→46→60→72→81→87→90px、字元 3→93 逐字亮起、圓圈 800→377、video 末段播放；版號 ?v=20260825k。
- **資源**：`static/images/wwa-01.png`（23KB）、`static/images/wwa-02.png`（29KB）、`static/animations/wwa.mp4`（8.4KB）下載自原站。

### 驗證（全 PASS，playwright-core 實測）
- **CDP 30/30**：結構（93 字元/圓圈/箭頭/img/video/文字原文）、id 無重複（arm/mcarrowwwa 兩組共存）、初始態（opacity .5、dashoffset 800/300、scale(0)）、**scrub 中間態**（progress 0.5 首字元亮/末字元未亮）、**scrub 最終態**（全亮、circle 377、arrow 0、spacer 90px、img scale(1)、video 播放）、**scrub 反向**（回滾頂部字元回 0.5）、響應式無溢出（375/768/1280/1920）、無 JS 錯誤。
- **佈局對照 15/15**（vs 原站 sukima.tokyo.jp 實測）：content-text 34px/180%/2.72px/max-width 640px、圓圈 158px **完整圈住 sukima 文字**（bbox 對照原站）、arrow 146px、text flex-end 靠右、img1/2 90px、video 76px、kicker 內容、標題 Who we are 56px。
- `manage.py check` 0 issues；既有 WS 403/`ws-fallback` 404 與本次無關。


## 33. sukima hero-title-svg 手繪圓形畫線動畫整合（about 頁 SERIES 副標題）🌿 — ✅ 2026-08-24

### 需求
- 將 https://sukima.tokyo.jp/ 的 `.svg` 手繪圓形動畫（hero-title-svg）整合到 about 頁「一種興奮感, 超越一杯的沉默」文字；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS。
- **追加（2026-08-24）**：SVG 形狀改為**手繪圓形**；追加修改：手繪圓圈改為**圈住整句「一種興奮感, 超越一杯的沉默」所有文字**（長橢圓）；再追加：**長橢圓增高**（viewBox 44→60、CSS 上下留白 -5→-14 / 高度 +10→+28），圓環高 33→47px；**再追加：整體加大**（inset 四邊 -14/-12 → **-24px**、寬高 +48px），圓環 244×47 → **269×65**；**再追加：動畫速度 +30%×2**（duration 2s→1.4s→**1.08s**，延遲 1s 保持），版號 ?v=20260824f。

### 原站動畫分析（index.DtjyLTTu.css）
- **結構**：SVG 內 `<mask>` 白線 path（`.leaf-flow-reveal-stream`，stroke-dasharray/offset）+ `<g opacity="0.75" mask clip-path>` 內 `#BFFF00` 填充。
- **動畫**：`.hero.show .leaf-flow-reveal-stream { animation: leafFlowReveal 2s ease-in-out forwards 1s }`——白線段沿輪廓移動，畫線揭示形狀。
- **觸發**：`.hero.show`（JS 加 class）。

### 實作（最終版）
- **about.html**：兩組 SERIES（主滑桿 L26 + 括號滑桿 L128）副標題**整句「一種興奮感, 超越一杯的沉默」**包 `.bc-leaf-circle-wrap`（position:relative 錨點）+ 內嵌手繪圓形 SVG；第二組 mask/clipPath id 加 B 後綴（`leafFlowRevealMaskB`/`leafFlowClipB`）避免 id 衝突。版號 ?v=20260824b。
- **手繪圓形 path（長橢圓，圈整句）**：`M160 5 C240 5 317 16 317 30 C317 44 240 55 160 55 C80 55 3 44 3 30 C3 16 80 5 158 9 C225 13 280 20 283 30`（viewBox **320×60**，增高版；不閉合螺旋長橢圓、起終點交錯 = 手繪感）；顯示為 `#BFFF00` 圓環（stroke 3、opacity 0.75）。
- **畫線參數（關鍵）**：增高版長橢圓 path 實際長度 775.4px（getTotalLength 實測）→ dasharray=776、dashoffset=776、動畫 to 0（776→0 全程畫線揭示）。
- **bc-series.css**（?v=20260824f）：`.bc-leaf-circle-wrap`（relative inline-block）+ `.bc-leaf-circle-wrap .hero-title-svg`（absolute **inset:-24px -24px**、width/height calc(100%+48px)、preserveAspectRatio="none" 拉伸、pointer-events none）；`.bc-series-hero.show .leaf-flow-reveal-stream` 動畫（**1.08s** ease-in-out forwards、延遲 1s）+ `@keyframes leafFlowReveal { to { stroke-dashoffset: 0 } }`。
- **bc-series.js**（?v=20260824b）：`initLeafFlowReveal()` 優化——**初始即在視口內的 hero 立即加 .show**（首屏第一組載入即播，等同原站）+ IntersectionObserver（threshold 0.15）滾動進入觸發；無 IO 時全部直接加。
- ⚠️ **教訓（regex 誤匹配）**：二次替換 wrap 時若用 `(?=.*maskB)` lookahead 會跨段落匹配到「第一處 wrap 開頭 → 第二處結尾」→ 誤刪整組滑桿內容（檔案 416→350 行）。已從 git 還原 + 用「section 開頭到 h2 結束」精確錨點重建。

### 驗證（全 PASS，playwright-core 實測）
- `node --check bc-series.js` ✅。
- **playwright computed style**：第一組 `.bc-series-hero.show` + `animName=leafFlowReveal` + **`animationDuration=1.08s`**（速度再 +30%）、延遲 1s、`dashOffset=0px`（動畫完成）；wrap 224×27 = **整句文字**、SVG **272×75**（加大版）圈住文字 ✅。
- **像素驗證**：長橢圓圓環 bbox x[17-286]（**寬 269 高 65**，加大版 244×47 → 269×65）、**中心空心 = 圓環** ✅；兩組皆正常。
- **行動端（375px）**：**無水平溢出**（SVG 右邊界 273<375）、SVG 272×75 與桌面一致 ✅。
- 檔案完整性：2 組 hero、wrap×2、leafFlowRevealMaskB×2、dasharray 766×2、452 行 ✅。

### 備註
- 位置：手繪長橢圓圓環圈住**整句**「一種興奮感, 超越一杯的沉默」（SVG absolute 覆蓋文字外圈 inset **-24/-24**，加大版）；viewBox 320×60，preserveAspectRatio none 拉伸。
- 畫線參數因 path 長度不同而調整（776→0），動畫機制/時長（2s ease-in-out、延遲 1s、forwards）與原站一致。
- 不新增任何視覺元素/裝飾，僅動畫所需 CSS 與觸發 JS。

### 追加（2026-08-24）：sukima title-hatarikata-svg 絲帶動畫整合到「雲仙黒糖ラテベース」🌿 → ✅

- **需求**：將 sukima.tokyo.jp 的 title-hatarikata-svg（flowing-ribbon 絲帶）整合到 about 頁第一處副標題「雲仙黒糖ラテベース」（使用者已改文字）；UI/動畫與原站完全一樣。
- **原站機制（index.DtjyLTTu.css）**：`.title-hatarikata-svg{position:absolute;left:-23px;bottom:7px;transform:translateY(50%);width:98px;opacity:.75}`（834px→154px/left-40、1920px→216px/left-44）；`.job-apply.show .comet-tail-reveal-stream{animation:cometTailReveal 4s ease-in-out forwards}`、`@keyframes cometTailReveal{to{stroke-dashoffset:0}}`。mask 白線 tracer（dasharray 600/offset 600，path 實測 543px → 原參數適用）。
- **實作**：about.html 第一處 SVG 替換為絲帶（`flowingRibbonRevealMask`/`flowingRibbonClip`、`flowing-ribbon-reveal-tracer`、`#BFFF00` 絲帶 fill）；bc-series.css 加 `.title-hatarikata-svg` 樣式 + `.bc-series-hero.show .flowing-ribbon-reveal-tracer` 動畫（cometTailReveal 4s）+ keyframes + 834/1920 media。版號 ?v=20260824g。
- ⚠️ **關鍵根因（path d 壓縮版）**：使用者提供的 ribbon path d 是**壓縮版**（每 C 命令只 2 數字，SVG C 語法需 3 對=6 數字 → path 無效 getBBox 0×0 → 絲帶不渲染）。從 sukima 原站直接抓取正確 d（C 後完整 3 對座標，2797 字元）替換 → bbox 154×22。
- **驗證（playwright-core）**：第一組絲帶 `.show`+`cometTailReveal`+`dashOffset=0px`+bbox 154×22+**綠色像素 728**（x27-150 y474-490）；行動端 w98 left2 無溢出；第二組長橢圓 `leafFlowReveal` 維持正常（offset 0px）。
- **備註**：第二處副標題仍為「一種興奮感, 超越一杯的沉默」+手繪長橢圓（未動）；如需也換絲帶/文字可告知。
- **追加（位置與速度）**：① 絲帶原在文字左側與文字水平重疊 → **移到文字下方**（top:100% + margin-top 8/12/16px，移除 bottom/translateY）；② 動畫**速度 +50%**（4s→**2.67s**）。版號 ?v=20260824h。驗證：桌面絲帶 y503（文字 y464-491）**無重疊**、animDur 2.67s、綠色 563px、行動端 y109 無溢出。
- **追加2（位置過低→上移 + 速度再 +50%）**：絲帶間距 12px→**4px**（margin-top 8→2/12→4/16→6，避免太低）；動畫 2.67s→**1.78s**（+50%×2）。版號 ?v=20260824i。驗證：桌面絲帶 y495（間距 4px）無重疊、animDur 1.78s、綠色 709px。
- **追加3（仍太低→緊貼 + 速度 +30%）**：margin-top 0（行動/834）與 2px（1920），絲帶**緊貼文字底部（間距 0px）**；動畫 1.78s→**1.37s**（+30%）。版號 ?v=20260824j。驗證：wrapBottom=ribbonTop=491（間距 0）、animDur 1.37s、動畫完成。
- **追加4（速度 +50%）**：動畫 1.37s→**0.91s**（+50%）。版號 ?v=20260824k。驗證 animDur 0.91s、動畫完成。

### 追加（2026-08-24）：sukima arrow-recruit-svg 手繪箭頭動畫整合到 way 區塊 h2 🏹 → ✅

- **需求**：將 sukima.tokyo.jp 的 arrow-recruit-svg（手繪箭頭）整合到 about 頁 way 區塊 h2「我們試著將看不見的熱度與香氣視覺化，創造出一種嗅覺與味覺之間的張力。」；UI/動畫與原站完全一樣。
- **原站機制**：`.arrow-recruit-svg{position:absolute;left:50px;bottom:-39px;transform:translate(-100%);width:191px}`（1920px→245px、更高→286px）；`.comet-tail-reveal-stream` 觸發於 `.show`，`cometTailReveal 4s ease-in-out forwards`、`to{dashoffset:0}`。tracer dasharray 500/offset 500（path 實測 **296.8px** → 原參數適用）。本次使用者 arrow path d 為**有效格式**（C 後 3 對座標，無需修正）。
- **實作**：about.html way 區塊 h2（加 position:relative）內嵌 arrow SVG（`cometTailRevealMask`/`cometTailClip`、`comet-tail-reveal-stream`、雙 `#BFFF00` 箭頭 path、g opacity 0.75）；bc-series.css 加 `.arrow-recruit-svg` 樣式 + `.col-main.way.show .comet-tail-reveal-stream` 動畫 + 1920/2560 media（keyframes cometTailReveal 與絲帶共用）；bc-series.js 加 `initArrowReveal()`（IO 監測 `.col-main.way` 進視口加 .show）。版號 ?v=20260824l（CSS）/ ?v=20260824c（JS）。
- **驗證（playwright-core）**：way `.show` 加上、箭頭 `cometTailReveal 4s`+`dashOffset=0px`、雙 path bbox 224×63、位置 h2 區域（y420 vs h2 y373-438）、綠色 4755px、行動端 w191 left-98 **無溢出**、**重複 id 無**。
- ⚠️ **修復（使用者回報「未顯示運行」）**：根因 = **blobs.css `.loaded .productFv path,.productFv path{opacity:0;transform:translateY(1em)}`** 會隱藏/位移 way 區塊（productFv 內）所有 path（含箭頭與 mask 內 tracer）→ 箭頭 opacity 0 不可見；tracer 位移使 mask 揭示偏移（只顯示右半）。修復：`.productFv .arrow-recruit-svg path{opacity:1!important;transform:none!important}`（覆蓋所有 path 含 defs 內 tracer）。驗證：opacities 全 1、transforms 全 none、箭頭區域綠色 27→**782**（左右半皆有）、動畫播放中 dashOffset 進度值。版號 ?v=20260824o。
- **追加（速度 +80%）**：箭頭動畫 4s→**2.22s**（+80%）。版號 ?v=20260824p。驗證 animDur 2.22s、動畫完成。
- **追加2（速度 +30%）**：箭頭動畫 2.22s→**1.71s**（+30%）。版號 ?v=20260824q。驗證 animDur 1.71s、動畫完成。

### 追加（2026-08-24）：sukima title-office-svg 手繪圓圈動畫整合到「那股香不只是味道」⭕ → ✅

- **需求**：將 sukima.tokyo.jp 的 title-office-svg（手繪圓圈）整合到 about 頁 way 區塊 summary 第一個 p「那股香不只是味道…」；UI/動畫與原站完全一樣 + 速度 +80%。
- **原站機制**：`.title-office-svg{position:absolute;top:34px;left:172px;transform:translate(100%,-100%);width:55px}`（834px→right134/top7/width72、1920px→right164/top10/width95）；`.company-content.show .fingerprint-reveal-flow{animation:fingerprintReveal 2s ease-in-out forwards}`、`@keyframes fingerprintReveal{to{dashoffset:0}}`。tracer dasharray 700/offset 700（path 實測 **345.5px** → 原參數適用）。使用者 circle path d 為**有效格式**（C 後 3 對）。
- **實作**：about.html summary 第一個 p（加 position:relative）內嵌 title-office-svg SVG（`organicFingerprintRevealMask`/`organicFingerprintClip`、`fingerprint-reveal-flow`、`#BFFF00` 手繪圓圈、g opacity 0.75）；bc-series.css 加 `.title-office-svg` 樣式 + `.col-main.way.show .fingerprint-reveal-flow` 動畫（**fingerprintReveal 1.11s = 速度 +80%**）+ `.productFv .title-office-svg path` 覆蓋（blobs.css path 隱藏）+ 834/1920 media。共用 way 區塊 .show 觸發（initArrowReveal）。版號 ?v=20260824r。
- **驗證（playwright-core）**：wayShow true、`fingerprintReveal 1.11s`+`dashOffset=0px`、path opacity 1/transform none、圓圈 bbox 71×85、**圓圈區域綠色 1730**（完整顯示）、行動端 right325 **無溢出**。
- **追加（位置：右側「味道」之後）**：依使用者指示，圓圈移到「那股香不只是味道」**右側**。做法：文字包 `.bc-smell-circle-wrap`（span inline-block position:relative）+ **SVG 移入 span 內**（否則 containing block 是 p，left:100% 會到 p 右緣）；CSS `left:100% top:50% translateY(-50%) margin-left:10px`（834px→w72、1920px→w95）。驗證：circle x327（span 右緣 317）+**gap 10px**、垂直居中（y439 vs span y465 h33）、圓圈區域綠色 1693、動畫 1.11s 正常。版號 ?v=20260824s。
- **追加2（上移：不疊第二行）**：圓圈高 85px > 文字行 33px，垂直居中會使下半部疊到第二行「而是會被記住的嗅覺記憶…」。改 `bottom:0`（底部對齊文字行底，移除 translateY）。驗證：circle y413-498（bottom 對齊 span 底 498）、**circleBottom 498 < pBottom 531（不疊第二行）**、gap 10px 維持。版號 ?v=20260824t。
- **追加3（再次上移：完全在文字上方）**：`bottom:100%`（底部對齊文字行頂）+ margin-bottom 6px。驗證：circle y374-459（**circleBottom 459 < spanTop 465**，完全在文字上方、間距 6px）、不遮任何文字。版號 ?v=20260824u。
- **追加4（向下移動一點）**：margin-bottom 6px→**0**（圓圈底部對齊文字行頂，下移 6px）。驗證：circleBottom 465 = spanTop 465、不遮文字、gap 10px 維持。版號 ?v=20260824v。

### 追加（2026-08-24）：sukima footer-arrow-svg 手繪圓圈（山形）動畫整合到「世界太快」⛰️ → ✅

- **需求**：將 sukima.tokyo.jp 的 footer-arrow-svg（手繪山形圓圈）整合到 about 頁 way 區塊 h1 morphing 第一個 word「世界太快」；UI/動畫與原站完全一樣 + 速度 +80%。
- **原站機制（playwright 實測 sukima）**：`.footer-arrow-svg{position:absolute;left:78px;right:-31px;top:-40px;bottom:-24px;width:259px;transform:translateX(-259px)}` 於 `.footer-cta-link-wrapper`（relative）；`.footer-cta-link-wrapper.show .mountain-range-reveal-tracer{animation:revealFooterSvg 6s ease-in-out forwards}`、`@keyframes revealFooterSvg{to{dashoffset:0}}`。tracer dasharray 1000/offset 1000（path 實測 **491.1px** → 原參數適用）。使用者 14 個 mountain path d 為**有效格式**。
- **實作**：about.html「世界太快」word（加 position:relative）內嵌 footer-arrow-svg（`organicMountainRevealMask`/`organicMountainClip`、`mountain-range-reveal-tracer`、14 個 `#BFFF00` 山形 path、g opacity 0.75）；bc-series.css 加 `.footer-arrow-svg` 樣式（照抄 sukima）+ `.col-main.way.show .mountain-range-reveal-tracer` 動畫（**revealFooterSvg 3.33s = 速度 +80%**）+ `.productFv .footer-arrow-svg path` 覆蓋。共用 way .show 觸發。版號 ?v=20260824w。
- **驗證（playwright-core）**：wayShow true、`revealFooterSvg 3.33s`+`dashOffset=0px`、14 path、pathOpacity 1、山形 path bbox 38×25、山形區域綠色 194、行動端**無溢出**。
- **備註**：SVG 因 sukima 樣式 left/right 同時設被 stretch（桌面 375×220、行動 312），位置在 word 左側（translateX(-259)）；如需縮小/調整位置可告知。
- ⚠️ **修復（使用者回報「模糊淡出、看不到」）**：① SVG 原本放在 morphing 的 `.word` 內 → `.morphing{filter:contrast(25) blur(1px)}` 扭曲山形 + `.word` 每 16s 輪換（非 active 時 `blur(1em) opacity:0`）→ SVG 被淡出隱藏。**修復：SVG 移出 word、插入 h1 內（morphing 後、h1 position:relative）**，脫離 morphing 濾鏡/動畫。② **blobs.css `.productFv.style_01 h1 svg{width:83.0769vw;height:48.718vw}`** 覆蓋 SVG 尺寸（375×220）→ `.productFv .footer-arrow-svg{width:259px!important;height:auto!important}` 覆蓋。③ 定位調整：`left:-105px;top:-5px`（山形 viewBox 右端對齊 word1 左側）。驗證：SVG 259×115、word1 附近綠色 1831、revealFooterSvg 3.33s、dashOffset 0。版號 ?v=20260824z。
- **追加（向左下方移動：不疊文字）**：left -105→**-150**、top -5→**30**。驗證：山形 x234-272（右緣 272 < word1 左緣 279，**不疊**）、SVG 259×115、動畫正常。版號 ?v=20260824aa。
- **追加2（模糊修復 + 再左移）**：使用者回報「箭頭模糊」→ 診斷發現 **SVG 實際仍在 morphing 容器內**（先前插入位置誤判，parent=morphing）→ 受 `contrast(25) blur(1px)` 濾鏡模糊。**修復：SVG 正確移到 morphing 容器外（h1 內、morphing 後）**，parent=ttl、svgFilter none。left -150→**-200**（再左移）。驗證：parentIsMorphing false、svgFilter none、山形 x184-222（word1 左側更遠）、dashOffset 0。版號 ?v=20260824ab。

### 追加（2026-08-24）：sukima who-arrow-svg 手繪箭頭動畫整合到「這就是起點」🏹 → ✅

- **需求**：將 sukima.tokyo.jp 的 who-arrow-svg 整合到 about 頁 way 區塊 summary 第一個 p 第二行「這就是起點」；UI/動畫與原站完全一樣 + 速度 +80%。
- **原站機制**：`.who-arrow-svg{position:absolute;bottom:3px;left:45%;width:114px;z-index:2;transform:translateY(100%)}`（834→146、1920→188）；`.members-title-desc.show .organic-reveal-brush444{animation:organicRevealAnimation 1.5s ease-in-out forwards}`、`@keyframes organicRevealAnimation{to{stroke-dashoffset:0}}`。tracer dasharray 300/offset 300（path 實測 **242.6px** → 原參數適用）。使用者 arrow path d 為**有效格式**（C 後 3 對）；tracer inline `style="stroke-dashoffset:0px"` 已移除（否則固定顯示無動畫）。
- **實作**：about.html「這就是起點」包 `.bc-who-arrow-wrap`（span inline-block position:relative）+ 內嵌 who-arrow-svg（`arm-arrowwwa`/`mcarrowwwa`、`reveal-brush-arrow-wwa`、`#bfff00` 手繪箭頭、g opacity 0.75）；bc-series.css 加 `.who-arrow-svg` 樣式（照抄 sukima）+ `.col-main.way.show .reveal-brush-arrow-wwa` 動畫（**organicRevealAnimation 0.83s = 速度 +80%**）+ `.productFv .who-arrow-svg path` 覆蓋 + 834/1920 media。共用 way .show。版號 ?v=20260824ac。
- **驗證（playwright-core）**：wayShow true、`organicRevealAnimation 0.83s`+`dashOffset=0px`、path bbox 146×79、pathOpacity 1、who-arrow 區域綠色 1379、行動端 x193-right307 **無溢出**。
- **追加（減慢 30%）**：who-arrow 動畫 0.83s→**1.19s**（減慢 30%）。版號 ?v=20260824ad。驗證 animDur 1.19s、動畫完成。

### 追加（2026-08-24）：sukima other-members-svg 手繪圓形動畫整合到「為什麼，Between Coffee…」⭕ → ✅

- **需求**：將 sukima.tokyo.jp 的 other-members-svg（手繪圓形）整合到 about 頁 topConcept 區塊 h2「為什麼，Between Coffee 會如此堅持 一杯好咖啡。」；UI/動畫與原站完全一樣。
- **原站機制**：`.other-members-svg{position:absolute;top:60%;left:50%;transform:translate3d(-50%,-50%,0) rotate(10deg);opacity:.75;z-index:0;width:102px}`；`.members-title-desc.show .organic-reveal-brush444{animation:organicRevealAnimation 1.5s ease-in-out forwards}`（keyframes organicRevealAnimation 與 who-arrow 共用）。tracer dasharray 800/offset 784（path 實測 **814.9px** → 照抄）。使用者 ring path d 為**有效格式**。
- **實作**：about.html topConcept 區塊 h2（加 position:relative）內嵌 other-members-svg（`organicRevealMaskMembersTitle`/`organicClip333`、`organic-reveal-brush444`、`#BFFF00` 手繪圓形、g opacity 0.75）；bc-series.css 加 `.other-members-svg` 樣式（照抄 sukima）+ `.bc-top-concept.show .organic-reveal-brush444` 動畫（organicRevealAnimation 1.5s）；**bc-series.js 加 `initTopConceptReveal()`**（IO 監測 `.bc-top-concept` 進視口加 .show，因 topConcept 非 way 區塊）。版號 ?v=20260824ae（CSS）/ ?v=20260824d（JS）。
- **驗證（playwright-core）**：topShow true、`organicRevealAnimation 1.5s`+`dashOffset=0px`、path bbox 111×54、pathOpacity 1、圓形區域綠色 2365、行動端 x86-right198 **無溢出**。
- **追加（他にもいます！文字動畫）**：sukima 中 `.other-members` 容器同時含「他にもいます！」span + other-members-svg。整合：topConcept h2 內包 `.bc-other-members` 容器（absolute top:8px right:0、translate3d(100%) rotate(-10deg) 滑入）+ span（scale 0→1、延遲 1s）+ 既有 svg 移入容器。CSS `.bc-top-concept.show .bc-other-members{translate3d(0) rotate(-10deg);transition .4s .5s}` + `.show span{scale(1);transition .4s 1s}` + 834/1920 字體。驗證：容器滑入（translateX 0 + rotate -10deg）、span scale(1) 完成、svg 動畫共存、位置 h2 右上。版號 ?v=20260824af。
- **追加2（修復：向左側位移）**：使用者回報「整個動畫向左側位移、起始/結束位置不同」→ 診斷：容器 `.bc-other-members` 初始 `translate3d(100%)`（x351）→ `.show` 後 `translate3d(0)`（x262），**向左位移 89px**。修復：**移除容器 translateX 滑入動畫**（容器固定 `transform: rotate(-10deg)`、移除 .show 容器過渡），僅保留 span scale 0→1 + svg 畫線動畫。驗證：BEFORE/AFTER 容器 transform 皆 `translateX(0)`、x262 一致（**起始=結束**）、span scale(1)、svgAnim organicRevealAnimation。版號 ?v=20260824ag。
- **追加3（移到「一杯好咖啡。」後）**：容器從 h2 右上移到 p 內「一杯好咖啡。」文字後（span inline-block relative、margin-left 12px）。驗證：容器 x254 y275（第三行）、svg 圓形旁、行動端無溢出。版號 ?v=20260824ah。
- **追加4（圓形加大）**：other-members-svg width 102→**140**（行動）、834px→**190**、1920px→**240**（補上原缺 media）。驗證：SVG 190×121、bbox 111×54、動畫正常。版號 ?v=20260824ai。
- **追加5（文字動畫加大）**：「他にもいます！」字體 10→**16**（行動）、12→**20**（834px）、16→**26**（1920px）。驗證：桌面 fontSize 20px、spanRect 148×55、span scale(1) 正常。版號 ?v=20260824aj。

---

## 32. Sticker 貼紙模組化（sticker-box 資料驅動）🏷️ — ✅ 2026-08-24

### 需求
- ① 並非所有咖啡都能看到 sticker（A 咖啡用 Sticker 1、B 咖啡用 Sticker 2、或留空不顯示）；② Django admin 添加自訂 sticker 功能，管理員自由使用每種 sticker 顯示；③ 不需要複製 8 個模組（資料驅動模組化）。

### 架構
- **不需複製 8 個 HTML 模組** → 建立 `Sticker` 模型（資料驅動），CoffeeItem/BeanItem 各加 `sticker` FK（留空 = 不顯示）。
- **Sticker 模型**（eshop/models/sticker.py）：背景款式（內建 4 款 CharField）+ 前圖（內建 4 款 preset **或** 上傳自訂 ImageField，上傳圖優先）+ text_en/text_zh（`\n` 換行）+ is_active + sort_order。
- **Seed 4 款**（data migration 0065）：Sticker 1(v1+咖啡杯+Follow Your Rhythm)、2(v2+咖啡豆+Crafting Perfection)、3(v3+咖啡杯變體A+Take It Easy)、4(sticker+咖啡杯變體B+Freshly Roasted)；現有 8 咖啡→S1、6 咖啡豆→S2（維持現況）。

### 實作
- **migration**：0064（CreateModel Sticker + CoffeeItem/BeanItem 加 sticker FK + **pickup_time drift 修復**）、0065（seed data）。
- **pickup_time drift（重要）**：`ordermodel.pickup_time` 資料庫欄位已存在（0050 添加、0052 SeparateDatabaseAndState 只移除 state）但 model 又加回定義 → makemigrations 每次誤判 AddField（若直接 AddField 會重複建欄位報錯）。0064 沿用 0052 手法 SeparateDatabaseAndState（database 空、state AddField）修復 → `makemigrations --check` 從此 No changes。
- **模板**（coffee.html/bean.html）：sticker-box 包 `{% if coffee.sticker %}`；背景圖改 inline style（`style="background-image: url('{{ sticker.bg_image_url }}')"`）；前圖/文字全由 sticker 輸出（`|linebreaksbr` 處理換行）。
- **CSS**（style-custom.css）：`.sticker .bg` 移除硬編碼 `url('/static/images/sticker_v1.png')`（保留 position/size/repeat/spin）；`.sticker .front img` 加 `object-fit: contain`（自訂圖不變形）。
- **Admin**（eshop/admin.py）：新增 `StickerAdmin`（背景/前圖縮圖預覽、文字、啟用、排序）；CoffeeItemAdmin/BeanItemAdmin 加「Sticker 貼紙（留空=不顯示）」fieldset + list_display 顯示。

### 驗證（全 PASS）
- `migrate` ✅、`makemigrations --check` No changes ✅、`manage.py check` ✅。
- 資料層：4 款 Sticker seed、8 咖啡→S1、6 咖啡豆→S2 ✅。
- Test client：coffee/bean 詳情頁 status 200、sticker-box 渲染（背景 inline/前圖/文字正確）；**sticker 留空 → sticker-box 完全不渲染**（transaction 回滾無污染）✅。
- Chrome DevTools（localhost:8081）：coffee/1 顯示 S1（v1 背景 spin 動畫、takeaway_cup 前圖、object-fit contain、文字正確）；**coffee/9 臨時換 S3 → v3 背景 + 咖啡杯變體A + Take It Easy**（還原）✅；Admin Sticker 列表縮圖/文字/排序正確、商品編輯頁 Sticker 下拉（空/1/2/3/4）✅。
- 上傳自訂前圖：property `front_image_url` 上傳圖優先（`/media/stickers/...`）、還原回 preset ✅。

### 備註
- Render 免費方案：上傳的自訂前圖（media/stickers/）重新部署後可能遺失（與現有商品圖相同限制）；內建款式不受影響。

---

## 31. 浮動購物車按鈕修復 🛒 — ✅ 2026-08-24

### 需求
- ① 點選浮動購物車按鈕後，右側購物車打開，浮動購物車按鈕疊加在頂部上；② 點選後錯誤右側位移。

### 根因
- **問題 1**：`.bc-floating-cart.hide` 只有 `pointer-events:none` + `animation:none`（2026-08-14 移除動畫）→ `_hideFloatingCart()` 移除 show 加 hide 後**按鈕仍顯示**（無 display none）→ 疊在購物車頂部（DOM 在購物車後、同 z-index 9999）。
- **問題 2**：`open()` 先執行 `_lockScroll()`（對浮動按鈕設 `right: 40+scrollbarWidth` → 按鈕左移）**之後**才 `_hideFloatingCart()` → 點擊瞬間按鈕位移可見。

### 實作
- **CSS**（bc-components.css）：`.bc-floating-cart.hide` 加 `display: none !important`（真正隱藏）。
- **JS**（bc-slideout-cart.js）：`open()` 調整順序——先 `_cartOpenHiddenFloating=true` + `_hideFloatingCart()`，再 `_lockScroll()`（按鈕在 right 補償前已隱藏，無位移）。
- **版號**：bc-components.css ?v=20260823p、bc-slideout-cart.js ?v=20260824a

### 驗證
- CDP：加入商品→浮動按鈕顯示；點擊→**浮動按鈕 display none**（不疊頂部）、購物車 open、body overflow hidden；關閉→浮動按鈕恢復 show+block、body 復原；無位移（先 hide 再 lockScroll）。
- **2026-08-24 追加（頁面跳轉靜默，避免每次滑入幹擾）**：頁面載入的 async fetch 同步超過 500ms 時 `_initialBadgeSync` 已 false → 每次跳頁滑入動畫。修復：`_updateBadge(count, animatedOverride)` 加覆寫參數，`_syncBadgeFromServer`（頁面載入/bfcache 恢復）傳 `false` 強制靜默；加入購物車操作不傳 → 仍動畫。驗證：跳頁載入 200ms/1.4s 皆 no-anim+animation none、加入購物車 bcFloatingIn；版號 bc-slideout-cart.js ?v=20260824b
- **2026-08-24 追加（已有商品時再次加入不重播動畫）**：`_showFloatingCart` 的 `toggle('no-anim', !animated)` 在 `if(contains('show')) return` **之前**——加入商品時 animated=true 移除 no-anim → CSS 動畫從 none 變 bcFloatingIn → 每次重播。修復：**先檢查 `show` 再 return**（不移除 no-anim、不重播）。驗證：badge 5→6（加入成功）、按鈕維持 no-anim show + animation none + animReplayed=false；首次加入（無 show）仍滑入動畫；版號 bc-slideout-cart.js ?v=20260824c

---


## 30. bean 頁 kariomons .staff 整合（賞味期限下方）🧑‍🍳 — ✅ 2026-08-23

### 需求
- 將 kariomons.com/onlineshop/1377 的 `.staff`（2 個 `.inner`：圓形照片 + 名字 + 評論）整合到 bean 頁「賞味期限」下方；UI 與原站完全一樣、無額外 UI/css、不衝突。

### 分析
- `.staff` = `.title-sub`（標題）+ 2× `.inner > .name(figure>img 圓形 + h3 strong) + .txt(p)`；**純 CSS 靜態**（無 JS 動畫）；`inner` 虛線背景（line-dot.svg repeat-x）；flex 布局、86px 圓形照片、min-height 115px。

### 實作
- **bean.html**：賞味期限 block-23 後插入 `.staff.bc-staff`（2 個 inner，內容品牌化：Chief Roaster / Barista 中文評論，照片用 bean_01/coffee_01 產品圖圓形裁切）。
- **bc-components.css**：`.bc-staff` 系列（1:1 複製 onlineshop.css：flex、虛線 data-URI 淺色點、86px 圓形、title-sub 絕對定位）；**深色適配**（標題品牌金、文字白/灰、字型 Noto Sans TC）；figure 覆蓋瀏覽器默認 margin(1em 40px)；行動端（≤575）響應式（標題置頂、內文正常寬、照片 64px）。
- **版號**：bc-components.css ?v=20260823h

- **2026-08-23 追加2（懸停邊框根因修復）**：`.bc-staff` hover 時出現金色邊框+陰影——**根因**：用了 `class="staff bc-staff"`，觸發 style-bootstrap.css 既有 `.staff`（團隊成員卡片）樣式：常駐 `border: 1px #1d150b`、`hover: border 金色 + box-shadow`、padding 25px。**修復**：移除 `.staff` class（只用 `bc-staff`）→ border/padding/hover 全部消失（驗證 border 0px、hover 無變化）；版號 ?v=20260823i
- **2026-08-23 追加3（頭像與名稱距離）**：員工照片與名稱視覺距離遠——根因是 PNG 頭像透明邊距（圓形頭像在容器內有留白）。放大頭像 86→96px（object-fit cover 裁掉透明邊）+ `max-width: none`（突破 figure max-width:100% 截斷）+ margin-left -5px 居中；版號 ?v=20260823k
- **2026-08-23 追加5（頭像變白/看不見）**：PNG 頭像是**深藍線稿**（平均 #125771，原站品牌藍）+ 90% 透明——原站米色底清晰、黑底上看不見（像白色空洞）。修復：img 加 `background: #f3eee2`（原站米色圓底）+ padding 8px → 線稿在米色圓圈上清晰、與原站視覺一致；版號 ?v=20260823m
- **2026-08-23 追加7**：移除頭像米色圓底（background #f3eee2、padding 8px），保留 96px 放大；版號 ?v=20260823o

---


## 29. bean 詳情頁烘焙程度 5 顆咖啡豆 SVG 🫘 — ✅ 2026-08-23

### 需求
- `bean/` 頁 roastrange（烘焙程度選擇器）：在 roastrange-label 內圓點上方添加 5 顆咖啡豆 SVG，表示烘焙程度（淺→深 5 級不同咖啡色）。

### 實作
- **bean.html**：5 個 `roastrange-item`（浅/中浅/中/中深/深）各加 inline 咖啡豆 SVG（`.roast-bean` + `--light/--medium-light/--medium/--medium-dark/--dark`），豆形橢圓 + S 裂縫。
- **bc-components.css**：`.roast-bean` absolute 定位於圓點上方（top -34px、left -14px、22×22px、z-index 2）；`.roast-bean-body` 5 級烘焙色階：`#D9B38C → #C08F5E → #A06A3E → #7C4E28 → #4B2E18`；`.roast-bean-crack` 裂縫（深灰 35% 描邊）。
- **版號**：bc-components.css ?v=20260823a

### 驗證
- CDP 桌面 1280：5 顆豆皆在點上方（aboveDot true）、fill 顏色漸層正確（217,179,140 → 75,46,24）；行動 375：豆間距 64px 無重疊、無水平捲動；bean/2 也 200。
- **2026-08-23 追加**：咖啡豆與圓點水平對齊修正（left -14→-8px，offset 6.2→0.2px）+ 咖啡豆旋轉 35°（transform rotate）；版號 ?v=20260823b
- **2026-08-23 追加2**：**5 種咖啡豆造型**（light 經典橢圓、medium_light 圓豆、medium 細長、medium_dark 淚滴、dark 雙瓣）+ 旋轉 35→55°；版號 ?v=20260823c
- **2026-08-23 追加3**：咖啡色調淺（#E3C29E/#CC9E70/#B07E52/#8A5C38/#5A3822）+ 旋轉視覺偏右補償（left -8→-11px）；版號 ?v=20260823d
- **2026-08-23 追加4**：行動端（≤767.98）咖啡豆縮小（22px→16px、top -28px）；getBoundingClientRect 顯示 22px 是旋轉 55° bounding box（16×√2），計算樣式確認為 16px；版號 ?v=20260823e

---


## 28. bc-series-list 咖啡名稱/Highlight 加大 + 更改字體（參考 coffee_menu）🎠 — ✅ 2026-08-23

### 需求
- bc-series-list（about.html SERIES 滑桿）咖啡名稱和 Highlight 文本加大，更改字體 → 參考 coffee_menu 頁。

### 實作
- **coffee_menu 樣式分析**：名稱 = Bootstrap h5（`Josefin Sans` 宣告但未載入 → 實際 Arial fallback、25.32px、uppercase、白）；highlight = `.bc-menu-highlight`（Noto Sans TC、18px、weight 500、品牌金）。
- **base.html**：Google Fonts link 加入 `Josefin+Sans`（coffee_menu 也受益，名稱真正顯示 Josefin）。
- **bc-series.css**：`.bc-series-caption-name` → Josefin Sans、26px（20→26）、weight 400、**uppercase**；`.bc-series-caption-highlight` → Noto Sans TC、18px（14→18）、**weight 500**；響應式（平板 22/15、行動 18/12）。
- **版號**：bc-series.css ?v=20260823a

### 驗證
- CDP 桌面 1280：名稱 Josefin Sans 26px uppercase 白、highlight 18px 500 品牌金、Josefin 已載入、名稱寬 272≤照片 420 無溢出；行動 375：18/12px、名稱 256≤260、無水平捲動。
- **2026-08-23 追加**：咖啡名稱 letter-spacing 0.08em → **normal**（與 coffee_menu 一致）；版號 ?v=20260823b

---


## 27. mauinterview rotate-mau 整合（about.html 旋轉標誌背景）🎠 — ✅ 2026-08-22

### 需求
- 將 https://mauinterview.musabi.ac.jp/ 首頁 `.rotate-mau`（SVG mask 標誌剪影 + 逆時針旋轉）整合到 about.html；UI/動畫與原站 100% 相同、不與其他部分衝突、不加任何額外 UI/css。

### 實作
- **HTML**：`<div class="rotate-mau">` 4 層巢狀空 div（完全複製原站），置於 block content 第一個位置（bc-series-hero 之前，等同原站 `<main>` 第一個元素）。
- **CSS**：新建 `bc-rotate-mau.css`（1:1 複製原站）：`.rotate-mau` absolute z-index 99 寬 100% 高 170vw pointer-events:none；`.rotate-mau__inner` 170vw 方形 left -35vw；`.rotate-mau__inner__item` 31.8KB SVG mask（「美はつづく」字形 data URI）裁切 + `kf__spin__re` 36s（桌面 50s）逆時針旋轉、背景 #eeecde opacity 0.9；reduced-motion 暫停。無 JS 需求。
- **定位基準**：`.bc-page-content`（position:relative）→ rotate-mau absolute 以它為基準，與原站 `<main>` 一致。
- **2026-08-22 追加**：
  - **z-index 99 → -1**（使用者要求置於背景層，不再與頁面前面內容重疊；SERIES/topConcept 內容全部在上層）
  - **mask 文字改為「Taste Right / Taste Time」**：原「美はつづく」是 SVG path 圖形無法編輯 → 用 fontTools + Mogra-Regular.ttf 把文字轉成 SVG path（scale y 翻轉 0.151/-0.151 修正顛倒、兩行 baseline 386/576 垂直居中）→ 之後改 CSS mask 內文字需重新生成 path
  - **2026-08-22 修正（重要）**：使用者指出動畫效果錯誤——原站文字是**沿圓形路徑排列的環形標誌**（radial 像素分析證實：墨水全在圓周 r=400-500、中心完全空洞、8 方向均勻），非兩行直排文字。重新用 fontTools 把「Taste Right Taste Time」沿圓周排列（22 字元含空格、R=355、scale 0.1736、每字元 rotate θ 到圓周 + translate(0,-R)、字頭朝外、y 翻轉正立）→ canvas 驗證：band10 歸零（不超出 viewBox）、centerPct 0%、外緣 485
  - **2026-08-22 字距/尺寸調整**：新增 `scripts/generate_rotate_mau_mask.py`（可參數化文字/字距/尺寸/半徑的可重用產生器）；字縮小 15%（scale ×0.85、字高 111、墨水外緣 485→474）、字距縮小（span 360°→300°，字元間距縮小、60° 缺口對稱置底）；版號 ?v=20260822e
  - **2026-08-22 再縮小 30%**：字尺寸 ×0.85→×0.595（字高 111→77、墨水高度 164→115）、字距 span 300°→210°（字元間距再縮 33%、缺口 160°）；版號 ?v=20260822f
  - **2026-08-22 兩組文字繞滿圓周**：span 210° 缺口 160° 過大 + 文字未完全在圓形路徑 → 使用者建議新增一組文字。**兩組「Taste Right Taste Time」**（44 字元）沿 360° 排列：span 350°、maxGap 10°（僅兩組自然分隔）、字元間距減半（字距縮小 50%）、字高維持 77px、外緣 432。腳本新增 `--font-size` 參數（直接指定 cap 高度，避免文字變長時 scale 自動稀釋）；版號 ?v=20260822g
  - **2026-08-22 字型換為 Playfair Display**：使用者要求改用 Playfair Display 字型（Google Fonts variable wght，下載至 ~/.cache/bc-rotate-mau/）。Playfair cap/asc=0.65 比 Mogra 低 → 視覺字高校正：--font-size 77→118（cap 高度維持 77px）、inkHeight 63→100、span 350°、gap 10°；腳本新增 `--font` 參數（可切換字型）；版號 ?v=20260822i
  - **2026-08-22 間隙異常修復（Ti/Ri）**：使用者指出「T→i」「R→i」間隙特別大。根因：角度分配用 advance（含不均 side bearing）——T/R 是寬 advance 且側留白大、i 窄且留白大 → 疊加後間隙爆大。修復：改用**字形實際 ink 寬 + 統一 gap** 分配角度（忽略 advance 留白）→ 字元間視覺間隙完全均勻（數學保證 = gap*scale）；44 字元合併為 17 段（間隙小到貼合）、剩餘大間隙僅在空格/兩組交界；腳本新增 `--gap` 參數（upem，預設 40）；版號 ?v=20260822j
  - **2026-08-22 ink 中心校正（Ti 仍鬆、me 重疊）**：上一版仍忽略 glyph 的 xMin（左側留白）——T xMin 大偏右→Ti 間隙仍大、m xMin 小偏左→me 重疊。修復：字元中心 = **xMin + inkW/2**，path transform 加 `translate(-center*s, 0)` 把 ink 中心對齊 θ 點。正確公式驗證：Ti=0.47°、me=0.47°、as=0.49°、Ri=0.48°（全部統一，無重疊）；eT 4.85° 為跨空格正常間距；版號 ?v=20260822k
  - **2026-08-22 gap 再縮小（25）+ 快取問題排查**：使用者仍回報 Ti 間隙大/me 重疊。排查發現**多個殘留 runserver 進程（含 8081）返回舊模板** → 全部停止重啟乾淨伺服器後輸出 l 版。gap 40→25（間隙 0.47→0.37°，Ti=me=0.373° 統一、無重疊）；版號 ?v=20260822l
  - **2026-08-22 scale 匹配修正（根本原因，最終修復）**：使用者第三次回報 Ti/Ri 間隙大 + me 重疊。**根因**：scale 用 font_size/asc 固定值（0.109），與步長不匹配（正確值 2πR/total_step≈0.1025）→ 字元 ink 弧長 ≠ 步長弧長 → 寬字元（T/R）間隙被撐大、部分字元重疊（me）。且生成 path 誤用 radius（355）而非反推 R（270）。**修正**：scale = 2πR/total_step（R 由 font-size 反推 =270）、path 用 R、gap=15 → 實際渲染間隙全部統一 1.06 viewBox（Ti=me=Ri=as=1.06，正無重疊）；版號 ?v=20260822m
  - **2026-08-22 Ti/Ri 視覺間隙收緊**：me 已修復但 Ti/Ri（寬字元 T/R 右側下半部內凹 + 窄字元 i）視覺空洞仍明顯。**解法**：新增 `--tight-gap` 參數，對「T/R→i」組合間隙收緊（gap 15→tight_gap 6）→ Ti=Ri=0.43 viewBox（收緊 60%）、me 維持 1.08 不重疊、其他對維持 1.06；版號 ?v=20260822n
  - **2026-08-22 字型換為 Roboto**：使用者要求改用 Roboto（Google 無襯線）。google/fonts repo 無 apache/roboto → 從 @fontsource/roboto 下載 woff2（brotli 解壓）+ fontTools 轉 ttf（~/.cache/bc-rotate-mau/Roboto-Regular.ttf）。Roboto cap/asc=0.77 → --font-size 100（cap 77px）、R=395；間隙 Ti=Ri=0.32 收緊、me=0.78 不重疊、其他 0.78 統一；版號 ?v=20260822o
  - **2026-08-22 移除 Ti/Ri 特殊間隙微調**：使用者指示不需要字元間微調整（Ti/Ri/me/as/st/im 全部統一）→ --tight-gap 改為 = gap（15，等同無收緊）→ 所有字元對間隙統一 0.74~0.84 viewBox（Roboto）；版號 ?v=20260822p
- **版號**：bc-rotate-mau.css ?v=20260822p

### 驗證
- CDP 1280/375：樣式與原站 1:1（170vw 方形、mask 31838 字元、z-index 99、pointer-events none）；動畫實際運行（rotate -34.5°→-43.2°/1.2s、50s/36s）；無水平捲動；SERIES 拖動正常（--js-x -150→-350px）；bc-top-concept scroll-scrub 31 leader 點亮正常；console 無新增錯誤（WebSocket 403 為既有問題）；版號 bc-rotate-mau.css ?v=20260822a。

---


## 26. SERIES 咖啡名稱 + Highlight 高亮 + 平板響應式 🎠 — ✅ 2026-08-21

### 需求
- 1) bc-series-hero 添加每種咖啡名稱和 Highlight 高亮文本在底部；2) bc-series-heading 平板端沒有響應式設計（文本疊加在照片下層）；3) 平板應基於桌面布局縮小尺寸；4) 括號框對齊照片中心；5) 名稱/Highlight 加大。

### 實作
- **名稱 + Highlight**：兩組 SERIES 滑桿各 6 張照片底部加 `.bc-series-caption`（名稱 + 金色 highlight），取自資料庫 `eshop_coffeeitem`（WakeMeup「雙產區，喚醒一天」等 6 組）；caption 名稱 20px / highlight 14px。
- **平板響應式（基於桌面縮小）**：768-1199 標題 140→52px、照片 420→300px、括號框 600→430px、pager bottom 30px。
- **括號框對齊**：`top: calc(50% - 33px)`（caption 高度 66px 一半）→ 框中心 = 照片圖片中心（CDP diff 0）。
- **照片 src 修復**：批次加 caption 時誤刪 `images/` 前綴 → 12 處加回。

### 驗證
- CDP 1280/1024/768/375 照片 imgLoaded=true；平板照片 300px、括號框 430px、標題 52px；括號框中心 = 照片圖片中心（diff 0）；caption 20/14px；node + manage.py check 通過；版號 bc-series.css ?v=20260821k。

---

## 25. topConcept 最終優化（全部照片 placeholder + 響應式 + 文字調整）🏷️ — ✅ 2026-08-21

### 需求
- 多輪優化：照片不壓字、文字 justify 填滿右緣、整體縮小、欄位左移、全部照片改 placeholder 加寬、行動端文字加大（參考 hakujuji）。

### 實作
- **照片**：hakujuji 原站照片 → 全部改為 placeholder（深色底 + 金色細邊框 + 咖啡 SVG）；桌面 thum--1 12vw、thum--4 8vw、thum--6 10vw 等；thum--1/4 佔 2 行、thum--6 佔 3 行。
- **欄位**：col 74%→55.5%、`flex-start` 靠左；桌面字級 2vw（後續 thum--4/6 加寬後 1.7vw）。
- **行動端**：thum--2/3/7 佔 2 行（13.0vw 高）、欄位 90%、字級加大至 3.8vw（參考 hakujuji 5.07vw 的 75%）、照片縮小騰空間。
- **驗證**：clearance（照片固定框 + 不重疊）1280/1024/768/375 全 PASS；覆蓋行數 thum--1/2/3/4/7 2 行、thum--6 3 行；justify 填滿 textW=W；scroll-scrub 200/200、198/198；版號 bc-top-concept.css ?v=20260821ag（最新）。

### 驗證
- CDP 四寬度：clearance PASS、照片覆蓋 2/3 行、文字填滿右緣、scroll-scrub 正常；`node --check` + `manage.py check` 通過。

---

## 24. hakujuji topConcept 整合（取代 bc-leader，scroll-scrub 逐字點亮）🏷️ — ✅ 2026-08-21

### 需求
- 將 hakujuji 首頁 `.boxBottomLine article.topConcept` 整合到 about.html；取代現有 bc-leader；忠實原站（全寬、原始 vw、sticky 標題 26%/leader 74%、了解按鈕）、無額外 UI/css。

### 實作
- **HTML**：`section.boxBottomLine.article.topConcept.bc-top-concept` > `.grid` > `__tob`（sticky 標題 3 行中文 + 「了解更多」cateBtn → coffee_menu；`__tobContents` 74% 含原 13+18 行 leader）。移除 .container。
- **CSS**：新 `bc-top-concept.css`（1:1 top.css/base.css/top-sp.css/base-sp.css + 深色適配 + 照片貼齊行尾；coffee_04 右緣對齊欄位右緣清出 Order 按鈕）。刪 bc-leader.css。
- **JS**：新 `bc-top-concept.js`（top.js wrapCharSpan + **scroll-scrub**：ScrollTrigger start 'top 60%' end 'bottom 50%' scrub 0.2，已捲過 1 / 未捲 0.4）。刪 bc-leader.js。
- **全域修復**：bc-components.css `html,body` overflow-x `hidden` → `hidden; clip`（hidden 建立 scroll container 破壞 sticky）。
- **驗證**：CDP 桌面/行動（13+18 li、7+6 縮圖、opacity 0.3→全 1、sticky 105、26/74、行偏移 PASS、照片貼行尾 PASS、無水平捲軸）+ node + manage.py check。

---

### 需求
- 1) bc-leader 目前全寬 → 加容器包住；2) 整個 UI 縮小 30%（文字+照片）；3) 右側全部照片（coffee_04/02/05/bean_01）「位移」（二修確認）。

### 根因（第 3 點）
- 原站 hakujuji 文字行很長、延伸到貼右緣（right:0）的照片；我們的中文文案短（~15 字），照片仍 right:0 → 文字與照片間 ~500px 空曠，照片孤獨浮在容器右緣。與固定按鈕無關（前次誤判已修正）。

### 實作
- **容器**：section 內包 Bootstrap .container（1140 max）；行動版容器 padding 歸零維持貼齊。
- **縮小 30%（桌面）**：--luv: min(0.7vw, 13.44px) 統一單位，所有桌面 vw → calc(var(--luv)*N)；1280 字級 42.2→29.5px。行動版不縮。
- **右側照片定位**：coffee_02/04/05/bean_01 由 right:0 改為 left（桌面 calc(var(--luv)*K)、行動 vw），貼齊各自文字行尾端（間距 5–9px）。

### 驗證
- CDP 四寬度（1280/1024/768/375）：照片左緣 − 行文字尾端 = 5–9px PASS（cdp_leader_clearance.py 改為行尾檢查）。
- 動畫 opacity 0.3→1、13/18 li、7/6 縮圖不變；像素分析確認 7 張杯身位置正確；node + manage.py check 通過。

---

## 22. about.html hakujuji csBlock__leader 整合（逐字亮起）🎠 — ✅ 2026-08-19

### 需求
- 將 https://www.hakujuji-g.co.jp/concept/ 的 `csBlock__leader--list` 整合到 about.html：建立新 `<section>` 不與其他區塊衝突，UI/動畫 100% 複製、無額外 UI/css。
- 內容（用戶確認）：中文咖啡品牌文案 + 咖啡去背圖（coffee_01~05/08 + bean_01），結構/動畫不變。

### 實作
- **about.html**：新 `<section class="bc-leader">`（括號滑桿後、ftco-section-blank 前）；`partsPc`（桌面 13 行）+ `partsSp`（行動 18 行）兩份 `.csBlock__leader`；7 個縮圖。
- **bc-leader.css**：100% 複製原站（base.css 桌面 3.29vw / base-sp.css 行動 5.07vw、逐行 letter-spacing、縮圖 vw 定位、partsPc/partsSp 767px 切換）；深色主題適配（文字 #fff、border-bottom var(--bc-border)、ul reset 40px、咖啡圖 object-fit:contain + 原長寬比高度）。
- **bc-leader.js**：複製 concept.js `wrapCharSpan`（逐字包 span）+ GSAP `opacity 0.3→1`、`stagger 0.02`；ScrollTrigger `once` 進入視窗觸發（區塊在頁面下方，載入觸發看不到）；defer 輪詢保護沿用 bc-attract.js。

### 驗證
- CDP 桌面：partsPc 顯示（13 li、7 縮圖、opacity 0.3→1）；行動：partsSp 顯示（18 li、6 縮圖、opacity 0.3→1）。
- 行偏移與原站 CSS 完全一致（桌面/行動 PASS）；無文字/縮圖水平溢出；node --check + manage.py check。

---

## 21. WhatsApp 就緒通知失效診斷 + Render token 更新 🔧 — ✅ 2026-08-17

### 問題
- 用戶反饋：客戶訂單「已就緒」狀態，發送 WhatsApp 取貨訊息不起作用，懷疑 API/token 過期。

### 診斷（唯讀驗證）
- **Token 未過期**：本地 Graph API `/me` HTTP 200（帳號 Employee）、權限完整（`whatsapp_business_messaging` granted）。
- **發送功能正常**：實際發送測試訊息 HTTP 200 成功（訊息 ID 產生）；`send_order_ready_notification(訂單#2852)` 返回 `True`。
- **真正原因（平台限制）**：WhatsApp 帳號仍在「測試模式」——`display_phone_number = +1 555-139-6249`（Meta 預設測試號碼）、`code_verification_status = NOT_VERIFIED` → 有 **24h 會話窗口限制**（客戶未在 24h 內先主動發訊息，主動推送會被拒，錯誤 `131030`）。
- **資料面**：ready 訂單 10 個中僅 2 個有 phone（舊訂單無電話 → 靜默跳過）。

### 修復
- ✅ 更新 Render 環境變數：`WHATSAPP_TOKEN`（206 長度新 token）+ `WHATSAPP_PHONE_NUMBER_ID`（1260339307158166）+ `WHATSAPP_BUSINESS_ACCOUNT_ID`（927032970425203），透過 Render MCP `update_environ`（服務 `srv-d8jce6rtqb8s73897t4g`）。
- ✅ 觸發新部署：`dep-da1d0n7qj5pc73col130`（build_in_progress）。

### template 程式碼已準備 ✅（2026-08-17）
- `settings.py` 新增 `WHATSAPP_TEMPLATE_NAME` / `WHATSAPP_TEMPLATE_LANGUAGE`（預設 zh_HK）環境變數。
- `whatsapp_notifier.py` 新增 `send_whatsapp_template_message()` + 提取 `_normalize_phone()` helper；`send_order_ready_notification` 優先走 template（設定了 NAME），否則 fallback 自由格式。
- 一鍵切換：Meta 審核通過後，`.env` 加 `WHATSAPP_TEMPLATE_NAME=order_ready_notification` 即切換（本地需重啟 server、Render 需重啟/重部署）。
- template body 變數對應：`{{1}}`=客戶名、`{{2}}`=訂單編號、`{{3}}`=取餐碼。
- ✅ 驗證：py_compile + manage.py check 0 issues + test_whatsapp_notifier 15 tests OK + mock 切換邏輯驗證。

### 待辦（需用戶手動 Meta 平台）
- 正式上線：換真實香港號碼 + 號碼驗證（code_verification）+ template message 審核（解決 24h 窗口限制，才能主動推送給未互動客戶）。

---

## 20. bc-welcome-panel 平板/手機右側圖片與文字溢出修復 🔧 — ✅ 2026-08-16

### 問題
- 使用者反饋：平板/手機端 `.bc-welcome-panel` 右側的圖片和文字超出容器外部。

### 診斷（CDP 量測 768/375px）
- **文字溢出（根因）**：`.bc-last-order`「按照之前口味落單?」`white-space: nowrap` 溢出 imgbox：
  - 平板：scrollWidth **115px** > imgbox **92px**（溢出 23px）
  - 手機：scrollWidth **72px** > imgbox **62px**（溢出 10px）
  - 根因：2026-08-13 將 imgbox 縮小（119→92→62px）讓出左側文字空間，但 last-order 文字 nowrap 未相應處理 → 文字向兩邊溢出、右緣貼近 panel 邊界。
- **圖片浮出**：`.bc-welcome-img` absolute `top:-50/-29px` 浮出 panel 頂部（平板 44px、手機 24px）——此為「浮出容器右上角」既有設計，保留。
- 水平方向經量測皆在 panel 內（-12/-8px），問題在文字 nowrap 溢出 imgbox。

### 修復（`bc-components.css`）
- `.bc-last-order` 平板/手機加 `white-space: normal + line-height: 1.25` → 文字換行 2 行，不再溢出 imgbox。
- 圖片縮小避免與換行文字重疊：平板 `.bc-welcome-img`/`.bc-welcome-img-link` 92→**76px**、手機 58/62→**55px**（手機 img-link top -35→**-29px** 與圖片對齊）。
- `base.html` → `bc-components.css?v=20260816z`。

### ✅ 驗證（CDP 768/375/1280px）
- 平板：lastOrder scrollW **92 = clientW 92**（不再溢出）、2 行、imgTextGap -2px（圖片底部與文字視覺連續，與桌面 -6px 一致）、未溢出 panel（-12px）。
- 手機：scrollW **62 = clientW 62**、2 行、imgTextGap 1px、未溢出 panel（-8px）。
- 桌面 1280px：不變（1 行、img 136px）。

### 涉及檔案
- `static/css/bc-components.css`（平板 ≤768 / 手機 ≤480 兩斷點 img/img-link/last-order）
- `templates/betweencoffee_delivery/base.html`（CSS version）
- 驗證資產：`docs/verify/cdp_diag_welcome_overflow.py`、`cdp_diag_welcome_center.py`、`cdp_shot_welcome_mobile.py`

---

## 19. navbar-brand「｛ Between ｝」移至最左 + 響應式縮小 + CSS 覆蓋修復 🔧 — ✅ 2026-08-16

### 已完成

**1. 需求 ✅**
- navbar-brand 移到瀏覽器最左；縮小尺寸（各端響應）；與漢堡選單水平對齊；離頂部有距離（統一響應）

**2. 最終方案 ✅**
- container 全寬（`max-width:100%` + padding 15px）→ brand 貼左、menu 靠右
- navbar `padding-top` 統一離頂（桌面 30 / 平板 24 / 手機 18 / 小手機 14）
- brand 字體響應縮小（桌面 36 / 平板 30 / 手機 24 / 小手機 20）
- 桌面 brand `margin-top:12px + margin-left:22px`；toggler `margin-left:auto` 靠右（修漢堡疊加）

**3. CSS 順序/覆蓋修復（兩次）✅**
- ① `font-size:30px` 寫在 media query 之後 → 覆蓋斷點縮小（手機仍 30px）→ 改 `min-width:992px` 限定桌面
- ② `margin-top` 寫在 media query（前面）→ 被 brand 區塊 `margin:0`（後面）覆蓋 → 移到 `margin:0` 之後

**4. 歷程 ✅**
- absolute left 方案（漢堡疊加/離頂不統一）→ 回 container 內 flex + container 全寬（最乾淨）；離頂多次微調（12→20→24px）→ 改 navbar padding-top 統一

## 18. 首頁 SERIES 滑桿（完全一致複製 designing.jp/series）🎠 — ✅ 2026-08-16

### 已完成

**1. 需求（第三次嘗試，按用戶明確規格）✅**
- 用戶描述實際效果並要求**完全一致**：左側文字 + 照片滑桿水平滾動時左側文字模糊 + 滑桿在底部 + 無背景；標題「SERIES」；獨立 `<section>` 標籤

**2. 網站規格提取（curl 分析 designing.jp CSS）✅**
- `.container_3HNAz` 100vh flex 無背景；`.heading_3yyjd` 140px（行動 50px）`::before backdrop-filter:blur(10px)` `[data-blurred]` 切換 0.6s；`.scrolling_iC60P` `padding-left:15.46vw` 橫向捲動 scrollbar 隱藏（行動 scroll-snap x mandatory）；`.slide_2tGjp` 350px（行動 69.33vw）+ `translate3d(var(--js-x)) skewX(var(--js-effect))`；`.picture_29AE2` aspect 280/374 375px（行動 92.8vw）無邊框 box-shadow cover hover scale(1.03)

**3. 實作 ✅**
- `index.html`：獨立 `<section class="bc-series-hero">`（home-slider 後）——`h2.bc-series-heading`（SERIES）+ `div.bc-series-scrolling > .bc-series-list > 6 × .bc-series-slide > .bc-series-picture > img`（coffee_01~05/08）；`bc-welcome-section` `margin-top:0` 相容
- `bc-series.css`：hero `height:100vh; flex column; align-items:flex-start; background:transparent`；heading 140px + `::before blur(10px)` data-blurred；scrolling `margin-top:auto` 貼底 `padding-left:15.46vw`；slide 350px；picture 280/374 375px 無邊框；行動 50px + scroll-snap 69.33vw + picture 92.8vw
- `bc-series.js`：scrolling scroll → `heading[data-blurred]`（scrollLeft>2）

**4. 驗證 ✅**
- test client：獨立 section / 標題 SERIES / 6 圖 / 無多餘內容 / css-js 載入 / 位置（home-slider 後 welcome 前）/ welcome margin-top:0
- `manage.py check` 0 issues、bc-series.js 語法 OK；CSS 數值與先前 CDP 驗證版一致（桌面 140px 左、滑桿貼底 gap 0、blurOpacity 1、無邊框/背景、行動 scroll-snap 無溢出）

## 17. 首頁 BETWEEN SERIES（完全複製 designing.jp/series）🎠 — ✅ 2026-08-16

### 已完成

**1. 需求（重做）✅**
- 用戶指正首次整合誤加內容/布局偏離：要**完全相同的效果**——左側文字 + 照片滑桿水平滾動時左側文字模糊 + 滑桿在底部 + 無背景 + 照片無邊框；不添加任何內容

**2. 結構分析（designing.jp container_3HNAz）✅**
- `.container_3HNAz` fixed 100vh flex align-items:center；`.heading_3yyjd` 140px 大字 `::before` `backdrop-filter:blur(10px)` `data-blurred` 切換；`.scrolling_iC60P` 橫向捲動 `padding-left:15.46vw`（行動 scroll-snap 69.33vw）；`.slide_2tGjp` 350px `translate3d(var(--js-x)) skewX(var(--js-effect))`；`.picture_29AE2` aspect 280/374 height 375px `box-shadow` 無邊框、img `object-fit:cover` hover scale 1.03

**3. 實作 ✅**
- `index.html`：`bc-series-hero` = `h2.bc-series-heading`（BETWEEN/SERIES）+ `div.bc-series-scrolling > .bc-series-list > 6 × .bc-series-slide > .bc-series-picture > img`（無卡片文字/無箭頭/pager）
- `bc-series.css`：hero `height:100vh; flex column; align-items:flex-start`（標題左上 140px 白 + scrolling `margin-top:auto` 貼底全寬 `padding-left:15.46vw`）；`heading::before` blur(10px) `[data-blurred=true]` opacity 1；picture 280/374 375px 無邊框柔陰影 hover scale 1.03；行動 50px + scroll-snap 69.33vw + picture 92.8vw
- `bc-series.js`：scrolling `scroll` 事件 → `scrollLeft>2` 切換 heading `data-blurred`

**4. 驗證 ✅**
- CDP 桌面 1280：標題 140px 左上（x0）、滑桿貼底（bottom gap 0）、scroll→data-blurred true + blurOpacity 1、pic 281×375 無邊框無背景、6 slides、無溢出
- CDP 行動 375：標題 50px、scrolling 全寬 scroll-snap x mandatory、slide 69vw（261px）、無邊框無背景、無溢出
- `manage.py check` 0 issues、bc-series.js 語法 OK

## 16. 首頁 BETWEEN SERIES 橫向滑動系列（參考 designing.jp/series）🎠 — ✅ 2026-08-16

### 已完成

**1. 需求 ✅**
- 參考 https://designing.jp/series/ 的 `container_3HNAz`（桌面 fixed 100vh 橫向滑動系列 + 行動 scroll-snap），以**普通區塊**整合到 index.html home-slider 之後

**2. 修改 ✅**
- `index.html`：`.bc-series-hero`（home-slider 後、bc-welcome 前）——大標題「Between / Series」（Playfair 6rem 兩行垂直）+ 6 系列卡片（咖啡豆/手沖/冷萃/季節限定/特調/烘焙 + 英文 Beans/Pour Over/Cold Brew/Seasonal/Signature/Roasting，用既有去背圖）+ 桌面箭頭/pager
- `bc-series.css`（新建）：黑底 + 背景 SVG 裝飾（opacity .05）、標題、卡片 hover 上移 + 金邊、圓形金箭頭、分頁點、≤767.98 行動 scroll-snap（stage overflow-x auto + `scroll-snap-type:x mandatory`、slide 72vw、pager/箭頭隱藏）
- `bc-series.js`（新建）：桌面 `--bc-series-x`（translateX 步進 326px）+ 箭頭/pager 點擊 + resize 防抖重算；行動原生捲動（transform none）

**3. 驗證 ✅**
- CDP 桌面 1280：標題 96px、6 slides、箭頭點擊 → transform `translateX(-326px)`、pager 5 dots flex、無溢出
- CDP 行動 375：stage `overflow-x:auto` + `scroll-snap x mandatory`、slide 72vw（270px）、pager/箭頭 `display:none`、transform none（原生捲動）、無溢出
- `manage.py check` 0 issues、bc-series.js 語法 OK

## 15. 首頁輪播第 3 格整合 magasinn 風格動畫區塊 🎠 — ✅ 2026-08-16

### 已完成

**1. 需求 ✅**
- 參考 https://magasinn.xyz/ `top-main-sec-logo-inner`（logo 動畫文字 + catch + 圖片輪播），整合到 index.html home-slider 第 3 個橫幅；**保留咖啡機影片背景**，內容層整個替換

**2. 修改 ✅**
- `index.html`：第 3 橫幅 `.bc-slider3-magasin` —— logo 動畫文字「A Craft Roastery」+ catch「Brewed / With / Soul」+ 6 張咖啡去背圖輪播（coffee_01~05/08.png）；**修正 magasinn 未閉合 span 語法**；響應式 hidden-sp/pc（行動「Cra─金色線─ft」跨行）
- `bc-magasin.css`（新建）：anime-elm/fade-up + delay1-22、文字工具類（of-hid/block/hidden-pc/sp）、品牌樣式（Playfair 3.2rem logo、金色線 --bc-gold、圖片輪播 260px）、≤767.98 響應
- `main.js`：`translated.owl.carousel`（active 更新後）+ `setTimeout(0)` 觸發 `.is-anime`（滑走移除→回來重播）；`.js-bc-magasin-slider` owlCarousel 初始化（loop/autoplay 3s/6 dots）

**3. 驗證 ✅**
- CDP 桌面 1280：logo「A CRAFT ROASTERY」、hidden-pc 隱藏、動畫 opacity 1、6 dots、無溢出
- CDP 行動 375：logo「A CRA─線─FT ROASTERY」跨行、金色線顯示、動畫 8 元素 opacity 1、無溢出
- `manage.py check` 0 issues、main.js 語法 OK

**4. 排除問題 ✅**
- `trigger('to.owl.carousel')` 不觸發 changed（測試方法差異）；改用實例 API `data('owl.carousel').to()` 與 `translated` 事件 + setTimeout(0) 保險時序

## 14. 首頁 bc-search lead SVG 文字圖 → CSS 小文本 ✍️ — ✅ 2026-08-16

### 已完成

**1. 需求 ✅**
- 首頁 SALON/STORE SEARCH 區塊 `.bc-search-lead` 內 `bc_search_txt_pc.svg`（DEMI DO 白色 SVG 字形文字圖）改為 CSS 小文本並刪除 SVG

**2. 文字與修改 ✅**
- 文字：「隱藏在工廠區只有百餘呎的咖啡店，每位員工必須先從自己開始了解咖啡，讓 {BETWEEN} 連接深愛著咖啡的人需求與喜好。」（`BETWEEN` 用 `.bc-search-lead-brand` 金色強調）
- `index.html`：移除 `<picture>`（pc/sp 兩 SVG）→ `.bc-search-lead` 文本；css 版本 bump `?v=20260816a`
- `bc-search.css`：`.bc-search-lead` 改文字樣式（Noto Sans TC、0.8rem、line-height 1.9、`rgba(255,255,255,0.72)`、320px）+ 響應式（≤768：0.9rem/寬 100%、≤575：0.85rem）
- `git rm static/images/bc_search_txt_pc.svg bc_search_txt_sp.svg`（兩檔刪除、無殘留引用）

**3. 驗證 ✅**
- CDP 實測：文本顯示、BETWEEN 金色 span、無 img 破圖、無水平溢出（width 187、font-size 12.6px）
- `manage.py check` 0 issues

## 13. profile 頁新增登出按鈕 🔒 — ✅ 2026-08-16

### 已完成

**1. 需求 ✅**
- `/profile/` 個人資料頁底部操作區（刪除帳戶旁）新增「登出」按鈕

**2. 修改 ✅**
- `socialuser/urls.py`：`path("logout/", LogoutView.as_view(next_page="index"), name="logout")`（Django 內建，POST + CSRF）
- `profile.html`：底部操作區新增登出 form（`onsubmit` 確認對話框）+ `.profile-logout-btn`（profile.css 金色系：`#c49b63` 邊框/字、hover 金底白字，與紅色 `.profile-delete-btn` 區分）

**3. 驗證 ✅**
- profile 頁含登出按鈕 + `action=/profile/logout/`；POST logout → 302 redirect `/`（index）；登出後訪 profile → 302 `/accounts/login/?next=/profile/`
- `manage.py check` 0 issues

## 12. coffee 自訂選項組功能（16 組）+ Admin 排序/UI 合併 + 顯示修復 🛠 — ✅ 2026-08-15

### 已完成

**1. 需求 ✅**
- 每種咖啡詳情頁依 Admin 設定顯示可自訂選項組（杯量/濃度/奶量/奶類/焦糖/黃油/椰奶/香草/特調/烏龍/茉莉/抹茶/綠茶/焙茶/面層配料/配豆 = **16 組**），供客戶選擇；Admin 可啟用/關閉各組並自由排序；訂單/購物車/員工端依排序顯示選項

**2. 後端/模型 ✅**
- `eshop/models/option_definitions.py`：16 組定義（key/label/icon/default/choices；杯量 choices 3 元素含 oz meta）
- `CoffeeItem`：+16 `option_*` 啟用開關（杯量/濃度 default=True 全咖啡顯示）+ 16 `option_order_*` 排序數字（0=預設）
- `CartItem.options_json` JSONField；**Migrations 0058-0063**（每支手動移除誤含 pickup_time）
- `sort_option_keys_for_coffee` helper：數字小在前、0=預設順序，統一 add_to_cart / cart_count / `_add_chinese_options`（修正 PostgreSQL jsonb 重排 dict 順序問題）

**3. 資料流 ✅**
- add_to_cart 收集 `option_<key>` → `extra_options`（依咖啡排序）→ cart key 含選項 → CartItem.options_json 同步 → 訂單 items.extra_options → `translate_option`（相容 3 元素 choices）→ 各顯示端（order_confirm/checkout/fps/cash/order_history/滑出購物車/員工端 renderers）
- `_get_last_order_link` 復購 query 含全部 option_ 預選

**4. Admin ✅**
- 自訂選項組 + 排序 UI **合併**：`OptionGroupConfigWidget`/`OptionGroupsConfigForm` 每組一行「勾選啟用 + 排序數字」（`option-group-config-grid`）；後去除白色背景、邊框改深灰 #555
- 原 JSON 陣列排序 → 16 個數字欄位（option_order_*）

**5. 顯示修復 ✅**
- order_confirm/checkout：移除 legacy fallback 硬編碼（杯量「中」/濃度「預設」/奶量「正常」假值）→ 有 extra_options 只顯示新選項，否則才 legacy（值存在時）
- `_add_chinese_options`：有選項時 pop legacy 欄位（舊訂單無選項保留 legacy）

**6. 驗證 ✅**
- 6 腳本全 PASS：`verify_all_options`（31 項：定義/渲染/資料流/各顯示端）+ cup_strength/bean_blend/milk_level/option_display/group_order
- `manage.py check` 0 issues；Black Blend 實測：無重複 + 依排序（配豆→杯量→濃度）

**7. 詳情頁復購預選單選修復 ✅**
- 問題：首頁 bc-welcome-panel 復購連結帶 `?option_<key>=<val>` → 詳情頁同一選項組多個按鈕同時已選（杯量「正常」+「追加」）
- 根因：coffee.html preselect JS 只對匹配按鈕 `classList.add('active')`，未清除同組其他按鈕 → 與靜態 default active 疊加
- 修復：改 `toggle('active', 是否匹配)`（與 bean.html 一致）；CDP 實測帶 query / 無 query 每組皆**恰 1 個 active** 且值正確

**8. 員工端等待中卡片選項修復 ✅**
- 問題：staff-management「等待中」標籤卡片咖啡自訂選項不顯示（杯量/濃度/配豆）；咖啡豆研磨/重量正常
- 根因：`queue-manager.js renderWaitingOrderItems`（waiting 專用舊版 UI）選項字串缺 `extra_options_cn` 迴圈（v2 renderers 皆有）
- 修復：補 `Object.entries(item.extra_options_cn||{})` 迴圈（含 icons/labels）+ 重量 `weight_cn` 優先（200克）；CDP 實測含杯量/配豆/濃度 + Kenya 研磨:中/重量:200克；node --check 語法 OK

## 11. bean_menu 桌面端咖啡豆產品照片加大 🎨 — ✅ 2026-08-15

### 已完成

**1. 需求 ✅**
- `localhost:8081/bean_menu/` 桌面端咖啡豆產品照片尺寸加大（僅 bean_menu；coffee_menu 共用 `.bean-mix-*` 不受影響）

**2. 修改（bean_menu.html 頁面級 style，純 CSS）✅**
- `@media screen and (min-width: 1080px)`：大卡 `.bean-mix-main .menu-wrap .menu-img img` **340→400px**、小卡 `.bean-mix-sub .menu-wrap .menu-img img` **280→320px**（皆 `!important` 覆蓋 bc-components 共用規則）

**3. 驗證（CDP 1280px）✅**
- bean_menu：大卡圖 **400px**、小卡圖 **320px**（組 1 小卡欄寬僅 286px 受 `max-width:100%` 物理限制顯示 286，組 2 flip 欄較寬完整 320）
- coffee_menu 對照：維持 340/280 完全不受影響
- 無水平溢出（scrollW 1265 < innerW 1280）

## 10. 全模板 HTML 結構/語法檢查 + 修正 + 冗餘清除 🧹 — ✅ 2026-08-14

### 已完成

**1. 檢查（59 個模板）✅**
- Django 引擎 `get_template()` 載入：55 成功、**0 TemplateSyntaxError**（4 個 restaurant 載入失敗因 app 已移除）
- 自訂 html.parser 堆疊檢查全模板 HTML 結構；關鍵交叉巢狀案例用 headless Chromium 實測真實 DOM
- 掃描全部 view/url/include/extends 建立「模板 ↔ 引用」對照，找出孤兒與損壞引用

**2. 修正 8 項結構錯誤 ✅**
- `coffee.html` / `bean.html`：breadcrumbs `<p><span><a>` 缺 `</span>` → 補閉合
- `base.html`：Material Icons link **重複 rel 屬性** → 移除
- `fps_payment.html`：商戶名稱多餘 `</b>` → 移除
- `order_confirm.html`：**`<form>` 交叉巢狀**（form 開於 col-xl-7 內、閉於 sidebar 後，實測 `#payment-button` 真實 DOM 在 `#payment-form` 外）→ form/`</form>` 移至 row 內包住兩欄；渲染驗證 `buttonInsideForm=true`
- `index.html` / `landing_v3.html`：SVG `<clipPath>`/`<path>` 未閉合 → 補 `/>` + `</clipPath>`
- `profile.html`：缺 1 個 `</div>`（container 未閉合）→ 補
- `order_history.html`：缺 2 個 `</div>`（row+container 未閉合）→ 補

**3. 修復損壞引用（view 渲染但模板不存在）✅**
- 補建 `socialuser/reactivate.html`（/profile/reactivate/ 原 500）
- 補建 `socialuser/activity_history.html`、`socialuser/points_summary.html`（/profile/loyalty/activities/ 與 points-summary/ 原 500；已確認 URL 有接線，非死 view）

**4. 刪除 15 個孤兒/死檔模板（git rm）✅**
- `index_backup.html`、`landing_new.html`、`landing_v2.html`（LandingNew 實際渲染 landing_v3）
- `layouts/rightcorner_menu.html`（僅註解引用）、`layouts/box.html`、`layouts/content.html`
- `admin/websocket_monitor.html`、`cart/templates/cart/cart_detail.html`（cart_detail view 渲染 checkout.html）
- `eshop/.../queue_dashboard.html`、`queue_statistics.html`、`customer_queue_status.html`
- `restaurant/templates/` 全部 4 個（app 已自 INSTALLED_APPS 移除）

**5. 冗餘區塊/死碼清除 ✅**
- `index.html` / `landing_v3.html` 重複 `noise-filiter` SVG（base 全域已有，DOM 重複 id noise-0~9）→ 移除子頁面副本（CDP 驗證首頁 noise-filiter 2→1）
- `order_confirm.html` debug 隱藏欄位去重（debug_session_key/debug_user 各兩份 → 一份）
- `coffee_menu.html` / `bean_menu.html` 卡片 `<form method=post>{% csrf_token %}<a>落單</a></form>`（永不 submit）→ 改 `<div class=pt-2>` 包 anchor
- `nav.html` 清理 hidden 死碼（HOME/Shop/US/user dropdown，共 -53 行）；保留 `#bc-cart-toggle`（JS 有引用）
- `base.html` 移除註解掉的 rightcorner_menu include

**6. 驗證 ✅**
- `get_template` 全部 **47/47 成功**；html.parser 結構檢查歸零（僅餘 bean_menu/coffee_menu 條件式 group div 的靜態誤判）
- `manage.py check` 0 issues
- HTTP 全頁 200：`/` `/coffee_menu/` `/bean_menu/` `/coffee/1/` `/bean/1/` `/about/` `/accounts/login/` `/profile/` `/profile/reactivate/` `/profile/loyalty/dashboard|activities|points-summary/`
- CDP 實測：order_confirm `#payment-button` 在 `#payment-form` 內 ✓；首頁 noise-filiter 1、nav 1 item、cart-toggle 正常；coffee_menu 落單按鈕 8 個正常；coffee/1 breadcrumbs span 閉合；全無水平溢出

**7. 追加修正：order_confirm 佈局回歸（2026-08-14 使用者回報）✅**
- 問題：A5 把 `<form>` 包住 `.row` 的兩欄 → 破壞 Bootstrap flex（col-xl-7/col-xl-5 不再是 row 直接子元素）→ 左欄（支付方式/聯絡電話）寬度縮小、右欄 sidebar 位移到左下方、選項圖示排列錯亂
- 修正：還原 `<form>` 至 `.col-xl-7` 內 + `</form>` 移回 col-xl-7 閉合前；sidebar 的 `#payment-button` 改用 HTML5 `form="payment-form"` 屬性關聯（維持「button 能提交」的 A5 目的，不需 DOM 巢狀）
- 驗證（CDP 1280px，登入 user kei + 購物車 2 項）：col-xl-7/col-xl-5 皆為 `row` 直接子元素、寬度比例 **58% / 42%**、sidebar 右側同行、`btn.form.id === 'payment-form'`、圖示順序正確（咖啡 water_full/bolt/humidity_mid、豆 roller_shades/scale）、無水平溢出

## 9. coffee 詳情頁杯量按鈕右上角 oz 標籤/文字加大 🎨 — ✅ 2026-08-14

### 已完成

**1. 需求 ✅**
- `localhost:8081/coffee/x/` 杯量按鈕右上角盎司標籤（`.bc-option-oz` 金色 chip）與盎司文字「相應加大」，含每個響應狀態處理

**2. 修改（純 CSS，不動 HTML/JS）✅**
- **桌面/平板（≥768px）**：`bc-components.css` 基底 `.bc-option-oz` font-size **0.72rem→0.85rem**（1280px ≈ 13.6px）、padding **3px6px→4px8px**（chip 22px 高）；coffee.html inline `<style>` `#cup-level-group .bc-option-oz` 同步 0.85rem/4px8px（inline !important 為桌面實際生效值）
- **行動端（≤767.98px）**：`.product-details #cup-level-group .bc-option-oz` font-size **8px→11px** + padding **3px6px !important**（(1,2,0)!important 勝過 inline (1,1,0)!important；行動按鈕 44px 高比例縮小）
- `base.html` → `bc-components.css?v=20260814w → v=20260814x`
- 無需平板專屬規則：平板沿用桌面基底尺寸（按鈕同樣 72px 高），三態（桌面/平板/行動）皆「相應加大」

**3. 驗證（CDP 量測 1280/1024/768/375/320px，`docs/verify/cdp_verify_oz_label.py`）✅**
- 1280px：oz **13.6px**、padding 4/8、chip 48×22（btn 210×72）、右上角貼齊、無溢出（scrollWidth 1265 < 1280）
- 1024/768px：oz **13.6px / 13.43px**（rem×html clamp）、chip 在按鈕內、無溢出
- 375px：oz **11px**、padding 3/6、chip 39×17（btn 117×44）、右上角貼齊、無溢出（375=375）
- 320px：oz **11px**、chip 39×17（btn 89×44）、右上角貼齊、無溢出（320=320）
- 全斷點 `chipInsideBtn=true`、`chipAtTopRight=true`、`docScrollWidth≤innerWidth`

## 0. .cart-popup 響應式設計修復（bean/coffee 詳情頁加入購物車 Toast）🎨 — ✅ 2026-08-14

### 已完成

**1. 問題診斷（CDP 量測 320~1280px × bean/coffee）✅**
- **只有容器寬度一層響應式**：唯一規則為 `@media ≤575.98px`（min-width:0 + width:92vw），內部元素零響應式
- 🔴 手機 320/375px：商品資訊區（`.popup-product-info` max-width:260px + flex-shrink:0）溢出被 `overflow:hidden` 裁切 → **名稱截斷、價格/數量完全看不見**（375px 時名稱 263~395 超出 popup 右邊 360、價格 401~431、數量 437~457 整個被裁掉）
- 🔴 **576~599.98px 斷層**：media 只覆蓋 ≤575.98，576px 起回到 min-width:600px → 576px 視窗時 popup 600px 超出視窗左邊 12px（2026-08-08 修復留下的斷層）
- 🟠 `.popup-product-price` 完全無 CSS 樣式

**2. 修復（style-utilities.css，純 CSS 不改 HTML/JS）✅**
- **全寬範圍 575.98 → 991.98px**：消除 576~599.98 斷層
- **平板級內層響應式（≤991.98px，追加）**：576~991.98 原維持桌面尺寸塞進 92vw → 新增縮小（padding 12/20、gap 12、字體 14/18/14、icon 40、img 40、按鈕 14）→ popup 高度 88→65px
- **新增 ≤575.98px 手機級內層響應式**：
  - `.popup-left/.popup-right` padding 12/14→10/12、gap 8px
  - `.popup-product-info` 改 `flex:1; min-width:0; max-width:none`（關鍵：讓名稱 ellipsis 生效）
  - `.popup-product-img` `display:none !important`（showPopup JS 會設 inline display:inline，需 !important 覆蓋；手機隱藏裝飾性商品圖，把空間留給名稱）
  - 字體：名稱/價格/數量 12px、總金額 15px、按鈕 12px、icon 34px、badge 18px
- **補上 `.popup-product-price` base 樣式**（color #fff / 15px / 600 / nowrap / flex-shrink:0，原本完全無樣式）
- `base.html` → `style-utilities.css?v=20260814b`

**3. 驗證（CDP 量測 320~1280px × bean/coffee，全測量點通過）✅**
- **全斷點無 CHILD-OVERFLOW / 無 POPUP-OUT-VIEW / 無 DOC-OVERFLOW**
- **三層級和諧遞進**：手機 popup 63→**56px**（字體 12/15/12）、平板 88→**65px**（字體 14/18/14、img 40、768px 543px 居中不再桌面尺寸）、桌面維持 88px/650px
- 手機名稱空間更大：375px **88px**（約 7 字）、320px 37px；**價格/數量完整可見**（修復前完全看不見）
- **576~599.98px 斷層消除**（576px popup 530px [23~553]，不再 600px 突出視窗）
- 1280px 完全無回歸

## 1. coffee_menu / bean_menu 平板端保留不對稱網格 🎨 — ✅ 2026-08-14

### 已完成

**1. 問題診斷（CDP 量測 768~1280px）✅**
- 平板（768~1079.98px）`.bean-mix-*` 原降級為**對稱 2 欄**：大卡整行全寬（768px 時 672px）+ 兩小卡並排（320px）→ 失去桌面不對稱瀑布感（使用者要求平板仍用不對稱網格）

**2. 修復（bc-components.css，純 CSS）✅**
- `≤1079.98px` media 改為**不對稱瀑布**：`grid-template-columns: 2fr 1fr`、大卡跨 2 行（`grid-row: 1/3` + 內容垂直置中）、兩小卡上下排（grid-row 1/2）
- flip 組鏡像：`.bean-mix-flip { grid-template-columns: 1fr 2fr }` + 大卡 col2 / 小卡 col1（原 flip 大卡落 1fr 小欄反了）
- 圖片縮小 **`!important`**（覆蓋桌面 340/280 的 !important）：大卡 `min(280px,100%)`、小卡 `min(200px,100%)`
- 錯落取消（平板空間有限）；coffee-mix-grid 向上錯落另有規則覆蓋
- `base.html` → `bc-components.css?v=20260814a`

**3. 驗證（CDP 量測 768/820/900/1024/1079/1080/1280 × 兩頁）✅**
- 平板全斷點：大卡 432px（1024 592px）+ 小卡 216px（296px）= **2:1 不對稱**、flip 鏡像正確、小卡上下排、**無水平溢出**
- 圖片 280/200（平板縮小生效）；桌面 1080/1280 維持 340/280 完全無回歸
- 視覺確認（CDP 截圖 768）：大卡左側主視覺 + 小卡右側上下排瀑布

## 2. bean/coffee 詳情頁一般文字統一 #ccc + 建立 --bc-text-ccc 變數 🎨 — ✅ 2026-08-14

### 已完成

**1. 診斷（CDP 掃描詳情區文字顏色）✅**
- 詳情頁文字原有 **8+ 種顏色**：商品名 #eee、描述/標籤 #adadad、圖示 rgb(108,108,108)、內容 rgba(255,255,255,0.7)、烘焙選項 #666、表單標籤 #aaa、價格 #f8b500 橘黃、active 金 #c49b63 等
- 使用者要求：一般文字統一 #ccc + 建立變數；**品牌金（價格、active 狀態）保留**；咖啡/咖啡豆圖片顏色不更動

**2. 修復（bc-components.css，純 CSS）✅**
- `:root` 新增 **`--bc-text-ccc: #ccc`** 變數（供後續引用）
- 新增「詳情頁一般文字統一」區塊，全部設 `color: var(--bc-text-ccc)`：
  - 商品名稱 `.coffee-title/.bean-title`（含內層 span——被 style-bootstrap `.product-details span{color:#eee}` 覆寫需同級覆蓋）
  - 描述 `.block-23 p.pb-2`、標籤 `.block-23 ul li span.text`、內容值 `.pl-3`、資訊圖示 `.icon`
  - 烘焙水平選項 `.roastrange-item span:not(.bc-roast-active)`（active 排除保留金）
  - 表單標籤 `.form-group p`（淨量/研磨/數量/杯量/奶量/濃度）、數量輸入框 `.input-number`
- **保留品牌金**：價格橘黃、選項按鈕（含 non-active 金/active 金底白字）、烘焙 active 金色、按鈕、oz 標籤
- `base.html` → `bc-components.css?v=20260814c`

**3. 驗證（CDP 掃描 bean/8 + coffee/8）✅**
- bean 詳情區 **19 個一般文字全部 #ccc**（含商品名 inner span）、coffee 14 個
- 金色 8/7 個（烘焙 active、選項按鈕、active oz）保留、價格橘黃保留
- 剩餘 #eee 僅 non-active 選項按鈕內元素（既有狀態，屬保留範圍）

## 3. coffee_menu / bean_menu 行動端「大卡/小卡並排瀑布」佈局 🎨 — ✅ 2026-08-14

### 已完成

**1. 需求演進（使用者指定）✅**
- 行動端（≤767.98px）原本單欄堆疊 → 第一輪 2 欄等大 + 錯落 + 隱藏描述 → 第二輪「大卡全寬橫幅 + 小卡並排」→ **第三輪改為「大卡/小卡相同並排、大卡不需全寬、像桌面端處理方法」**
- 最終：採用與平板/桌面相同的不對稱瀑布（大卡 2fr 跨 2 行 + 小卡 1fr 上下排、組間 flip 鏡像）

**2. 修復（bc-components.css，純 CSS）✅**
- 改寫 ≤767.98px 手機規則：
  - **大卡 2fr 跨 2 行**（`grid-column: 1`、`grid-row: 1/3`、內容垂直置中）+ **兩小卡 1fr 上下排**（grid-row 1/2）
  - **組間 flip 鏡像**：`.bean-mix-flip { grid-template-columns: 1fr 2fr }` + 大卡 col2 / 小卡 col1（與桌面相同）
  - **第二小卡 `translateY(1rem)` 微錯落**（`!important` 覆蓋 `.coffee-mix-grid` transform:none）
  - 尺寸縮小：大卡圖 `min(200px,100%) !important`、小卡圖 `min(130px,100%) !important`、小卡名稱/價格 12px、按鈕 11px
  - 描述 `.bean-mix-group .coffee-menu-desc { display: none }`（保留）
- **第四輪平衡調整（2026-08-14）✅**：
  - **比例 2fr 1fr → `1.5fr 1fr`**（flip 對應 `1fr 1.5fr`）→ 小卡加大、大卡縮小（375px：大 208→**187**、小 104→**125**，比例 2:1→1.5:1 更平衡）
  - 大卡圖 `min(200px→180px,100%)`
  - **名稱/價格統一縮小**：名稱 19.4→**13px**、價格 15→**12px**（大卡+小卡；高 specificity `.bean-mix-grid .bean-mix-group ...` (0,5,1) 覆蓋「卡片文字加大」區塊 (0,4,1)）
- **第五輪按鈕統一 + 錯落加大（2026-08-14）✅**：
  - **大小卡按鈕固定相同寬度**：統一 `width: 96px`、字體 12px、padding 6px 12px（大卡+小卡一致）
  - **佈局錯落加大**：第二小卡 `translateY(1rem → 2rem) !important`（下移 32px，階梯感更明顯）
  - **按鈕居中修復**：按鈕 `display:block` 不受 `text-align:center` 影響 → 靠左偏移（大卡偏 45px）；加 **`margin: 0 auto`** 強制水平居中 → CDP 驗證 btnCx=cardCx（375px 大卡 257=257、小卡 86=86，btnL=btnR 完全對稱）
- **第六輪平衡微調（2026-08-14）✅**：
  - **大卡照片縮小**：`min(180px → 150px, 100%)`（375px 大卡圖 180→150）
  - **大小卡間距縮小**：gap `1rem → 0.5rem`（16px→8px，更緊湊）
- **第七輪平衡微調（2026-08-14）✅**：
  - **大小卡照片再次縮小**：大卡 `min(150→130px)`、小卡 `min(130→110px)`（375px 大卡圖 130、小卡圖 110）
  - **間距再次縮小**：gap `0.5rem → 0.25rem`（8px→4px）
- **第八輪：三端錯落距離加大（2026-08-14）✅**：
  - 行動端：sub2 `translateY(2rem→3rem) !important`（29→44px）
  - 平板：sub2 `transform:none → translateY(2rem) !important`（0→32px，覆蓋 coffee-mix-grid ≤1079.98 none）
  - 桌面：bean `4rem→5rem`（64→80px）、coffee `-6rem→-7rem`（-96→-112px）
- **第九輪：同行橫向大小卡內容錯落加大（2026-08-14）✅**：
  - 小卡1 內容 `margin-top`：行動端 **12px**、平板/桌面 **24px**（`.bean-mix-main + .bean-mix-sub .menu-wrap`，只命中小卡1，佈局內位移不重疊）
  - CDP 驗證：小卡1 圖片下移 12/24/24px、名稱下移同步
- `base.html` → `bc-components.css?v=20260814s`

**3. 驗證（CDP 量測 320~1280px × 兩頁）✅**
- 行動端：**大卡 1.5fr 並排**（375px 187px）、**小卡 1fr**（375px 125px）、flip 組間鏡像正確、小卡上下排、**名稱/價格 13/12px 全部縮小生效**、內容無溢出、無水平溢出
- 平板/桌面（768+）完全無回歸：大卡 432px+、描述顯示、佈局維持

## 4. 咖啡/咖啡豆 highlight 亮點標語（菜單卡片名稱下方）🎨 — ✅ 2026-08-14

### 已完成

**1. 需求 ✅**
- 添加咖啡/咖啡豆 highlight 中文亮點文本（12-15 字），顯示在 coffee_menu / bean_menu 卡片**名稱下方**

**2. 實作 ✅**
- **模型**：`CoffeeItem`/`BeanItem` 加 `highlight = CharField(max_length=100, blank=True, verbose_name="亮點標語")` + **Migration 0057**（移除誤含的 ordermodel.pickup_time——DB 已存在，屬既有 model/migration 不同步）
- **文案**：8 咖啡 + 6 咖啡豆依商品特性填寫 12-15 字中文（shell 依 name 更新；如 Black Blend「黑金拼配，醇厚風味日夜相伴」、Sumatra Kerinci「蘇門答臘醇厚，草本香料大地風味」）
- **Admin**：CoffeeItemAdmin/BeanItemAdmin 的 list_display、search_fields、fieldsets 加 highlight
- **模板**：名稱 `<h5>` 下方加 `<p class="bc-menu-highlight">{{ coffee/bean.highlight }}</p>`（coffee_menu + bean_menu）
- **CSS**：`.bc-menu-highlight` 品牌金 12px（行動端 11px）；需覆蓋 style-bootstrap `.menu-wrap p`（16px/#ccc/-webkit-box line-clamp 截斷）→ 用 `.menu-wrap` 前綴 specificity (0,2,0)>(0,1,1) + 覆寫 display/line-clamp
- `base.html` → `bc-components.css?v=20260814k`

**3. 驗證（test client + CDP）✅**
- test client：coffee_menu 8 highlight、bean_menu 6、status 200
- CDP 320~1280px：**belowName=True（名稱下方）**、顏色**品牌金 #c49b63**、字體行動端 11/桌面 12px、文字無截斷、無水平溢出

**4. 單行顯示 + 響應式字體修正（2026-08-14 追加）✅**
- **重新建立精簡文案**：12-15 字 → **8-9 字**（行動端窄卡單行可完整顯示；如 Black Blend「黑金拼配，醇厚相伴」、Sumatra「蘇門答臘，草本大地」）
- **CSS 單行**：`.bc-menu-highlight` 加 `white-space: nowrap; overflow: hidden; text-overflow: ellipsis` → 全斷點 **lines=1**（原 320/375 小卡 2 行）
- **三級響應式字體**：行動端 ≤767.98 **11px**、平板 768~1199 **16px**、桌面 ≥1200 **18px** + **font-weight 500**（原 600 → 500，使用者指定；平板/桌面字體 12/13→14/15→16/18 逐輪加大）
- `base.html` → `bc-components.css?v=20260814o`

## 5. 詳情頁隱藏右側 Buy & Order 按鈕 🎨 — ✅ 2026-08-14

### 已完成

- **需求**：bean/coffee 詳情頁無需顯示右側懸浮按鈕（Buy & Order）；**保留**懸浮購物車按鈕與右側虛線（使用者指定）
- **實作**：`bean.html` / `coffee.html` `{% block content %}` 加頁面級 style：
  ```css
  .bc-attract-nav { display: none !important; }
  ```
  （與 order_confirm 等流程頁一致，但不隱藏 `.bc-floating-cart` 與 `#borders`）
- **驗證（CDP 375/1280px）✅**：詳情頁 Buy & Order=`none`、虛線=`block`（保留）、浮動購物車保留（購物車有商品時 JS 顯示）；coffee_menu 對照 `flex` 正常、其他頁面不受影響

## 6. 首頁 .mid-banner 響應式 🎨 — ✅ 2026-08-14

### 已完成

- **問題**：`.mid-banner` 全固定值（min-height 620px / span 48px / lg_message 6em=84px）**完全無響應式**——手機也 620px 高、84px 文字，375px 時寬度 **423px 超出視窗**
- **修復**（style-custom.css 新增三級響應式）：
  - **手機 ≤575.98**：min-height **300px**、span **28px**、lg_message **2.6em**（36px）、padding 16px
  - **平板 576~991.98**：min-height **460px**、span **40px**、lg_message **4.5em**（63px）
  - **桌面 ≥992**：維持 620px / 48px / 6em
  - 全部加 `max-width: 100%`（修正 423px 溢出）
- `base.html` → `style-custom.css?v=20260814a`
- **驗證（CDP 320~1280px）✅**：320px 寬 242（原 423 不再溢出）、高 300；平板 460/40/63；桌面無回歸；全斷點 hScroll=False
- **行距加大（追加）✅**：`.lg_message` line-height **0.8 → 1.15**（手機 29→42px、桌面 67→97px）；高度自動撐高（320px 371、1280px 631）、無溢出；`style-custom.css?v=20260814b`

## 7. 菜單頁隱藏右側 Buy & Order 按鈕 🎨 — ✅ 2026-08-14

### 已完成

- **需求**：bean_menu / coffee_menu 無需顯示右側 Buy & Order 按鈕（coffee_menu 上自指冗餘、bean_menu 上 nav 可替代）；保留懸浮購物車與右側虛線
- **實作**：`bean_menu.html` / `coffee_menu.html` 頁面級 style `.bc-attract-nav { display: none !important }`（與詳情頁一致）
- **驗證（CDP 375/1280px）✅**：兩頁 Buy & Order=`none`、虛線=`block`（保留）、浮動購物車保留；詳情頁維持

## 8. 浮動購物車初始載入靜默顯示（修正每次跳轉彈出）🛠 — ✅ 2026-08-14

### 已完成

- **問題**：購物車有商品時，每次從一頁跳到另一頁，浮動購物車都滑入彈出一次（`bcFloatingIn` 0.4s）→ 視覺幹擾
- **根因**：`_syncBadgeFromServer` 被呼叫**兩次**（constructor 直接 + `_initFloatingCartScrollListener` rAF），第二次 `_updateBadge` 把 `_initialBadgeSync` 設 false → `_showFloatingCart(true)` 移除 `no-anim` → 動畫觸發
- **修復**：
  - JS `_showFloatingCart(animated)`、`_updateFloatingCartVisibility(count, animated)`、`_updateBadge(count, animated)` 傳參；`animated=false` 時加 `.no-anim`（禁動畫）
  - `_initialBadgeSync` 延遲 **500ms** 切換 false（確保 constructor + rAF 兩次初始同步皆靜默）
  - CSS `.bc-floating-cart.no-anim.show { animation: none }`
  - `base.html` → `bc-components.css?v=20260814u`、`bc-slideout-cart.js?v=20260814b`
- **驗證（CDP，真實 session 有商品）✅**：coffee_menu/bean_menu/bean 詳情頁載入 → `no-anim` + `animation:none`（靜默）、badge=1；加入購物車路徑維持動畫

**9. 完全移除滑入動畫 + 伺服器端初始渲染（2026-08-14 追加）✅**
- **需求**：加入購物車時的滑入動畫也是視覺幹擾 → 完全移除；數量增減維持顯示；切換頁面不閃出（維持顯示）
- **修復**：
  - CSS：`.bc-floating-cart.show/hide` 改 `animation: none`（移除 bcFloatingIn/Out，含加入購物車）
  - base.html：浮動購物車**伺服器端渲染**——`{% if not cart_count %}display:none{% endif %}` + badge `{{ cart_count }}`（複用 cart context processor）→ 有商品時頁面載入即顯示，無「延遲出現」閃出
- **驗證（CDP）✅**：無商品 display=none；有商品兩頁載入 display=block+animation=none（初始即顯示）；模擬加入後 animation=none

**10. 數量徽章文字閃爍修復（2026-08-14 追加）✅**
- **問題**：浮動購物車數量徽章內文字會閃爍
- **根因**：徽章文字用 webfont（Noto Sans TC）→ 字體載入延遲/交換（FOUT）造成文字閃爍；`_updateBadge` 相同值仍重設 textContent 觸發重繪
- **修復**：
  - CSS `.bc-floating-cart-badge` 加 `font-family: Arial, Helvetica, sans-serif`（數字用系統字體立即渲染，無 FOUT）
  - JS `_updateBadge` 值相同不重設 textContent（避免重繪閃爍）
  - `bc-components.css?v=20260814w`、`bc-slideout-cart.js?v=20260814c`
- **驗證（CDP）✅**：徽章 font=Arial、animation=none；`_updateBadge(1)` 正常

**11. 右側虛線加深灰色（2026-08-14 補記）✅**
- `#borders .bc-borders__right` 背景改 `rgba(128,128,128,0.6)`（原白 0.5）；`bc-attract.css?v=20260814a`

---

# 今日任務總覽 (2026-08-13)

## 0. 行動端訂單流程 UI 統一調整（order_confirm + order_payment_confirmation）🎨 — ✅ 2026-08-13

### 已完成

**1. 問題診斷（CDP 量測 375px）✅**
- **payment-confirmation**：
  - 🔴 狀態卡片被壓扁：CSS 強制 `width: calc(25% - 12px)` 全域生效 → 行動端每張僅 **62px 寬×189px 高**（3~4 張擠一行垂直條狀）
  - 🔴 二維碼溢出容器：`.bc-qr-img` 250px > 容器可用寬 209px
  - 🟠 提取碼 51px、標題 25.6px、支付 icon 44px、商品圖 98px 全偏大
  - 🟠 二維碼區 padding 44px（p-5=3rem）
- **order_confirm**：
  - 🟠 支付方式選項 55px 高、輸入框 52px 高
  - 🟠 「確認並支付」按鈕 238×49px 但字體僅 12px（比例失調，pr-8/pl-8=6rem 過寬）
  - 🟠 sidebar-box 摘要 padding 40px

**2. 統一方案（CSS 層，不改 HTML）✅**
- **`style-utilities.css`**：`.status-cards-container .row > [class*="col-"]` 行動端覆蓋 → **2 張一排**（calc(50% - 8px)），卡片 min-height 118px、icon 1.25rem、title 0.88rem、description 0.72rem、time 0.68rem
- **`bc-components.css`**：新增「訂單流程頁行動端統一調整」media 區塊（≤767.98px）：
  - payment-confirmation：標題 h3 1.5rem / h5 1rem、icon 2.25rem（!important 覆蓋行內 3rem）、二維碼容器 padding 1.5rem、`.bc-qr-img` 170px、提取碼 2.4rem、商品圖 72px、摘要 0.9rem、積分條 40px、返回首頁按鈕 width auto
  - order_confirm：輸入框 10px 14px、支付方式 11px 14px、icon 1.1rem、`確認並支付` 12px 28px、sidebar-box padding 24px 0 28px、小計/總計 h5 1rem
- `base.html` → `bc-components.css?v=20260813c`、`style-utilities.css?v=20260813a`

**3. 驗證（CDP 量測 375/1280px）✅**
- 狀態卡片 **62→141px**（2 張一排）、二維碼 250→170px（不再溢出）、提取碼 51→35.1px、標題 25.6→21.9px、icon 44→33px
- order_confirm：輸入框 52→46px、支付方式 55→48px、「確認並支付」238×49 fs=12.1 → **200×47 fs=13.9**（比例協調）、總計 18.3→14.6px、sidebar-box 40→24px
- 桌面 1280px 完全無回歸（media query 僅 ≤767.98px）


## 1. order_confirm 訂單詳情 accordion 結構與商品顯示修復 🛠 — ✅ 2026-08-13

### 已完成

**1. 問題診斷 ✅**
- 使用者回報「payment-confirmation 頁面」HTML 結構有問題，實際為 **order_confirm.html**（兩頁皆 /eshop/order/ 路徑易混淆）
- **寬度不一致**（CDP 量測 375px）：`.Rtable` 全域 `margin: 15px 15px 15px 0`（style-utilities.css）→ 訂單詳情區 312px（left 24）vs 表單區 col 297px（left 39）對不齊
- **商品未顯示**：訂單詳情 accordion 預設收合（aria=false + hiddenSmall）+ **responsiveTable 被初始化兩次**（order_confirm.html 內嵌 + main.js 全域），兩個 click handler 基於互相更新的 aria 值反向操作 → **點擊互相抵消，商品永遠隱藏**

**2. 修復（order_confirm.html + bc-components.css）✅**
- **HTML 初始展開**：`.Accordion` aria-selected `false→true`、`.Rtable-cell` 移除 `hiddenSmall` → 商品進頁面即顯示
- **移除重複 JS**：刪除 order_confirm.html 內嵌 `// table config //`（responsiveTable + ready），統一由 `main.js` 的 responsiveTable 處理（單一 handler，點擊正常）
- **移除重複 jQuery**：刪除 order_confirm.html 頂部 `jquery-3.6.0.min.js`（與 base.html 的 3.7.1 衝突，雙 jQuery 造成事件 registry 分裂）
- **容器對齊**（bc-components.css）：`.ftco-section-billing .hiddenLarge .js-RtableAccordions { margin: 0 15px; width: calc(100% - 30px) }` → 訂單詳情區與表單區 col **完全對齊**（297px / left 39 / right 336）
- `base.html` → `bc-components.css?v=20260813d`

**3. 驗證（CDP 375px）✅**
- 容器對齊：Rtable **297px（39~336）** = 表單 col **297px（39~336）** ✅
- 商品顯示：初始 `visibleItems=1` ✅；點擊1收合（aria=false, visible=0）✅；點擊2展開（aria=true, visible=1）✅
- 無水平溢出；payment-confirmation 頁面無 hiddenLarge（商品明細正常，`order.get_order_display_items`）
- 桌面 1280px 無回歸（hiddenLarge 於 ≥1200px 隱藏）


## 2. order_confirm 訂單詳情 accordion 視覺調整（文字/箭頭縮小對齊）🎨 — ✅ 2026-08-13

### 已完成
- **需求**：訂單詳情文字縮小、向下箭頭縮小、三者對齊到同一水平中心
- **實作**（`bc-components.css` `@media (max-width: 1198.98px)`）：`.Accordion` 改 `inline-flex + align-items:center`、文字 1rem→**0.9rem**、arrow 由 absolute 改 flex 子項縮小至 **13px**
- **驗證**（CDP 375/768px）：btn/arrow/price centerY 三者一致（112=112=112、164=164≈165）；1280px 桌面無影響

## 3. order_confirm 行動端商品未顯示 —— 最終排查與伺服器層防快取 🛠 — ✅ 2026-08-13

### 已完成
- **全面驗證**：Django test client（aria=true、無 hiddenSmall、商品兩處）+ CDP 多寬度掃描（320~1280px **全部商品顯示**）→ 伺服器端無 bug，問題為**瀏覽器快取舊版頁面**
- **伺服器層防快取**（`order_views.py`）：`OrderConfirm` 加 `@method_decorator(never_cache)`、`order_payment_confirmation` 加 `@never_cache` → 響應 `Cache-Control: no-cache, no-store, must-revalidate, private`
- **輔助**：`base.html` 加 no-cache meta、`main.js?v=20260813e` 版本更新

## 4. order_confirm 行動端訂單詳情折疊面板重新設計（預設關閉）🎨 — ✅ 2026-08-13

### 已完成
- **需求**：行動端重新加入購物車商品折疊面板；**預設關閉**、「訂單詳情」文字 + 向下箭頭點擊展開
- **實作**（全新 `.bc-order-collapse`，不沿用舊 Rtable/Accordion）：
  - `order_confirm.html`：折疊面板（`aria-expanded="false"` + 商品列表）+ **vanilla JS**（不依賴 jQuery）切換 aria；右欄恢復 `hiddenSmall`（<1200px 隱藏避免重複）
  - `bc-components.css`：`.bc-order-collapse` 系列（header flex 對齊、chevron 旋轉、body 由 `[aria-expanded="true"]` 控制、≥1200px 隱藏）
- **驗證**：375/768px 預設關閉→點擊展開→收合 ✅；1280px 折疊隱藏右欄顯示 ✅

## 5. 折疊面板寬度對齊修正（container > row > col-12）🔧 — ✅ 2026-08-13

### 已完成
- **問題**：折疊面板直接為 section 子元素（僅 margin 15px）→ 與表單 col（container 24px + col 15px）位置/寬度不同
- **實作**：`order_confirm.html` 折疊面板包入 `container > row > col-12`（與表單相同 gutter）；`.bc-order-collapse` margin `0 15px → 0`
- **驗證**：折疊面板與表單輸入框**同水平邊界**（left 39 / right 336 / w 297）✅

## 6. 移除折疊面板圓角容器樣式 🎨 — ✅ 2026-08-13

### 已完成
- 移除 `.bc-order-collapse` 的 `border`、`border-radius: 10px`、`background`、`overflow:hidden` → 簡潔無框列表樣式（保留 header hover 與 body border-top 分隔線）

## 7. 折疊面板 body 內容縮小（除照片）+ 行距縮小 🎨 — ✅ 2026-08-13

### 已完成
- **內容縮小**（`bc-components.css` 行動端區塊）：商品名 0.95→**0.88rem**、價格 1→**0.9rem**、選項 0.8→**0.72rem**、icon 0.9rem、數量徽章 0.6rem；**照片保持 70×70**
- **行距縮小**：line-height 1.2~1.3、商品間距 12→8px、body padding 20/14→12/8px、header 底部 20→12px、meta `padding-bottom 4px !important`（覆蓋 Bootstrap `.pb-2`）
- **響應式修正**：`.meta { flex-wrap: wrap }` → 320~360px 窄屏選項換行，不再溢出裁切

## 8. 圖示縮小 + 文字水平中心對齊 🎨 — ✅ 2026-08-13

### 已完成
- **問題**：meta 圖示 `padding-top:5px`（`.block-21 .icon`）造成字形偏下、且 icon 偏大
- **實作**：icon 0.9→**0.8rem**、`padding-top:0`、`.meta > div { display:flex; align-items:center }`
- **驗證**：icon 11.7px、icon/文字/行 centerY 完全一致 ✅

## 9. 支付方式 radio 縮小（桌面+行動端）🎨 — ✅ 2026-08-13

### 已完成
- 全域：circle 20→**16px**、dot 10→**8px**；行動端：circle 16→**14px**、dot 8→**7px**（後調整 dot→6px 修正 active 視覺居中）
- **驗證**：375px circle 14/dot 6、1280px circle 16/dot 8，dot center = circle center（offset 0,0）✅

## 10. 確認並支付 / 返回購物車按鈕行動端居中 🎨 — ✅ 2026-08-13

### 已完成
- **實作**：`.form-group { width:100% }` + 兩按鈕 `display:block; width:fit-content; margin:auto`
- **驗證**：兩按鈕 centerX = 頁面中心 188 ✅（內容寬度居中，非全寬）

## 11. 訂單詳情向下箭頭縮小 + 水平中心對齊 🎨 — ✅ 2026-08-13

### 已完成
- arrow 9→**7px**、移除 margin-top ±2px 偏移（改 flex `align-items:center`）
- **驗證**：title/arrow/total centerY 三者皆 109（收合與展開）✅

## 12. 誤覆蓋恢復（VS Code 覆蓋按鈕）🛠 — ✅ 2026-08-13

### 已完成
- 使用者誤點覆蓋刪除了：`container > row > col-12` 包裝層、`mr-4`、折疊面板切換 JS、右欄 `hiddenSmall`
- **已恢復**全部 4 處 → 折疊面板功能/對齊/圖片（70×70）完整回歸 ✅


## 13. 訂單流程頁隱藏懸浮按鈕與右側虛線 🎨 — ✅ 2026-08-13

### 已完成
- **需求**：order_confirm / payment-confirmation 不需顯示右側 Buy & Order 按鈕、懸浮購物車按鈕、右側 dot line
- **實作**：兩個頁面 `{% block content %}` 加頁面級 style：`.bc-attract-nav, .bc-floating-cart, #borders { display: none !important }`
- **驗證**：兩頁三個元素皆隱藏；coffee_menu 對照正常顯示；不影響 nav 購物車/滑出購物車功能

## 14. pending-order-warning-card 內聯 CSS 搬移 + 響應式 🛠 — ✅ 2026-08-13

### 已完成
- **搬移**：order_confirm.html JS 模板的內聯 style（卡片/關閉/標題/icon/訂單行/按鈕）→ `bc-components.css` 新增 `.pending-order-warning-*` 系列（16 個 class）；hover 改 CSS `:hover`；移除死碼 `pendingPulse`
- **響應式**：`@media ≤767.98px` 卡片 padding 16px、訂單行 `flex-wrap`、按鈕組換行靠右、名稱 max-width 130px
- **驗證**：test client + CDP 卡片渲染正常、無溢出

## 15. pending-order-warning 內容縮小（多輪）🎨 — ✅ 2026-08-13

### 已完成
- 第一輪：標題 0.9rem、副標題 0.75rem、名稱 0.8rem、價格/徽章/倒數/按鈕 0.78rem、icon 圓圈 30px、按鈕 padding 5px 10px
- 第二輪（再次縮小）：標題 0.85rem、副標題 0.7rem、名稱 0.75rem、價格/徽章/倒數/按鈕 0.72rem、icon 圓圈 26px、按鈕 padding 4px 8px、卡片 padding 14px
- 按鈕圖示與文字水平中心對齊（`margin-top: -1px`）

## 16. 倒數計時器徽章位置調整 🎨 — ✅ 2026-08-13

### 已完成
- 倒數從「待支付」徽章拆出再放回（最終整個徽章保留倒數）
- 行動端排列：資訊區第一行 → 整個「待支付」徽章第二行靠左 → 與按鈕同一行（徽章左、按鈕右 `flex:1`）

## 17. 警告卡顯示位置移到訂單詳情上方 🎨 — ✅ 2026-08-13

### 已完成
- `showPendingOrderWarning` 插入邏輯：行動端（`matchMedia ≤1199.98px`）優先插入 `.bc-order-collapse` 前方；桌面維持表單前
- **驗證**：375px 卡片在折疊面板上方（cardTop 100 < collapseTop 272）；1280px 維持 col-xl-7

## 18. 訂單詳情總價「總計:」+ 向下箭頭白色 🎨 — ✅ 2026-08-13

### 已完成
- `.bc-order-collapse__total` 加「總計:」前綴（`總計:$xx`）
- `.bc-order-collapse__arrow` 邊框金色 → 白色 `#ffffff`

## 19. 確認並支付按鈕容器寬度 🎨 — ✅ 2026-08-13

### 已完成
- 行動端 `.bc-payment-btn`：`width: fit-content → 100% !important`（強制容器寬度，與輸入框同寬 39~336px）
- **驗證**：btn 297px 與表單輸入框完全對齊

## 20. 桌面支付方式文字加大 + 圖示水平中心對齊 🎨 — ✅ 2026-08-13

### 已完成
- `@media (min-width: 768px)` `.payment-label-text { font-size: 1rem }`（12.8px → 16px）
- text 為 `inline-flex align-items:center` → 圖示與文字同一水平中心（iconVsText=0）

## 21. FPS/Cash 付款頁行動端響應式調整 🎨 — ✅ 2026-08-13

### 已完成
- **問題**：付款頁無行動端調整（card p-5 44px、FPS logo 110px、現金 icon 78px、QR 300px 溢出、標題過大）
- **實作**（bc-components.css 行動端區塊）：卡片 padding 1.25rem、logo 72px、icon 42px、總金額 1.5rem、標題 1rem、QR `min(200px, 85%)`、商品圖 70px、付款說明 1rem、按鈕 0.9rem
- **驗證**：375px 全縮小無溢出；1280px 完全無回歸

## 22. 首頁 bc-welcome-panel 最後訂單連結：咖啡豆選項記錄/預選修復 🛠 — ✅ 2026-08-13

### 已完成
- **問題**：首頁「按照之前口味落單?」連結（`.bc-welcome-img-link`）本應記錄客戶上次訂單的咖啡與咖啡豆選項，但**咖啡豆選項完全失效**：
  - 後端 `_get_last_order_link()`（views.py）只處理 `cup_level`/`milk_level`/`strength_level` 三個**咖啡**選項；咖啡豆訂單 item 中這三個 key 皆為 `null` → 連結退化成 `/bean/{id}/`，**上次的重量/研磨度選項被丟棄**
  - 前端 `bean.html` 完全沒有 query 預選 JS（coffee.html 有 `preselectLastOrderOptions`，bean 沒有）→ 即使帶 query 也不會預選
- **修復**：
  - `views.py` `_get_last_order_link()`：依商品類型分流 → 咖啡豆（bean）取 `weight` + `grinding_level`；咖啡維持 cup/milk/strength
  - `bean.html`：DOMContentLoaded 內新增 `preselectLastOrderOptions`（與 coffee.html 同風格）→ 讀取 `weight`→`#weight-group`、`grinding_level`→`#grinding-group`，同步 active 按鈕 + hidden input；重量預選後 `updatePriceDisplay()` 同步價格
- **驗證**：
  - Django test client：真實 user58 `/coffee/8/?cup_level=Medium&milk_level=Medium&strength_level=Normal` ✅；模擬 bean `/bean/8/?weight=500g&grinding_level=Medium` ✅；無選項 `/bean/3/` ✅；bean.html 渲染含 preselect JS + `node --check` 語法通過 ✅
  - CDP 真實瀏覽器（docs/verify/cdp_verify_last_order_link.py）：`/bean/8/?weight=500g&grinding_level=Medium` → 按鈕 **500g/Medium**、hidden 同步、價格 **$119** ✅；無 query 對照 → 200g/Non/$59（預設）✅；coffee 回歸 Large/Extra/Extra 正常 ✅

### 涉及檔案
- `betweencoffee_delivery/views.py`（`_get_last_order_link`）
- `templates/betweencoffee_delivery/bean.html`
- 驗證腳本：`verify_last_order_link_fix.py` / `verify_bean_preselect_fix.py` / `docs/verify/cdp_verify_last_order_link.py`

## 23. 首頁 bc-welcome-panel 行動端文字錯亂 + bc-search hover 動畫反應慢 修復 🛠 — ✅ 2026-08-13

### 已完成

**1. bc-welcome-panel 行動端文字錯亂**
- **問題診斷（CDP 375px 登入狀態）**：文字區僅 **126px** 寬（imgbox 94px + avatar 44px + gaps 擠壓）→ greeting「歡迎回來!fb_kei, 喝返杯先~~」與 points「當前積分可減免 -5 訂單及帳戶詳情」**被迫換行 2 行**、字體縮至 10px → 視覺錯亂
- **修復**（`bc-components.css` ≤768/≤480 media query）：
  - ≤768：text gap 18→12px、avatar 51→44px、imgbox 119→92px、greeting 15→13px、points 14→12px、`.bc-welcome-info` 加 `flex:1`
  - ≤480：panel gap 7→6px、text gap 18→10px、avatar 44→38px、imgbox 94→70→**62px**、img 83→58px、greeting 10→11px、lastOrder 0.6→0.5rem
- **驗證**：375px 文字區 **126→173px**、greeting/points **單行（greetLines=1/pointsLines=1）**完整顯示；768/1280px 無回歸（`docs/verify/cdp_verify_welcome_mobile.py`）

**2. bc-search hover 動畫反應慢**
- **問題診斷（CDP 追蹤）**：
  - 快速 hover 進出時 `is-on` + `is-out` **同時存在** → CSS 中 is-out 後定義勝出 → hover 中背景圖反向移出
  - `hide()` 的 1500ms setTimeout **強制移除 `is-on`** → 長時間 hover 圖會消失
  - 進入動畫 250ms delay + 1000ms = **1.25s 才完成**
- **修復**：
  - `bc-search.js`：`show()` 取消 pending hideTimer + 移除 is-out；`hide()` 移除 is-on、hideTimer 可取消（快速進出不卡住）
  - `bc-search.css`：動畫縮短（duration 1000→700ms、delay 250→120ms）
  - `index.html`：`bc-search.css/js?v=20260813a`、`base.html`：`bc-components.css?v=20260813ba`（避開快取）
- **驗證**（`docs/verify/cdp_verify_search_hover.py`）：進入動畫 **0.7s 完成**（原 1.25s）；長時間 hover `is-on` 保持；快速進出無 `is-on is-out` 並存；1.2s 後回到初始狀態 ✅

### 涉及檔案
- `static/css/bc-components.css`、`static/js/bc-search.js`、`static/css/bc-search.css`
- `templates/betweencoffee_delivery/index.html`、`templates/betweencoffee_delivery/base.html`
- 驗證腳本：`docs/verify/cdp_verify_welcome_mobile.py` / `cdp_verify_search_hover.py` / `cdp_diag_welcome_auth.py`

## 24. coffee_menu 咖啡產品區域改為 A+C 混合不對稱網格（方案 A）🎨 — ✅ 2026-08-13

### 已完成
- **需求**：coffee_menu 產品區域參考 bean_menu 的不對稱網格，改掉原本的 Z 字對角 2×2（`.coffee-menu-zgrid`）
- **方案比較與迭代**：提供 3 種設計（A：A+C 混合翻轉=bean 樣式／B：跨欄瀑布=首頁 Best Sell 樣式／C：雙瀑布階梯）
  1. 先實作 **方案 C**（`.coffee-duo-*` 雙瀑布階梯）→ 使用者**不滿意**
  2. 切換 **方案 B**（複用 `asymmetric-grid-v1` 跨欄瀑布）→ 使用者**不滿意**
  3. 切換 **方案 A**（與 bean_menu 完全一致的 A+C 混合翻轉）→ 定案 ✅
- **最終實作（方案 A，左右鏡像反轉）**：
  - `coffee_menu.html`：商品區改用 **`.bean-mix-*` 共用 class**（與 bean_menu 同一套佈局）→ 每 3 個一組（DOM=大 小 小）、組間 `.bean-mix-flip` 鏡像翻轉；**flip 判斷用 `forloop.counter0|divisibleby:6`** → 組1 flip（大卡右）、組2 非 flip（大卡左）、組3 flip（大卡右），**與 bean_menu（大卡左右交替）成左右鏡像**；8 商品 = 3 組（組3 尾組 2 個）；卡片回歸 `menu-wrap` 結構（menu-img + 名稱 + 價格 + `.coffee-menu-desc` + 落單）
  - **錯落**：coffee_menu 第二張小卡改為**向上錯落**（`.coffee-mix-grid` wrapper 覆蓋 `translateY(-6rem)`），bean_menu 維持向下 4rem；小卡2 頂部與大卡底部重疊約 48px（浮上效果）；響應式 ≤1079.98/≤767.98px 取消位移
  - `base.html` → `bc-components.css?v=20260813bi`
  - **零新增 CSS**：完全複用 bean-mix 既有規則（1.7fr 1.15fr 1.15fr、大卡跨 2 欄 340px、小卡 280px、第二小卡 `translateY(4rem)`、≤1079.98px 降級、≤767.98px 單欄）→ **兩頁佈局保證 100% 一致**
  - 清理死代碼：移除方案 C 的 `.coffee-duo-*`（134 行）與舊 `.coffee-menu-zgrid`/`.coffee-z-*`（95 行）；保留 bean_menu 使用的 `.coffee-menu-desc`
- **驗證**：
  - Django test client：3 組（含 1 flip）、3 main + 5 sub、8 商品、8 menu-wrap；無 asymmetric-grid / coffee-image-container 殘留
  - CDP 1280px：組1 大卡左（l=87, img 340）+ 小卡右階梯（280px）、組2 鏡像翻轉大卡右（l=558）、組3 尾組 2 個 ✓；1080/768/375px 無溢出；375px 單欄 ✓（`docs/verify/cdp_verify_coffee_beanmix.py`）
  - 無回歸：首頁/bean_menu/coffee/bean 詳情頁全 200

### 涉及檔案
- `templates/betweencoffee_delivery/coffee_menu.html`
- `static/css/bc-components.css`（清理死代碼 + bean-mix 註解更新）
- `templates/betweencoffee_delivery/base.html`（`bc-components.css?v=20260813bc`）
- 驗證腳本：`docs/verify/cdp_verify_coffee_beanmix.py` / `verify_coffee_beanmix.py`

## 25. Django 管理後台咖啡/咖啡豆卡片排序功能（方案 A：sort_order + list_editable）🛠 — ✅ 2026-08-13

### 已完成
- **需求**：管理員可在 Django admin 自由修改咖啡與咖啡豆卡片的排序，應用於 coffee_menu / bean_menu 頁面
- **方案**：數字排序（零新依賴，與現有 hot_item_order 模式一致）
- **實作**：
  - `eshop/models/shop_items.py`：CoffeeItem / BeanItem 各加 `sort_order = PositiveIntegerField(default=0, verbose_name="菜單排序", help_text="數字越小顯示越靠前")`；**不設 Meta.ordering**（避免影響首頁 Best Sell / 搜尋）
  - `eshop/admin.py`：CoffeeItemAdmin / BeanItemAdmin 的 `list_display` + `list_editable` 加 `sort_order`（列表頁直接輸入數字即時儲存）
  - `betweencoffee_delivery/views.py`：CoffeeMenu / BeanMenu / CoffeeMenuSearch / BeanMenuSearch → `order_by("sort_order", "id")`（id 為次要排序，未設定時維持現有順序）
  - Migration `0056`（手動移除 ordermodel.pickup_time AddField——該欄位 DB 已存在，0052 移除後手動重建，makemigrations 誤判）
- **驗證**（`tests/integration/test_menu_sort_order.py`，4 測試全過）：
  - coffee_menu / bean_menu 頁面按 sort_order 升序渲染 ✓
  - 全 0 時維持 id 順序 ✓
  - admin 列表有 `form-N-sort_order` 可編輯欄位 ✓
  - 無回歸：首頁 / 詳情頁 / admin 全 200

### 涉及檔案
- `eshop/models/shop_items.py`、`eshop/admin.py`、`betweencoffee_delivery/views.py`
- `eshop/migrations/0056_beanitem_sort_order_coffeeitem_sort_order_and_more.py`

## 26. 首頁 Best Sell 咖啡卡片排序功能（hot_item_order）🛠 — ✅ 2026-08-13

### 已完成
- **需求**：首頁 Best Sell 咖啡卡片允許管理員在 Django admin 自由排序
- **實作**：
  - `betweencoffee_delivery/views.py`：`_build_landing_context` / `Index` 的 hot_coffees 查詢 → `.order_by("hot_item_order", "id")[:4]`（hot_item_order 欄位早已存在但從未使用）
  - `eshop/admin.py`：CoffeeItemAdmin `list_display` + `list_editable` 加 `hot_item_order`（「热门商品排序」，與 menu 的 sort_order 獨立，互不干擾）
  - **零 migration**（hot_item_order 欄位已存在）
- **驗證**（`tests/integration/test_home_hot_sort.py`，2 測試全過）：
  - 首頁 Best Sell 按 hot_item_order 升序取前 4、非熱門不顯示 ✓
  - admin 列表有 `form-N-hot_item_order` 可編輯欄位 ✓
  - 無回歸：首頁 / menu / 詳情頁全 200

### 涉及檔案
- `betweencoffee_delivery/views.py`、`eshop/admin.py`

## 27. 首頁 .feed 水平移動 SVG 蒙版動畫消失修復 🛠 — ✅ 2026-08-13

### 已完成
- **問題**：首頁 `.feed`（branding Deco）水平移動 SVG 蒙版動畫消失
- **根因**：commit `7dad800`（perf: CSS Phase 4 條件載入）把 `landing.css` 從 base.html 全域移除後，只在 landing_v3.html 的 extra_css 加回，**漏加 index.html** → 首頁 .feed 失去 feedScroll 動畫樣式
- **修復**：`index.html` `{% block extra_css %}` 加載 `landing.css`（附註解說明）
- **✅ 驗證**（`docs/verify/cdp_verify_feed_animation.py`）：landing.css 已載入、`animation-name: feedScroll`（60s）、`clip-path: url(#mask)`、背景 index_feed_image.png；transform 持續移動（-118→-199→-280px）→ 動畫正常運作

### 涉及檔案
- `templates/betweencoffee_delivery/index.html`

## 28. bean 詳情頁返回按鈕桌面端居中修復 🛠 — ✅ 2026-08-13

### 已完成
- **問題**：bean/x/ 詳情頁返回按鈕桌面端沒有水平居中（偏左 193px）
- **根因**：coffee.html 的返回按鈕包在 `.w-100.form-group` 內（佔滿寬度），bean.html 的 `.text-center.mt-3` 直接是 `.row`（flex）的子元素 → flex item 寬度=內容寬 → 靠左；既有的居中 CSS 只在 ≤767.98px 生效
- **修復**：bc-components.css 把 `.product-details .text-center.mt-3 { width:100%; display:flex; justify-content:center }` 從行動端 media query 改為**全域**（桌面+行動一致）；`base.html` → `bc-components.css?v=20260813bj`
- **✅ 驗證**（`docs/verify/cdp_measure_return_btn.py`）：bean 1280 btnCenterVsFormCenter **-193 → 0**；375/coffee 全部 0 無回歸；首頁/menu/詳情頁全 200

### 涉及檔案
- `static/css/bc-components.css`、`templates/betweencoffee_delivery/base.html`

## 29. FPS/Cash 付款頁按鈕樣式統一（參考 coffee_menu 落單按鈕）🎨 — ✅ 2026-08-13

### 已完成
- **需求**：FPS/Cash 付款頁按鈕與其他頁面不同，參考 coffee_menu 的落單按鈕（`btn btn-primary btn-outline-primary`、97×45、金色描邊）修改
- **修改**：
  - `fps_payment.html` / `cash_payment.html`：主按鈕移除 `calltoaction-btn px-4 py-3`（固定 230×48 → 內容寬度）；返回按鈕 `btn-outline-secondary`（灰色）→ `btn-outline-primary`（金色）、移除 inline 灰色 hover style
  - `bc-components.css`：`.bc-payment-actions` 移除 flex 固定寬度（246/194px）→ `flex: 0 0 auto` 內容寬度；行動端同步
  - `base.html` → `bc-components.css?v=20260813bk`
- **✅ 驗證**（`docs/verify/cdp_compare_payment_buttons.py`）：FPS 主 246→184×45、返回 194→151×45 且**灰→金**；Cash 主 153×45、返回 151×45 金；全按鈕金邊金字透明 6px 圓角 45px（與 coffee_menu 一致）；首頁/menu/詳情/付款頁全 200 無回歸

### 涉及檔案
- `eshop/templates/eshop/fps_payment.html`、`eshop/templates/eshop/cash_payment.html`
- `static/css/bc-components.css`、`templates/betweencoffee_delivery/base.html`

## 30. FPS/Cash 付款頁 .payment-item-fps/cash 內聯 CSS 搬移至 bc-components.css 🛠 — ✅ 2026-08-13

### 已完成
- **需求**：付款頁 `.payment-item-fps` / `.payment-item-cash` 使用內聯 CSS，搬移到 CSS 檔案
- **實作**：
  - `bc-components.css`：新增 `.payment-item-fps, .payment-item-cash` 共用規則（bg rgba(255,255,255,0.05)、border 1px solid rgba(255,255,255,0.1)、radius 10px、overflow hidden、margin-bottom 1.5rem）——與既有的 `.payment-list-simple` 同風格
  - `fps_payment.html` / `cash_payment.html`：移除內聯 style，改用 class
  - `base.html` → `bc-components.css?v=20260813bl`
- **✅ 驗證**（`docs/verify/cdp_verify_payment_item_style.py`）：FPS/Cash 兩頁 computed style 與原內聯完全一致（bg/border/radius/overflow/margin-bottom 24px）、`inlineStyle: null`（內聯已移除）；無內聯殘留、全頁 200 無回歸

### 涉及檔案
- `static/css/bc-components.css`、`eshop/templates/eshop/fps_payment.html`、`eshop/templates/eshop/cash_payment.html`、`templates/betweencoffee_delivery/base.html`

## 31. bean 詳情頁烘焙水平 active 狀態改金色 🎨 — ✅ 2026-08-13

### 已完成
- **問題**：bean/x/ 烘焙水平（Roast level）active 狀態顯示灰色
- **根因**：style-custom.css `.roastrange-item span { color:#666 }` specificity (0,1,1) **高於** bc-components.css `.bc-roast-active { color:var(--brand-primary) }`（(0,1,0)）→ 灰色覆蓋金色
- **修復**（bc-components.css）：`.bc-roast-active` 改為 `.roastrange-item span.bc-roast-active`（高 specificity (0,2,1) 勝出）；active 圓點 `.roast .roastrange-label::before` 也改金色（`--brand-primary`）
  - `base.html` → `bc-components.css?v=20260813bm`
- **✅ 驗證**（`docs/verify/cdp_verify_roast_active.py`）：bean/1 中浅、bean/2 中、bean/3 深 → active 文字 **rgb(196,155,99) 金色** + weight 700 + 圓點金色 ✓（bean/4 不存在，bean id 為 1,2,3,6,7,8）；全頁 200 無回歸

### 涉及檔案
- `static/css/bc-components.css`、`templates/betweencoffee_delivery/base.html`

---
---
---
---
---
---
---
---


---


---


---

---

---

---

# 今日任務總覽 (2026-08-11)


## 22. FPS/Cash 付款頁隱藏懸浮元素與虛線 🎨 — ✅ 2026-08-13

### 已完成
- fps_payment.html / cash_payment.html `{% block content %}` 加頁面級 style 隱藏 `.bc-attract-nav`（右側 Buy & Order）、`.bc-floating-cart`（懸浮購物車）、`#borders`（右側虛線）
- 與 order_confirm / payment-confirmation 一致；驗證 375/1280px 三元素皆隱藏

## 23. 員工訂單管理頁隱藏懸浮元素 🎨 — ✅ 2026-08-13

### 已完成
- `templates/admin/staff_order_management.html` 加相同隱藏 style（懸浮購物車原本已由 bc-slideout-cart.js 排除，CSS 再加一層）
- 驗證：三元素 display:none、頁面正常載入

## 24. 漢堡選單與右側虛線中心對齊 🎨 — ✅ 2026-08-13

### 已完成
- **問題**：行動端漢堡選單中心（334）與右側虛線（342）偏差 8px
- **實作**（bc-attract.css ≤767.98px）：`.bc-attract-menu { left: 8px }`
- **驗證**：320px diff 0、375px diff 0、414px diff -1（亞像素）全對齊

## 25. payment-confirmation 商品明細與訂單詳情一致 🎨 — ✅ 2026-08-13

### 已完成
- 商品名 0.88rem（!important 覆蓋 .mb-1.text-white）、價格 0.9rem、數量 0.8rem、單價/選項 0.72rem、圖片 70px、間距 8/4px
- 選項 icon 0.8rem !important（覆蓋全域 .bc-options-row .icon 0.9rem !important）
- 驗證 coffee（2790）與 bean（2796）商品名 12.87px 一致、與折疊面板一致

## 26. 移除商品明細價格「HK$」🎨 — ✅ 2026-08-13

### 已完成
- order_payment_confirmation.html 商品價格/單價加 `|cut:"HK$"` → 顯示「119.00」（純模板 filter，無 CSS 變更）

## 27. 商品明細選項單行顯示 🎨 — ✅ 2026-08-13

### 已完成
- **問題**：選項 flex-wrap 換行（杯量+濃度一行、奶量第二行）
- **實作**：`.order-items .bc-options-row { flex-wrap: nowrap; font-size: 0.65rem; icon 0.7rem; gap 3px; overflow hidden }`
- **驗證**：三個選項全部同一行（top 1327）、奶量完整顯示（右緣 285 < 容器 288）

---

## 0. bc-welcome-panel：avatar +10%、-5 金色粗體、容器高度保持 🎨 — ✅ 2026-08-11

### 已完成

**1. .bc-welcome-avatar 增加 10% ✅（2026-08-11）**
- **需求**：index.html 內 bc-welcome-panel 的 `.bc-welcome-avatar` 增加 10%
- **實作**（`bc-components.css`）：
  - 桌面 45→**50px**、≤768 46→**51px**、≤480 40→**44px**（×1.1）
  - user icon 隨容器比例加大：桌面 1.8→**2.0rem**、≤768 1.5→**1.65rem**、≤480 1.25→**1.375rem**

## 2. order_confirm 訂單詳情 accordion 視覺調整（文字/箭頭縮小對齊）🎨 — ✅ 2026-08-13

### 已完成

**1. 需求與問題 ✅**
- 訂單詳情文字太大（fontsize-md 1rem=14.6px）、向下箭頭 18px 太大且垂直偏位（箭頭 centerY 119 vs 按鈕 111，差 8px）
- 使用者回報「商品未顯示」：實際驗證（真實 UI 流程：表單加入購物車 → order_confirm）商品**正常顯示**（visibleItems=1、aria=true、hiddenSmall=false），上輪修復已生效；可能為瀏覽器快取舊版

**2. 實作（`bc-components.css`）✅**
- 新增 `@media (max-width: 1198.98px)` 區塊（hiddenLarge 顯示範圍）：
  - `.Accordion` 改為 **inline-flex + align-items:center + gap 10px**，`font-size: 0.9rem`（14.6→13.2px）
  - `.arrow` 由 `position:absolute`（left 78px/top 38%）改為 **flex 子項**（static），縮小至 **13px**，`::before/::after` 線條 8px/1.5px
  - 文字、箭頭、右側價格三者由 flex 自動垂直置中
- `base.html` → `bc-components.css?v=20260813e`

**3. 驗證（CDP 375/768/1280px）✅**
- 375px：btn fs **13.16px**、arrow **13px**、btnCenterY **112** = arrowCenterY **112** = priceCenterY **112**（三者同一水平中心）✅
- 768px 平板：btn 164 = arrow 164 ≈ price 165 ✅；商品顯示 ✅
- 1280px 桌面：.Accordion display:none（hiddenLarge 隱藏）無影響 ✅
- 點擊功能：展開 → 收合 → 展開 正常 ✅

---

- `base.html` → `bc-components.css?v=20260811a`

**2. 積分減免「-5」金色粗體 ✅（2026-08-11）**
- **需求**：「當前積分可減免 -5」的 `-5` 文字改為 **bold + 金色**
- **實作**：
  - `index.html`：`-5` 包成 `<strong class="bc-welcome-discount">-5</strong>`
  - `bc-components.css`：新增 `.bc-welcome-points .bc-welcome-discount { color: var(--bc-gold); font-weight: 700; }`

**3. 容器高度保持 ✅（2026-08-11）**
- **高度保持原理**：容器高由 imgbox（82/73/60）+ padding 決定；avatar 變大後（50/51/44）+ padding（24/12/10）皆 < imgbox → 不撐高
- ✅ 驗證（CDP 量測 1280/768/375px）：容器高度**保持 106/85/70px** 不變；avatar **50/51/44**（+10%）
- ✅ 驗證（Django test client 登入 kei）：`<strong class="bc-welcome-discount">-5</strong>` 渲染正確、HTTP 200
- 驗證資產：`docs/verify/cdp_measure_welcome.py`

## 3. order_confirm 行動端商品未顯示 —— 最終排查與伺服器層防快取 🛠 — ✅ 2026-08-13

### 已完成

**1. 全面驗證（排除伺服器端問題）✅**
- **Django test client**（純伺服器渲染）：order_confirm HTTP 200、`aria-selected="true"`、hiddenLarge 無 hiddenSmall、商品名 `['WakeMeup','WakeMeup']`（hiddenLarge + 桌面右欄兩處）
- **CDP 多寬度掃描**（320/360/375/390/414/480/768/991/1024/1198/1199/1200/1280px）：**所有 <1200px 寬度商品皆顯示**（`hiddenSmall=False`、`aria=true`、`vis=1`）；≥1200px 切換桌面右欄（設計行為）
- 網路請求無失敗、jQuery 3.7.1 正常載入
- 確認僅一份 order_confirm.html（無殘留舊模板）、伺服器 13:47 重啟讀取最新版

**2. 結論：使用者端瀏覽器快取舊版頁面**
- 「桌面顯示、行動端不顯示」完全符合**舊版頁面**行為（舊版行動端 hiddenLarge accordion 強制收合 → 商品隱藏）
- 新版模板伺服器必定回傳，但瀏覽器快取了舊版 HTML/CSS/JS

**3. 伺服器層防快取（最強）✅**
- `eshop/views/order_views.py`：
  - import `never_cache`
  - `OrderConfirm` view 加 `@method_decorator(never_cache, name="dispatch")`
  - `order_payment_confirmation` 加 `@never_cache`
- 驗證：兩頁響應 header 皆為 `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private` ✅
- 此前已加：`base.html` no-cache meta、`bc-components.css?v=20260813e`、`main.js?v=20260813e`

---


---

## 1. home-slider 橫幅停留時間 7 秒 → 10 秒 ⏱ — ✅ 2026-08-11

### 已完成

**1. autoplayTimeout 7000 → 10000 ✅（2026-08-11）**
- **需求**：index.html home-slider owl-carousel 輪播橫幅停留時間調整為 10 秒
- **實作**：

## 4. order_confirm 行動端訂單詳情折疊面板重新設計（預設關閉）🎨 — ✅ 2026-08-13

### 已完成

**1. 需求 ✅**
- 行動端重新加入購物車商品折疊面板（重新設計，非沿用舊 Rtable/Accordion）
- **預設值：關閉**；「訂單詳情」文字 + 向下箭頭點擊展開；再點擊收合

**2. 實作 ✅**
- **`order_confirm.html`**：
  - 在 `ftco-section-billing` 內、表單前插入全新 `.bc-order-collapse` 折疊面板：
    - `<button class="bc-order-collapse__header" aria-expanded="false">`（訂單詳情 + 金色向下 chevron + 總價，flex 同列）
    - `.bc-order-collapse__body` 含 `{% for item in items %}` 商品列表（coffee/bean 選項）
  - **恢復右欄 `sidebar-box` 的 `hiddenSmall`**（<1200px 隱藏右欄，避免與折疊面板重複顯示）
  - 底部加 **vanilla JS**（不依賴 jQuery）切換 `aria-expanded`
- **`bc-components.css`**：新增 `.bc-order-collapse` 系列：
  - 容器半透明卡片（圓角 10px、左右 15px margin 與表單 col 對齊）
  - Header `flex + align-items:center`，文字/箭頭/總價同一水平中心（chevron `rotate(45°)` 向下 → `rotate(-135°)` 展開）
  - Body `display:none`，由 `[aria-expanded="true"] + body` 控制
  - `@media (min-width:1200px)` 隱藏（桌面用右欄）
- `base.html` → `bc-components.css?v=20260813h`

**3. 驗證（CDP 375/768/1280px + test client）✅**
- 375/768px：**預設關閉**（aria=false、body none、商品隱藏）→ 點擊 **展開**（aria=true、商品 visible=1）→ 再點擊 **收合** ✅
- 對齊：title/arrow/total centerY 同水平（±1px）✅
- 1280px：折疊面板 `display:none`、右欄商品顯示 ✅；無重複顯示 ✅；無溢出 ✅
- test client：HTTP 200、`aria-expanded="false"`、面板含商品、右欄 hiddenSmall ✅

---

  - `static/js/main.js`：`autoplayTimeout: 7000` → **`10000`**（每張橫幅保持 10 秒；smartSpeed 700ms 滑動動畫不變）
  - `base.html`：`main.js?v=20260807i` → **`?v=20260811b`**（Whitenoise 1 年長快取，改 JS 必須加版本參數）
- ✅ 驗證（CDP 1280px）：owl 實例 `autoplayTimeout: 10000`、`autoplay: true`、`smartSpeed: 700`、載入 `main.js?v=20260811b`

---

## 2. coffee_border_02.svg 增加 5%（首頁第 1 個 slider 裝飾）🎨 — ✅ 2026-08-11

### 已完成

**1. noise-img 尺寸 ×1.05 ✅（2026-08-11）**
- **需求**：index.html 第 1 個 slider 內 `coffee_border_02.svg`（`.noise-img`）增加 5%
- **實作**（`style-utilities.css` 2818-2839，`.slider-item.slider-first .noise-img`）：
  - 桌面 `27.4vw / min 383px` → **`28.8vw / min 402px`**（×1.05）
  - 平板 `88.6vw` → **`93vw`**、手機 `104.7vw` → **`110vw`**、小手機 `120.8vw` → **`126.8vw`**（皆 ×1.05）
  - `max-width: 92vw` cap **維持**（手機已達 container 滿寬物理極限，防溢出）
- `base.html` → `style-utilities.css?v=20260811c`
- ✅ 驗證（CDP 1280/768/375/320px）：slider1 = **402/402/345/294px**（桌面/平板 +5%；手機維持 92vw cap）；slider3（owl_title_bg_01）對照 238/422/281/240 不受影響；`no_overflow: true` 全斷點無溢出

---

## 3. bean_menu 不對稱網格小卡組加大 🎨 — ✅ 2026-08-11

### 已完成

**1. 小卡組加大（grid 比例 + 圖片 260→280px）✅（2026-08-11）**
- **需求**：bean_menu 不對稱網格小卡組整體太小
- **根因**（CDP 量測）：組 1（A 瀑布）小卡欄 1fr = 249px，圖 260px 被壓到 249px；組 2（C 棋盤）小卡欄 498px 但圖僅 260px 留白多 → 小卡圖僅大卡的 73~76%
- **實作**（`bc-components.css` `.bean-mix-*`）：
  - grid `2fr 1fr 1fr` → **`1.7fr 1.15fr 1.15fr`**（大卡欄 498→423px、小卡欄 249→286px）
  - 小卡圖 `260px` → **`280px`**（小卡/大卡視覺比 82%）
  - 大卡圖維持 340px；平板/手機斷點規則不變（320px 並排欄 / 單欄皆可容納）
- `base.html` → `bc-components.css?v=20260811d`
- ✅ 驗證（CDP 1280/768/375px）：小卡圖 **280px 完整呈現**（組 1 不再被壓縮）、大卡圖 340px 保持、組 2 flip 小卡欄 423px、全斷點 `no_overflow`；coffee_menu（zgrid 290px）不受影響

---

## 4. bean_menu 描述文字寬度平衡（小卡加寬 / 大卡減寬）🎨 — ✅ 2026-08-11

### 已完成

**1. 描述寬度平衡 ✅（2026-08-11）**
- **需求**：1) 小卡組描述文字增加寬度 2) 大卡組描述文字相應減少寬度（現在看起來不平衡）
- **根因**（CDP 量測）：全域 `.coffee-menu-desc` `max-width: 75%` 套用於大小卡 → 組 1 大卡 758×0.75 = **568px** vs 小卡 286×0.75 = **215px**（差距 353px 極不平衡）
- **實作**（`bc-components.css`，`@media (min-width: 768px)` 內）：
  - `.bean-mix-sub .coffee-menu-desc { max-width: 100% }`（小卡加寬：組1 215→286px、組2 317→423px）
  - `.bean-mix-main .coffee-menu-desc { max-width: 55% }`（大卡減寬：組1 568→417px、組2 466→341px）
  - 手機單欄（<768px）大小卡同寬 → 沿用全域 75% 自然平衡，不覆蓋
  - 限定 `.bean-mix-*`，coffee_menu zgrid 不受影響
- `base.html` → `bc-components.css?v=20260811e`
- ✅ 驗證（CDP 1280/768/375px）：組1 描述 417 vs 286px（差距 353→131px，-63%）；組2 341 vs 423px 協調；平板大卡 370px / 小卡 320px；手機單欄大小卡皆 245px（75%）；全斷點 `no_overflow`
- **追加（2026-08-11）**：小卡描述**再次加寬** → `.bean-mix-sub .coffee-menu-desc` padding `1rem(≈20px) → 4px`（固定 px 脫離 rem 依賴）；文字區組1 **246→278px**（+13%）、組2 **383→415px**（+32px）；`bc-components.css?v=20260811f`；CDP 驗證：1280px 小卡 278/415px、大卡 377/301px 不受影響、手機單欄沿用 75% 不變、無溢出
- **追加2（2026-08-11）**：bean-mix 卡片**文字加大**（名稱 lg→xl、價格 md→lg、描述 md→base，響應式變數手機自動縮小）：1280px 名稱 **19.5→25.32px**、價格 **15.72→19.5px**、描述 **15.72→17.66px**；⚠️ 教訓：responsive-system.css 描述規則 `.menu-wrap .text .coffee-menu-desc` 是 **3 class (0,3,0)** 與覆蓋規則同級 → 後載入的 responsive 勝出 → 描述需 `.menu-wrap` 前綴到 (0,4,0) 才生效（名稱 (0,4,1)/價格 (0,5,0) 已足夠）；CDP 1280/768/375 驗證名稱無截斷、無溢出（`bc-components.css?v=20260811h`）

---

## 5. sticker-box 重構（修復容器塌陷 + 響應式）🎨 — ✅ 2026-08-11

### 已完成

**1. sticker-box 容器與結構修復 ✅（2026-08-11）**
- **澄清**：sticker-box 只存在於**商品詳情頁** `/bean/x/`、`/coffee/x/`（bean.html、coffee.html）；**bean_menu/coffee_menu 菜單頁無 sticker**（grep 確認 0）
- **診斷**（CDP 量測）：`.sticker-box` 高度 **塌陷為 0**（子元素全 absolute、容器無明確尺寸）；冗餘 `background-image: takeaway_cup.png`（與 coffee 頁 `.front` 圖重複、bean 頁兩圖並存混亂）；`.sticker` absolute 但無偏移值依賴隱含 static position；**完全無響應式**（260px 固定）
- **實作**（`style-custom.css` Rotating Sticker 區塊重構）：
  - `.sticker-box`：`width/height: 260px`（不再塌陷）+ `margin-left: auto` 靠右（取代 `left:10%`）+ 移除背景圖 + `z-index: 5` + `pointer-events: none`
  - `.sticker`：`inset: 0` 明確填滿容器
  - **響應式**：新增 `@media ≤575.98px`（容器 170px、`scale(0.65)`、front 圖 58×68、文字 16/11px）
- `base.html` → `style-custom.css?v=20260811i`
- ✅ 驗證（CDP bean/coffee × 1280/768/375px）：容器 **260/260/170px**（不再塌陷）、`bgImage: none`、貼紙 208/208/169px、手機文字縮小、全斷點 `no_overflow`、scrollWidth 不溢出
- **追加（2026-08-11）**：貼紙**位置修正**（原浮在產品圖上方 y=136，與圖重疊）→ 移至**名稱右側**：
  - HTML（bean/coffee.html）：`sticker-box` 移入名稱 `.block-23` 內（加 `position-relative`）
  - CSS：`.sticker-box` 改 `absolute`，`top:-107px`（貼紙中心 = 名稱中心，名稱高 46/2 - 260/2）、`right:-10px`；手機 `top:-67px`、`right:-6px`、170px
  - ✅ CDP 驗證：`sticker_centerY_vs_title = 0`（1280/375）、768px 差 3px（名稱高 40px）；貼紙右緣 = block 右緣 +10；全斷點無溢出（`style-custom.css?v=20260811k`）

---

## 6. coffee 詳情頁產品照片 404 修復（非 CSS 問題）🛠 — ✅ 2026-08-11

### 已完成

**1. 圖片 404 診斷與 DB 修復 ✅（2026-08-11）**
- **現象**：使用者反饋「產品照片無響應式設計」——coffee/4/ 照片僅 91px（bean 正常 504/297px）
- **診斷**：
  - CSS `.img-box .img-4 { max-width: 100%; object-fit: contain }` 本身**是響應式的**（bean 頁驗證 516/642/297px 正常縮放）
  - coffee/4/ 的 `get_detail_image` 指向 `/media/coffee_images/black_blend_Rcu39Op.png` → **404**（檔案不存在）→ 破圖無固有尺寸 → 顯示 91px 佔位 → 看似「無響應式」
  - 全庫掃描：**僅 1 個缺失**（CoffeeItem id=4）；`black_blend.png`（1200×840）存在
- **修復**：DB `CoffeeItem(4).image` 更新為 `coffee_images/black_blend.png`
- ✅ 驗證（CDP coffee/bean × 1280/768/375px）：coffee 圖 **516×361 / 642×449 / 297×208**（等比例縮放、`complete: true`）；bean 516/642/297；全斷點 `no_overflow`
- ⚠️ 提醒：Render 生產 Supabase 的 CoffeeItem 4 可能同樣指向缺失檔案，部署後需一併檢查/更新

---

## 7. 詳情頁產品照片行動端縮小 🎨 — ✅ 2026-08-11

### 已完成

**1. 行動端照片縮小（91% → 64%）✅（2026-08-11）**
- **需求**：咖啡/咖啡豆詳情頁產品照片在行動端太大
- **量測**：375px 照片 297px（佔容器 91%）、414px 336px（92%）
- **實作**（`style-custom.css`）：`@media ≤575.98px` 內 `.img-box .img-4 { max-width: 70% }`
- `base.html` → `style-custom.css?v=20260811l`
- ✅ 驗證（CDP）：375px 照片 **297→208px**（64%）、414px **336→235px**（64%）；桌面 1280px 維持 516px（max-width 100% 不變）；全斷點 `no_overflow`
- **追加（2026-08-11）**：使用者反饋「沒有減少反而變大」→ **根因**：原 `@media ≤575.98px` 未涵蓋 576-767px 視窗（如小平板/大手機），該區間照片維持 100%（比 297px 更大）→ 將 media query 擴大為 `≤767.98px`（手機+平板全涵蓋）；CDP 驗證：375px=208px(64%)、**600px=323px(66%)**（原先 100% 約 540px）、1280px 桌面 516px 不變；`style-custom.css?v=20260811m`；需硬刷新（Ctrl+Shift+R）清除瀏覽器快取
- **追加2（2026-08-11）**：sticker 行動端顯示異常（iPhone 12 Pro 390px / XR 414px）——文字與 front 圖縮小但**背景沒縮小** → **根因**：`.sticker .bg` 背景圖 `background-size` 未設定（auto = 260px 固有尺寸），手機容器縮至 169px 時背景圖維持 260px 被裁切 → 加 `background-size: contain`（shorthand `/ contain`）；CDP 驗證 390/414px：`bgSize: contain`、sticker 169×169、front 38×44、文字 16px、無溢出（`style-custom.css?v=20260811n`）
- **追加3（2026-08-11）**：使用者反饋仍沒修復 → **深層根因**：`transform: scale(0.65)` 只縮視覺不改 **layout 尺寸**（`.sticker` 仍 260×260），`.bg` 的 `background-size: contain` 相對 **260px layout 容器**計算 → transform scale + background-size 組合在瀏覽器繪製異常 → **根治**：手機 media 內 `.sticker` 直接設 `width/height: 170px; transform: none`（layout 真實 170px），`.bg` contain 以 170px 計算 → 背景圖直接 170px；CDP 驗證 390/414px：sticker **170×170**（cssW 170px、transform none）、bg cssW **170px** + contain、front 55×68、文字 146×78、無溢出（`style-custom.css?v=20260811o`）
- **追加4（2026-08-11）**：使用者反饋「sticker-box 沒有響應式縮小」→ **最終方案**：改用 **`clamp(170px, 44vw, 260px)`** 響應式尺寸（無 @media 依賴，任何視窗寬度自動縮放），**移除 transform scale**（改 width/height 100% 跟隨容器），front/img/文字皆 clamp；DevTools 檢查時 `.sticker-box` 只有一條規則不會混淆；CDP 驗證：390px=**172px**、414px=**182px**、768px/1280px=**260px**，bg contain 全一致、front 55-83px、文字 16-25px、全斷點無溢出（`style-custom.css?v=20260811p`）
- **追加5（2026-08-11）**：sticker-box 行動端**整體縮小 20%** → clamp 行動端部分 ×0.8：box `clamp(136px, 35.2vw, 260px)`、front img `clamp(46px, 12.8vw, 84px)`、文字 `clamp(13px, 3.2vw, 25px)`、span `clamp(9px, 2.4vw, 17px)`；桌面 max 260px 不變；CDP 驗證：403px box **177.3→142px**（-20%）、390px **172→137px**、bg/front/文字同步縮小、1280px 桌面 260px 不變、無溢出（`style-custom.css?v=20260811q`）
- **追加6（2026-08-11）**：sticker-box 行動端**再次縮小 20%** → clamp 行動端部分再 ×0.8：box `clamp(109px, 28.16vw, 260px)`、front img `clamp(37px, 10.24vw, 84px)`、文字 `clamp(10px, 2.56vw, 25px)`、span `clamp(7px, 1.92vw, 17px)`；CDP 驗證：403px box **142→113px**（-20%）、390px **137→110px**、bg/front/文字同步縮小、1280px 桌面 260px 不變、無溢出（`style-custom.css?v=20260811r`）
- **追加7（2026-08-11）**：1) **桌面/平板端 -20%**：box clamp max 260→**208px**、front img max 84/98→**67/78px**、文字 max 25/17→**20/14px**（手機不變）；2) **內部文字響應式 class**：新增 `.bc-sticker-text`（clamp 10px→20px）與 `.bc-sticker-text-sub`（clamp 7px→14px），HTML p/span 加 class；CDP 驗證：390px box 110px 不變、768/1280px box **260→208px**、front 67×78、文字 19.7-20px/span 14px、全斷點無溢出（`style-custom.css?v=20260811s`）

---

## 10. 詳情頁行動端 UI 整體縮小（統一響應式）🎨 — ✅ 2026-08-11

### 已完成

**1. 統一縮小 coffee/bean 詳情頁行動端 UI ✅（2026-08-11）**
- **現象**：coffee/x/ 與 bean/x/ 行動端整個 UI 太大（文字、圖示、按鈕）不平衡
- **量測**（CDP 390px）：選項按鈕 60px（杯量 inline 72px）、數量 54px、購買按鈕 54px、圖示 24px、名稱 25.3px
- **實作**（`bc-components.css` 新增 `@media ≤767.98px` 區塊，使用者選「更激進 + 文字全處理」）：
  - 文字：名稱 25.3→**20px**、價格 19.5→**17px**、描述 16.1→**14px**
  - 按鈕/選項：**40px**（含覆蓋杯量 inline 72px、`.product-details button` 54px !important）
  - 數量：input 90×54→**64×38px**、+/- 按鈕 54→**38px**、padding 16×20→6×12
  - 圖示：24→**18px**、寬 32→26px
  - ⚠️ 教訓：需 `.product-details` 前綴提高 specificity（(0,2,0)!important 勝 (0,1,1)!important）對抗 style-bootstrap `.product-details button` 54px；描述需 (0,4,1) 勝 `.block-23 p.pb-2` (0,3,1) 的 1.1rem
- `base.html` → `bc-components.css?v=20260811i`
- ✅ 驗證（CDP coffee/bean × 390/1280px）：行動端全部縮小生效（40/38/18px、20/17/14px）、桌面 1280px 維持原值（60/54px、32.9/25.3px）、無溢出
- **追加（2026-08-11）**：使用者反饋「仍然太大」→ **第二輪縮小**（更激進）：名稱 20→**18px**、價格 17→**16px**、描述 14→**13px**、資訊文字 14.6→**13px**、表單標籤 15.4→**14px**、圖示 18→**17px**、選項按鈕 40→**36px**、數量 38→**34px**、+/- 34px、購買按鈕 40→**36px**（`padding: 6px 12px !important` 修正覆蓋 Bootstrap .px-4/.py-3 !important）、返回按鈕 38→**32px**、烘焙 label→**12px**；CDP 驗證 375/390/414px 全部生效、桌面 1280px 維持原值（title 32.9/option 60/quantity 54px）、無溢出（`bc-components.css?v=20260811j`）
- **追加2（2026-08-11）**：1) **表單數量行對齊**：`.input-group.col` 原 x=39/w=312（Bootstrap col padding）與選項行 x=54/w=282 不對齊 → `margin-left/right: 15px + width: calc(100% - 30px)` → 數量行 **x=54/w=282** 與選項行對齊、label x=54 一致；2) **navbar 行動端水平居中**：navbar-brand（｛Between｝）與漢堡 toggler 分居兩側 → `.ftco_navbar .container { justify-content: center; gap: 16px }` + toggler `margin-left: 0 !important` → logo+漢堡並排水平居中（範圍中心 195 = navbar 中心）；CDP 驗證 390px 兩項皆生效、無溢出（`bc-components.css?v=20260811k`）
- **追加3（2026-08-11）**：使用者澄清（navbar「非頁面中心，是水平中心點」）+ 表單仍大未左對齊 → 1) **第三輪縮小**：名稱 17、價格 15、描述/資訊 12、表單標籤 13、圖示 16px、選項/數量/購買按鈕 **32px**、返回 28px、烘焙 label 11px；2) **左對齊**：`.w-100.form-group` margin 15px（數量行 x=39→**54** 與其他行一致）；3) **navbar 中心點**：移除 justify-content:center（恢復 logo 左/漢堡右），brand padding-top 8→**4px**（文字視覺中心 cy **49→45** = 漢堡 cy 45）；CDP 驗證：brandTextCy 45 = toggler 45、表單 rows 全 x=54、無溢出（`bc-components.css?v=20260811l`）
- **追加4（2026-08-11）**：使用者並行改 coffee.html 表單結構（col-md-12 → `.w-100.form-group`，數量行 `.input-group.mb-3` 無 col）後：1) **全部按鈕增加高度**：選項/數量/購買 **32→36px**、返回 28→**32px**；2) **「數量 :」字體統一**：`.product-details .input-group > p { font-size: 13px }`（數量行 label 在 .input-group 內，原 15.4px ≠ 其他 13px）；CDP 驗證：全部 label 13px、按鈕 36px/返回 32px、無溢出（`bc-components.css?v=20260811m`）
- **追加5（2026-08-11）**：行動端**全部按鈕文字縮小** → 統一 **11px**（option/qty/input/action/rbtn）、杯量 oz 標籤 **9px**；⚠️ 教訓：`.r-btn` 需 `.product-details` 前綴（勝 responsive `.btn` 同級）；`.bc-option-oz` 需 `(1,2,0)!important` 勝過 coffee.html inline `<style>` 的 `#cup-level-group .bc-option-oz`（(1,1,0)!important）；CDP 驗證：全部 11px、oz 9px、無溢出（`bc-components.css?v=20260811n`）
- **追加6（2026-08-11）**：使用者反饋「文字仍未修復」→ CDP 確認文字已全 11px（疑瀏覽器快取需硬刷新）；並新增**按鈕內部圖示縮小**：杯量 icon-coffee **16.1→13px**、數量 +/- 圖示 11→**9px**、option label 11.7→**11px**；CDP 驗證：icon 13px、qty icon 9px、全部文字 11px、無溢出（`bc-components.css?v=20260811o`）
- **追加7（2026-08-11）**：**再次縮小**：全部按鈕文字 11→**10px**、oz 9→**8px**、杯量 icon 13→**11px**、+/- 圖示 9→**8px**、option label 11→**10px**；CDP 驗證：全部文字 10px、icon 11px、qty icon 8px、無溢出（`bc-components.css?v=20260811p`）
- **追加8（2026-08-11）**：**標籤文字與按鈕文字水平中心對齊**：根因 label 被 style-bootstrap 設 `align-self: flex-end`（貼行底，杯量差 3px/奶量差 8px/數量差 7px）→ 覆蓋 `align-self: center` + `display:flex; align-items:center; line-height:1.2; margin:0`；杯量按鈕（含 icon+label 內容較高）padding-top/bottom 0；CDP 驗證：奶量/數量 **1px**、杯量 4px（icon+label 結構殘差）、無溢出（`bc-components.css?v=20260811s`）
- **追加9（2026-08-11）**：**杯量按鈕增加高度**：36→**44px**（oz+icon+label 三層內容）+ 杯量 label-text `translateY(11px)` 對齊（icon/label 水平線）；CDP 驗證：杯量按鈕 **44px**、文字 cy 594 vs label 595（**1px** 對齊）、icon 596、無溢出（`bc-components.css?v=20260811t`）
- **追加10（2026-08-11）**：1) **Footer 行動端響應式**：跑馬燈 22px/1108px→**16px/720px**、padding 2rem→1rem（scroller 高 101→88px）、footer 文字 16→**14px**、copyright→**13px**、social 圖示 50→**40px**、icon 26→**20px**；2) **bean 返回按鈕居中**：根因 bean 的 `.text-center` 無 w-100 包裝（coffee 有）→ 容器僅 46px 靠左 → `.product-details .text-center.mt-3 { width:100%; display:flex; justify-content:center }` → wrapper **312px**、a x=185 居中；CDP 驗證兩項皆生效、無溢出（`bc-components.css?v=20260811u`）
- **追加11（2026-08-11）**：使用者反饋兩問題 → 1) **跑馬燈斷開**：li 固定 720px 容不下文字換行成 2 行（lines:2）→ 改 `width: max-content; white-space: nowrap` → **單行**（lines:1、li 790px、scroller 高 60px）；2) **杯量文字下移**：我加的 `translateY(11px)` 過度把文字推下（label-text cy 607）→ 移除改 `align-self: center` → label-text cy **596** = icon 596 = label 595（1px 對齊）；CDP 驗證兩項皆生效（`bc-components.css?v=20260811v`）
- **追加12（2026-08-11）**：**Footer 二次縮小**：跑馬燈 16→**14px**（li 685px 單行）、scroller padding 1→**0.75rem**（高 60→49px）、footer 文字 14→**13px**、copyright 13→**12px**、social 圖示 40→**34px**、icon 20→**16px**；CDP 驗證：全部生效、跑馬燈單行無縫、無溢出（`bc-components.css?v=20260811w`）
- **追加13（2026-08-11）**：**.bc-roast-range-field 行動端間距**：`padding-bottom: 4vh`（844px 視窗 = **33.8px**）過大 → 行動端覆蓋為固定 **16px**；CDP 驗證：pb **33.8→16px**（-53%）（`bc-components.css?v=20260811x`）
- **追加14（2026-08-11）**：**首頁 bc-welcome-panel 桌面端崩潰修復** 🚨：現象 panel 變滿寬 block（w=1265/h=1201/img 860×1100）、所有 bc-welcome-* 樣式失效；**根因**：`.product-details .w-100.form-group` 規則的閉合 `}` 被註解（`/* margin-right: 15px;\n} */`）→ `@media (max-width: 767.98px)`（2405）**未閉合** → 吞掉後續全部規則（含 .bc-welcome-panel 2883）→ 桌面 1280 不匹配 media → 樣式全失效；CSSOM 確認 3 條 .bc-welcome-panel 規則皆被包進 @media 767.98；**修復**：恢復 `.w-100.form-group` 正常結構（margin-left/right: 15px + 閉合 `}`）；CSSOM 驗證規則回到 (none)、規則總數 357→521；CDP 首頁桌面：panel **599×106 flex**、avatar 50×50、imgbox 160×82、無溢出（`bc-components.css?v=20260811y`）
- **追加15（2026-08-11）**：**詳情頁資訊圖示顏色改為 rgb(78,78,78)**（使用者需求，按鈕內圖示除外）：`.product-details .block-23 ul li .icon { color: rgb(78, 78, 78) }`（原繼承白 70%）；CDP 驗證：coffee/bean 資訊圖示 **rgb(78,78,78)**、杯量 icon/數量 +/- 圖示保持金色、桌面/行動端一致（`bc-components.css?v=20260811z`）
- **追加16（2026-08-11）**：**詳情頁項目圖示更換**（coffee.html）：健康攝取建議 `coffee`→**`health_and_safety`**、賞味期限 `coffee`→**`calendar_today`**（使用者選定）；風味維持 `coffee`（使用者提供多批 Material/FA 選項後決定不再更改）
- **追加17（2026-08-11）**：**CSS 審計 + Phase 2 清理死資產**：新增 `scripts/audit_css_references.py`（掃描模板 CSS 引用/標記死資產/重複/條件載入/HTTP 驗證，輸出 `docs/css_audit_report.md`）；**Phase 2 清理**（使用者批准）：刪除 `animate.css`（75KB）、`bootstrap.min.css`（137KB）、`dist-aggressive/`（147KB）、`bootstrap/`、`css/` 子目錄（~52KB）、`loyalty-table.css`（12KB）、`profile.css`（9KB）、`fontawesome/css/all.min.css`（851KB，未引用）、`.DS_Store`×2、`staff_order_management.css.bak`；**死資產歸零**（2798KB→1509KB，移除 1288KB）；CDP 驗證首頁/菜單/詳情/登入無 404 無溢出；⚠️ 待優化：Font Awesome 本地 all.css（943KB）+ CDN all.min.css 雙載入、圖示字型過多（icomoon 77KB+ionicons 45KB）
- **追加18（2026-08-11）**：**Profile/Loyalty 頁面 CSS 異常修復** 🚨：使用者反饋 /profile/ 與 /profile/loyalty/dashboard/ 載入 CSS 失敗 → **根因**：1) 審計腳本只掃 `templates/` 遺漏 app templates（`socialuser/templates/`）→ 誤判 `profile.css`、`loyalty-table.css` 為死資產並刪除（實際被 profile.html/loyalty_dashboard.html 引用）；2) `member-nav.css` 死引用（樣式已合併 bc-components.css 2810，檔案已由 Phase A 清理但模板引用未移除 → 404）；**修復**：git 恢復 profile.css/loyalty-table.css、移除 3 個模板 member-nav.css 死引用、審計腳本改掃所有 `*/templates` 目錄；✅ 驗證：profile/loyalty 頁面無 404、審計死資產 0、無溢出；⚠️ 教訓：審計腳本需涵蓋所有 app templates
- **追加19（2026-08-11）**：**CSS Phase 3 合併精簡**：移除 **Font Awesome CDN 雙載入**（保留本地 all.css）；移除未用圖示字型 **ionicons/open-iconic/flaticon**（45+9+1KB）+ **aos.css**（25KB，無 data-aos 元素）引用與檔案；**blobs.css 條件載入**（從 base 移出，加到 index/landing_v3 extra_css，其他頁面不再載入 33KB）；同步更新 admin/audit_log.html；✅ CDP 驗證首頁（blobs 載入）/菜單/詳情/profile/loyalty 無溢出、Font Awesome 本地正常；審計腳本確認死資產 0；CSS 全域 21→16 個、首頁節省 ~160KB
- **追加20（2026-08-11）**：**CSS Phase 4 條件載入優化**：`owl.carousel`+`owl.theme`（~5KB）與 `landing.css`（6KB）從 base 移出 → 加到 index/landing_v3 extra_css（僅首頁類頁面載入）；同步 admin/audit_log；保守保留 magnific-popup（main.js 用）、select2、timepicker；✅ CDP 驗證：首頁 19 CSS（含 owl/blobs/bc-search）、菜單/詳情/profile 僅 **15 CSS**（省 ~44KB）、無溢出；全域 base 核心 CSS 21→**14 個**
- **追加21（2026-08-11）**：**CSS Phase 5 全面驗證** ✅：審計腳本死資產 **0**；CDP 檢查 **9 頁面**（/、/coffee_menu/、/bean_menu/、/coffee/4/、/bean/8/、/about/、/cart/、/cart/checkout/、/accounts/login/）：首頁 19 CSS（welcome-panel+slider 存在）、其餘 15 CSS、**全部無 404、無溢出**；CSS 重構最終成果：全域 2798KB → **1450KB**（-48%）、全域核心 21→14 CSS、非首頁頁面 15 CSS

---

## 8. coffee 詳情頁直向照片過高修復（參考 bean 方形圖）🛠 — ✅ 2026-08-11

### 已完成

**1. 直向圖高度限制（max-height 56vw）✅（2026-08-11）**
- **現象**：使用者反饋 coffee/x/ 產品照片太大（參考 bean/x/ 處理）
- **診斷**：大部分 coffee 為**直向圖**（860×1100），響應式 70% 後手機 **218×279px**（比 bean 方形 218×218 高 28%）、桌面 516×660；只有 Black Blend 是橫向（1200×840）
- **實作**（`style-custom.css`）：`@media ≤767.98px` 內 `.img-box .img-4` 加 **`max-height: 56vw`**（手機直向圖高度 218px = bean 方形圖高度，視覺協調；桌面 ≥768px 不影響）
- `base.html` → `style-custom.css?v=20260811t`
- ✅ 驗證（CDP 390px）：coffee/1/ 直向 **218×279 → 171×218**（高度=bean）、coffee/4/ 橫向 218×153 不變、bean 218×218 不變；桌面 1280px 直向 516×660 保持原樣
- **追加（2026-08-11）**：使用者提供桌面 computed（516×660）確認**桌面也過大** → 增加桌面/平板限高：`@media 768-1079.98px max-height: 600px`、`@media ≥1080px max-height: 516px`（= 各斷點 bean 方形圖高度）；CDP 驗證：coffee/1/ 直向 **390px=171×218、768px=469×600、1280px=403×516**，各斷點高度與 bean 方形圖**完全一致**（218/600/516）；bean 方形圖同步受 max-height 影響（768px 600×600）；`style-custom.css?v=20260811u`

---

## 9. 背景文字 SERVED FRESH 行動端字距修復 🎨 — ✅ 2026-08-11

### 已完成

**1. letter-spacing 固定 -10px → em 響應式 ✅（2026-08-11）**
- **現象**：bean/x/ 背景文字 SERVED FRESH 桌面字距 OK、行動端每個文字太近（無響應式）
- **根因**：`.bc-section-with-bg-text::before`（及 .title-bg-head 系列）`letter-spacing: -10px` 固定值，而字體 `20vw` 響應式 → 桌面 256px 時 -3.9% OK、行動端 78px 時 **-12.8%** 文字重疊
- **實作**（`style-utilities.css` 4 處）：`-10px` → **`-0.04em`**（em 相對字體自動縮放）
- `base.html` → `style-utilities.css?v=20260811d`
- ✅ 驗證（CDP）：行動端 390px letter-spacing **-10px → -3.12px**（78px×-0.04）、桌面 1280px **-10px → -10.24px**（幾乎不變）；coffee BREWED FAST、訂單確認頁等同機制頁面同步受益
- **追加（2026-08-11）**：行動端字距再加大 → 新增 `@media ≤767.98px` 覆蓋背景文字 letter-spacing 為 **0.05em**（正值，文字分散開）：390px **-3.12px → +3.9px**、414px **+4.14px**；桌面維持 -0.04em（-10.24px）不變；`style-utilities.css?v=20260811e`

---

# 今日任務總覽 (2026-08-10)

## 0. cheesetart.com c-attract 流動選單整合 🎨 — ✅ 2026-08-10

### 已完成

**1. 流動選單（c-attract）整合至全站**
- 逆向分析 cheesetart.com：`.c-attract` 容器（負 margin 擴展 hover 熱區 + `perspective:87rem` 3D 透視）、`.c-attract__layer`（preserve-3d）、UnifiedEffect（hover 3D tilt + elastic 回彈）
- 新增：`static/css/bc-attract.css`、`static/js/bc-attract.js`、`static/images/dots_40.svg`
- 修改：`base.html`（GSAP 全域化 + bc-attract 引用 + `#borders` + `.bc-page-content` wrapper）、`nav.html`（漢堡三條線 + Buy & Order 按鈕）、`index.html`（移除重複 GSAP）

**2. Buy & Order 按鈕（多次反饋調整）**
- 垂直長條 50×225、右側浮動（`right:17px` 中心對齊虛線）、垂直文字 `writing-mode:vertical-lr`
- 純黑 `#000000` 背景、白色 1px 邊框、hover 邊框不變色
- z-index `99999`（最頂，高於虛線 9999）
- hover「吸引」動畫：純位移跟隨游標（`translate3d 48px`）+ proximity 60px 熱區（滑鼠靠近即吸引）；修復 `navigator.maxTouchPoints>0` 誤停用（觸控筆電 hover 失效）

**3. #borders 右側全屏虛線**
- 全高（top 0 → 100%）、`z-index:9999`、`dots_40.svg` mask 點狀、灰色 `rgba(255,255,255,0.5)`
- `pointer-events:none`（不阻擋互動）、中心對齊 Buy 按鈕；左側虛線已隱藏

**4. 浮動購物車（bc-components.css）**
- 縮小 15%（桌面 68→58px、手機 58→49px）、透明→黑底、移除陰影/backdrop-filter、白色邊框
- 徽章縮小 10%（24→22px）、金色背景、白色文字

**5. Buy & Order 按鈕 z-index 最頂、右側虛線在下 修復 ✅（2026-08-10 追加）**
- **根因**：`#ftco-navbar`（`.ftco-navbar-light`）為 `position:absolute + z-index:3`，建立 **stacking context**；`.bc-attract-buy`（z-index:99999）巢狀在 nav 內，被鎖死在層級 3，無法與 body 直接子層的 `#borders`（z-index:9999）比較 → 實際渲染虛線蓋住按鈕
- **修復**（`nav.html`）：把 `.bc-attract-buy` 移到 `</nav>` 之後、body 直接子層（與 `#borders` 同層）→ `99999 > 9999`，按鈕最頂、虛線在下
- `bc-attract.css` 更新註解說明層級關係；`base.html` → `bc-attract.css?v=20260810x`
- ✅ 驗證：/、/coffee_menu/、/bean_menu/、/about/、/cart/、/cart/checkout/ 全站渲染 DOM 順序 `#borders < </nav> < .bc-attract-buy`；CSS z-index 99999 > 9999

**6. 首頁輪播第 3 個橫幅：背景圖片 → 全幅背景影片（無橢圓遮罩）✅（2026-08-10）**
- **需求**：第 3 個橫幅的整面背景圖片（`bg_3.jpg`）改為影片容器填滿整個橫幅，**無橢圓形遮罩**（與第 2 個橢圓 morph 影片呈現方式不同）；影片使用與第 2 個相同的 `roasting.webm`
- **實作**（`index.html` 第 3 個 slider-item + `style-utilities.css`）：
  - 移除 inline `background-image: bg_3.jpg`，改為 `<div class="bc-banner-video loadEnd">` + `<video>`（`roasting.webm` + `data-lazy-video` 延遲載入）
  - **複用 `.bc-banner-video` 基礎樣式**（`position:absolute` 全幅 + `flex` 置中 + `video object-fit:cover` 鋪滿），**不加 `blobsVideo`**（無 morph 橢圓遮罩、無 border-radius）
  - 保留 `.overlay`（黑 0.6）蓋在影片上 → 暗色調
  - 移除 `.bc-banner-video-3 / .banner-stage-3 / .inner-3 / morph-3` 橢圓系列樣式（死碼清理）
- `base.html` → `style-utilities.css?v=20260810b → v=20260810c`
- ✅ 驗證（CDP 375px/1280px）：`background-image: none`、容器 `fills: true`（375×480 / 1265×750 填滿橫幅）、`borderRadius: 0px`、`animationName: none`、切到該格 `paused:false` 正常播放

**7. 浮動購物車徽章上移 3px + 圖示縮小 10% ✅（2026-08-10 追加）**
- 徽章 `.bc-floating-cart-badge`：`top: -3px → -6px`（向上 3px）
- 圖示 `.bc-floating-cart-btn .material-icons`：桌面 `1.5rem → 1.35rem`、手機 `1.3rem → 1.17rem`（×0.9）
- `base.html` → `bc-components.css?v=20260810f → v=20260810g`

**8. 第 3 個橫幅影片容器行動端 CDP 驗證 ✅（2026-08-10 追加）**
- 驗證：行動端 375px + 桌面 1280px 皆 `background-image: none`、影片容器完整填滿橫幅（`fills: true`）、`borderRadius: 0px`（無橢圓）、`animationName: none`（無 morph）、`video.src=roasting.webm`（與第 2 個相同）、切到該格 `paused:false` 正在播放
- 驗證資產：`docs/verify/cdp_verify_slide3.py`

**9. bean_menu 產品區域：A+C 混合不對稱網格（瀑布 × 棋盤翻轉）✅（2026-08-10）**
- **需求**：提供 3 個不對稱網格方案（瀑布交錯 A / 蛇形對角 B / L 形棋盤 C），使用者選 **A+C 混合**
- **布局**：每 3 個一組（DOM = 大 小 小），6 商品 = 2 組：
  - A 瀑布：大卡左側跨 2 欄（`grid-column 1/3`）+ 小卡右側上下、第二張下移錯落（`translateY(4rem)`）
  - C 棋盤：組 2 翻轉（`.bean-mix-flip`：大卡右側 `2/4`、小卡左側）
- **實作**（`bean_menu.html` + `bc-components.css`）：
  - 獨立 class `.bean-mix-*`（不影響 coffee_menu 的 `.coffee-menu-zgrid`）
  - 大卡圖片 340px、小卡 260px（覆蓋 style-bootstrap 36vh）
  - ⚠️ 教訓：小卡定位改用 **sibling 選擇器**（`.bean-mix-main + .bean-mix-sub`），不用 `nth-of-type`（依賴 div 類型計數，main 也是 div 會錯位）
  - 響應式：≤1080px 大卡整行 + 兩小卡並排；≤768px 單欄堆疊
- `base.html` → `bc-components.css?v=20260810g → v=20260810i`
- ✅ 驗證（CDP 375/768/1280px）：組 1 大左小右（1280）、組 2 翻轉大右小左、小卡錯落 64px、平板大卡整行小卡並排、手機單欄、全斷點無溢出；coffee_menu 不受影響
- 驗證資產：`docs/verify/cdp_verify_bean_mix.py`

**10. 首頁第 1 個輪播橫幅 coffee_border_01.svg：增大 40%→再+15%（×1.61）+ 改白色 ✅（2026-08-10）**
- **需求**：第 1 個 slider 內的 `coffee_border_01.svg` 增大、改為白色（後續再增大 15%）
- **SVG**（`static/images/coffee_border_01.svg`）：兩個 path 加 `fill="#ffffff"`（原無 fill = 預設黑色，在深色背景不可見）
- **CSS**（`style-utilities.css`）：只影響第 1 個 slider（`.slider-item.slider-first`）的 `.noise-img`，各斷點 ×1.61（桌面 17vw→27.4vw/min 238→383px、平板 55→88.6vw、手機 65→104.7vw、小手機 75→120.8vw）
- `index.html`：第 1 個 slider-item 加 `slider-first` class；`base.html` → `style-utilities.css?v=20260810e → v=20260810f`
- **⚠️ 教訓**：不用 `.slider-item:first-child`——owl 結構中每個 `.slider-item` 都是其 `.owl-item` 父的 `:first-child`，會**誤匹配全部** slider；用明確 class 標記
- ✅ 驗證（CDP 1280/768/375/320px）：slider1 = 383/383/345/294px（桌面/平板 ×1.61；手機維持 92vw cap = container 滿寬物理極限）；slider3 對照不受影響（238/422/281/240px 原尺寸）；`svg_white: true`、全斷點無溢出
- 驗證資產：`docs/verify/cdp_verify_coffee_border.py`

**11. bean_menu banner 內複製 footer 的 .scroller-box 水平遮罩動畫 ✅（2026-08-10）**
- **需求**：使用 footer 內的水平遮罩動畫 `.scroller-box`，複製到 bean_menu 的 `ftco-subpage-banner` container 內
- **實作**（`bean_menu.html`）：在 banner container 內（icon_text 之後）加入 `.scroller-box > .scroller > ul.tag-list.scroller__inner > 2×li`；文案品牌化「ROASTED FRESH・BREWED FAST・SERVED FRESH・HUG IN A CUP」
- **零新增 CSS/JS**：複用 style-utilities.css 既有 `.scroller-box` 樣式；main.js `querySelectorAll('.scroller')` 全域初始化（自動設 `data-animated=true` + 複製 li 無縫循環）
- **⚠️ 注意**：banner 高度被內容自然撐高（桌面 500→701px、手機 82vw→482px），非 overflow 問題，視覺可接受
- ✅ 驗證（CDP 1280/375px）：`data-animated=true`、li 複製成 4（無縫循環）、`animation: scroll 60s` transform 位移中、footer scroller 不受影響、無水平溢出
- 驗證資產：`docs/verify/cdp_verify_banner_scroller.py`

**12. bean_menu banner 跑馬燈換新：移除 .scroller-box → 自訂 .bc-marquee（Mogra 20px 右→左）✅（2026-08-10）**
- **需求**：移除現有 ftco-subpage-banner 內 .scroller-box，相同位置新增水平跑馬燈（使用者選 Mogra 品牌字 20px、右→左、精簡 padding）
- **實作**：
  - `bean_menu.html`：移除 `.scroller-box`，改為 `.bc-marquee > .bc-marquee__track > 2×.bc-marquee__item`（文案同 ROASTED FRESH・BREWED FAST…）
  - `bc-components.css`：新增 `.bc-marquee` 系列（Mogra 20px、白色、`bcMarqueeScroll 28s linear infinite` 右→左無縫循環、`padding-block 0.75rem` 精簡、`prefers-reduced-motion` 停用）
  - **純 CSS animation**，不依賴 main.js（vs 原 scroller-box 需 JS 複製 li）
- `base.html` → `bc-components.css?v=20260810j`
- ✅ 驗證（CDP 1280/375px）：scroller-box 已移除（`banner_scroller_removed: true`）、bc-marquee 動畫執行中（transform 位移）、banner 高度降低（701→654px、482→438px）、跑馬燈 60px 高（原 107px）、footer 不受影響、無溢出
- 驗證資產：`docs/verify/cdp_verify_bc_marquee.py`

**13. bc-marquee 無縫無限循環修正（移除 item padding）✅（2026-08-10）**
- **問題**：使用者反饋跑馬燈「斷開連接、文字間斷」，需要連續無限循環
- **根因**：`.bc-marquee__item` 有 `padding-inline: 0.5rem` → 兩個 item 接縫處 **1rem 空白**（遠大於文字內部間距），視覺「斷開」
- **修正**：
  - 移除 `.bc-marquee__item` 的 `padding-inline`（0px）
  - HTML item 內容統一用 `&nbsp;` 間距（`ROASTED FRESH&nbsp;•&nbsp;BREWED FAST&nbsp;•&nbsp;...•&nbsp;`），接縫與內部間距一致
  - 無縫保證：2 item 等寬 + track = 2×item + gap 0 + `translateX(-50%)` 恰好一個 item 寬
- `base.html` → `bc-components.css?v=20260810k`
- ✅ 驗證（CDP 1280/375px）：`items_equal_width: true`、`gap_between_items: 0`、`padding 0px`、動畫連續位移（-74→-128 / -83→-137，2.5s）無跳動

**14. bc-marquee 抖動跳動修復（移除 letter-spacing + will-change）✅（2026-08-10）**
- **問題**：使用者反饋跑馬燈「抖動跳動、一段接一段」，需連續無限循環
- **根因**（CDP 診斷）：
  - `letter-spacing: 0.5px` → 每字符非整數字距累積 → item 亞像素寬度差異（604.140625 vs 604.1405639）→ 位移子像素抖動
  - `will-change: transform` → 強制合成層，非整數位移時 GPU 子像素渲染 → 文字抖動
  - `inline-flex` 寬度計算 sub-pixel 間隙
- **修正**：移除 `letter-spacing`、移除 `will-change`、track 改 `display: flex + width: fit-content`（與 footer scroller 一致，寬度確定）
- `base.html` → `bc-components.css?v=20260810l`
- ✅ 驗證（CDP）：`letter_spacing: normal`、`will_change: auto`、`display: flex`、手機 item 完全等寬（`item_equal_exact: true`）；**4 次取樣位移完全均勻**（-90.9→-107.3→-123.7→-140.1，每 800ms -16.4px）、`monotonic: true` 無跳動

**15. bc-marquee 抖動終極修復：JS rAF 整數像素驅動 ✅（2026-08-10）**
- **問題**：CSS animation 的線性插值產生非整數位移（如 -107.306px）→ 文字子像素渲染 → 用戶仍見「一段後重新接一段」抖動
- **根因**：CSS `animation` 每幀插值為小數像素，合成器/繪製對非整數位移的文字做子像素渲染 → 每幀微振動
- **終極方案**（新增 `static/js/bc-marquee.js`）：
  - **JS rAF 驅動**：每幀位移累積（SPEED 0.35px/frame ≈ 21px/s）+ `Math.round()` 到**整數像素** → 文字永遠在整數位置渲染，物理上不可能抖動
  - **模循環**：位移達 -itemW 時 `x += itemW`（連續變數跨越，非動畫重啟）→ item2 對齊 item1 → 無縫無限循環
  - `resize` / `document.fonts.ready` 重算 itemW；`prefers-reduced-motion` 停用；CSS animation 保留為無 JS fallback（JS 接管後 `animation: none`）
- `base.html` → 引入 `bc-marquee.js?v=20260810a` + `bc-components.css?v=20260810m`
- ✅ 驗證（CDP）：`CSS animation: none`（JS 接管）、位移序列 -82,-83,-84... **全部整數**、步進均勻 -1px、模循環連續變數無跳變
- 驗證資產：`docs/verify/cdp_track_marquee_loop.py`

**16. bc-marquee 閃出修復：循環 buffer 取代模循環 ✅（2026-08-10）**
- **問題**：使用者反饋「第1段結尾有間隙、第2段閃出接1段」——模循環 `x += itemW` 跳變時，視窗開頭從「item1 結尾 •&nbsp; + item2 開頭 ROASTED」變成「item1 開頭 ROASTED（無前綴）」→ 「• 」前綴閃失
- **修復**（`bc-marquee.js` v2）：**循環 buffer**——第一個 item 完全移出視窗（`x <= -itemW`）時 `appendChild` 移到 track 尾端 + `x += itemW` 補償 → track 成**環形**，視窗內容任意時刻連續（文字從左緣平滑滑入），無「起點裸露」
  - 確保 ≥3 個 item（視窗寬 < 2×itemW 時右側內容充足）
- `base.html` → `bc-marquee.js?v=20260810b`
- ✅ 驗證（CDP）：item 數 3、`order_before[1] === order_after[0]`（`continuous: true` 視窗內容連續）、transform 整數（-28）無跳變
- 驗證資產：`docs/verify/cdp_verify_marquee_buffer.py`

**17. 首頁第 3 個 slider 影片更改為 coffee_machine.webm ✅（2026-08-10）**
- **需求**：第 3 個輪播橫幅內影片更改為 `coffee_machine`（先 mp4、後改用 **webm**）
- **實作**（`index.html`）：第 3 格 `<source>` → `{% static 'images/coffee_machine.webm' %}` type="video/webm"（webm 8.3MB、時長 20.4s）
- ✅ 驗證（CDP）：`currentSrc: coffee_machine.webm`、`readyState: 4`（可播放）、`video_error: null`、時長 20.4s
- 驗證資產：`docs/verify/cdp_verify_slide3_video.py`

**18. bc-welcome-panel 整體高度降低 15% ✅（2026-08-10）**
- **需求**：index.html 內 `.bc-welcome-panel` 整體高度降低 15%
- **實作**（`bc-components.css`）：各斷點高度相關元素等比縮小 ×0.85：
  - 桌面：padding 14→12px、avatar 46→39、info gap 10→8、greeting 1→0.85rem、points 0.9→0.77rem、imgbox min-height 97→82、img 160→136/top -92→-78、img-link 同步
  - 平板 ≤768：padding 7→6、avatar 47→40、imgbox 86→73、img 140→119/-77→-65
  - 手機 ≤480：padding 6→5、avatar 41→35、imgbox 70→60、img 98→83/-45→-38
- `base.html` → `bc-components.css?v=20260810n`
- ✅ 驗證（CDP 量測）：桌面 **125→106px**（-15.2%）、平板 **100→85px**（-15%）、手機 **82→70px**（-14.6%）精確達成
- 驗證資產：`docs/verify/cdp_measure_welcome.py`

**19. 隱藏導航選單「登入」✅（2026-08-10）**
- **需求**：隱藏導航選單中的「登入」
- **實作**（`nav.html`）：未登入狀態的「登入」dropdown-item 加 `hidden` 屬性（與「註冊」一致）
- ✅ 驗證：渲染後 `<a hidden class="dropdown-item" href="/accounts/login/">`；首頁 bc-welcome-panel 的登入連結保留（非導航選單）

**20. bc-welcome-greeting/points 縮放動畫：加入後依使用者指示移除 ✅（2026-08-10）**
- **需求（後撤銷）**：greeting/points 初始縮小→放大動畫（使用者最終指示「不需要動畫」→ 移除）
- **曾實作**：`transform: scale(0.5→1)` + opacity（不動 font-size、不需 !important、順序放系列後）；0.6s ease both
- **移除**：`bc-components.css` 刪除 `bcWelcomePop` 規則（無殘留）；`base.html` → `bc-components.css?v=20260810p`
- ✅ 驗證：grep 無 `bcWelcomePop` 殘留

**21. bc-welcome-greeting/points 文字大小抖動修復：rem → 固定 px ✅（2026-08-10）**
- **問題**：使用者反饋 greeting/points「初始狀態時文字大小抖動」
- **根因**：兩者用 **rem 單位**，而 `responsive-system.css`（最後載入）設定 `html { font-size: clamp(14px, 0.3vw+13.5px, 16px) }` → 載入時 bc-components 先以預設 16px 計算、responsive-system 後載入覆蓋 html 基準 → **rem 重新計算 → 文字大小跳變**（視窗 <1280px 時 clamp≠16px 必發生）
- **回答用戶**：CSS 順序有影響（html clamp 後載入）；**!important 無法解決**（擋不住 html font-size 變化對 rem 的影響）
- **修復**：greeting/points 改用**固定 px**（脫離 rem/html clamp 依賴）：桌面 14/13px、≤768 13/12px、≤480 8/8px
- `base.html` → `bc-components.css?v=20260810q`
- ✅ 驗證：三處 font-size 皆 px（10 個匹配）；⚠️ 若仍抖動可能是字體載入 FOUT（`display=swap` 交換 fallback 字體）

**22. 文字抖動最終修復：Google Fonts display=swap → display=block（消除 FOUT）✅（2026-08-10）**
- **問題**：px 化後 greeting/points 硬刷新仍輕微抖動，`.bc-search-txt` 也出現同樣問題
- **根因**：**FOUT（字體載入交換）**——base.html 用 `display=swap` → fallback 字體先顯示、Noto Sans TC/Mogra 載入後**交換** → 字寬變化 → 文字大小抖動（greeting/points/bc-search-txt 皆繼承 Noto 字體）
- **修復**（`base.html`）：Google Fonts URL `display=swap` → **`display=block`** → 字體載入前文字隱藏、載入後顯示 → **無 fallback→目標交換 → 徹底消除抖動**
- **取捨**：首次載入字體前文字短暫空白（延遲顯示）；之後瀏覽器快取即時顯示
- ✅ 驗證：渲染 HTML 含 `display=block`

**23. 全域文字穩定修復：`<html>` inline font-size clamp + 審計腳本 ✅（2026-08-10）**
- **需求**：創建腳本直接執行和測試全域網站「載入時文字大小跳變/抖動」，一起修復全域文字穩定
- **審計**（`scripts/audit_text_stability.py`，可直接執行）：
  - 全域 CSS 有 **339 個 `font-size: rem`**（11 檔案）→ 全部依賴 html font-size clamp
  - 檢查 base.html 標記 + HTTP 渲染 7 個主要頁面（首頁/菜單/豆/關於/購物車/結帳/登入）
- **根因**：rem 依賴 html clamp，而 responsive-system.css 最後載入覆蓋基準 → 載入時 rem 重新計算跳變
- **修復**：`base.html` 的 `<html>` 加 **inline `style="font-size: clamp(14px, 0.3vw + 13.5px, 16px)"`** → HTML 解析即設定基準，所有 rem 元素載入即穩定（不依賴 CSS 順序，保留響應式縮放）
- 清理 base.html 含 `display=swap` 的死碼註解（Playfair）
- ✅ **審計結果：全部通過**（html inline + display=block + 無 swap 殘留 + 7 頁面渲染）
- 審計資產：`scripts/audit_text_stability.py`

**24. bc-welcome-panel：avatar +15%、文字加大、容器高度保持 ✅（2026-08-10）**
- **需求**：1) `.bc-welcome-avatar` 增加 15% 2) greeting/points 文字加大 3) **bc-welcome-panel 保持現有容器高度**
- **實作**（`bc-components.css`）：
  - avatar：桌面 39→**45px**、≤768 40→**46px**、≤480 35→**40px**（+15%）；icon 隨容器加大（1.8/1.5/1.25rem）
  - 文字：greeting 14→**16px**、≤768 13→**15px**、≤480 8→**10px**；points 13→**15px**、≤768 12→**14px**、≤480 8→**10px**
  - **高度保持原理**：容器高由 imgbox（82/73/60）+ padding 決定；左側 avatar（45/46/40）+ 文字（~50px）皆 < imgbox → 不撐高
- `base.html` → `bc-components.css?v=20260810r`
- ✅ 驗證（CDP 量測 1280/768/375px）：容器高度**保持 106/85/70px** 不變；avatar 45/46/40（+15%）；文字 16/15、15/14、10/10（手機實測 10px）
- 驗證資產：`docs/verify/cdp_measure_welcome.py`

**25. bc-welcome-imgbox 圖片與 last-order 文字水平對齊修復 ✅（2026-08-10）**
- **需求（使用者澄清）**：圖片（wakemeup/產品圖）與 `.bc-last-order` 文字的對齊（非容器內垂直位置）
- **問題**：圖片 `.bc-welcome-img` 用 `right: 0`（靠右）→ 圖片中心偏右：桌面 **12px**、手機 **6px**（平板 img=imgbox 等寬故對齊）；last-order 文字居中 → 圖片與文字水平中心不對齊
- **修復**（`bc-components.css`）：`.bc-welcome-img` / `.bc-welcome-img-link` 改 `left: 50% + translateX(-50%) + right: auto`（水平居中於 imgbox）
- `base.html` → `bc-components.css?v=20260810t`
- ✅ 驗證（CDP 1280/768/375px）：**centerX_diff = 0**（圖片中心 = 文字中心，精確水平對齊）；圖片底部距文字頂 2-6px（視覺連續）
- 驗證資產：`docs/verify/cdp_measure_welcome.py`

**26. /accounts/login/ deco_01.svg 抖動修復 + 改白色 ✅（2026-08-10）**
- **需求**：1) deco_01.svg 初始載入時抖動 2) deco_01.svg 改為白色
- **抖動修復**（`templates/account/login.html`）：deco_01 背景移除 `noise_animation` class（`desktop_noise_animation 1s infinite` 噪點 filter 動畫是抖動源）→ 靜態背景
- **改白色**（`static/images/deco_01.svg`）：`.st1/.st2` stroke `#000 → #ffffff`；根 svg 加 `style="fill: #ffffff"`（無 class path 填充變白）→ 深色背景可見
- ✅ 驗證：SVG `#ffffff` 2 處、無 `#000` 殘留；login 頁 deco_01 無 noise_animation（剩餘 2 個為全域 noise-filiter 容器）；socialaccount/signup 也使用 deco_01 同步受益
- **追加修復（2026-08-10）**：使用者反饋「仍抖動、CSS 順序？」→ **非 CSS 順序問題**，根因是 **Stellar.js 視差**（`data-stellar-background-ratio="0.73"`，blank.html 繼承 base.html 載入 `parallaxBackgrounds`）→ 移除該屬性 → CDP 驗證 `stable: true`（background-position/left 恆定、animation none）

**27. bc-welcome 登入後顯示 username + 積分連結 ✅（2026-08-10）**
- **需求**：1) greeting 顯示客戶名字 `Hey, (username) 歡迎回來, 喝返杯先!` 2) 積分文字改為 `當前積分可以減免 -5 訂單及帳戶詳情`（「訂單及帳戶詳情」為文字連結）
- **實作**：
  - `index.html`：greeting 加 `{{ user.username }}`（Django auth context processor 提供）；points 改文字 + `<a href="{% url 'socialuser:profile' %}" class="bc-welcome-link">訂單及帳戶詳情</a>`
  - `bc-components.css`：新增 `.bc-welcome-points .bc-welcome-link` 樣式（金色、下底線、hover 變亮）
- `base.html` → `bc-components.css?v=20260810u`
- ✅ 驗證（Django test client 登入 kei）：`Hey, kei 歡迎回來, 喝返杯先!`、`當前積分可以減免 -5`、連結 `/profile/`、Buddy 區塊登入後消失、HTTP 200

**28. bc-welcome-panel 容器寬度 -5% ✅（2026-08-10）**
- **需求**：bc-welcome-panel 容器寬度 -5%（使用者澄清：非 -15%）
- **實作**（`bc-components.css`）：桌面 `max-width: 630→599px`、平板 `width: 92→87%`、手機 `width: 96→91%`（×0.95）
- `base.html` → `bc-components.css?v=20260810w`
- ✅ 驗證（CDP 1280/768/375px）：寬度 630→**599px**（-4.9%）、670→**633px**（-5.5%）、322→**305px**（-5.3%）；高度 106/85/70 保持、avatar/文字/圖片對齊不受影響

**29. bc-welcome-greeting 登入後文案與字重調整 ✅（2026-08-10）**
- **需求**：1) `Hey, (username) 歡迎回來, 喝返杯先!` → `歡迎回來 (username) , 喝返杯先!` 2) 字重：歡迎回來(300)、username(400)、, 喝返杯先!(300)
- **實作**：
  - `index.html`：greeting 拆三個 span（`.bc-greet-normal`×2 + `.bc-greet-user`）
  - `bc-components.css`：`.bc-greet-normal { font-weight: 300 }`、`.bc-greet-user { font-weight: 400 }`
- `base.html` → `bc-components.css?v=20260810x`
- ✅ 驗證（Django test client 登入 kei）：文案 `歡迎回來 kei , 喝返杯先!`、span 結構正確、Hey 已移除
- **追加（2026-08-10）**：歡迎回來 與 (username) 之間新增間距 → `.bc-greet-user` 加 `margin-left: 6px`、移除 span 內前導空格；`base.html` → `bc-components.css?v=20260810y`；test client 驗證 username 內容 `'kei'` 無前導空格
- **追加2（2026-08-10）**：文案改為 `歡迎回來!`（加驚嘆號）與 `, 喝返杯先~~`（!→~~）；test client 驗證完整 `歡迎回來!kei, 喝返杯先~~`

### 涉及檔案
- 新增：`bc-attract.css`、`bc-attract.js`、`bc-marquee.js`、`dots_40.svg`
- 修改：`bc-components.css`、`style-utilities.css`、`base.html`、`index.html`、`nav.html`、`bean_menu.html`、`coffee_border_01.svg`

### 待辦（後續 session）
- 咖啡/咖啡豆詳情頁按鈕間距（進行中，CSS 覆蓋/順序診斷）
- SALON SEARCH 背景圖可替換、search_txt 文案可品牌化
- c-attract 漢堡選單動畫目前僅視覺（三條線 tilt），可考慮加展開動畫

---

## 1. SALON SEARCH 區塊整合 + 菜單網格響應式優化 🎨 — ✅ 2026-08-10

### 已完成（6 項任務）

**1. bean_menu 使用 Z 字對角網格（與 coffee_menu 相同）**
- `bean_menu.html`：extends 改 `layouts/blank.html`、商品區替換為 `.coffee-menu-zgrid`（每 4 個一組 = 大 小 小 大）
- 零新增 CSS：完全複用 `.coffee-z-*`（bc-components.css）響應式規則
- ✅ 驗證：cell 結構與 coffee_menu 逐標籤一致、7 斷點響應式狀態一致、無溢出

**2. title_bg_img_02.svg 行動端裁切修復**
- 根因：`.svg-bg-2` 基礎 `background-size:cover` + 手機 `width:300px` → 直式 SVG 放大裁切
- 修復（`responsive-system.css` + `base.html?v=20260809k`）：≤767px 手機改 `auto+650px+top:-20px`（與 `.svg-bg` 一致）
- ✅ 驗證：375/767px 兩頁一致無裁切；桌面維持 cover 不受影響

**3. 移除「所有咖啡/所有烘焙豆」section**
- `coffee_menu/bean_menu.html` 移除 `.bc-coffee-all-grid` section；`responsive-system.css` 清理 -46 行
- ✅ 驗證：兩頁無 bc-coffee 殘留、Z 網格保留、無溢出（`base.html?v=20260809l`）

**4. ani_bean_line_il 動畫全頁面橫跨修復**
- 根因：`absolute` 無 `left/top` 落在 `.post_archive`（flex row-reverse）→ static position 偏移（只顯示 2/3）
- 修復：移到 `.ftco-subpage-section` 直接子層 + `left:0 + width:100vw`；selector 加 `.ftco-subpage-section >`
- ✅ 驗證：1280/768/390px 全寬、無溢出（`animate-custom.css?v=20260810a`）

**5. demido.jp SALON SEARCH aside 整合至首頁**
- 新增 `bc-search.css/js` + `search_img01/02/03.png`（咖啡圖替代）+ `bc_search_txt_pc/sp.svg`；引入 GSAP CDN
- `index.html` 加 `<aside class="bc-search">`（連結→coffee_menu、文字品牌化、SALON_SEARCH SVG 保留原樣）
- ✅ 驗證：桌面 480px/手機 1160-900px、PC/SP 標題切換、hover is-on/is-out 正常、無溢出

**6. SALON SEARCH 滑鼠移出動畫修復**
- 根因 1：`.is-out` 缺 transform（demido 有 -60%/-60%/-150%）；根因 2：JS `transitionDuration` 恆 0s 中斷動畫
- 修復：補 is-out transform（桌面/手機 SP 位移）+ JS 改監聽 `transitionend` + `setTimeout` 保險 + `done` 旗標
- ✅ 驗證：CDP 追蹤 transform 序列完整播放（is-on 浮入→is-out 上移→1.3s 重置）（`index.html?v=20260810b`）

## 1. SALON SEARCH 後續視覺與動畫調整 🎨 — ✅ 2026-08-10（commit 927e84f 已推送）

### 已完成（多輪反饋調整）

**1.1 取消 hover 容器上移**
- `.bc-search-link:hover` 移除 `transform: translateY(-2px)`，只保留 box-shadow
- ✅ 驗證：hover 前後 Y 座標不變、背景圖 is-on 動畫仍正常

**1.2 容器背景改白色 → 後改深色**
- 容器 `background-color: #ffffff`（白底），文字同步改深色
- 之後（依使用者後續指示）容器實際渲染為深色 `rgb(23,22,23)`
- 背景圖 `opacity: 0.7` + 模糊柔化

**1.3 icon hover 動畫對齊 demido**
- 根因：keyframes 用錯（兩段式跳動 vs demido 左下角滑入）
- 修正：`@media(hover:hover)` 包裝、`ease-out-expo`（cubic-bezier(0.19,1,0.22,1)）、`scale(0.9) translate3d(0,0,0)`、箭頭 `translate3d(-300%,300%,0)`→原位
- ✅ 與 demido 原始效果一致

**1.4 img-01 位置修復（中間產品圖看不見）**
- 根因：`top:-258px` 過大 → 圖片完全在容器頂部外（y:-243），被 overflow:hidden 裁切 → 看似「沒有模糊/沒顯示」
- 修復：img-01 `top:-30px`、img-02 `top:-20px`
- ✅ 三圖皆在容器內可見

**1.5 滑鼠移出不流暢卡頓修復**
- 根因：img-01/img-02 is-out 位移不足（-60%），圖殘留容器內（img-01 底部 172px、img-02 445px）
- 修復：img-01 is-out `-150%`、img-02 `-120%`（完全移出）
- JS `hide()` 簡化為單一 `setTimeout(1500ms)` 移除 class
- ✅ CDP 幀追蹤：is-out 平滑移出→class 移除回初始隱藏，無卡頓

**1.6 標題替換為 branding Deco 文字**
- 移除損壞的 SALON_SEARCH SVG（先前 Python 替換產生重疊 `<svg><svg>`，24KB 非法 HTML）
- `.bc-search-ttl` 改為：
  - `Between Say:`（Mogra 字體、金色 `--bc-gold`）
  - `We made the rules,<br>No bullsh*t.....<br>Just good Caffeine!!`（Playfair 字體）
- 響應式：≤768px / ≤575.98px 漸進縮放

**1.7 文字顏色調整**
- 主文案 `.bc-search-ttl-message`：白色 `#ffffff`（深色容器上可讀）
- 底部說明 `.bc-search-txt`：灰色 `rgba(255,255,255,0.7)`
- Between Say: 標籤：金色

**1.8 背景圖模糊調整**
- img-01（中間產品圖）：**取消模糊**（`filter:none`，清晰）
- img-02/img-03：`blur(3px)`（輕柔模糊）

### 涉及檔案
- `static/css/bc-search.css`、`static/js/bc-search.js`、`templates/betweencoffee_delivery/index.html`
- commit `927e84f` 已推送（`f1f4dea..927e84f main -> main`）

### 待辦（後續 session）
- 咖啡/咖啡豆詳情頁按鈕間距（進行中，CSS 覆蓋/順序診斷）
- SALON SEARCH 背景圖如需更換其他咖啡圖可直接替換 search_img*.png
- search_txt_pc/sp.svg 內為 DEMI DO 英文文案（保留原樣），如需品牌化可再調整
- SALON SEARCH 主標題文字目前為「Between Say: We made the rules...」，可依品牌需求再調整

---

# 今日任務總覽 (2026-08-04)

## 0. 新 Landing Page（landing_v3）🎨 — 進行中（續）

### 已完成
- 建立 `templates/betweencoffee_delivery/landing_v3.html`（複製 index.html 改造，原始 index.html 未動）
- `betweencoffee_delivery/views.py` LandingNew → 渲染 `landing_v3.html`；`/landing/` 路由
- 快速下單容器改造為深金容器（#6b4f2a、圓角16px、居中疊加 banner）
- 左側：user icon「Hey, 歡迎回來, 隨時來一杯」+「您的當前積分可以減 -5」（白字）
- 右側：wakemeup.png **230px**、浮出容器右上角（以 panel 為錨點 absolute，top:-48px right:-36px）
- 圖片底部居中「(icon) 上次訂單慣常口味」（margin-top + width:100% + text-align:center）
- 容器縮小：寬度 **70% + max-width:819px（-30%）**、高度 **padding 14px 22px（-15%）**、margin:0 auto 居中
- 瀏覽器驗證 ✅（819px / 210px / 居中 / 230px 圖片浮出 / 文字置中）

### 下次續做（新 session）
- 繼續修改該 Landing UI（用戶將於新 session 指示）

---
# 今日任務總覽 (2026-08-03)

## 0. 訂單/付款頁面 UI 統一修復 🎨 — ✅ 2026-08-03（晚上）

### 0.1 Cash 付款頁面圖標調整
- `fa-money-bill-wave` 圖標：尺寸調整為 **78px**（桌面 + 行動一致）
- 新增 `.payment-icon-cash` class（bc-components.css）

### 0.2 訂單確認頁 4 個支付 Icon 統一
- 新增 `.bc-payment-label-icon` 獨立 class（**1.3rem**、品牌金色）
- 與文字**水平對齊**（`.payment-label-text` 設 `display:inline-flex; align-items:center` + `gap:12px`）

### 0.3 訂單確認頁背景文字改為與 coffee.html 相同機制
- 用 `data-bg-text` + `.bc-section-with-bg-text`（`::before` 偽元素）取代 `<span class="title-bg-head-v3">`
- **位置**：獨立 div 置於導覽列與內容之間（content 開頭）
- **高度 0 不佔文件流**（`.bc-bg-text-top { height:0 }`），主內容不再被向下推
- **頂部**：`top: 150px`；**大小**：`16vw`；**左側**：`left: 1vw`
- **CSS 順序**：`.bc-bg-text-top::before` 必須在 `.bc-section-with-bg-text::before` 之後覆蓋

### 0.4 profile 3 頁面導航列統一（與卡片同寬）
- `profile.html` / `loyalty_dashboard.html` / `order_history.html`
- 導航列容器：`col-12 col-lg-8`（與下方卡片 `col-lg-8` 一致，原為全寬 col-12）

### 0.5 會員導航列響應式統一修復
- **移除** `member_nav.html` 的 inline `<style>`（與全局 @media 衝突造成行動螢幕縮放異常）
- **統一在 bc-components.css 管理**：
  - 容器：`display:flex; width:100%`（撐滿父欄）
  - 按鈕：`flex:1` 均分、文字置中、`white-space:nowrap`、span 省略號保護
  - 移動（≤576px）：`flex:1 1 auto`、`padding:10px 12px`、`font-size:0.85rem`（文字不縮放、激活狀態正常）

### 0.6 涉及檔案（9 個）
- `eshop/templates/eshop/cash_payment.html`
- `eshop/templates/eshop/order_confirm.html`
- `socialuser/templates/socialuser/includes/member_nav.html`
- `socialuser/templates/socialuser/loyalty_dashboard.html`
- `socialuser/templates/socialuser/order_history.html`
- `socialuser/templates/socialuser/profile.html`
- `static/css/bc-components.css`
- `static/css/style-custom.css`
- `static/css/style-utilities.css`

## 1. MCP 伺服器修復 🤖 — ✅ 2026-08-03
- **django-manager MCP**：
  - 原因：設定指向 `django-mcp-server.js` 但檔案不存在（MODULE_NOT_FOUND）
  - 修復：建立新 `django-mcp-server.js`（django_run_command / django_order_info / django_queue_status / django_recent_orders）
  - 技術：SDK exports 攔截 bare specifier 導致路徑重複 → 絕對路徑載入 SDK + zod
- **chrome-devtools MCP**：
  - 原因：預設找 Google Chrome stable 但未安裝
  - 修復：`--executable-path=/snap/bin/chromium` + `--isolated`（臨時 profile）
  - 驗證：手動啟動成功開頁

## 2. 全站行動響應式修復 📱 — ✅ 2026-08-03
- 支付確認頁 Y 軸滾動條（.svg-bg-4 → 還原原始結構）
- 行動導航背景透明化（.navbar.ftco-navbar-light.bg-dark → transparent）+ 漢堡圖標白色
- profile 3 頁面 body 外部邊距（.svg-bg-container overflow:hidden）
- .ftco-section-blank-small 響應式（991/768/480 三級漸進）
- FPS/Cash 付款頁按鈕（flex 容器 + CTA +12%/-12% + 行動 56%/44%）
- FPS 付款頁 logo：fps-logo.png → fps_icon.svg（128px 桌面 / 110px 行動）
- 支付確認頁頂部圖標：fa-badge-check（Pro-only 方塊）→ fa-circle-check（Free）

## 3. 推送狀態
- **GitHub 待推送**：全部變更（MCP + 響應式 + 付款頁 UI + docs）

---

# 歷史任務總覽 (2026-08-01 ~ 2026-08-02)

## 1. 全站安全修復 🔐

### 1.1 敏感憑證洩漏處理（最嚴重）— ✅ 2026-08-01
- 從 git 追蹤移除 4 個金鑰檔案：
  - `keys/alipay_private_key.pem`、`keys/alipay_public_key.pem`
  - `betweencoffee_delivery/keys/private.key`、`betweencoffee_delivery/keys/public.key`
- `.gitignore` 加入 `keys/`、`betweencoffee_delivery/keys/`、`*.pem`、`*.key`、`*.crt`
- `settings.py` 移除明文密碼註釋（DeepSeek API key、PayPal 密碼、支付寶帳號密碼、Supabase 密碼、手機號）
- `settings.py` 移除硬編碼 PayPal Client ID/Secret（僅從環境變數讀取）

### 1.2 DebugMiddleware 個資洩漏修復 — ✅ 2026-08-01
- 從 `MIDDLEWARE` 移除（不再記錄訂單 POST 電話/地址/個資與 Session）

### 1.3 加入 HSTS + Referrer Policy — ✅ 2026-08-01
```python
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
```

### 1.4 強化密碼驗證 — ✅ 2026-08-01
- 加入 `CommonPasswordValidator` + `NumericPasswordValidator`

### 1.5 IDOR / 未授權訪問漏洞修復 — ✅ 2026-08-01（20:52）
**🔴 嚴重：訂單 IDOR（可直接存取他人訂單）**

| 漏洞 | 檔案 | 修復內容 |
|------|------|---------|
| `api_cancel_order` 取消任意訂單 | `payment_views.py` | 加入訂單所有權驗證（登入用戶只能取消自己的；訪客只能取消 session 中的） |
| `OrderConsumer` WS 查看任意訂單 | `consumers.py` | 加入 `_check_order_access()`：員工可看所有、登入用戶只能看自己的、訪客拒絕連線 |
| `QueueConsumer` WS 隊列資料暴露 | `consumers.py` | 只允許員工（is_staff）連線 |
| `ws_fallback_api` 查詢任意訂單+取餐碼 | `websocket_views.py` | 加入所有權驗證（登入用戶只能查自己的、訪客只限 session、員工可查所有）+ 隊列僅員工可看 |

**🟡 中等：缺少權限保護的 API**

| 端點 | 修復內容 |
|------|---------|
| `get_recent_orders` | 加入 `@login_required` |
| `get_active_orders` | 加入 `@login_required` |
| `update_order_pickup_times_api` | 加入 `@staff_api_required` |
| `generate_fps_qr_api` | 加入 `@login_required` |

**驗證結果（2026-08-01 21:02）：**
- ✅ `python manage.py check` — 通過
- ✅ 56 個既有單元測試全部通過（test_status_display + test_payment_handler + test_audit_logger + test_whatsapp_notifier）
- ✅ **新增 27 個安全驗證測試全部通過**（`eshop/tests/test_security_fixes.py`）：
  - 5 個 `api_cancel_order` IDOR 測試（訪客/用戶A/用戶B/員工）
  - 4 個 `OrderConsumer` 訂單所有權測試
  - 3 個 `QueueConsumer` 員工權限測試
  - 8 個 `ws_fallback_api` IDOR + 隊列權限測試
  - 4 個 API 端點權限保護測試
  - 3 個安全標頭測試
- 🔄 待部署到 Render 後進行生產環境驗證

## 2. 支付寶金鑰輪換 🔑

### 已完成
- openssl 生成新 RSA2 金鑰對（2048-bit）
- 用戶在支付寶控制台完成「加簽變更」：上傳新應用公鑰 + 取得新支付寶公鑰
- 更新本機 `keys/alipay_private_key.pem`（新私鑰）+ `keys/alipay_public_key.pem`（新支付寶公鑰）
- `settings.py` 改為環境變數優先 `read_alipay_key()`（Render 用環境變數，本地 fallback 到 keys/ 檔案）
- 從 `.env` 移除不匹配的舊私鑰 + 單行 PEM 格式問題
- **Render 環境變數已設定**：
  - `ALIPAY_APP_PRIVATE_KEY` = 新私鑰
  - `ALIPAY_PUBLIC_KEY` = 新支付寶公鑰
  - 已透過 Render API 觸發部署（需用戶手動 Deploy latest commit，因 autoDeploy=off）

## 3. FPS 付款頁面 UI 修改 📄
- 新增「商品明細」+「訂單資訊」區域（與 Cash 頁面一致，位於付款說明上方）
- 隱藏參考編號（不顯示給客戶）
- 付款說明組件改為全寬（與商品明細同寬）
- 按鈕樣式統一為 `calltoaction-btn px-4 py-3`
- 主按鈕（我已完成支付）：金色 `btn-primary btn-outline-primary`
- 返回修改按鈕：灰色 `btn-outline-secondary`（預設 + 懸停皆灰框灰字）

## 4. Cash 付款頁面 UI 修改 📄
- 付款說明組件改為全寬（與商品明細同寬）
- 確認訂單按鈕：金色 `calltoaction-btn`
- 返回修改按鈕：灰色（同 FPS）

## 5. 咖啡/咖啡豆詳情頁按鈕間距 🛠️（進行中）
- `coffee.html` / `bean.html`：立即購物與加入購物車按鈕之間添加空間
- 已嘗試 `mr-3`（可能被 CSS 覆蓋）、`gap: 1rem`（inline style）
- **狀態：用戶反饋仍未修復，需進一步診斷 CSS 覆蓋/順序問題**

## 6. 推送狀態
- 安全修復（第一階段：金鑰移除 + settings.py）已 commit `46fb0d3` 並 push ✅
- 安全修復（第二階段：IDOR + 未授權訪問）已 commit `52038ef` 並 push ✅
  - 4 個檔案修改（consumers.py / api_views.py / payment_views.py / websocket_views.py）
  - 155 行新增、14 行刪除
- 後續 FPS/Cash UI 修改 與 coffee/bean 按鈕（尚未 commit/push）
- 註：`eshop/tests/test_security_fixes.py` 因 `.gitignore` 的 `test_*.py` 規則未被追蹤（符合既有設計）

## 7. 優先處理徽章大小統一 — ✅ 2026-08-01（21:12）
- **問題**：員工頁面只引用 `staff_order_management.css`，優先處理徽章使用 Bootstrap 默認 `badge badge-warning`（font-size 75%，太小）
- **修復**：
  - `staff_order_management.css` 新增 `.badge-expedited`（品牌金色、font-size:0.85rem、較大內距）
  - 統一 4 個 JS 檔案：`queue-manager.js` / `preparing-orders-renderer-v2.js` / `ready-orders-renderer-v2.js` / `completed-orders-renderer-v2.js`

## 8. WhatsApp 通知失效診斷 — 🔴 2026-08-01（21:15）
- **問題**：客戶訂單「已就緒」時，WhatsApp 就緒通知不起作用
- **診斷結果**：**Token 已於 2026-07-27 過期！**
  - 錯誤：`Session has expired on Monday, 27-Jul-26 08:00:00 PDT`
  - 環境變數已設定（WHATSAPP_ENABLED=True、token 長度 300、PHONE_NUMBER_ID=1260339307158166）
  - Graph API `/me` 回傳 HTTP 401
- **解決方法**（需用戶手動操作）：
  1. 前往 https://developers.facebook.com/apps/ → 你的 App → WhatsApp → API Setup
  2. 重新生成 Access Token
  3. 更新本機 `.env` 的 `WHATSAPP_TOKEN`
  4. 更新 Render 環境變數 `WHATSAPP_TOKEN`（Render Dashboard）
  5. 重新部署
- **驗證**：`python test_whatsapp_diagnosis.py`（診斷腳本已建立）

- **✅ 已修復（2026-08-01 21:22）**：
  - 用戶提供新 Token，已更新根目錄 `.env` + `betweencoffee_delivery/.env`
  - Graph API `/me` 驗證 HTTP 200，帳號 Employee
  - ⚠️ 需更新 Render 環境變數 `WHATSAPP_TOKEN`

## 9. 訂單狀態卡 Icon 全面優化 — ✅ 2026-08-02（00:10）
- **問題**：狀態卡 icon 前後端衝突（獎盃閃爍後變雙勾）
- **修復**（4 檔案一致）：
  - `eshop/models/order.py` 第 314 行：已完成 icon → `fa-circle-check`
  - `order_payment_confirmation.html` 第 169 + 244 行：已完成 → `fa-circle-check`
  - `static/js/order_status_cards.js` 第 699 行：動態更新 → `fa-circle-check`
- **icon 全面更新**：
  - 製作中：`fa-coffee` → `fa-mug-hot`（冒煙熱咖啡）
  - 待取餐：`fa-check-circle` → `fa-bell`（鈴鐺）
  - 已完成：`fa-trophy`/`fa-check-double` → `fa-circle-check`（圓圈勾選）
- **最終流程**：`📋 fa-clipboard-check → ☕ fa-mug-hot → 🔔 fa-bell → ✅ fa-circle-check`
- **其他**：優先處理徽章 `.badge-expedited` 統一、WhatsApp Token 更新、測試診斷工具
- **驗證**：`grep fa-trophy` 無殘留、`python manage.py check` 通過
