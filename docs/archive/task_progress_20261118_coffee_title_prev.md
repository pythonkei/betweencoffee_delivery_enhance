# task_progress 封存段（2026-11-18 再次精簡 task_progress.md 時移出）

> 內容：`/coffee_menu/` 移除首屏「從下到上」進場動畫（11-18）、插畫移入字容器左側＋放大＋「捲動互動反轉」修正（11-18）、`( Line Up )` 改直排（11-18）。


**/coffee_menu/ 首屏移除「從下到上」進場動畫（COFFEE 文字 ＋ title_bg_img_01.svg）— 2026-11-18 完成（本地驗證）**

- 需求：「將 title_bg_img_01.svg 和 COFFEE 文字移除初始時的從下到上的動畫效果」
- 只動「進場」，捲動托住（pin）／逐字出場完全保留：
  · `static/css/bc-coffee-title.css`：刪 `__char` 的 `translate3d(0,.16em,0)`＋`transition`＋`will-change`、
    刪 `.bc-coffee-title.is-ready .bc-coffee-title__char{transform:none}`、刪 `--bc-ct-dur／--bc-ct-ease` 變數塊、
    刪 `.bc-coffee-title-bg--anim`（translate .16em 起點）與其 `.is-ready` 規則；
    `will-change: transform` 改掛在 `.bc-coffee-title-bg`（捲動用）；reduce-motion 只留 `__char-inner` 歸零。
    檔頭 [4] 保留移除紀錄與還原配方（起點 .16em／.95s／60ms from edges／`.is-ready` 掛勾）。
  · `static/js/bc-coffee-title.js`：刪 `STAGGER_MS`、`splitChars()` 的 inline `transitionDelay`、
    init 的 ① 強制 reflow 與 ①b（`--anim` ＋ rAF 加 `.is-ready`）⇒ ①＝只拆字、①b＝只取插畫節點。
    拆字保留（出場是逐字往上滾掉，需要逐字節點）。
  · 模板註解同步：`coffee_menu.html` inline 插畫說明、`partials/bc_coffee_title.html` 檔頭。
- 版號：`bc-coffee-title.css ?v=20261118h`、`bc-coffee-title.js ?v=20261118b`。
- 實測（Playwright ＋ 本地 runserver）：1440／1280／390／1920 載入後 `__char` 的 transform 全 `none`、
  插畫 `translate:none`、`document.getAnimations()` 裡沒有任何 CSSTransition（＝無進場過場）；
  捲動照舊：scrollY 400 → 字內層 0／−2.04／−36.42／−36.42／−2.04／0（中央先走）、900 → 全 −569、
  `__pin` +858、插畫同步 −569；版面與移除前相同（1440 插畫 385.3×499.4、字框 358.4、kicker top 178.5）；
  390／1280／1920 無水平捲軸；reduce-motion 不拆字、靜態置中；0 console error、`manage.py check` clean。

**/coffee_menu/ 插畫移入字容器左側（白色不透明）＋ 放大 ＋「捲動互動反轉」修正 — 2026-11-18 完成（本地驗證）**

- 需求①：「title_bg_img_01.svg 放到 COFFEE 文字左側、放進文字容器，整組頁面居中對齊、插畫改白色不透明」
  ⇒ 插畫從 banner 搬進 `partials/bc_coffee_title.html` 的 `.bc-coffee-title__stage` 第 1 欄
  （`grid-template-columns: auto auto`：第 1 欄插畫／第 2 欄 h1 ＋ kicker 疊同一格），
  整組由 `__pin` 的 `place-items:center` 置中；`( Line Up )` 位置不動。
- 需求②（同日追加）：「向下滾動時的互動效果異常、反轉了」
  成因：插畫搬進 `__pin` 內之後，托住位移已由 `__pin` 的 `translate3d` 帶著走，
  `bc-coffee-title.js` ③ 又補一次 `hold` ⇒ 變成 2 倍，插畫比字多滑一段（看起來像反轉）。
  修法：新增 ②c `bgInPin[]`（`pin.contains(bg)`）⇒ 在 `__pin` 內 `hold` 加 0（在 `__pin` 外才補）；
  `lastBg` 由單一值改成逐元素陣列，其餘快取邏輯不動。
- 需求③（同日追加兩次）：「將 title_bg_img_01.svg 放大尺寸」→ 再追加「enlarge」
  `coffee_menu.html` inline 改 `width: min(0.86em, calc(100vw - 2.072em - 2vw))`：
  大螢幕 385.3×499.4（≈ banner 的 500px 高 ＝ 字框 358.4 的 1.39 倍；
  沿革 0.52em 233×302 → 0.62em 277.8×360「與字同高」→ 0.86em），
  窄螢幕由 calc 那項讓出剩餘寬度（1280 → 326.1、1180 → 228.1、390 → 59、320 → 48.4）。
  ⚠ 副作用與修法：插畫變高會把 grid 那一列撐成 499px ⇒ `align-self:start` 的 kicker 被推到列頂
  （離 'C' 墨跡頂約 70px）；改成插畫上下各 `-0.1574em`（＝(1.1148em − 0.8em)/2）等量負 margin
  ⇒ 插畫佔的列高回到 0.8em（字框高）、kicker 重新對齊 C 頂，插畫中心不變（對稱負 margin）。
- 版號：`bc-coffee-title.css ?v=20261118g`、`bc-coffee-title.js ?v=20261118a`（JS 本次未改）。
- 實測（Playwright）：插畫 inline transform 與第 0 個字（'C'）逐格**完全相同**（捲 0/300/600/750/1000/1300）；
  尺寸 1920/1600/1440 → 385.3×499.4、1280 → 326.1×422.8、1180 → 228.1×295.7、390 → 59×76.4；
  `stage.height == word.height`（358.4）、kicker top − word top ＝ 7.7px（＝C 墨跡頂）；
  320/360/390/430/768/1024/1180/1280/1440/1600/1920 皆無水平捲軸；
  進場 translate 71.68px → 0 正常、`translate:none`＋無 inline transform；0 console error、`manage.py check` clean。


**/coffee_menu/ `( Line Up )` 改直排（貼 'C' 左上角、欄頂對齊 'C' 頂）— 2026-11-18 完成**

- 需求：「將（Line Up）更改為垂直文本, 位置在'C'左上角, 保留 'C'頂部相一對齊, 保留互動效果」；
  11-18 追加：「整個文本是垂直，但是文字均為全部垂直的（整串轉 90°），不是 L／I／N／E 一字一行站直」
  ⇒ 首版用 `text-orientation: upright`（字母站直堆疊）被否決，改 `sideways`。
- 改動只落在 `static/css/bc-coffee-title.css [H]`（HTML 標記不動、JS 不動）：
  · kicker 自己 `writing-mode: vertical-rl` ＋ `text-orientation: sideways`
    ⇒ 整串由上往下、每個字母轉 90°（＝把整條橫排字轉成直書）；直排時 `line-height:1.1` ＝欄的厚度、
    `letter-spacing:.04em`。
  · 括號**不再** `rotate:90deg`：整串已一起轉，括號自然就是直書的 ︵／︶（再轉會歪 90°）。
  · 位置：`translate: calc(-100% - 8px) calc(var(--bc-ct-fs) * var(--bc-ct-cap-offset))`
    ⇒ 欄貼 'C' 字框左緣外側 8px、**欄頂對齊 'C' 墨跡頂**。
  · 新根變數 `--bc-ct-cap-offset: 0.0172`（em of 大字字級；canvas `measureText` 實測
    ascent 433／descent 104／'C' ink 336 ⇒ half-leading −89.3，字框頂比字形頂高 7.7px @448）。
  · 標籤展開動畫 `max-height 0→4em`。`sideways` 的欄長＝原橫排寬度（實測 "Line Up" 3.827em
    ＝84.2px @22px），`max-height` 要貼著實測值（4em 留 4% 餘裕），值過大會在時間軸前段就吐完而失去動畫感；
    括號 0.5s／0.55s、標籤 0.8s ease／0.85s 全部照舊（互動效果不變）。
  · 字級 `clamp(11px, --bc-ct-fs × .05, 22px)`（跟著大字縮放）⇒ 欄長 ≈ 'C' 字高的
    0.32 倍（1920／1440）、0.50（390）、0.61（320）。
- 版號：`bc-coffee-title.css ?v=20261118c`（`coffee_menu.html`）。
- 實測（Playwright 1920／1440／390／320；0 console error、0 水平溢出）：欄頂 − C 墨跡頂 **0.00px**、
  欄右距字框左緣 **8.00px**、欄寬 24.19／12.09px（390）；字元平均步進 12px（upright 為 22px）⇒ 每字已轉 90°；
  動畫重播 label 高 0 → 0 → 43.7 → 72.4 → 84.2px（全長）；捲 700px 時 kicker inline transform 與 C 逐字相同
  （translate3d −457.98px）、捲回歸零；`prefers-reduced-motion` 下 label 直接 84.2px、JS 不拆字。
