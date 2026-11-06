# 2026-11-05 封存：氣泡頭像換 baker SVG ＋ 首頁環形照片列改名／hover 徽章

> 由 `task_progress.md` 移出（檔案 12.4K > 11.7K 上限）。兩筆皆已完成、待 commit；現況摘要仍留在 `task_progress.md`。

## 咖啡／咖啡豆詳情頁氣泡頭像換成 `baker_01–04.svg` — 2026-11-05 完成（未 commit）

| 項目 | 內容 |
|---|---|
| 指示 | `/coffee/x/` 的 `bc-coffee-comment` 頭像 `staff01–04.png` → `baker_01–04.svg` |
| 改動 | `static/css/bc-coffee-comment.css:223–239`：`.blowing.staff-comment-1/2/3::after` 的 `background-image` 改 `baker_01/02/03.svg`，並補 `.staff-comment-4::after`（`baker_04.svg`，目前頁面只用到 1–3）；`coffee.html:543`／`bean.html:638` 版號 `?v=20261024a → 20261105a` |
| 關鍵換算 | 舊 PNG 是已裁切圖（實繪 ≈ 100% 畫布）⇒ box ＝ 圖高 `0.95rem`（`0.8/0.69/0.73 × 0.95`）。新 SVG 是「正方形畫布＋內部留白」（實測實繪佔比 `baker_01 0.668×0.903`／`02 0.737×0.933`／`03 0.652×0.853`／`04 0.712×0.900`，實繪中心皆 ≈ `0.5`）⇒ box 改正方形 `1.05rem`（`1.05×0.903 ≈ 0.95rem`）＋ `contain`，`::after` 的 `top` 由 `-0.3rem → -0.35rem` 補償留白，讓實繪上緣仍貼齊氣泡尾端 |
| 未動 | `staff0N.png` 全數保留（`/about/` 的 `.bc-sake-mv` 仍用：`bc-sake-mv.css:248/256/264/272`）；`bean.html` 的 `.bc-staff` 員工區照片（`staff_ito.png`／`staff_natsu.png`）與本模組無關 |
| 驗證 | `manage.py check` 0 issue；Playwright（8081，`DEBUG=True`＋`WHITENOISE_USE_FINDERS`，`?v=20261105a` 已載入）：`/coffee/10/` 與 `/bean/3/` 三顆氣泡 computed `background-image` ＝ `baker_01/03/02.svg`、box `75.59×75.59`（`1.05×72`）、**實繪高 68.3px（舊版 68.4px）**、頭像中心與氣泡中心差 `0.01–0.02px`、p-1 實繪上緣與氣泡底差 `0.1px`；390px 手機：box `48.3px`（`1.05×46`）、實繪高 ≈ 43px（舊 43.7px）；console 0 error；截圖確認三顆頭像（麵包師插畫）皆正常顯示 |

## 首頁環形照片列類別改名 ＋ hover 徽章改文案／去白框 — 2026-11-05 完成（未 commit）

| 項目 | 內容 |
|---|---|
| 指示 | ① CSS 類別名 `footer-logo-list-wrap` → `hero-ring-list-warp`、`hero_hand_item` → `hero_bc_item`；② hover 圓形徽章內文 `view more` → `Detail`；③ 移除徽章白色外框；④ 稍後：「圓形內部互動顯示的文字僅顯示 Detail，無需咖啡名稱」⇒ 徽章移除咖啡名稱、只留 Detail；⑤ 晚間：「Detail 字體加粗 500」；⑥ 晚間：「hover 後有手形 cursor 遮擋了文字，如何修復？」⇒ 徽章圓心偏移游標右上方 30px／32px |
| 改動 | `partials/bc_brand_stage_hero.html`（外層 wrapper 改名＋環上 7 格）、`index.html`（GUNTE hero 那組 7 格＋徽章 markup 只剩 `<span class="bc-hand-badge__more">Detail</span>`＋三支靜態檔版號）、`bc-hand-ring.css`（15 處選擇器改名／`.bc-hand-badge` `border` 刪除改 `border: 0`／刪掉 `.bc-hand-badge__name` 規則、`.bc-hand-badge__more` 0.5rem → 0.8rem 且不再壓 0.66 透明度／仍 `uppercase` ⇒ 畫面顯示 `DETAIL`）、`bc-hand-hover.js`（`ITEM_SELECTOR` 改名；刪 `NAME_SELECTOR`／`labelOf()`／`nameEl`，`show(item, e)` → `show(e)`）、`bc-hand-ring.js`（`querySelectorAll`）、`bc-gunte-hero.css`＋`bc-brand-stage.css`（僅註解中的類別名）、`docs/verify/*.py` 4 支驗證腳本同步 |
| 刻意未動 | `.hero_hand`／`.hero_hand_list`（容器名不動）；about 頁真頁尾 `partials/bc_brand_stage.html` 的 `.footer-logo-list-wrap`（那裡裝的是 deco 標誌輪播、不是環形照片；且 `bc-brand-stage.css` 本來就沒有該 class 的選擇器 ⇒ 純語意改名不影響版面） |
| 版號 | `bc-hand-ring.css` → `?v=20261105d`（同日四次改動，a→b→c→d）；`bc-hand-hover.js` → `?v=20261105c`（僅更新註解仍照規矩升版）；`bc-hand-ring.js` → `?v=20261105a`（本次未再改）；`bc-gunte-hero.css`／`bc-brand-stage.css` 只改註解、無樣式變更 ⇒ 未升版號（若要嚴格照「改 CSS 必升版」的規則可再補升 index＋about） |
| 驗證 | `manage.py check` 0 issue；Playwright（新啟的 8099 dev server，8081 那台是改動前啟動、模板為舊快取）：`#bc-stage-photo-ring-list` 內 `.hero_bc_item` **7 個**、`.hero_hand_item` **0 個**、`.hero-ring-list-warp` 命中、隱藏的 `#hero_hand_list` 也 7 個；`.bc-hand-badge` `childElementCount` **1**（只剩 `<span class="bc-hand-badge__more">Detail</span>`）、`[data-bc-hand-badge-name]`／`.bc-hand-badge__name` **0 個**、`textContent` = `Detail`（`text-transform: uppercase` ⇒ 畫面 `DETAIL`）、字級 `12.8px`、`font-weight 500`（`document.fonts.check('500 12.8px "Josefin Sans"')` = true ⇒ 真實 500 字重，非合成粗體）、`border 0px/none`、`border-radius 50%`、`108×108`；hover current 格 → `is-on`、圓心貼齊游標、照片 `scale 1.08`；截圖確認圓內只有 `DETAIL` 且筆畫變粗；console 0 error。**游標遮字修正複驗**（真滑鼠 `page.mouse.move` 到照片中心）：徽章圓心相對游標 `+30, -32`（CSS 變數 `--bc-hand-badge-dx/-dy`）、游標距圓心 41.8px < 半徑 51.3px（游標落在圓的左下緣）、`cursorHitsText = false`（游標在文字框下方 20.5px、左側 3.6px）、`transform: matrix(1,0,0,1,-24,-86)`、載入的 CSS 為 `?v=20261105d` |
