# task_progress 封存段（2026-11-18 精簡 task_progress.md 時移出）

> 內容：`/coffee_menu/` kicker 首版（11-17）、行動端 logo 字級（11-17）、
> 首屏插畫與「COFFEE」同套互動首版（11-17）、「EVEN MORE COFFEE」分層文字（11-16）。


**/coffee_menu/ 首屏「COFFEE」左上角 `( Line Up )` kicker — 2026-11-17 完成（本地驗證；版面已於 11-18 改直排，見上則）**

- 標記：`partials/bc_coffee_title.html` 的 `__pin` 內新增 `.bc-coffee-title__stage`（一格 grid，字與 kicker 疊放）
  ＋ `.bc-coffee-title__kicker`（`<p>`，內含 `__kicker-anim` / `__parenthis` ×2 / `__kicker-label`）。
  ⚠ `__stage` 必須保持 **static**（變定位元素會攔走 `word.offsetParent` ⇒ `geo.lift` 少算「置中偏移」）；
  ⚠ kicker **不可放進 h1**（`splitChars()` 會 `textContent=""` 重建）。
- 樣式 `[H]` 參數照抄首頁 `bc-who.css:190-213`（括號 0.5s `cubic-bezier(.25,1,.5,1)`、標籤 0.8s ease／
  相對延遲 0.3s、整組 0.55s、`gap:4px`）；唯一差異＝**觸發方式**：banner 就是第一屏 ⇒ transition 改寫成
  載入即播一次的 CSS animation（`fill:both`），不必新增 IntersectionObserver。
- 腳本：`bc-coffee-title.js`「④ kicker 出場」——只補 ② 的位移，沿用第 0 個字 `C` 的 `local`；
  位移寫 `transform`、位置寫 `translate`（兩者相加，互不覆蓋）。



**行動端 logo 文字縮小（`｛ Between ｝`）— 2026-11-17 完成（本地驗證）**

- 需求：手機上左上角 logo 文字太大。
- 改動：`static/css/bc-components.css:172-182` 的兩個小螢幕斷點，只改 `font-size`
  → `≤767.98px` 36→**32px**、`≤575.98px` 34→**28px**；`top`／`left`／`text-indent:-0.71em` 全不動
  ⇒ 墨跡左緣仍固定 16px、字上緣仍與右側圖示同一水平線。≥768px（tablet 42／桌機 48）不變。
- 不動的東西：`.bc-navbar-brand-spacer`（nav 內隱形佔位）rect 不變 ⇒ 選單、浮動購物車／ORDER 對齊不受影響；
  仍需保持 `mix-blend-mode: difference`（勿改 color）。
- 版號：`base.html:49` 的 `bc-components.css ?v=20261114b` → **`20261117a`**。
- 實測（390／414／576／768／1024；Console 0 error）：28／28／32／42／48px，320px 也不與右側圖示重疊；
  首頁（照片背景）同字級、差值混合仍清楚。

**/coffee_menu/ 首屏插畫 `title_bg_img_01.svg` 與「COFFEE」大字吃同一套互動 — 2026-11-17 完成（本地驗證）**

- 需求：banner 內 `.svg-bg`（插畫）與大字一起「進場／托住／出場」，且插畫層級在字之上、商品卡片之下。
- 現況摘要：`bc-coffee-title.css` 新增 `[G]` 區塊 `.bc-coffee-title-bg--anim`（`translate: 0 .16em` → `.is-ready` 收回原位，
  同 `--bc-ct-dur`／`--bc-ct-ease`，變數改掛 `.bc-coffee-title, .bc-coffee-title-bg`＝`[A0]`）；`bc-coffee-title.js` 選
  `[data-bc-coffee-title-bg]` 走與字相同的進場＋捲動流程（hold 同 `__pin`，出場跟隨第 0 字 `C`，可用根節點
  `data-bc-ct-bg-char` 換字）；`coffee_menu.html` 的 `.svg-bg` 加 `bc-coffee-title-bg` ＋ `data-bc-coffee-title-bg`（inline 仍 `z-index:3`）。
  版號 `bc-coffee-title.css ?v=20261117e`、`bc-coffee-title.js ?v=20261117c`。
- **補（同日，使用者「z-index 位置在 COFFEE 文字上」）**：堆疊本來就對（`.svg-bg` 3 > 字 2），看不到是因為
  `style-bootstrap.css:3367` 的 `opacity:.06` —— 6% 白線疊在白字上等於消失。改在 `coffee_menu.html` inline 蓋
  `opacity:.5`（選擇器 0,3,0 勝過原 0,2,0；其他頁仍 0.06）。實測 1440：線稿清楚壓在 C 上、字仍可讀；0.3 較含蓄、
  0.75 以上像白色貼紙，要調只改那一行。僅改模板 → **不需升 `?v=`**，但要重啟 dev server（template cache）。
- 關鍵技巧：進場用 CSS **`translate` 屬性**、捲動用 **`transform` 屬性**（兩者獨立相加）；若都用 transform，JS 寫的 inline
  transform 會整條蓋掉進場。
- **踩到（已修）**：插畫元素本來是 `translate:none`，JS 直接加 `--anim` 會先跑一段 0→.16em 過渡、緊接著 `.is-ready` 又拉回 0
  ⇒ 完全看不到進場（量測只看到 `none`／`0px`）。修法＝加 `--anim` 前先 `style.transition='none'`、強制 reflow、再還原過渡，
  下一帧才加 `.is-ready`。字沒有這問題：span 是 JS 新建、出生就帶起點位移。
- 實測（Playwright 1440×900／390×844）：進場插畫與 `C` 的位移逐帧相等（71.68 → 60.65 → 50.63 …）；捲動全程插畫中心
  與 `C` 墨跡中心 `dy` ≒ -0.01px（`dx` -0.45 為字面留白，原本如此）；`prefers-reduced-motion: reduce` ⇒ JS 整支跳過、
  插畫 `translate:none`、無 inline transform；0 console error、`manage.py check` clean。


**/coffee_menu/ 首屏「EVEN MORE COFFEE」分層文字（移植 global-tree.jp/service/ 的 `.layeredTextVertical`）— 2026-11-16 完成（本地驗證）**

- 現況摘要：`static/css/bc-even-more.css`（`?v=20261116c`）＋`static/js/bc-even-more.js`（`?v=20261116a`）＋
  `partials/bc_even_more.html`，掛在 `coffee_menu.html` 的 `.subpage-banner-h500` 內（`title_bg_img_01.svg` 背景保留，
  模組不畫底色、純覆蓋層 `z-index:1`）；資產由本頁 `extra_css`／`extra_scripts` 載入（`extra_scripts` 來自
  `base.html:409`）⇒ **改模板後要重啟 dev server**。
- 動畫逐值照抄原站：`__stack scale(1.7)→1`（1s）、三層 `translateY(32%) → 0 / -41.5% / -103%`（1.3s）、
  `clip-path: inset(.5em/.3em/0 0 0)`、`delay .2s`、`cubic-bezier(.16,1,.3,1)`；`is-show` 由 IO 15% 加上、只播一次。
- **照片三層各放一張**（原站 `.photList` 也在文字行內）：`images/bean_menu.jpg`、`height:.79em`、`aspect-ratio:194/109`
  ⇒ clip-path 連照片一起切，才有「套印不準」的錯位鬼影；只留一張就沒有這個效果（CSS 檔頭已寫警告）。
- 文案 `EVEN MORE AMAZING` → `EVEN MORE COFFEE`（右半段品牌金）；字級 `clamp(2.6rem, 10.6vw, 156px)`
  （1440 → 152.6px、390 → 41.3px、1920 封頂 156px）；行內容 `flex + space-between + baseline`、`padding-inline:2.5vw`。
- 實測（Playwright）：1440×900／390×844／768×1024／1920×1080／320×568 皆 `documentElement.scrollWidth == vw`、
  0 console error；終態 3 行字＋照片切片與原站截圖同構。`body.scrollWidth` 在 390 仍為 398（＝`.svg-bg ftco-counter`
  既有的 8px，非本模組）。關閉 JS（`javaScriptEnabled:false`）＝`<noscript>` 直接給同一終態；`manage.py check` clean。
- 踩到：`{# #}` 不可跨行／內文不可再含 `{#`、`#}` ⇒ 說明一律用 `{% comment %}`（與 `bc_next_link.html` 同寫法）。
