# bc-reviews 內文放大 ＋ 膠囊內距三輪加大（2026-11-13）

> 由 `task_progress.md` 封存（2026-11-13，檔案超預算時移出）。現況摘要仍留在 `task_progress.md`。

## 文字與幾何（`static/css/bc-reviews.css`）

- 文字：桌機 15→16.5px（lh 23）、≤768 14.5（lh 20）、≤480 12（lh 16）；`--maru` 15.5／13.5／11。
  首頁 `--rv-scale:1.15` ⇒ 實測 18.975px、375px 13.8px。
- **置中改由版面保證**：`.reviewsBox` `inline-block → inline-flex + align-items/justify-content:center`，
  `.reviewsBox__text` 只留左右 padding ⇒ 行高不必整除也永遠垂直＋水平置中（含 `scaleX(1.15)`）；
  實測 `gapTop = gapBottom`、`inkDx = 0`。
- **內距三輪**（回報「內距再加大，文字與邊框相應」／「邊框高度加大內距、文字保持居中」）：
  - 膠囊高 25→27→29→**31** / 22→24→26→**28** / 18→20→22→**24**（第三輪垂直呼吸 2→3px，左右內距不變）
  - 左右內距 15→16.5→18 / 12→13→14.5 / 9→10→11.5；`--borderR` 25→27→30 / 20→22→24 / 15→16.5→18
  - `--maru` 直徑與 `reviewsMark__box` 高同步，垂直呼吸 1→2→3px（31 − 2 邊框 − 23 行高）
  - 實測（×1.15）：首頁 1440 高 35.64／左右 34.5、700 32.19／27.6、375·320 27.59／20.7；about 1440 高 31／左右 30
- JS（`static/js/bc-reviews.js`）：抽出 `start()`（kill 舊 tween → 依現況 `scrollWidth` 重量、`progress()` 保留進度），
  `fonts.ready`／`resize`(150ms) 後 `refreshAll()`；`PX_PER_SEC = 80` 不變（字變寬 → duration 自動變長）。
- 版號：`bc-reviews.css ?v=…20261113b→d→e→f→g`、`bc-reviews.js ?v=…20261113a→c`（index／about 同步）。
- 驗證：首頁 29 組→58、about 28 組；speed 恆 80（half 首頁 12408／about 4599，duration 自動換算）；
  `gapTop = gapBottom`（首頁 4.59／4.59、about 4／4＝邊框 1＋呼吸 3）；四種寬度無溢出／無水平捲軸／console 無新增錯誤。
  截圖 `_shot/bc-reviews-{padding,bigger,pad2,pad3}-*.png`。
