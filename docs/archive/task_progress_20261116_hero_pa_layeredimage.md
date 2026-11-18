# 封存：首頁 hero 背景照片 `.layeredImage` 移殖（2026-11-14）＋ 移除錯位疊印（2026-11-16）

> 自 `task_progress.md` 移出（2026-11-16，檔案超標）。現況摘要見 `docs/home-photoarea.md`「四之五」。

**首頁 hero 背景照片移殖 global-tree.jp `.layeredImage`（三階梯滑入＋斜向擦除）— 2026-11-14 完成（本地驗證）**

- 需求：「為什麼顯示圖片效果不移植??」⇒ 原站 hero 除 `.layeredText` 外還有 `.layeredImage`（同一張圖 3 份
  遞增裁切＋斜向 wipe）；套在首頁 hero 照片區 `.bc-photoarea` 的 4 個照片格（第 3 格是影片輪播，不做階梯）。
  **第二輪：佈局與動畫「完全一樣、完全移植」** ⇒ 直接抓原站 build 檔逐值對齊，不再用推估。
- 原站值（實查）：`__image-wrapper > __image ×3`、寬 49／97／293px @1440（後兩層 `-1px` 疊縫）、
  起始 `translateX(-100%/-151%/-50%)`＋`-index-3 img{width:0}`、進場 1s `cubic-bezier(.16,1,.3,1)`（`--delay:0s`）、
  擦除＝wrapper `clip-path`（GSAP 0.9s `expo.out`，`--tr=v²`、`--br=v`、`--tl=0`、`--bl=1`）。
- 改動：`partials/bc_brand_stage_hero.html` 4 個 `<img>` → `.bc-pa-stair > .bc-pa-stair__track > __slice ×3`
  （`x_n／y_n／d_n／data-para` 全搬到外層 ⇒ 落點洗牌、視差、層序不變）；`bc-photoarea.js` **無改動**。
- CSS（`bc-photoarea.css` 檔尾）：切片寬 `flex: 49/97/293 1 0`（比例一字不差）＋後兩層 `-1px` 疊縫；
  `@keyframes bc-pa-slice`／`bc-pa-image`（1s `cubic-bezier(.16,1,.3,1)`）＋`bc-pa-wipe`（0.9s，
  `expo.out` **每 1% 取樣 101 格**，直接寫 `tr=v²`／`br=v`）；全部包在
  `@media (prefers-reduced-motion: no-preference)`、`fill: backwards`（收合只在 0% 影格 ⇒ 不先閃完整照片；
  基底＝終態 ⇒ 動畫關掉／被中斷仍是靜態照片）。版號 `?v=20261109h → 20261114b`。
- 驗證（CDP 暫停 `getAnimations()` 逐點比對 `expo.out`＝完全相符）：45ms→tr 8.579／br 29.289、90ms→25／50、
  180ms→56.25／75、450ms→93.848／96.875、900ms→100／100；版面 1440 四格 479.52×671.19、三層
  53.52／105.95／320.05，390 為 162.23×227.08、三層 18.11／35.84／108.28（手機保留三層），`ovfX=0`，
  reduced-motion `bc-pa-*` animation = 0、clip 全開、0 console error。
- 細節與對照表：`docs/home-photoarea.md`「四之五」。回退：`git checkout -- static/css/bc-photoarea.css
  templates/betweencoffee_delivery/partials/bc_brand_stage_hero.html`（＋`index.html` 版號降回 `20261109h`）。
- **2026-11-16 使用者後續指示「hero 內 bc-photoarea 沒有這個錯位疊印圖片效果，移除它」**：三層 `<img>`
  原本各自把整張圖 `cover` 進自己的窄條（同一張照片重複 3 次、接縫錯位）⇒ 改成三層都放大成
  **整個 track 寬**、`left` 分別 `0`／`-(49/97)%`／`-(146/293)%`（寬 `439/49`／`439/97`／`439/293`
  倍切片寬）⇒ 每層只露出自己那一段、拼回原本一張完整照片；結構／三條 keyframes／`--pa-x` 全不動，
  `bc-pa-image` 改成只寫 `from{width:0}`（終態由基底寬度決定）。順手查清：11-14 抄來的
  `margin-left:-1px` 疊縫一直被 `bc-brand-stage.css` 的 `#bc-brand-stage span{margin:0}` 蓋掉
  ⇒ 三條本來就無縫，偏移用純比例（不需補 px）。版號 `?v=20261114c → 20261116a`。
  驗證：1440 三層 img 左緣偏移 0／0／0、寬 479.45／479.52／479.52、高 671.19；390 為 0／0.02／0、
  寬 162.2；動畫實測（重播抽樣）t=0 clip 0%、img3 寬 0 → t=350 clip 78.7/88.7%、img3 413 → t=1200
  `transform:none`、img3 479.5（＝track 寬）；無 console error、`ovfX=0`。
