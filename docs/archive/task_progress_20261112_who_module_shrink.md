# 首頁 who 模組：整體縮小（×1.3 → ×1.15）— 2026-11-12 完成（封存）

> 從 `task_progress.md` 移出的完整紀錄（2026-11-12 精簡時封存）。

- 指示：`.who-content-text` 整個模組（文字、照片、GIF、SVG、相關動畫）稍微縮小。
- 改法（只動 `static/css/bc-who.css`，JS／markup 未動）：把 11-11 的「全模組 ×1.3」等比下調為 **×1.15**
  （≈ −11.5%），四個斷點的長度值全部等比重算，幾何關係（圓圈 `top:73%`／箭頭 `left:45%`、gif 底緣、
  `--who-spacer-w` 等 scrub 目標寬度）同步縮放 ⇒ 動畫時間軸與觸發點不用改。
- 主要新值：base text 27px／max-w 460／title 42px／circle 118／arrow 131／bubble 49；
  ≥834 text 39px／max-w 736／title 65px／circle 181／arrow 168／bubble 69；
  ≥1920 text 57px／max-w 986／title 92px／circle 234／arrow 216／bubble 92。
  section 外距 padding 96/80（≥1080 96/40、≤834 96/20）不動。
- 版號：`bc-who.css` `20261111c`→**`d`**（`index.html:948`）；檔頭註解改記「原始值 ×1.15」對照表。
- 驗證（dev 8081）：1280×900 section 1042.4→**949.8px**（文字 44→39px、仍 7 行不破版；circle 205→181、arrow 190→168、
  bubble 78→69）；1920 文字 57px／6 行；834 文字 39px、kicker label 需求 97px < 133px 不截字；
  390×844 section 1069→**882.4px**（標題 47→42px 4 行→3 行、文字 31→27px 10 行→9 行）；四斷點 `overflowX=0`；
  scrub 正常（390：54→86→93 字、circle dash 377／arrow 0）；console 0 error、`manage.py check` 0 issue。
