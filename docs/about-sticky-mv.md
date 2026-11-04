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
- **覆蓋層**：`.sticky-bg__bg::before` 的 `rgba(0,0,0,.75)`（2026-11-04 定案 75%；不是真實元素，量測要 `getComputedStyle(el, '::before')`）。
- **版號**：動到 css/js 必須升 `about.html` 的 `?v=`（WhiteNoise 快取 1 年）。
- **這排 6 張卡都吃 `CoffeeItem.get_index_image()`**（`image_index` 空 → 自動 fallback 到詳情頁 `image`）。詳情圖是 `860×1100`／杯身佔畫布寬 80%，列表圖是 `840×1200`／杯身佔 62–87%，兩者在同一個 3:4 `.p-image` 盒 `object-fit: contain` 下渲染出的杯身寬差可達 40%（例：`nicestep_detail` 217px vs `nicestep_index` 156px）→ 該組看起來「比別組擠／間距不一樣」。
  **修法一律補 `image_index`，不要在 CSS 針對單品加間距**（2026-11-04：`#7 Nice Step` `image_index` 一直空著，migration `0084` 補 `coffee_images/nicestep_index.png`，杯身 217 → 156px，與抹茉 154／Flat White 162 一致）。

## 3. 驗證

Playwright／CDP 量測（載入後動態 resize，不需重載）：`--mv-per` = 1/1/2/2/3/3/3（360/390/768/1024/1280/1440/1920）、
無水平溢出、聚焦卡片中心 = 視窗寬 / 2（拖曳與 autoplay 換手後亦然）、`nameBottom < innerHeight`。
