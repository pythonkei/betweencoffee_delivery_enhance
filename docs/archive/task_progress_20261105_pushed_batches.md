# 任務進度封存 — 2026-11-05（已 push 的批次：about 首屏／首頁製程／#61 推薦雙卡／#59–#60）

> 自 `task_progress.md`「前一批（about 首屏換版…）」整段移出（檔案大小超標時依規則封存）。
> 內容為 2026-10-24 ~ 2026-11-05 **已 push** 的任務摘要；只在追查細節時讀。

## 前一批（about 首屏換版；#59／#60／#61 已完成並 push；只剩部署）

**about 頁首屏「sticky 影片 ＋ 產品照弧形輪播」（移植 yurumaru.life `.page-top__mv__wrap`）— 2026-11-03 完成**

| 現況 | 位置／新檔（`bc-sticky-mv.css`＋`.js`）／sticky 機制／輪播參數／資料來源／影片遮罩／踩雷／驗證數據 → `docs/archive/task_progress_20261105_sticky_mv_details.md`。時程：2026-11-03 完成 → 2026-11-04 三項修正（loop 歸位抖動／拖曳被原生 drag 中斷／複製品牌舞台三段）→ 2026-11-05 影片換 `media/hero_bg_v2.webm`（webm 優先＋mp4 後備）＋ 黑遮罩 `.75 → .8`；以下皆已 push（`e9bdefdb` 之後） |

**首頁「咖啡豆製程」捲動模組（移植 union-tec.jp `homeService`）— 2026-10-30 完成，已 push `e9bdefdb`**：
位置＝首頁 `[2b-2]`（`aside.bc-recommended-pages` 之後、`.bc-capabilities` 之前）；新檔 `partials/bc_home_service.html`、`bc-home-service.css/js`（`?v=20261030a`）、`scripts/make_hs_images.py`；完整數據（幾何公式／素材規格／驗證值／`{# #}` 不支援跨行踩雷）→ `docs/archive/task_progress_20261102_home_service.md`。

**#61 首頁「推薦頁面」雙卡（移植 union-tec.jp `recommendedPages`）— ✅ 完成（已 push `d27f7c90`）**
逐筆追加記錄（2026-10-24 ~ 10-27 共 8 次）→ `docs/archive/task_progress_20261027_issue61_homepage.md`

| 現況 | 內容 |
|---|---|
| 位置 | 首頁 `<aside class="bc-recommended-pages">`（`[2b]`）緊接 `.bc-brand-stage-hero`，中間無留白 section |
| 檔案 | `static/css/bc-recommended-pages.css`、`static/js/bc-recommended-pages.js`、`static/images/recommended-pages/{coffee,bean}_bg.webm`、`clip-{coffee,bean}-ani.png` |
| 現行數值 | 卡片 692×540（375＝345×225）、title 56px（375＝26.25）、label 16／11.25、clip 507×166（375＝255×83）；背景 WebM（hover 播放、觸控裝置不下載）、clip APNG（`object-fit:contain`）；inactive `scale(.666)`；模組黑底已移除 |
| 其他 | 首頁 `#bc-stage-socials` 由 extra_css 隱藏（about 頁保留）；版號 css `?v=20261027a`／js `?v=20261025a` |

**2026-10-27 ~ 10-28 UI／字型調整（已封存）**：capabilities 搬家＋`--cap-scale` 放大置中（`bc-capabilities.css?v=20261027a`）、`/bean/<id>/` `.bc-staff` 字級 17／16／16px（`bc-components.css?v=20261028a`）、`trade-gothic` 自架字型（`bc-fonts.css?v=20261028a`）、bean SERIES 標題兩行＋行距 0.85–0.9／字級 32–160px（`bc-series.css?v=20261028d`）。逐筆記錄 → `docs/archive/task_progress_20261028_ui_series_fonts.md`


**`/bean/<id>/` 咖啡豆 SERIES 括號滑桿（2026-10-28）**：模組自 `/about/` 整組搬到商品主區下方＋`views.Bean` 補 `series_beans`＋箭頭方向修正＋間隔兩次加大（桌機不換照片 280、slide 520／gap 240；平板 340／140；行動 gap 70）；逐筆記錄 → `docs/archive/task_progress_20261028_bc_series.md`。

**已完成任務的詳細記錄**：
- #60 品牌舞台環形照片列第一張進場動畫（`7a073263`）→ `docs/archive/task_progress_20261025_issue60_hand_ring.md`
- #59 咖啡豆詳情頁氣泡（`edf3e87c`）→ `docs/archive/task_progress_20261024_issue59_bean_bubbles.md`
- #58／#58b 首頁四步 Rive 圖示列（`a732cc28`）→ `betweencoffee_memory_bank/04_SYSTEM_STATE.md`
