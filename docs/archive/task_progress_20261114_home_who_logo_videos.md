# 任務封存：手機 who 內文縮小＋左上 logo 貼左緣＋首頁 hero 影片 3→6 支（2026-11-14）

> 由 `task_progress.md` 移出（2026-11-14，docs_size_check 超標）。

**手機：who 內文縮小＋左上 logo 貼左緣；首頁 hero 影片 3→6 支 — 2026-11-14 完成（本地驗證）**

- ① who 內文（使用者：`.who-content-sticky` 內部文字縮小）：`bc-who.css` 兩處固定 px → **clamp**
  ⇒ `.who-content-text` `clamp(21px,5.85vw,27px)`（@320 21／@375 21.9／@430 25.2／≥462 仍 27）、
  `.section-title__text` `clamp(34px,9.2vw,42px)`（@375 34.5／≥457 仍 42）；`letter-spacing` 2.2px → `0.0815em`
  （＝27px 時的 2.2px，隨字級等比）。**桌機／平板（≥834：39／65px、≥1920：57／92px）完全不變**；
  em 系列裝飾（手繪圈 4.62em／緞帶 4.28em／gif 間距）自動等比例縮小。
  附帶解掉既有問題：≤375px 段落 `scrollWidth` > 盒寬（`body{overflow-x:clip}` 裁字）→ 現 `sw === cw`。
- ② 左上 logo（使用者：`.bc-navbar-brand-fixed` 離左邊緣太遠）：根因＝字串開頭全角「｛」Mogra 沒有
  ⇒ 落後備字型、字面左側留白 **≈0.71em**（實測 34px→24px、42px→30px）⇒ 舊 `left:15px` 墨跡其實從 **39px** 起。
  `bc-components.css` ≤991.98：`left:15 → 16px` ＋ `text-indent:-0.71em` ⇒ 墨跡左緣 **16px**（像素量測
  320/375/390/430/768 全為 16），與推薦雙卡手機內距對齊；≥992 桌機 `left:37px`／indent 0 不動。
  ⚠ canvas `measureText().actualBoundingBoxLeft` 只回 0.38em（與實際 paint 不符）⇒ 以後一律用截圖像素量測。
- ③ `bc-photoarea` 第 3 格影片輪播（使用者：現有 3 支之後依序加上 hero_03／02／06）：
  `views.PA_VIDEOS` 3 → 6 支，順序 `hero_00 → hero_04 → hero_05 → hero_03 → hero_02 → hero_06`（不洗牌）。
  模板／CSS／JS 都不用改（`{% for pa_video in pa_videos %}`＋`preload="none"`＋逐支 `prime()`）⇒ 首屏仍只抓 1–2 支。
  `hero_06.webm` 先前在工作目錄被刪（`hero_06_.webm` 為同 md5 備份）→ 已 `git checkout` 還原，本機不再 404。
- 版號：`bc-who.css ?v=20261114c`（index.html:1016）、`bc-components.css ?v=20261114b`（base.html:49）。
- 驗證（CDP headless 320/375/390/430/768/1440）：墨跡 16px、內文 21／21.9／22.8／25.2／27／39px、
  影片 `6 支`＋6 個 `HEAD 200`＋實際輪播 `0→2→4→5→1→3`（7s 取樣，clip ≈5s 故跳號但順序正確）、
  `docOverflowX=0`、0 exception、`manage.py check` 0 issue、`docs_size_check` 全在預算內。
  截圖 `_shot/bc-fix-mobile-{logo,who}-375.jpeg`、`_shot/bc-fix-mobile-who-320.jpeg`。
