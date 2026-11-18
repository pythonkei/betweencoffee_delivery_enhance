# 已封存：bc-reviews 跑馬燈接縫／複製修正（2026-11-13）

> 由 `task_progress.md` 於 2026-11-13 移至本檔（只留現況）。

**bc-reviews 跑馬燈「跳回第一組／內文沒全部顯示」修正 — 2026-11-13 完成（本地驗證）**

- 根因：`bc-reviews.js` 沿用原站前提「`.reviewsInner` 內容重複 2 份」，只捲 `scrollWidth/2`。
  `about.html` 的 28 組正好是「兩份相同的 14 組」→ 正常；但 `index.html` 的 28 組是
  **28 組不同文案**（前半／後半不同）⇒（a）捲到 `-半寬` 時接縫文字 ≠ 開頭 → 視覺上像跳回第一組；
  （b）x 只走半寬 → 最後約 1/4 內容永遠不進視窗。
- 修法（`static/js/bc-reviews.js`）：啟動前 `halvesMatch()` 比對前後兩半 `innerHTML`；
  不同就把整份 strip `insertAdjacentHTML('beforeend', innerHTML)` 自我複製（28→56 組），
  循環距離即「一份 strip 寬」→ 接縫完全相同；相同（about）則維持原行為不複製。
  另改為逐個 `.reviewsInner` 各自建 tween（原 selector 字串會共用第一個的寬度）、
  `data-bc-reviews-ready` 防重複初始化。版號：`bc-reviews.js ?v=20260906a → 20261113a`（index／about 同步）。
- 驗證：首頁 56 組、`halvesMismatch=[]`、接縫前後 frame 左緣位置完全相同（0/371/636/1300）、
  200 步取樣 28 組全部出現（missing 0）、速度仍 80px/s、390px 行動端 28 組全出現、console 無新增錯誤；
  about 仍 28 組（未複製）且接縫無縫。截圖 `_shot/bc-reviews-seam-v7.png`。
