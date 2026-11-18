# 封存：首頁 who section 主視覺（global-tree .layeredText/.layeredImage 移植）

> 2026-11-16 從 `task_progress.md` 移出（控制 11.7K 預算），內容逐字保留。
> 現況摘要仍在 `task_progress.md`「最近任務」第一則。

**首頁 who section 主視覺＝global-tree.jp「照片 ＋ 大字」整塊（已放進首頁）— 2026-11-14 完成（本地驗證）**

- 需求 ①：原站 `<div class="sm:flex flex-row-reverse justify-end items-center">`（`.layeredText` ＋ `.layeredImage`）
  的版面與動畫要**完全一樣** ⇒ `static/css/bc-gt-mv.css`＋`static/js/bc-gt-mv.js`＋`partials/bc_gt_mv.html`
  （數值全部取自原站 build 檔：照片欄 `30.3472vw`＝49/97/293−2、第 3 條 `aspect-ratio:293/380`、`mr 20px`／
  `mt −20px`、字級 `10.0694vw`（@1440 145px、lh 94%）、文字 `.25/.36/.1em`＋`94%`＋`−12%`、`scale(1.5→1)`，
  1s `cubic-bezier(.16,1,.3,1)`；圖片動畫沿用 `bc-photoarea.css` 的 `bc-pa-*`）。
- 需求 ②（本次）：「現在 / 看不見，替換此內容到 `.section-title__text`」⇒ 從 `?mv=gt` 對照模式**正式放進
  首頁 who section 的 `.section-title__text`**（原「Hmm...........」`.who-title-layers` 的位置）。
- 改動：`index.html` 刪掉 `request.GET.mv` 對照入口＋舊 `h2` 內容，改 `<div class="section-title__text">`＋include；
  `bc-who.css` 移除 `.who-title-layer*` 與思考氣泡 SVG 樣式、`.section-title__text` 改 `display:block`；
  `bc-gt-mv.css` 刪 `.bc-gtmv--preview`（fixed 鋪滿），檔尾 [6] 把 row 左右 padding 歸零（對齊 kicker 左緣）
  ＋小螢幕 `overflow-x: clip`（文字最寬行只多 3.3px）。
- 起播改「進視口才播」：`bc-gt-mv.js` 用 `IntersectionObserver`（25% 可見）加 `.is-live`（文字 zoom／切片）
  ＋第一片 `.is-on`（照片 wipe／slice／image）；之後每 5s 只搬 `.is-on`（文字不重播，與原站一致）。
  沒有 JS／reduced-motion 時由 `.bc-gtmv__item.-index-1{opacity:1}` 保證第一片可見（拿掉 markup 的 `is-on`
  後會 opacity:0 的坑已補；手動移除 JS class 模擬無 JS＝靜態完成態）。
- 實測（1440／390，0 console error、`ovfX=0`、`manage.py check` 0 issue）：照片欄 x=80／437×380（三條 49-97-293）、
  文字 x=537／145px／lh 136.3；390 照片欄 x=20／289.1×251.2、字 39.27px；捲入時同時 9 個 animation、
  `.is-on` 每 5s 換片；reduced-motion animation 0。
- **2026-11-14 使用者後續指示**：①「clear this section blk bg color」⇒ `.bc-gtmv` 由 `--bc-bg`
  `#0e0e0e` 改 `background: transparent`（body 的 `bg_4.jpg` 會透出來，不再是一塊純黑）
  ②「Follow your phythm change to Hm.......」⇒ 大字 3 行改單行 `Hm.......`（`.bc-gtmv__line` 只剩 1 個、
  `.visually-hidden h2` 同步改；`-accent` 金色行移除）。行高／位移比例／照片欄不變 ⇒ 模組高 405→360px
  （1440）、文字 443.7×132.7；390 文字高 36、`ovfX=0`。
- 版號 `bc-gt-mv.css ?v=20261116a`、`bc-gt-mv.js ?v=20261114f`。
- **2026-11-16 使用者指示「文字 Hm..... 移到圖片頂部對齊」**（完成，本地驗證）：≥640px
  `align-items` 由 `center` 改 `flex-start`、`.bc-gtmv__text{margin-top:calc(-0.10361em - 20px)}`
  （行盒墨跡落差 0.12861em − 切片既有 −0.025em，再 −20px 抵照片欄的負 margin）。
  @1440 墨跡頂 249.79 vs 照片頂 249.78（差 0.01px；1024／834／640 差 0.23／0.69／0.51），
  照片位置／模組高 360／下方內容都不變；<640 區塊堆疊不受影響、`ovfX=0`、0 console error。
- 細節（逐值對照表＋放置說明）：`docs/home-photoarea.md`「四之六」。回退：`git checkout --
  templates/betweencoffee_delivery/index.html static/css/bc-who.css docs/home-photoarea.md` ＋刪 `bc-gt-mv.*`。
- **2026-11-16 使用者指示（同日第二批）「who-section 照片換圖 ＋ 內文改字」**（完成，本地驗證）：
  ① 三片「錯位疊印」照片依序 `who_01.jpg` / `who_02.jpg` / `who_01.jpg`（原 `photoarea/pa-1`、`pa-2`、`pa-4.webp`；
  `partials/bc_gt_mv.html`，`?v=20261116a`）。直幅素材（1280×1920／1920×2880）走
  `.bc-gtmv__px > img{object-fit:cover}` ⇒ 版面／動畫參數不動（1440：row 1280×360、照片欄 437×380、照片區 283.6 寬）。
  ② `index.html` 內文「先鎖得住最純粹嘅果香回甘！」→「先鎖得住最純粹產地嘅極緻, 釋放咖啡豆最真實靈魂提供俾
  Lover! Stay Warm, Stay Awake.」（逐字 `.wwa-anim-char` 82 → 120；`wwa-visual-02` 小圖仍掛同一句句尾，原「！」移除）。
  揭示時序是 `progress × totalDur`（`bc-who.js` 動態依元素數推算）⇒ 新增字元只是把序列拉長，仍隨文字滾到視口頂走完。
  ③ `bc-who.css` 新增 `.bc-who-section .wwa-nowrap{white-space:nowrap}`，包住 `Lover!`／`Stay Warm, Stay Awake.`／
  `Office`／`承包。`，修掉逐字 span 造成的斷行瑕疵（句號被擠到下一行開頭、`O`/`ffice` 被拆）；版號
  `bc-who.css ?v=20261114e → 20261116a`（index.html:1028）。
  ④ 驗證（1440／390，0 console error、`ovfX=0`、`manage.py check` 0 issue）：三片照片 `naturalWidth` 1280×1920／
  1920×2880／1280×1920（每片 3 條切片都載入）、1440 內文 7 行、390 內文 10 行（末行「承包。」，不再單獨一個句號）、
  手繪箭頭仍錨在「腦力」正下方（`left:50%` of 2 字 wrapper）。
- **2026-11-16 使用者指示（同日第三批）「文字縮小／修掉兩句黏字／wwa-02 間距」**（完成，本地驗證）：
  ① `bc-who.css` `.who-content-text` 字級 ×0.93：27→25（`clamp(20px,5.45vw,25px)`）、≥834 39→36、
  ≥1920 57→53，字距 3.1→2.9／4.6→4.3（base 仍 `0.0815em` 隨字級走）；`max-width`／`min-height` 不動
  ⇒ 區塊寬度與捲動節奏不變。**三張小圖尺寸完全不動**（`--who-visual01-w` 66／103／165、
  `--who-visual03-w` 62／88／145 仍為 px；使用者明示「照片不要修改」）。
  ② 「Stay Warm, Stay Awake.」與「飲完…」在 DOM 內原本沒有任何空白（小圖 container 展開前寬度 0）⇒
  斷行／貼字時會讀成「Awake.飲完…」；`index.html` 在 nowrap `</span>` 與 `wwa-visual-02` container
  之間補**一個真正的空白字元**（同行＝一個空格；剛好在這裡斷行時空白被瀏覽器吃掉、下一行由小圖開頭）。
  ③ `bc-who.css` 新增 `.wwa-visual-02{margin-right:.5em}`：原本 0 ⇒ 圖右緣直接貼着「飲」（比 gif 的
  0.4em 再寬一點）；手法與 `.wwa-visual-03` 相同（只推開後面的文字，不動 absolute 的 img）。
  ④ 驗證（1440／1280／834／390，0 console error、`ovfX=0`、`manage.py check` 0 issue）：字級實測
  36／36／36／21.26px；1440＋1280 內文 7 行（原 8 行，末行「腦力由我哋承包。」）；「.」→ 圖 11px、
  圖右緣→「飲」15px（1920：16.2／15.5px、字級 53px）；逐字 `.wwa-anim-char` 仍 120
  （新增的空格不是 char span ⇒ 揭示時序不變）。版號 `bc-who.css ?v=20261116a → 20261116b`。
- **2026-11-16 使用者指示（同日第四批）「wwa-02.png、wwa-01.svg 交換 ＋ who 照片換 who_03」**（完成，本地驗證）：
  ① `index.html` 把兩個 `.wwa-anim-visual` 容器**整組對調**（class＋img 一起搬）：現在
  `wwa-visual-01` 放 `wwa-01.svg`（在「…Stay Warm, Stay Awake.」之後）、`wwa-visual-02` 放 `wwa-02.png`
  （在「帶包豆返 Office」之後、「，」之前）。容器 class 隨圖走 ⇒ `--who-visual01-w`／`--who-visual03-w`
  尺寸與 JS 揭示時序都不用改（實測兩者 img 皆 103px 寬 @1440）。
  ② `bc-who.css` 新增 `.wwa-visual-01{margin-right:.5em}`：互換後 svg 右邊緊接「飲」，原樣只有 **3px**
  （svg 原本掛在「Office」與「，」之間、右側不需要 margin）⇒ 補成與 png 相同的 18px；手法同
  `.wwa-visual-02/03`（只推開後方文字，不動 absolute 的 img）。
  ③ `bc_gt_mv.html` 第三片 `who_01.jpg` → `who_03.jpg?v=20261116b`，片單＝`who_01`／`who_02`／`who_03`。
  ④ 驗證（1440／1280／834／390，`manage.py check` 0 issue、`ovfX=0`、0 console error）：
  「.」→svg 11px、svg→「飲」**21px**（＝3＋18）、「Office」→png **0px**、png→「，」15px；
  1440／1280／834 內文仍 **7 行**、`.wwa-visual-01` 後方的「飲」沒有被擠到下一行；
  390 小圖 66px、svg→「飲」13.6px、png→「，」7.6px、10 行、無孤字；gtmv 三片 `naturalWidth` 1280／1920／1080、
  切片 box 49／97／293×380 不變。版號 `bc-who.css ?v=20261116b → 20261116c`。
- **2026-11-16 使用者指示（同日第五批）「who-section 改為 'Hm.......' → 'Hmmm...'，and 文字縮小」**（完成，本地驗證）：
  ① `bc_gt_mv.html` 三份重疊切片＋`.visually-hidden` h2 → `Hmmm...`。
  ② `bc-gt-mv.css` 字級改 `calc(var(--gt-fs-scale) * clamp(1.25rem, 10.0694444vw, 24.1666667rem))`，
  `--gt-fs-scale:0.8` ⇒ @1440 145 → **116px**；檔內其餘值都是 em（裁切 0.25／0.36em、位移 0.1em、
  對齊補正 −0.10361em）⇒ 自動等比縮小，不必逐一改。要再放大／縮小只動這一個變數。
  ③ 驗證（1440／834／390，0 console error、`ovfX=0`、`manage.py check` 0 issue）：單行寬 461.5
  （原 444，`m` 比 `.` 寬 ⇒ 縮 0.8 倍後略寬）、高 109（原 136.3）；**墨跡上緣與照片上緣仍齊平**
  （1440 實測 172／172px、834 差 0.03px；比例不變故對齊補正不用改）；390 font 31.42、文字盒 350×28.8。
  版號 `bc-gt-mv.css ?v=20261116a → 20261116b`。
