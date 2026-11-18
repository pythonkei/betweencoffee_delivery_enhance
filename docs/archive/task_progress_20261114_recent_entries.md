# task_progress 封存：2026-11-13 ~ 11-14 舊任務段

> 2026-11-14 由 `task_progress.md` 移出（該檔超過 11.7K 上限）。內容未改動，只做搬移。
> 需要追查 11-11 ~ 11-14 的 who／reviews／next-link 細節時 grep 本檔即可。

**手機：who 內文縮小＋左上 logo 貼左緣；首頁 hero 影片 3→6 支 — 2026-11-14 完成（本地驗證）**
（全文封存 → `docs/archive/task_progress_20261114_home_who_logo_videos.md`）

- `bc-who.css` 內文 `clamp(21px,5.85vw,27px)`、標題 `clamp(34px,9.2vw,42px)`（≥834 桌機平板不變）。
- 左上 logo 墨跡 16px（`left:16px` ＋ `text-indent:-0.71em`，全角「｛」缺字造成的 0.71em 偏移）。
- `views.PA_VIDEOS` 3 → 6（`hero_00/04/05/03/02/06`，不洗牌）；`hero_06.webm` 已 `git checkout` 還原。
- 版號 `bc-who.css ?v=20261114c`、`bc-components.css ?v=20261114b`。

**首頁推薦雙卡（標題字體／大小）＋ 手機平板三項間距修正 — 2026-11-14 完成（本地驗證）**
（全文封存 → `docs/archive/task_progress_20261114_home_mobile_spacing.md`）

- 標題 `COFFEE` / `BEANS`（`text-transform:uppercase`＋Mogra 400＋`letter-spacing:-0.04167em`、`#spacing` 28→26／56→52）。
- 卡片間隙 <64rem `--gap-stack: clamp(20px,24×spacing,36px)`（@375 22.5／@768 36）、≥64rem `--gap:max(12px,…)`（@1024 12）。
- yama `.tax-nav` `right` ≤768 20px／744–1199.98 28px；`wwa-visual-03` `clamp(48px,14vw,62px)`＋底緣定位。
- 版號 `bc-recommended-pages.css`／`bc-who.css`／`bc-who.js` `?v=20261114b`、`bc-yama-header.css ?v=20261114a`。



**bc-reviews 內文放大約 10% ＋ 膠囊內距同步 ＋ 動畫重新量測 — 2026-11-13 完成（本地驗證）**
（全文封存 → `docs/archive/task_progress_20261113_reviews_scale_padding.md`）

- 文字 `15→16.5 / 14.5 / 12px`；`.reviewsBox` 改 `inline-flex` 置中；內距三輪後膠囊高 **31／28／24**、左右 **18／14.5／11.5**。
- 版號 `bc-reviews.css ?v=20261113g`／`bc-reviews.js ?v=20261113c`；驗證 1440／700／375／320 置中對稱、無溢出。


**bc-reviews 跑馬燈「跳回第一組／內文沒全部顯示」修正 — 2026-11-13 完成**（全文封存 → `docs/archive/task_progress_20261113_reviews_seam.md`）

**素材更新上線（wwa 圖＋hero 影片）— 2026-11-14 完成並已上線驗證**

- commit `17f3f96d`：`wwa-02.png` 換高解析版（`index.html` 該 `img` 補 `?v=20261114a`）、`hero_00/01.webm` 內容互換、`hero_05.webm` 換片
  （webm 走 `views._mv_versioned_static()` 的 mtime 版號，不用改模板）；線上已驗證（首頁 `bc-who.css?v=20261114a`、hero 三支 `content-length` 與本地一致）。
- **刻意未提交**（使用者指示不動刪除檔）：`wakemeup.png`／`bg_5.jpg`／`staff01–04.png`／`hero_06.webm` 刪除仍在工作目錄
  （模板仍有引用 ⇒ 只有本地 dev 會 404，origin/main 保留）。清理時 `hero_06_.webm` 改名覆蓋回 `hero_06.webm`，其餘 `git restore`。

**首頁 who：「有溫度」筆刷換成 sukima `#careers` 的 `.content-block-title` SVG — 2026-11-14 完成**
（全文封存 → `docs/archive/task_progress_20261114_who_brush_careers_svg.md`）

- `.wwa-anim-members` 內 SVG 換成 sukima `#careers` 的 `svg.title-hatarikata-svg`（id 改 `flowingRibbonRevealMaskWwa`／`flowingRibbonClipWwa`）。
- `bc-who.js` dashoffset `784→0` 改 `600→0`、`dur 1.2→1`；`.wwa-members-svg` `left:-0.84em; bottom:-0.03em; width:4.28em`。版號 `bc-who.css/js ?v=20261114a`。

**首頁 who（11-12 三筆）：gif 右側間隔／圓圈再寬 10%／visual 互換＋圓圈下移 10px／模組 ×1.3→×1.15**
（全文封存 → `docs/archive/task_progress_20261112_who_visual_and_circle.md`、
`task_progress_20261112_who_circle_grow.md`、`task_progress_20261112_who_module_shrink.md`）

- 摘要：`.wwa-anim-visual.wwa-visual-03` 加 `margin-right:0.4em`；`.who-circle-svg--cjk` `4.2em→4.62em`、
  `top:48%→calc(48% + 0.26em)`；`wwa-01.svg`／`wwa-03.gif` 節點互換（class 不動 ⇒ CSS／JS 未改）。
  版號 `bc-who.css 20261112c→e`。

**首頁 who 文字揭示動畫放慢（初始出現太快）— 2026-11-11 完成**

（全文 → `docs/archive/task_progress_20261111_who_scrub_slow.md`）

- 病因：scrub 進度以 `section` 頂端為基準，文字區塊還低 381px ⇒ 文字未進畫面已跑掉 42%。
- 改法（`bc-who.js`，版號 `20261111a`→`b`）：進度基準改 `.who-content-text`；新增 `MAX_STEP_PER_SEC = 0.45`（全程 ≥2.2s）。

**next-link「( NEXT )」＋首頁 who 標題改用 Akzidenz Grotesk Pro — 2026-11-11 完成**（全文封存 → `docs/archive/task_progress_20261111_next_link_and_font.md`）

- 摘要：`bc_next_link.html` 文案 `( NEXT )`；`.bc-next-link__label` 用 `var(--bc-font-akzidenz)`（woff2 在 `bc-fonts.css`），上捲動畫移到 `.bc-next-link__loop`（1450ms infinite）。版號 `bc-fonts 20261111a`／`bc-next-link 20261111h`／`bc-who 20261111c`。
- 未解：`/coffee/2/` 等 6 款 `staff_comment_1~3` 全空 ⇒ 詳情頁氣泡整塊不渲染（**資料問題**，非 CSS／JS；模板條件 `coffee.html:54`／`bean.html:51`）。




**11-11 同日其他完成（全文封存）** → `docs/archive/task_progress_20261111_next_link_and_font.md`

- `/coffee/<id>/` 頁尾 next-link 面板（`bc-next-link.{css,js}`＋`partials/bc_next_link.html`）、左上 logo +8px、
  浮動購物車數字 +1.92px／圖示改 `onlineshop-cart.svg`、who 素材換 `wwa-01.svg`／`wwa-03.gif`。詳見封存檔。

**yama 圓球底色三端統一近黑（桌機原為品牌金）— 2026-11-14 完成（本地驗證）**
（2026-11-14 由 `task_progress.md` 移入本檔：該檔超過 11.7K 上限，內容未改動。）

- 使用者：`.bc-yama-deco` 在桌面端、與手機／平板正常狀態時顏色不一樣 → 統一為手機／平板的顏色。
- 根因：deco 白圖三端色值本來都是 `#ffffff`，差的是**球底色**——≥769 `--bc-yama-circle`＝品牌金
  `#c49b63`（2026-10-08 改的），≤768 硬寫 `#131211` ⇒ 同一張白圖落在金球／近黑球上觀感不同
  （桌機 hover 掃層又是白色 → 白 deco 融進白球）。
- 修法（`static/css/bc-yama-header.css`，三端一率對齊 ≤768）：
  ① `:root --bc-yama-circle` → `#131211`（≤768 的硬寫值不動）。
  ② 刪掉檔尾 ≥769「亮球可讀性收尾」整段（`--bc-yama-circle-hover:#ffffff` ＋ 球內文字 `#1b1b1b`；
     深字對 `#131211` 僅 1.03:1、等於看不見）。
  ③ ≥769 主行 `a p > span:first-child` 白 → **`#ba833a`**（＝≤768 同值，對 `#131211` 7.27:1 AA 通過）。
  ④ 現況三端完全一致：球 `#131211`｜hover `#1a1919`｜主行 `#ba833a`｜tagline 白｜`-5` 品牌金｜em 底線白｜deco `#ffffff`。
- 版號 `bc-yama-header.css ?v=20261114a → 20261114b`（`index.html:1035`）。
- 驗證（CDP headless 1440/1200/1024/820/768/390）：ball `rgb(19,18,17)`、`--bc-yama-circle-hover:#1a1919`、
  主行 `rgb(186,131,58)`、tagline 與 em 底線 `#fff`、deco `rgb(255,255,255)` 且 mask 生效、`docOverflowX=0`、
  hover 後球 `rgb(25,25,25)` 且 deco 仍清楚可見（該區白色像素 1161 點）、0 console error、`manage.py check` 0 issue。
  截圖 `_shot/bc-yama-ball-dark-1440.jpeg`、`_shot/bc-yama-ball-dark-390.jpeg`。
- 回退：`:root --bc-yama-circle` 改回 `var(--bc-gold, #c49b63)` ＋ 恢復「深字＋白 hover」兩段（原值見 `c3f7509c`）。

