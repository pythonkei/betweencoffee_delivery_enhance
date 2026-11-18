# 封存：task_progress 2026-11-12 who 視覺/圓圈 ＋ 2026-11-11 next-link/字型（原文）

**首頁 who 模組：gif 右側間隔＋手繪圓圈再寬 10% — 2026-11-12 完成**

- 使用者兩點：① `wwa-03.gif` 與「——有溫度」之間要留間隔；② 圓形 SVG 寬度再增加 10%。
- ① `bc-who.css` 新增 `.wwa-anim-visual.wwa-visual-03 { margin-right: 0.4em }`（27／39／57px 字級
  ⇒ 10.8／15.6／22.8px）。`img` 是 absolute 定位，margin 只推開後續文字、不動 gif 位置；
  JS 動的是 `width`（inline style），兩者不衝突。
- ② `.who-circle-svg--cjk` `4.2em → 4.62em`（×1.1；`height:auto` 依 158:88 同步長高）：27px 字級
  113×63 → **125×69**、39px 164×91 → **180×100**、57px 239×133 → **263×147**；39px 下對「執著」
  字寬 84px 的左右留白 40 → 48px。≤410px guard 維持 3.6em（4.62em 會讓 390px 右緣 402.9 > 390，
  被 `body{overflow-x:clip}` 裁掉弧線）。
- 版號 `bc-who.css` `20261112d` → **`e`**；`index.html` 檔頭註解同步（4.62em＋gif 間隔）。
- 驗證（dev 8081）：375（guard 3.6em）／390（右緣 389.2）／411（右緣 403、餘裕 8px）／414（餘裕 11px）／
  1280（圈 180.2×100.3、gif 後間隔 15.6px）／1920（圈 263.3×146.7、間隔 22.8px）全 `overflowX=0`；
  三個 visual 皆 scale 1（槽寬 103／88／103）；0 console error；`manage.py check` 0 issue。

**首頁 who 模組：visual 互換＋手繪圓圈下移 10px — 2026-11-12 完成**

- 使用者兩點：① `wwa-01.svg` 與 `wwa-03.gif` 位置互換；② 圓形 SVG 無法完全圈住文字，需向下移 10px。
- ① 模板內兩個 `<span class="wwa-anim-visual …">` 節點整塊互換（類別名不動）⇒
  「有熱無凍」後＝**動圖 wwa-03.gif**；「帶包豆返 Office」後＝**線稿 wwa-01.svg**。
  尺寸／位移（`--who-visual01-w` / `--who-visual03-w`、`top/left`）與 JS 觸發規則皆為 class 判斷，
  因此 CSS／JS 未改一行，只有揭示先後變成「gif 先、線稿後」。
- ② `.who-circle-svg--cjk` `top: 48%` → `calc(48% + 0.26em)`（39px 字級＝+10.1px；27／57px 等比
  +7／+14.8px）。用 em 不用 px：圈寬本身是 em，固定 px 位移會讓大螢幕圈的相對位置愈偏上。
- 版號 `bc-who.css` `20261112c` → **`d`**；`index.html` 檔頭註解同步（ⓑ／ⓔ 對調＋top 說明）。
- 驗證（dev 8081）：1280（圈 164×91、top 37.02px、完全圈住執著）、1920（圈 239×133、留白 58.1／119.7px、
  尾巴不壓「同時」行）、390（guard 3.6em、右緣 389.2px、`overflowX=0`）；visual 順序
  spacer → gif → png → svg 且 scale 1；82 幀＋`circleDash 377`＋`arrowDash 0`；0 console error；
  `manage.py check` 0 issue、`docs_size_check.py` 全在預算內。

---

**next-link「( NEXT )」＋首頁 who 標題改用 Akzidenz Grotesk Pro — 2026-11-11 完成**（全文封存 → `docs/archive/task_progress_20261111_next_link_and_font.md`）

- `bc_next_link.html` 文案 `( NEXT )`；`.bc-next-link__label` 字型 `var(--bc-font-akzidenz)`（自架 woff2，`@font-face`／變數補在全站 `bc-fonts.css`）、
  字級 `clamp(0.875rem, 0.8125rem + 0.3vw, 1.0625rem)`（16.84px＠1280／13.09px＠390）；上捲動畫搬到 `.bc-next-link__loop` 本體 → 常駐 1450ms infinite；
  `bc-who.css` 的 `.bc-who-section .section-title__text` 只換 `font-family`。版號：`bc-fonts.css 20261111a`、`bc-next-link.css 20261111h`、`bc-who.css 20261111c`。
- 未解：`/coffee/2/`（Sunshine）等 6 款的 `staff_comment_1~3` 全空 ⇒ 詳情頁氣泡整塊不渲染（**資料問題**，非 CSS／JS；
  模板條件 `coffee.html:54`／`bean.html:51`）。待決定只補 #2、還是 #1/#2/#3/#8 一起補。
