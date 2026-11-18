# 首頁 who：「有溫度」筆刷換成 sukima `#careers` 的 `.content-block-title` SVG — 2026-11-14 完成

（封存自 `task_progress.md`。）

- 使用者：把「有溫度」的動畫改成 sukima.tokyo.jp `#who`／`#careers > .career-intro` 內
  `.content-block-title > svg.title-hatarikata-svg` 那一支（原本是 about 的大塗抹塊，11-13 版）。
- 模板：`.wwa-anim-members` 內 SVG 整支換掉 ⇒ `viewBox 0 0 190 33`、mask 白線 tracer
  `dasharray 600`／`offset 600` 掃過 ⇒ #BFFF00 亂線筆刷；id `flowingRibbonRevealMaskWwa`／
  `flowingRibbonClipWwa`。class 仍沿用 `.wwa-members-svg`／`.wwa-members-brush` ⇒ JS 只動數值。
- JS：`bc-who.js` item type `members` 的 `784 → 0` 改 `600 → 0`（tracer 實長 ≈543，dasharray 設 600
  保證起點全遮）、`dur 1.2 → 1`（對齊原站 `animSvgStrokeTo 1s ease-in-out`）。其餘 scrub 邏輯不動。
- CSS：`.wwa-members-svg` 改 `left:-0.84em; bottom:-0.03em; width:4.28em`（移除 `top/left 50%` 與
  `rotate(10deg)`）。實測墨水（`ink path getBBox`）在 viewBox 內為 x33→187、y7→29 ⇒ 寬 3.47em
  （3 個 CJK ≈3.26em，左右各出 0.03~0.08em）、左緣 −0.84em 剛好抵掉 svg 左側 33 單位空白；
  `bottom:-0.03em` 讓墨跡下緣貼在字形底部下方（與原站 `bottom:9px` 的「底線式筆刷」一致）。
- 版號：`bc-who.css 20261113b → 20261114a`、`bc-who.js 20261113a → 20261114a`；`index.html` 檔頭註解加 `ⓖ`。
- 驗證（dev 8081 + headless CDP 9333）：320／375／390／414／768／1280／1920 全部
  `dashoffset=0`（scrub 到位）、墨跡寬 94／94／93／—／93／136／198px（= 3.47em @ 27／39／57px）、
  與三字 union 左右差 −2~−6／+3~+8px、`overflowX=0`；近照比對與 sukima 原站一致；`manage.py check` 0 issue。
- 被取代：2026-11-13 的 `.bc-other-members` 大塗抹塊版（dasharray 800／offset 784、`4.44em`、`rotate(10deg)`）
  同日改版後不再使用，細節見 git `9d57b031`／`f7e70195`。
