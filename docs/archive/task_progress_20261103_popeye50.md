# about 頁首屏「年份 loader ＋ 慣性字輪」（popeye50）— 2026-11-02 完成

> 2026-11-03 已被 `bc-sticky-mv`（yurumaru.life sticky 影片＋產品照弧形輪播）取代，
> 本檔保留當時的實作與踩雷記錄供追查；現況見 `task_progress.md`。

**about 頁首屏「年份 loader ＋ 慣性字輪」（移植 popeyemagazine.jp/50interviews/）— 2026-11-02 完成**

| 項目 | 內容 |
|---|---|
| 新檔 | `static/css/bc-popeye50.css`、`static/js/bc-popeye50.js`（皆 `?v=20261102a`）；`about.html` 最上方（`.rotate-mau` 之後、`.bc-series-hero` 之前）＋ `extra_scripts` |
| 資料 | `About.get()` 新增 `wheel_items`＝`{word: coffee.name, name: coffee.highlight or name, image: get_index_image()}`（`series_coffees` 6 筆）→ `{{ wheel_items|json_script:"bc-popeye50-data" }}`；`WHEEL_MIN_ITEMS=10` 不足時前端重複排列補滿圓周（6→12） |
| 原樣保留 | (1)loader 時間軸；(2)轉輪物理 AUTO_SPEED 0.05°/frame、FRICTION 0.92、IDLE_DELAY 1200ms、MIN_VEL 0.001、WHEEL_K 0.25；(3)`spacingWeight`／`buildAngles`／`fitMobileWordSize`；(4) `--cw-size = max(7.5rem, min(w,h)*0.92)` |
| 改寫 | 選擇器 scope `.bc-popeye50`、`fixed`→`absolute`、`body.is-*`→root class；年份改 `data-year-start/end`（2020→2026）；尺寸讀 stage rect；`IntersectionObserver` 捲出即停 rAF；`prefers-reduced-motion` → 終態＋不自動轉 |
| 踩雷 | ①`bc-components.css` 給「內容首個 section」`margin-top:100/72/60px`（預留 navbar）→ 需以 `.bc-page-content > section.bc-popeye50:first-of-type{margin-top:0}` 抵銷，否則模組中心低於視窗中心、loader 底部年份掉出視窗；②`.cw-stage{overflow:hidden + overscroll-behavior:contain}` 會把滾輪鎖在 stage 內（整頁不能捲）→ 改 `auto`；③`touch-action:none` 會讓手機首屏無法上下滑 → 改 `pan-y`（垂直＝捲頁、水平＝轉輪）；④`wheel` 只認水平 deltaX，垂直交還瀏覽器；⑤直排副標原站掛右緣，本站右緣被 Order／會員／購物車佔滿 → 移到左緣 navbar 下方 |
| 驗證 | `manage.py check` 0 issue、`node --check` OK、flake8／black 無新增問題；headless Chromium 實測 1440×900／768×1024／390×844：字輪 12 字、`scrollWidth==clientWidth`、console 0 error；拖曳 194°＋慣性 22°＋1.2s 後恢復自轉；垂直滾輪捲頁 600px、水平滾輪轉 156°；捲出視窗凍結／回捲恢復；reduced-motion 凍結 |
| 微調 | 中心照片放大：`.cw-center` `0.4`→`0.5`（×`--cw-size`）＋`.cw-center-picture` `scale(.9)`→`1`（手機 `.85`→`.94`）＝可見尺寸 +38%（1440：298→414px、390：122→168px）；中心品名 `clamp(.7rem,1.25vmin,.85rem)`／手機 `.78rem` → `clamp(.82rem,1.5vmin,1rem)`／手機 `.9rem`＝13.5／13.1／13.2px；字輪直徑係數 `0.92→0.86`（手機長字內端會靠近品名 → `.cw-wheel` 加徑向遮罩 54%→76% 淡出，取代原站深色底塊）。CSS `?v=20261102f`／JS `?v=20261102c` |
| 詳情頁連結 | 中心圖文（照片＋品名）＝`<a class="cw-center-link">`，href 由 `wheel_items[].url`（`views.About` 以 `reverse("coffee")` 產生）依高亮品項同步；`/about/` 與 `/bean/<id>/` 的 SERIES 項目 `<a href>` 連到各自詳情頁。防誤觸：字輪拖曳位移 >8px 才 `setPointerCapture`（bc-popeye50.js）；bc-series.js 移除 pointerdown 的 `preventDefault`/capture、改 capture 階段吃掉拖曳後的 click、`dragstart` 一律 preventDefault，圖片與連結 `draggable="false"`＋CSS `-webkit-user-drag:none`／`pointer-events:none`。實測：點中心→`/coffee/3/`、點 SERIES→`/coffee/1/`、手機 tap→詳情頁、拖曳（字輪 17.6°→293.4°／SERIES `--js-x` 改變）皆不導頁、console 0 error |
| 移除黑底 | 2026-11-02（使用者指示「移除黑色背景」）：本模組原本鋪 `#0e0e0e` 純黑，是整頁唯一黑帶。**不能只改 transparent**：`about.html` 的 `.rotate-mau`（`height:170vw`、`z-index:-1` 的巨型米色字母環 `#eeecde`）原本被這層黑底蓋住，透明後字母會直接壓在字輪與杯子上（實測）。改鋪「和 body 完全相同的一張圖」＝`url(../images/bg_4.jpg)` + `no-repeat fixed` + `background-size:cover` + 原點 `0% 0%`（對齊 `style-bootstrap.css:3123` 的 body）→ 第一屏與下方 section 同一塊黑板材質、接縫不可見，同時擋住字母環。連帶：`.cw-loader` 黑幕→`transparent`（stage 本就 `opacity:0`）；手機 `.cw-center-img-wrap` 的 `background`/`box-shadow` 與 `.cw-center-name` 的 `radial-gradient`/`text-shadow` 深色遮罩全移除（字輪半徑大於照片盒與名稱方塊，字不會壓到）。實測 1440／390：`rootBg=rgba(0,0,0,0)`、`bgAttach=fixed`、`bgSize=cover`、loader/name/wrap 皆無底色、捲動接縫無黑線、console 0 error。CSS `?v=20261102d` |
