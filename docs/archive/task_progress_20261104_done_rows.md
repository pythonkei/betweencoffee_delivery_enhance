# 已完成任務一行式紀錄（2026-11-04 自 `task_progress.md` 移入）

> 原因：`task_progress.md` 超出 11.7K 預算（該檔只留現況）。以下為 2026-10-23 ~ 2026-11-04
> 的一行式完成紀錄（皆已 push），原封不動搬來此處；新任務請只更新 `task_progress.md`。

| 日期 | 任務 | 狀態／commit |
|---|---|---|
| 2026-10-28 | `.bc-series-heading` 英文字型 trade-gothic＋行距縮小＋字級加大（about `140→160`／bean `80/40/26→96/48/32`，圓圈與字母留 4–5px） | `f57eb768`＋`f730abab`（已 push） |
| 2026-10-28 | 咖啡豆 SERIES 括號滑桿自 `/about/` 整組移至 `/bean/<id>/`（商品主區下方）＋`views.Bean` 補 `series_beans`＋左右箭頭方向修正（`bc-series.js?v=20261028a`） | `29eb67d1`（已 push） |
| 2026-10-28 | `/bean/<id>/` `.bc-staff` 文字放大（17／16／16px；`bc-components.css?v=20261028a`） | 未 commit |
| 2026-10-24 | #61 首頁推薦雙卡＋搬到品牌舞台正下方＋隱藏首頁社群列 | `d27f7c90`（已 push） |
| 2026-10-24 | #59 咖啡豆詳情頁店員氣泡（10 欄位＋幾何自動量測＋migration `0081`–`0083`） | `edf3e87c`（已 push） |
| 2026-10-24 | #60 品牌舞台環形照片列第一張咖啡改用標題文字的 goo 揭示（不再從小放大） | `7a073263`（已 push） |
| 2026-11-04 | about 首屏（bc-sticky-mv）：修 loop 歸位時卡片往上抖（`jump()` 加 `.is-jumping` 同步關掉 slide 過渡）＋修滑鼠拖曳被原生 `dragstart` 中斷＋產品列下方新增 `.mv-stage`（複製品牌舞台 Fresh beans／roasted daily／BETWEEN 跑馬燈，**改用原站 7 欄 grid 格位**，位置與 about 頁一致） | 已 push `0bd7172d`（`bc-sticky-mv.css?v=20261104c`／`bc-sticky-mv.js?v=20261104b`） |
| 2026-11-02 | `/about/` 首屏字輪微調（直徑係數 `0.92→0.86`、中心品名放大到 13.5px／手機 13.2px、手機 `.cw-wheel` 加徑向遮罩避免長字壓到品名）＋中心圖文與 SERIES 項目連結到該咖啡詳情頁（拖曳 >8px 不誤觸導頁） | 已 push `87d66040`／`33a4c06a`（`bc-popeye50.css?v=20261102f`／`bc-popeye50.js?v=20261102c`／`bc-series.css/js?v=20261102b`） |
| 2026-10-31 | `/about/` 新增「字體輪播」模組（移植 eightdesign.co.jp `.PZL1xq_catch`：3 行 × 每行 4 種字體處理、`.74s` step-end／每格 185ms 硬切、行相位 −0.09／−0.18s 保證三行永遠三種字體、**純 CSS 無 JS**＋`prefers-reduced-motion` 靜止）置於 `.bc-reviews-section` 正下方 | 已 push `e9bdefdb`（`bc-catch.css?v=20261031a`；先前只 commit 了引用它的 about.html，檔案漏提交 ⇒ 正式站一度 404） |
| 2026-10-29 | 首頁品牌舞台環形照片列**加回左右拖曳**（`bc-hand-ring.js` 新增 `bindDrag()`：Pointer Events 1:1 跟手、30% 格距或快甩換張、放手吸附、手勢期間停自動輪播×放手後 5s 恢復、直向手勢交還頁面捲動、拖曳不誤觸跳頁；CSS `cursor:grab`／`touch-action:pan-y`／`.is-dragging`） | 已 push `e9bdefdb`（`bc-hand-ring.js/css?v=20261029a`） |
| 2026-10-23 | #58／#58b 首頁品牌舞台（`bc-bg-footer` → `bc-brand-stage`）＋四步 Rive 圖示列（hover／靜止 4s 自動循環／純白） | 本機 `a732cc28` |
