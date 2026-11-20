# /coffee/<id>/ 首屏「上一杯／下一杯」帶（v1–v9）完整紀錄

> 2026-11-20 從 `task_progress.md` 移出（新增 bc-popeye50 移植條目，控制 12K 預算）。
> 現況摘要見 `task_progress.md`；程式碼＝`static/css/bc-coffee-dirs.css`、`static/js/bc-coffee-dirs.js`、`partials/bc_coffee_dirs.html`。

**/coffee/<id>/ 首屏「上一杯／下一杯」（鄰杯圖片＋名稱）— 2026-11-19 九版定案、已上線**

- 結構：`views.Coffee.get` 算 `prev_coffee`／`next_coffee`（`sort_order, id`、首尾循環、僅 1 杯時 `None`）
  → `partials/bc_coffee_dirs.html`（`<nav class="bc-coffee-dirs">` ＋ `<a rel=prev|next>`，內含
  `.bc-coffee-dirs__media`＝3:4 圖盒＋`.bc-coffee-dirs__arrow`＋`.bc-coffee-dirs__name`）
  → `static/css/bc-coffee-dirs.css`（＋第七版起 `static/js/bc-coffee-dirs.js`：捲動淡出）。
- 內容（第四版）：圖片＝`CoffeeItem.get_index_image`（840×1200 去背 PNG、`object-fit:contain`）＋名稱
  （第六版：寬度＝圖片寬、`text-align:center`、字級 `--bc-cd-name-fs` .9rem／1.15rem、單行 ellipsis；
  第七版：白色 `--bc-text`）；名稱寫進 `aria-label`（「上一杯：X」）、圖片 `alt=""` 避免重覆朗讀。
- 位置：`position:fixed`（不佔流）＋`justify-content:space-between` 貼左右緣；≥992 `--bc-cd-top:
  max(352px, calc(50% - var(--bc-cd-h)/2))`（1440 → y352，在貼紙下緣 336／頭像 348 之下、重疊 0）；
  768–991 用「navbar 高 + 6px」（768 → 108）。圖寬 768–991 `clamp(96px,13vw,118px)`、≥992
  `clamp(130px,11.5vw,176px)`，高＝寬×4/3；右組 `--bc-cd-inset-r`（`clamp(56px,11vw,96px)`、≥992 歸零）。
- 行動端（第五版）：≤767.98px 整組 `display:none`（含箭頭；<768 的尺寸微調一併移除）。
- 箭頭：`c-icon--bracket_l/r` 本站無字碼 ⇒ inline SVG 細角括號（stroke 1、取文字色）貼圖片盒內側垂直居中，
  尺寸由 `--bc-cd-mark-*` 依圖高換算（高＝圖高×.5）；hover／focus 由內側滑入（`translateX ±35% → 0`，.15s）。
- 第四～六版實測（本地、0 console error、皆無水平滾動）：390／767 `display:none`；768 nav `[0,108,768,268]`；
  992 商品敘述未被杯子遮擋；1200×800 nav `[0,352,1200,569]`；1440×900 `[0,352,1440,606]`；名稱中心＝
  照片盒中心（1440 `82.8/1357.2`、1200 `69/1131`、992 `65/927`、768 `49.9/633.6`）；
  `/coffee/1/` prev `/coffee/2/`、next `/coffee/7/`（首尾循環正常）。
- **第七版（使用者「咖啡名稱改為白色」＋「捲動出 `.ftco-subpage-section` 此部分新增淡出動畫、
  捲入則反向淡入」）**：① `__name`／`__dir` 色彩金色 → **白**（`--bc-text`＝rgba(255,255,255,.9)，
  與箭頭同色）；② 新增 `.bc-coffee-dirs.is-out`：`opacity 1→0`（.45s、`cubic-bezier(.4,0,.2,1)`）、
  `visibility:hidden` 延到淡出結束才切（同時退出 Tab 序／讀屏）、`pointer-events:none`；
  ③ `static/js/bc-coffee-dirs.js`（IntersectionObserver `threshold:0`）觀察商品主區
  `.ftco-subpage-section.ftco-section-single-product`：完全離開視窗 → `.is-out`，回到視窗內 → 移除；
  無 IO 時退化成 scroll＋rAF 手算 `rect`；無 JS 時永遠顯示（＝第六版行為）。
  ④ 實測（1440×900）：`is-out` 時 opacity 淡到 0 後才 hidden（同時退出 Tab 序）；390 `display:none` 照切 class；
  reduced-motion → `transition-duration 0s`；0 console error、無水平滾動。
- **第八版（使用者「反轉動畫，hover 狀態時正常顯示和箭頭動畫，正常狀態時暗」）**：明暗反轉 ——
  `__dir` 預設 `opacity .4`（連圖片一起變暗＝靠背景透出，不加遮罩/漸層），`:hover`／`:focus-visible`
  回 **1** ＋ 原箭頭動畫（`opacity 0→1`、`translateX ±35% → 0`）；移出淡回 .4（.25s，沿用既有 transition）。
  觸控 `hover:none` 無 hover 可觸發 → 常駐 .4、箭頭提亮 .8（淨值 ≈.32）當可點提示。
  實測（Playwright）：idle dir .4／arrow 0／translate 34.2px → hover 1／1／0；另一側維持 .4；
  390 `display:none`；reduced-motion `0s`。0 console error、無水平滾動。
- **第九版（使用者「修正正常狀態時暗，不是不透明值，讓照片顯示變暗」＋「修正捲動淡出淡入動畫，
  捲動入則反向，不包含頁腳 footer section」）**：
  ① 變暗由 `__dir { opacity:.4 }` 改為 `filter: brightness(var(--bc-cd-dim＝.4))`（`__dir` opacity 固定 1）
  —— 照片**真的變暗且仍不透明**（背後 {BREWED FAST} 大字不再透出），名稱／箭頭同受濾鏡；
  `:hover`／`:focus-visible` → `brightness(1)`（.25s），移出回 .4；箭頭動畫、觸控 `hover:none` 箭頭 .8 不變。
  ② `.is-out` 條件改為「**主區填不滿視窗**」：`section.bottom <= innerHeight` → 淡出、回到 `>` → 反向淡入。
  第七版條件（`isIntersecting === false`）下，主區很高（y190–1492）時
  頁腳（y1610）／next-link（y2248）都還算「看得到主區」⇒ 帶子一路掛在頁腳上。改後 1440×900 於
  scrollY 592 淡出、頁腳出現（810）時已淡完；主區比視窗矮（罕見）時退回舊規則，避免一捲動就消失。
  ③ 實作改 scroll＋rAF＋`load` 校正（passive；IO 的 threshold 表達不了「bottom 與視窗高比較」）。
  實測：idle `brightness(.4)`／arrow 0 → hover `brightness(1)`／arrow 1／translate 0、
  另一側仍 .4；邊界對稱（1200×800 `bottom 795 → is-out`／`805 → in`、768×1024 `1019`／`1029`）；
  頁腳出現時 `opacity 0`；捲回 580 → 1；0 console error。
- 版號：`bc-coffee-dirs.css?v=20261119i`＋`bc-coffee-dirs.js?v=20261119b`（第九版 `3d8b92f9`／docs
  `105968fa`）**已 push、待 Manual Deploy**（autoDeploy 關閉，正式站仍 h／a）；第八版 h／`a`／`226f2785`
  （deploy `dep-dbvf013l550s739j6ha0` live 12:50:21Z）、第七版 g／`b46ef12f`、第六版 f／`9c66cd66`。
- ⚠ 地雷：改 `coffee.html` 的 `?v=` 後**必須重啟 runserver**（模板快取會吐舊版號連結，看起來像沒生效）；
  淡出狀態 `.is-out` 必須連 `prefers-reduced-motion` 區塊一起列（`.bc-coffee-dirs.is-out` 特異度 0,2,0
  會壓過單一 class 的 `transition:none`）；Django `{# #}` 不可跨行、內文不可再出現 `{#`／`#}`
  （partial 的說明一律用 `{% comment %}` 區塊）。
