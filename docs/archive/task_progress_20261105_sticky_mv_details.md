# task_progress 封存：about sticky-MV 細節（2026-11-03 ~ 11-05）

> 2026-11-05 由 `task_progress.md` 移出（該檔超過 11.7K 上限）。只在追查 sticky-MV 踩雷時讀。

| 踩雷 | ①`aspect-ratio` 單用無效（img 原始比例把盒子撐高）→ `.p-image` 固定比例盒 ＋ `img{position:absolute;inset:0;object-fit:contain}`；②手機 `--mv-pad:25%` 在寬度 `calc()` 內對父層解析 → 卡片變 293px（應 195）→ 改 `25vw`；③`setPointerCapture` 在 pointerdown 就鎖 → click 全落在容器、商品連結永遠點不到 → 位移 >8px 才 capture；④`bc-components.css` 給「內容首個 section」`margin-top:100/72/60px` → `.bc-page-content > section#bc-sticky-mv:first-of-type{margin-top:0}`，影片改從頁面最頂端鋪（文字區另有 `--mv-nav` padding） |
| 驗證 | `manage.py check` 0 issue、`node --check` OK；headless Chromium 1440×900／390×844：`scrollWidth==clientWidth`、active 中心 720／195、卡片 240×320／195×260、桌機 3 杯可見（中心＋左右各一，弧形錯落）／手機單張＋左右露邊、sticky `bgTop=0`（scroll 620／560）、scroll 1700 交棒下一 section、影片 `readyState 4` 播放中、autoplay 前進、拖曳換張不導頁、點商品圖→`/coffee/1/`、reduced-motion（影片暫停＋transition 0s＋不自動輪播）、console 0 error |
| 2026-11-04 修正 | ①**loop 歸位抖動**（使用者：繞完一圈回到 Coffee 01 後卡片異常往上抖再回原位；手動滑動同樣發生）→ 根因＝`jump()` 只瞬移 `.mv-product__list`，slide 的 `translateY(-18%)` 仍走 1.75s 過渡，歸位那幀新聚焦卡正從 **-73.5px 爬回 0**；修法＝`jump()` 期間加 `.is-jumping`（CSS 關掉 slide／img 過渡）並在無過渡狀態下先切角色再改位移、reflow 後移除 → 歸位幀 `ty=0`（實測 idx 14→8 前後皆 0）。②**滑鼠拖曳被原生 drag 中斷**（`<a>` 觸發 HTML5 dragstart → `pointercancel`，拖 30px 就停）→ `product.addEventListener('dragstart', e => e.preventDefault())`；實測 defaultPrevented=true、無 pointercancel、idx 6→7、放手不導頁。③**複製品牌舞台三段到產品列下方**（`#bc-stage-headline-fresh-beans`／`-roasted-daily`／`-marquee`）→ `.mv-stage`（id 改 `bc-mv-*`；`.p1`、Mogra 跑馬燈；右側 `max(6vw,104px)` 讓開浮動購物車；`scrollWidth==clientWidth` 1280／390 皆無橫向溢出、頁面 id 無重複、`manage.py check` 0 issue、console 0 error）。④**三段位置與 about 頁不同**（使用者提問）→ 第一版 flex 直向堆疊是錯的：`.mv-stage` 必須照抄 `#bc-brand-stage` 的 7 欄明確格位（≤991 為 6 欄），完整格位／字級公式／實測值見 `docs/about-sticky-mv.md` §2，三斷點 0 溢出、console 0 error |

## 模組概況（2026-11-05 由 task_progress.md 移入，保留給需要追規格時查）

| 項目 | 內容 |
|---|---|
| 位置 | `about.html` 最上方（`.rotate-mau` 之後、`.bc-series-hero` 之前），**取代 2026-11-02 的 popeye50 字輪**；舊檔仍留在 `static/` 但本頁不再載入（當時記錄 → `docs/archive/task_progress_20261103_popeye50.md`） |
| 新檔 | `static/css/bc-sticky-mv.css`（`?v=20261105a`）、`static/js/bc-sticky-mv.js`（`?v=20261104b`）；影片 `static/media/hero_bg_v2.webm`（1280×720 / VP8 / 30fps / 11.17s / 3.4MB；兩層 `<source>`：webm 優先＋`hero_bg-720p.mp4` 後備）＋ poster `hero_bg_v2-poster.jpg`（v2 第 2 秒截圖） |
| sticky 機制 | 三層照抄：`.sticky-bg__bg{position:sticky;top:0;height:100vh}` ＋ `.sticky-bg__content{margin-top:-100vh;z-index:1}`（`--mv-len:200vh`＝一屏釘住＋一屏滑過、`--mv-text-h:64vh`／手機 60vh）；root 用 `isolation:isolate` ＋ `background:var(--bc-bg)` 蓋掉 `.rotate-mau` 的 `z-index:-1` 透出；黑遮罩 `.sticky-bg__bg::before` 2026-11-05 由 `.75` → **`.8`** |
| 輪播 | 原生 JS 重寫 Splide（不引入 Splide／GSAP，CDN 失效也能跑）：per 3／gap 10vw／pad 14vw（≤680px：1／15vw／25vw）、autoplay 4000、speed 1750、easing `cubic-bezier(.83,0,.17,1)`、flickPower 200、focus center（每次讓 active 張中心＝視窗中心）；**前後各複製一組 slide**（5 筆 → 共 15 個 `li`）→ 第一張左側也有鄰卡、`pos` 超出 `[n,2n)` 瞬移一組無縫接續 |
| 資料／樣式 | 資料＝`About` view 的 `mv_coffees`（**5 筆**：`MV_EXCLUDE_IDS={7}` 排除 #7 Nice Step，2026-11-04 使用者指示；下方 SERIES 括號滑桿仍用 `series_coffees` 6 筆）；分層上浮 `translateY -18%/-6%/0` 全在 CSS（`.is-active/prev/next-logical`），手機非聚焦卡文字淡出（避免邊緣半截字） |
