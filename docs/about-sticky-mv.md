# `/about/` 首屏 sticky MV 實作細節（bc-sticky-mv）

> 移植 `yurumaru.life` 的 `.page-top__mv__wrap`：`position: sticky` 影片釘住一屏 + 產品照弧形輪播。
> `templates/betweencoffee_delivery/about.html` 最上方引用；對應 `static/css/bc-sticky-mv.css`、
> `static/js/bc-sticky-mv.js`（原生 JS 重寫 Splide：autoplay 4s、前後複本循環）。
> 概要規則在 `.clinerules/project-core.md` §3；本檔只放「改了會壞」的細節。

## 1. 尺寸變數

| 變數 | 值 | 說明 |
|---|---|---|
| `--mv-vh` | `100vh` → `100svh` | 手機工具列會讓 `100vh` > 可見高；`--mv-len`／`--mv-text-h`／影片高／負 margin 全吃它 |
| `--mv-len` | `--mv-vh × 2` | 一屏釘住 + 一屏滑過 |
| `--mv-text-h` | `× 0.64`（≤680 `× 0.6`） | 文字區高度 |
| `--mv-lift` | `200px`（≤680 `150px`） | 文字區 `min-height` 扣掉此值 → 產品列整組上移（`min-height` 是下限，不會壓字） |
| `--mv-pull` | `32px`（≤680 `22px`） | **產品列自身負 margin**：`--mv-lift` 在文字內容高於 `min-height` 的寬度（1280/1440 實測 398>312、416>376）完全無效，故另設獨立上移量，所有寬度都確實上移 |
| `--mv-per/gap/pad` | 見下表 | 張數／間距／左右留白 |
| `--mv-card-cap` | `vh × 0.30`（平板 `.335`／手機 `.42`） | **卡片寬上限（高度預算）**；生效時 `--mv-pad-eff` 自動加大留白保持置中 |
| `--mv-stage-gap` | `clamp(4.5rem, 18vh, 12rem)`（≤680 `clamp(3.5rem, 13vh, 7rem)`） | 產品列 ↔ `.mv-stage`（Fresh beans）的間隔。原本寫死 `5vh`（1440×900 只有 46px）→ 2026-11-04 第一輪 9vh（81px）→ 第二輪 14vh（126px）→ 使用者「再次加大」後為 18vh（同尺寸 162px、1920/1440×1080 為 192px、1280 為 144px、768 為 184px、390 為 103px）。下方 `.page-top__mv__foot` 是 `margin-top:auto` 貼底，吃掉中間彈性空白 → **加大不影響 `#bc-sticky-mv` 高度（仍為 2 屏）**，也仍有充裕空間（1440 stageBottom 1368 vs foot 1800） |
| `--mv-gap` / `--mv-pad` | 見下表 | 組與組的間距／左右留白。**兩者互補**：卡片寬＝`(100vw − 2pad − (per−1)gap)/per`，只拉大 gap 會讓卡片（＝照片）變小，故 per=3 用 `Δpad = −Δgap`、per=2 用 `Δpad = −Δgap/2` 同時調整。2026-11-04 三輪：8→12vw（pad 10→8vw）→ 使用者「略微減少間隔」→ 10vw／9vw（比原始 8vw 仍大 25%） |

斷點：≥1440 `3 / gap 10vw / pad 9vw`、1025–1439 `3 / 8 / 5.5`、681–1024 `2 / 8 / 4.5`、≤680 `1 / 13 / 13`（gap 對 per=1 不影響卡片寬）。實測卡片寬：1920 324、1440×1080 298、1440×900 270、1366 230、1280 240、1024 257、768 319、390 289（皆與拉開間距前一致，因為 gap 與 pad 互補）。

## 2. 地雷

- **照片 `max-width`**：原站 `.p-image` 是固定 `240px` → 卡片再寬照片也停在 240px（平板／桌機看起來像「沒放大的桌機版」）。現為 `400px`。
- **卡片高度**：照片放大 → 3:4 卡片變高，1280×800 會把品名推出第一屏（實測 `nameBottom` 897 > 800）。故卡片寬取 `min(寬度公式, --mv-card-cap)`；`bc-sticky-mv.js` 用 `paddingLeft` 算基點，改 `--mv-pad-eff` 不必動 JS。
- **產品列淡入**：`.page-top__mv__product` 預設 `opacity: 0`，JS `jump()` 後才加 `.is-mv-ready`。若拿掉，JS 執行前瀏覽器已畫出 `-18%`，整排看起來往下掉；`about.html` 的 `<noscript>` 還原。
- **瞬移**：loop 歸位／尺寸重算時必須同時關掉 slide 與 img 過渡（`.is-jumping`），否則新聚焦卡片會從 `-18%` 往上抖。
- **`.mv-stage`**：複製品牌舞台三段（id 用 `bc-mv-` 前綴避免與頁尾重複），必須是 **7 欄 grid 且照抄原站格位**：fresh `1/3/2/6`、roasted `2/4/3/7` + `mt 8px`、marquee `2/3/3/5`（與 roasted 同列左）；≤991 6 欄：`1/1/2/5`／`2/4/3/7`／`2/1/3/4` + `justify-self:start`。字級照原站流體公式（14.4／≤991 3.93），`.scroller-box` `line-height: 1`；**不可改成 flex 堆疊**。
- **覆蓋層**：`.sticky-bg__bg::before` 的 `rgba(0,0,0,.75)`（**2026-11-07 使用者指定 75%**；演進 80% → 70%（11-06）→ 75%（11-07）。不是真實元素，量測要 `getComputedStyle(el, '::before')`）。**2026-11-06 起 `z-index` 由 `1` 提到 `10`**：多層影片的最新層是 `z-index: 3`，遮罩不抬高就會在交叉淡入那 0.6s 露出沒遮罩的亮畫面。
- **影片**：`about.html` 用 `<source type="video/webm">` 而非 `src`（第 0 層檔案來自 `views.MV_VIDEOS[0]`，模板不寫死）。2026-11-06 第二輪起片單整組換成 **`media/hero_00.webm` ~ `hero_06.webm` 七支**（全部 webm，1280×720），**沒有 mp4 後備、也沒有 poster**（舊 `hero_bg_v2-poster.jpg` 是舊影片截圖，內容不符 ⇒ 影片解碼前是品牌黑底 `#0e0e0e`）。不吃 WebM 的極舊瀏覽器會只剩黑底。
- **版號**：動到 css/js 必須升 `about.html` 的 `?v=`（WhiteNoise 快取 1 年）。影片不用手動升版號，見 §3 的快取機制。
- **這排卡的資料來源＝`mv_coffees`（不是 `series_coffees`）**：`betweencoffee_delivery/views.py` 的 `About` 用 `MV_EXCLUDE_IDS = {7}` 從 6 筆裡排除 #7 Nice Step → 首屏只放 5 張；下方「咖啡 SERIES 括號滑桿」與字輪仍用完整 6 筆。要增減首屏品項改那個常數，不要在模板加條件。
- **杯身大小不一致的根因**：這排吃 `CoffeeItem.get_index_image()`（`image_index` 空 → fallback 到詳情頁 `image`）。詳情圖 `860×1100`／杯身佔畫布寬 80%，列表圖 `840×1200`／杯身 62–87%，在同一個 3:4 `object-fit: contain` 盒裡渲染出的杯身寬可差 40%（`nicestep_detail` 217px vs `nicestep_index` 156px）→ 該組看起來「比別組擠／間距不同」。**修法補 `image_index`（data migration `0084`），不要針對單品加 CSS 間距**。

## 3. 影片多層輪播（2026-11-06，移植 weekday.co.jp `.p-hero__videos`）

**資料來源** `betweencoffee_delivery/views.py` 檔頭：`MV_MAX`（層數上限，2026-11-06 第二輪改 **7**
⇒ 層數＝min(片單長度, `MV_MAX`)）、`MV_VIDEOS`（片單，每筆可含 `webm`／`mp4`／`poster`；
2026-11-06 第二輪依使用者指示整組換成 **7 支 webm、依檔名順序**：`hero_00.webm` → `hero_01.webm` →
… → `hero_06.webm`（實測長度 7.0 / 6.1 / 10.0 / 7.0 / 4.0 / 5.0 / 4.0 s，總量約 8.0MB））。
`About.get` 用 `django.templatetags.static.static()` 轉成絕對 URL 放進 context
（`mv_videos`／`mv_max`）→ 模板 `json_script` 輸出 `bc-sticky-mv-videos`／`bc-sticky-mv-max`。
**快取（2026-11-07 修正）**：`WHITENOISE_MAX_AGE`＝1 年 ⇒ 同名檔換內容瀏覽器不會來問。
原本的做法是「換影片要改新檔名」；2026-11-07（使用者回報「`hero_00~06` 換了內容還顯示舊版」）
改成 `views._mv_versioned_static()`：URL 後面自動加 `?v=<檔案 mtime>`，換檔即換網址 →
一定重新下載，平時網址穩定、長快取照樣有效。**覆蓋同名 `hero_*.webm` 即可，不必改名、也不必手動升版號**。
（css/js 仍走 `?v=YYYYMMDDx` 手動升版號。）
ℹ 舊素材（`hero_bg_v2.webm`／`hero_bg-720p.mp4`／`hk_topshot-720p.mp4`／`roasting.mp4`／
`bean_bg.webm`／`13687671-hd_720_1280_60fps.mp4`）仍留在 `static/media/`，只是不在片單裡；
`index_hero_bg.mp4`（3.6MB，未被任何頁面引用）已於 2026-11-07 刪除。

**分層**：第 0 層由模板渲染（`#mv-video-0`，帶 `autoplay/muted/loop` ⇒ 無 JS 時等於舊版單支）；
第 1～N 層由 `bc-sticky-mv.js` 的 `initVideo()` 建立後 `append` 到 `.sticky-bg__bg`（**必須是直接子元素**，
才吃得到 `> * { position:absolute; inset:0; object-fit:cover }`）。

**播放邏輯**：**依清單順序**（2026-11-06 第二輪移除洗牌：原為每次載入 `shuffle()`，現固定
`0→1→…→6→0`）→ 先只 `loadLayer(1)`（前兩支）→ 當前層 `timeupdate` 距結束
`MV_LEAD_S`＝0.75s 時找下一個「就緒」的層（`isReady()`＝`readyState >= 3` 即時判斷，不只看 `canplaythrough`）
→ 加 `.is-on`（CSS `.6s` 淡入、`z-index:3`）→ 0.6s 後才暫停舊層、歸零、移除 `.is-on` → `loadNextUnloaded()`
補載下一支。找不到就緒層時也呼叫 `loadNextUnloaded()`，否則載入鏈會停住（2026-11-06 修）。

**與原站刻意不同**：① `z-index` 固定 3（原站累加）——遮罩要永遠最上層；② 找層有 `MV_MAX_ITER` 上限
（現 16；原站 `do…while` 在只剩一支載好時會無限迴圈）；③ 每層保留 `loop`（下一支還沒好時不會凍在最後一幀）；
④ 播放順序固定（原站洗牌）。

**常見誤解**：`json_script` 的 `<script>` 要放在 `.sticky-bg__bg` **外面**（放進去會變成 direct child，被
`> *` 規則 `display:block` 撐開）；`reduced-motion` 下只留 1 層且不播（`transition:none`）。

## 4. 驗證

Playwright／CDP 量測（載入後動態 resize，不需重載）：`--mv-per` = 1/1/2/2/3/3/3（360/390/768/1024/1280/1440/1920）、
無水平溢出、聚焦卡片中心 = 視窗寬 / 2（拖曳與 autoplay 換手後亦然）、`nameBottom < innerHeight`。
