# task_progress 封存段（2026-11-17 精簡 task_progress.md 時移出）

> 內容原本在 `task_progress.md` 的「最近任務」，皆為 2026-11-05 ~ 11-14～16 的已完成項；
> 只在此保留全文供追查，現況請看 `task_progress.md`。

**首頁 who section 主視覺＝「照片 ＋ 大字」（`bc-gt-mv.*`）＋`/coffee_menu/` banner 去 container — 2026-11-14～16 完成（已封存）**

- `bc-gt-mv.css ?v=20261116b`＋`bc-gt-mv.js ?v=20261114f`＋`partials/bc_gt_mv.html`：照片 3 切片＋單行 `Hmmm...`（字級 ×0.8）、
  IO 25% 起播、之後每 5s 換片；含 11-16 三～五批（字級／容器對調／文案）⇒ 明細 `docs/archive/task_progress_20261116_who_gtmv_rounds.md`。
- `/coffee_menu/` banner 內容清空、只剩 `.svg-bg`：section 加 `bc-banner-bgonly`、banner 改 `position:static`、
  `.svg-bg{top:0;bottom:0;height:auto;padding:0}`（選擇器要帶 `#section-counter` 才壓得過 style-custom.css）；明細同上檔。
- 踩到：模板快取 ⇒ 改 `templates/**` 要重啟 dev server（已寫進 `.clinerules/project-core.md` 第 7 節）。

**首頁 hero 背景照片移殖 `.layeredImage`（三階梯滑入＋斜向擦除）＋移除錯位疊印 — 2026-11-14／11-16 完成** → `docs/archive/task_progress_20261116_hero_pa_layeredimage.md`

**首頁 who kicker（sukima-label）：文案 About＋居左＋字級放大 — 2026-11-14 完成（本地驗證）**

- `index.html:322` 括號內文案 `Between Say:` → `About`（＝`( About )`；`.sukima-parenthesis` 與 flex gap 4px 不動）。
- `bc-who.css` `.who-kicker`：`margin-left` 100／199／302（三斷點）→ **0** ⇒ `(` 左緣＝`.section-title__text` 左緣
  （桌機 80px、≤834 20px；原站是內縮排版）。
- 字級 16 → **18px**（≥834 **21**／≥1920 **26**，括號同一層字級同步變大）；`--label-width` 仍 133px
  （僅 `max-width` 上限，26px 的 `About` 實測 71px ⇒ 不截字）。
- 版號 `bc-who.css ?v=20261114c → 20261114d`（index.html:1016）。
- 驗證（CDP 1920／1440／1180／834／768／390／320）：文字 `( About )`、`ml 0`、paren 左緣與 title 左緣 gap **0**、
  字級 26/21/18、label 未截字、`docOverflowX=0`、0 exception、`manage.py check` 0 issue。
  截圖 `_shot/who-kicker-about-1440.jpeg`、`_shot/who-kicker-about-390.jpeg`。

**yama 圓球底色三端統一近黑 — 2026-11-14（已封存）** → `docs/archive/task_progress_20261114_recent_entries.md`

**11-11 ~ 11-14 其餘完成（已封存）** → `docs/archive/task_progress_20261114_recent_entries.md`

who 內文縮小／logo 貼左緣／hero 影片 3→6、推薦雙卡標題字體、bc-reviews 放大與跑馬燈修正、
素材上線、who「有溫度」筆刷 SVG、who 11-12 三筆版面、who 揭示放慢、next-link＋Akzidenz 字體等。

**11-09 ~ 11-10（已 push，待部署）** — 明細全在 `docs/archive/`：品牌舞台 `footer*`→`bc-stage-*`
（`task_progress_20261110_brand_stage_rename.md`）、who section 搬到首頁 `bc-recommended-pages` 正下方
（`task_progress_20261110_who_move_and_hero_0920.md`）、浮動購物車圖示改手提包線稿
（`task_progress_20261109_floating_cart_icons.md`）、hero 黑蒙版 75%＋落點洗牌＋第 3 格影片輪播＋
「咖啡豆製程」移 `/about/`（`task_progress_20261109_photoarea_dim_shuffle.md`、`docs/home-photoarea.md`）。

**11-05 ~ 11-07（已 push，待部署）** — 明細：`/about/` 首屏遮罩 `.7`→`.75`、7 層依序輪播（`docs/about-sticky-mv.md`）、
`bc-popeye50` 字輪重新顯示並移到 `#bc-sticky-mv` 下方、詳情頁氣泡頭像 `baker_01–04.svg`＋環形照片列改名／hover 徽章、
navbar 天氣模組手機位移 → `docs/archive/task_progress_20261106_preceding_entries.md`、
`task_progress_20261105_baker_ring_badge.md`、`task_progress_20261105_weather_navbar.md`。

## 前一批（已 push，只剩部署）

about 首屏 sticky 影片／首頁「咖啡豆製程」`[2b-2]`／#61 推薦雙卡／#59–#60 等的摘要與數據 → `docs/archive/task_progress_20261105_pushed_batches.md`。
