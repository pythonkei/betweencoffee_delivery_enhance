# 04_SYSTEM_STATE 歷史變更日誌（封存）

> 2026-09-06 記憶庫瘦身：由 `04_SYSTEM_STATE.md`（1787 行 / ~57K tokens）拆出。
> **此檔不會被自動載入**。逐筆詳細變更以 `git log` 為準；現況摘要見 `04_SYSTEM_STATE.md`。

## 近期修復記錄
### 2026-09-01：ramen REAL + reviews 整合（about 頁）＋ 平板照片放大置中 ＋ sake-shirakiku product-mv 整合 🍜 🍶 ✅

- **reviews 跑馬燈時序修正**：`bc-reviews.js` 原為 body 尾同步執行（GSAP defer 尚未載入 → `!window.gsap` 提早 return 不動畫）→ 改 `DOMContentLoaded` 內檢查 gsap 後觸發；驗證 tween×1、repeat -1、55s、目標 x=-4402、-80px/s 線性。reviews 區塊包 `section.bc-reviews-section` 移至 row-animation 下方、capabilities 前（about.html 行 466-671）；dot 垂直居中（`.reviewsMark__box` inline-flex align-items:center height:25px，移除 margin/padding hack）。
- **ramen REAL（bc-ramen-product）**：行動端（≤680px）`.c-real-txt > .r` `margin-top: calc(-29.07vw - 30px)` 重疊照片約 25%（照片高 = 100vw×100/86 → 29.07vw，-30px 補償間隙）；**+ 符號位移修復**：原 `.c-real-txt .r` 後代選擇器同時誤傷 `.ui-btn-more > .r`（+ 符號線條容器被加 -139px margin）→ 改子選擇器 `.c-real-txt > .r`；**平板照片放大 + 置中**（768-1279px）：width 33.33vw→42vw→**48vw**、left 26vw（50vw-半寬 24vw）、top `calc(50vh - 27.8vw)`（48vw×556/480÷2）→ 照片中心與頁面中心重合（offsetX/offsetY = 0，三單元一致）；1280px+ 桌面維持 33vw 原設計。
- **sake-shirakiku.jp/products/vibran product-mv section 整合**（about 頁 `.boxBottomLine` 下方）：新 `section.bc-sake-mv` 包住原站 `<section id="shopify-section-template--16830511972551__main" class="shopify-section product-mv">`（完整複製）：
  - **結構**：4 個 staff-comment 氣泡（`.blowing` pattern-1/3/4/5 + staff01~04 圖章 `::after` + 日文 vertical-rl 文字）+ 產品照片（vibran.jpg 2600×2600、淺底 rgb(240,244,244)、mix-blend-mode:multiply、img-load `loaded` clip-path 進場 1.3s+1s）。
  - **rem 基準轉換（關鍵）**：原站 html font-size 響應式縮放（≤767:26.67vw / 768-1099:80.527px / 1100-1365:7.32vw / ≥1366:100px），Between Coffee html 為 `clamp(14px,0.3vw+13.5px,16px)` → 整合 CSS 用 `--sake-rem` 變數模擬四段縮放 + 全部 `Xrem` → `calc(X * var(--sake-rem))`（否則尺寸縮小 ~6 倍）。
  - **Bootstrap 衝突修復**：`.p-1~p-4` 在 betweencoffee 是 Bootstrap spacing utilities（padding:0.5rem !important）→ scoped `.bc-sake-mv .p-1~p-4 { padding:0 !important }`。
  - **黑底文字覆寫**：betweencoffee 全域把文字設灰/白 → 整合區塊 `color:#111`、`letter-spacing:.02em`、`line-height:1.8`（原站排版）。
  - **字型**：載入原站 YakuHanJP（jsdelivr CDN，開放授權）；dnp-shuei-gothic-gin-std 為 Adobe Typekit 商業字型無法本機載入（fallback 日文黑體）。
  - **動畫**：`bc-sake-mv.js` 複製原站 common.js 的 `mvStaff`（每 3 秒亂序切換 `.staff-comment` 的 `is-show`，scoped 至 `.bc-sake-mv`）。
  - **氣泡超出 mv 頂部修復**：staff 未 sticky 時（mv 頂部在視口中間）氣泡（`.blowing .img` bottom:100% 向上）超出 mv 遮住上方 topConcept；先加 `overflow:clip` 會裁切動畫中氣泡頂部 → 改 `@media(min-width:768px) .bc-sake-mv .staff-comment { margin-top: calc(2.5 * var(--sake-rem)) }`（≥ 最大氣泡高 1.92rem + 動畫 translate -40px），氣泡恆在 mv 內、動畫完整、不影響 position:sticky。
  - **新檔**：`static/css/bc-sake-mv.css`、`static/js/bc-sake-mv.js` + `static/images/sake-mv/`（vibran.jpg + blowing-pattern01~03.svg + staff01~04.png）。
- **版號**：bc-sake-mv.css ?v=20260831e、bc-sake-mv.js ?v=20260831a、bc-ramen-product.css ?v=20260828z、bc-reviews.css ?v=20260828c、bc-reviews.js ?v=20260828b。
- **驗證**：1280px 桌面與原站逐項對照（product-mv 1280×1280、p-1~p-4 位置/尺寸全一致：128/407.6 147×161、320/468.5 201×180、768/407.6 201×180、1088/451.7 164×147）；平板 834（--sake-rem 80.527px）與行動端 375（26.67vw、absolute staff、overflow hidden）換算全正確；is-show 輪播切換、img-load 進場動畫、氣泡動畫完整不裁切、不超出 mv（pixel 分析 + rect 量測）；scoped 確認 `.staff-comment` 僅存在 .bc-sake-mv（4 個）不影響其他 section；console 無新增錯誤。
- **fujiya-peko.co.jp/cakebrand #photo_area 鎖定頁面整合**（about 頁 `.boxBottomLine` 下方）：
  - **結構**：新 `section.bc-fujiya-photo` 包住原站 `#photo_area`（`.content` sticky top:0 鎖定、高度 700vh / SP 600vh）：`#photo_ttl` 三組標語 copy（`txt_up_slide` 逐字 span + mark.svg）+ `#photo_slide` 三張全寬蛋糕照片（photo1~3.jpg 2720×1200 + picture.b 半解析底圖 + SP 直立版）以 `sv_shape_pc.svg` / `sv_shape_sp.svg` mask 揭示 + `photo_line1/2/3` 滾動刻度線（PC 1px top 100/300/500vh、SP 30vh top 100/250/400vh）。
  - **CSS**：複刻原站 screen.css 4 斷點（≥1921 px 大版 copy top 3.75px/mark 80px/txt 30px、1360-1921 px 小版 3px/64px/24px、768-1359 vw 版 0.22059vw/4.70588vw/1.76471vw、≤767 SP 52.26667vw title + padding 24vw 0 0 8.53333vw + txt 4.26667vw）+ cmn.css `txt_up_slide`（span translateY(102%)→0、transition .133s cubic-bezier(.61,1,.88,1)）；**深色頁適配**：section 黑底 #0e0e0e、標語 `#fff`（白字）、日文字型 fallback；SP `.copy` 需 `transform:none`（PC base `translateX(-39.92647vw)` 未覆蓋會左移 -39.93vw）。
  - **動畫**：`bc-fujiya-photo.js` 複製原站 script.min.js photo_area——Waypoint ×6（photo_line1/2/3 於 offset `.79*(windowH−copyH)` 切換 showPhoto/closePhoto、offset `10%` 切換 `.photo_slide_item.open` → picture.b 淡出）+ GSAP ScrollTrigger ×3（scrub，mask-position `windowH→0`、mask-size progress>.85 時 `100→100+t%`，PC t=85 / SP t=200）+ resize（#photo_slide 高 = windowH−ttlH+80 PC / windowH−ttlH SP）；2026-09-01：`.mark` 內容更改為 `.bc-other-members` 動畫（二次修訂：一份置 title 層、文字 span z-index 2 疊在手繪 svg z-index 0 上層完整顯示、svg 190/240px（SP 80px）、與第一組文字綁定——copy1 顯示時顯示首播、copy2/3 或向上捲離時 `.hide` 隱藏）。
  - **時序修正（關鍵）**：本檔 body 尾同步執行早於 head defer 的 GSAP → 頂層 `typeof gsap === 'undefined'` 檢查會直接 return（與 bc-reviews.js 相同根因）→ 改 DOMContentLoaded 後 `boot()` 才檢查 gsap/ScrollTrigger。
  - **依賴**：沿用 base.html 既有 jQuery 3.7.1 + Waypoints 4.0.0 + GSAP 3.12.5（無新增外部庫）。
  - **新檔**：`static/css/bc-fujiya-photo.css`、`static/js/bc-fujiya-photo.js` + `static/images/fujiya-photo/`（photo1~3.jpg 2720×1200 + _b/_sp/_b_sp + mark.svg + sv_shape_pc/sp.svg）；版號 bc-fujiya-photo.css ?v=20260901k、bc-fujiya-photo.js ?v=20260901h。
  - **驗證**：桌面 1920/1360-1921 斷點（txt 24px、mark 64px、slideH 927=1080−233+80、copy left 193=50%−39.93vw）；平板 834 vw 版（txt 14.72px=1.76471vw、mark 39px、700vh、pc mask sv_shape_pc）；行動端 375（600vh、photo_line 30vh、sp 圖 750×1040、slideH 471=667−196、copy left 0 / padding 24vw 0 0 8.53vw）；滾動全程 photo_line1/2/3 各階段 copy 切換 + item.open + mask 0px/185%（SP 300%）+ 逐字 y:0 + mark 滑入全驗證；逆滾 closePhoto 反向；sticky 鎖定 rectTop 0（navbar absolute 滾離不遮）；console 無新增錯誤。

### 2026-08-27：Timber Wharf 全域應用 + weekday 徽章 + SERIES 資料庫驅動（咖啡/咖啡豆）🌍 ✅

- **weather 全域應用**：nav.html 移除 `{% if url_name=='about' %}` 條件 → weather/時鐘/日期/weekday 全站右上角顯示；base.html 全域載入 bc-weather.css/js（head/scripts）；about.html 移除重複引用。
- **weekday 徽章**：整合 yokohama-timberwharf event/1125 的 `.weekday`（膠囊：border-radius 100px、白 12% 背景——黑底適配原站 #0000001a）；香港真實星期（inline script + bc-weather.js `getDay()`）；桌面/平板 inline 與日期水平對齊（vertical-align middle）、移動端（≤767.98）block 換行下方（原站 .mb）；加大 10/9px（weekday 變寬 → weather 容器 80→84px → c-attract 對齊 -11→-9px）。
- **虛線 z-index**：`#borders` 9999→2（navbar 3 > 虛線 2 > 內容 1）——weather 顯示於虛線之上（elementFromPoint 驗證）。
- **「他にもいます！」**：字體 16/20/26→13/16/21 + 【 他にもいます！】符號。
- **SERIES 調整**：`.bc-series-caption` text-align:center（照片與文字水平居中）；highlight 18/15/12→16/13/11。
- **SERIES 資料庫驅動**：About view 加 `series_coffees`（CoffeeItem id 1,2,3,4,7,8）與 `series_beans`（BeanItem id 1,2,3,6,7,8）；兩組咖啡 SERIES 滑桿 + 新建 **BEANS 括號滑桿**（`<section class="bc-series-hero bc-series-bracket show">`、SVG id C 後綴、bc-series.js 自動支援多組）；圖片統一主圖 `image.url`（先前誤用 image_index 已修正）。
- **照片 2 修復**：Sunshine 主圖 `coffee_08_B0g2qHs.png` 工作區被刪（404）→ git checkout 從 HEAD 恢復（861KB）。
- **驗證**：weekday 全站（index/coffee_menu）顯示 Thu 與日期水平對齊、移動端換行；虛線對齊各斷點（1280=1214、375=342）；caption 名稱中心=照片中心（3 斷點）；咖啡照片 HTTP 200；BEANS 滑桿 pager 0→-420→0、SVG id 無衝突；`manage.py check` 0 issues。
- **版號**：bc-weather.css ?v=20260827f、bc-attract.css ?v=20260827a、bc-series.css ?v=20260827c、bc-weather.js ?v=20260827a。

### 2026-08-26~27：yokohama-timberwharf weather 天氣/時鐘元件整合 to about 頁右上角 🌤️ ✅

- **需求**：將 https://yokohama-timberwharf.com/ 的 `<div class="weather -font_en">`（天氣/溫度/日期元件）整合到 about 頁右上角；UI/動畫與原站完全一樣、不添加額外 UI/CSS、不與其他部分衝突。後續追加：時鐘（動畫順序 **時鐘→天氣→溫度**）、初始狀態修復、c-attract 對齊、隱藏年份+日期增大、navbar logo 增大、天氣改香港葵涌、移除底部邊框、載入同步修復。
- **原站機制**：`.view`（80×40 overflow hidden 重疊裁切窗）+ `.date` + `.border`；icon/溫度 GSAP x 位移滑動切換（每 5 秒、duration .8）；OpenWeatherMap `q=Yokohama`；`-font_en` SaansSemiBold/Helvetica Neue；`-color_white` filter 反白。
- **實作**：`nav.html` container 內、僅 about 頁（`{% if url_name=='about' %}`）加入 weather 結構 + `.clock`（動畫首位）+ inline script（立即同步填時鐘+日期）；`static/css/bc-weather.css`（原站樣式 scoped `#ftco-navbar .weather`、黑底反白、**CSS 初始定位**避免載入跳動、**c-attract 對齊** 4 斷點 transform -11/-21/+8/+12px、時鐘 28/24px、日期 12px + year 隱藏、border 隱藏）；`static/js/bc-weather.js`（原站邏輯還原 + 時鐘每秒 HH:MM + **3 元素循環狀態機** 時鐘→icon→溫度 + 初始定位立即/循環延後 + API 改 `q=Kwai Chung` **香港葵涌**）；`bc-components.css` navbar-brand +4px（40/34/28/24）；資源 7 個 `header_weather_*.svg`（thunderstorm 原站 404 → 依風格補建）。
- **⚠️ 關鍵修正歷程**：① 初始狀態異常——`setupAnimation` 只在 API 回應後執行 → 三元素疊中央顯示溫度再跳動；修復 CSS 初始 transform + `setInitialPositions()` 立即 + `startLoop()` 延後；② `.value` selector 撞名——時鐘加入後 `querySelector('.value')` 誤選時鐘 → 溫度不更新；修復精確 `.temperature .value`；③ c-attract 對齊——weather 中心對齊右側虛線（= Order 按鈕中心），各斷點位移不同（虛線 right 65/36/32 + weather 寬 80/60）；④ `--:--` 閃現 + 時間日期不同步——inline script 立即同步填入時鐘+日期。
- **驗證**：桌面 1280 weather 中心 = 虛線中心（1214=1214）、葵涌 30°C cloudy、時鐘即時、日期「Aug, 27」、動畫 5 秒循環（5 點取樣）、響應式 768/600/375 全對齊、navbar logo 40/34/28/24 無重疊、CSS-only 降級正確、`manage.py check` 0 issues。
- **版號**：bc-weather.css ?v=20260826f、bc-weather.js ?v=20260826e、bc-components.css ?v=20260826a。

### 2026-08-25：sukima row-animation + content-block-title 氣泡 + capabilities-gallery 整合 to about 頁 🎬 ✅

- **row-animation（video scroll scrub 條帶）**：完整複製原站 `.row-animation`（who 後、topConcept 前）；黑底適配（原白底）、`mix-blend-mode:hard-light` 保留；高度 96/160/200px（base/≥1024/≥1920）；**video 播放進度跟隨滾動**（start top 90% → end bottom 25%、scrub 0.2、30fps 節流、10.25s）。**⚠️ 關鍵適配**：Django dev server 不支援 Range + mp4 moov 在尾部 → video seek 失敗 → **fetch → Blob → objectURL** 載入（記憶體 seek 可靠，所有環境通用）；moov 前置修復（純 python 重封裝 + 修正 488 stco offsets）。資源 `static/animations/row-animation.mp4`（452KB）；新檔 bc-row-animation.css/js（版號 ?v=20260825c/b）。
- **content-block-title 思考氣泡（Who we are 右側）**：完整複製原站 `.culture-kangaeteiru-svg`（60×78、mask `thoughtBubbleRevealMask2` + tracer + 4 個 #BFFF00 path）；absolute 於標題右側上方（top 8/22/41、right -8/-8/-14、width 42/60/80px——使用者要求右移 8px）；`.bc-who-section.show .thought-bubble-reveal-tracer` 觸發 `animSvgStrokeTo` 2s 畫線（dashoffset 500→0）；沿用 who section 既有 .show 觸發（無新 JS）。版號 bc-who.css ?v=20260825e。
- **capabilities-gallery（scroll scrub 逐幀動畫）**：完整複製原站（row-animation 後）；cgi-left/right 團隊照片（606×1140）初始位移 → scroll 歸位；`capabilities-anim-char` **36 幀**逐幀切換（`/animations/wwcd/1~36.webp` + sp/ 行動版）；surprise「！」手繪閃電（reveal-brush 305→0）。資源 74 個下載；移除 srcset（單圖）；SVG id 加 2 後綴；新檔 bc-capabilities.css/js。
  - **後續微調（使用者反饋）**：① 照片分離修復（補 gallery `display:flex`）；② 照片錯開修復（移除 cgi y 微移，頂部對齊）；③ 時機/速度多輪調整（cgi 延後開始、frame 加快、分段重寫）；④ 「！」動畫消失修復（brush 段 0.44-1 太長 → **0.44-0.60** 快速畫線，galTop -75 完成接近原站 -152）。版號 bc-capabilities.js ?v=20260825k、css ?v=20260825b。
- **驗證**：CDP row 18/18、cbt 18/18（+右移 8px）、capabilities 22/22、who+row+capabilities 共存 9/9；`manage.py check` 0 issues。

### 2026-08-25：sukima who section（.section.who #who）整合 to about 頁 🎬 ✅

- **需求**：將 https://sukima.tokyo.jp/ 的 `<section class="section who" id="who">` 整合到 about 頁（建立新 section）；UI/動畫效果與原站完全一樣，不添加額外 UI/CSS，不與其他部分衝突。**顏色決策（使用者確認）**：融入本地黑底白字，#BFFF00 高亮保留。
- **原站機制**：who-content-sticky（flex column center）→ section-title（kicker 括號 `(sukimaって何の会社？)` + Who we are）→ who-content-text（93 個 wwa-anim-char 逐字 + sukima-anim-wwa（s/u/k/i/m/a + who-circle-svg 手繪圓圈 dashoffset 800→**377**）+ wwa-visual-01/02（img wwa-01/02.png）+ video-anim-wwa（映/像 + who-arrow-svg 手繪箭頭 300→0）+ wwa-visual-03（video wwa.mp4 76×55px、1.08s））。動畫為 **GSAP ScrollTrigger scrub**（滾動跟隨）：元素間隔 0.5s、char 0.3s、spacer、visual/img/video 3s、circle/arrow 1s。響應式 base/704/834/1920（content-text 24/34/50px、spacer 75/90/140px、visual 58/90/144px 等）。
- **實作**：about.html 第二組 SERIES 滑桿後、topConcept 前插入 `<section class="section who bc-who-section" id="who">`（日文原文完整複製）；SVG mask/clipPath id 加 **2 後綴**（animatedRevealMaskWwaCircle2/mainClipWwaCircle2/arm-arrowwwa2/mcarrowwwa2）避免與 summary 區塊既有 id 衝突；`static/css/bc-who.css`（原站樣式完整 scoped 到 .bc-who-section、黑底白字、CSS 變數 --who-spacer-w 等）；`static/js/bc-who.js`（**原生 scroll + rAF 重現 scrub**，含 GSAP scrub 平滑 0.12、spacer dur **46s** 讓縮排展開跨越整個 who 滾動——使用者三輪反饋調慢 2→10→20→32→40→46s）；資源 wwa-01.png/wwa-02.png/wwa.mp4 下載自原站。版號 ?v=20260825k。
- **⚠️ 關鍵修正歷程**：① scrub 範圍 60px→(h+vh)→**vh**（who 頂部到視口頂完成）；② video 在 timeline 93% 處，範圍不足時 scale(0) 隱藏 → vh 範圍下正常播放；③ sukima-anim-wwa 必須 **inline**（非 inline-block），否則圓圈 top:73% 定位偏移（對照原站實測 bbox 高 34 vs 61.2）；④ 縮排動畫（spacer）原站靠 lenis 平滑滾動拉伸過程，本地無 lenis → dur 拉長至 46s。
- **驗證**：CDP 30/30 PASS（初始/中間/最終/反向 scrub/響應式 375-1920/無 JS 錯誤）；**佈局對照原站 15/15**（content-text 34px/180%/2.72px、圓圈 158px 圈住 sukima、arrow 146px、img 90px、video 76px、kicker、標題 56px）；`manage.py check` 0 issues。慢速滾動實測：spacer 12→28→46→60→72→81→87→90px（縮排貫穿 8 步滾動）、字元 3→93 逐字亮起、圓圈 800→377、video 末段播放。

### 2026-08-24：sukima hero-title-svg 手繪圓形畫線動畫整合（about 頁）🌿 ✅

- **需求**：整合 sukima.tokyo.jp 的 hero-title-svg 手繪圓形動畫到 about 頁「一種興奮感, 超越一杯的沉默」；UI/動畫與原站一致、不添加額外 UI/CSS。追加修改：形狀改手繪圓形、圓圈**圈住整句所有文字**（長橢圓）。
- **原站機制**：SVG `<mask>` 白線 path `.leaf-flow-reveal-stream` + `#BFFF00` 填充（opacity 0.75）；`.hero.show .leaf-flow-reveal-stream { animation: leafFlowReveal 2s ease-in-out forwards 1s }`、`@keyframes leafFlowReveal{to{stroke-dashoffset:0}}`（長橢圓 path 實測 765.6px → dasharray/offset 766→0）。
- **實作**：about.html 兩組 SERIES 副標題**整句**包 `.bc-leaf-circle-wrap` + 手繪長橢圓 SVG（viewBox 320×44、不閉合螺旋 path，第二組 mask id 加 B）；bc-series.css 加 `.bc-leaf-circle-wrap`/SVG absolute 圈住文字（inset -5/-12、preserveAspectRatio none）+ 動畫；bc-series.js 加 IO 觸發（初始視口內立即 .show + threshold 0.15）。版號 ?v=20260824b。
- **驗證**：playwright-core 實測 computed（show/animName/dashOffset=0）+ 像素（長橢圓 244×33 圈住整句 224×27、中心空心、行動端 375px 無溢出、兩組皆觸發）。
- **追加（絲帶）**：第一處副標題文字改「雲仙黒糖ラテベース」後，整合 sukima title-hatarikata-svg 絲帶動畫（flowingRibbonRevealMask/clip、cometTailReveal 4s ease-in-out forwards、dasharray 600/offset 600、位置 left:-23px bottom:7px width:98px opacity:.75 + 834/1920 media）。**關鍵根因**：使用者提供的 ribbon path d 為壓縮版（C 命令只 2 數字 → path 無效 getBBox 0×0 不渲染），從 sukima 原站抓取正確 d 替換（C 後完整 3 對座標）→ bbox 154×22 正常。版號 ?v=20260824g。
- ⚠️ 教訓：二次替換 wrap 用 `(?=.*maskB)` lookahead 會跨段落誤匹配刪內容 → 從 git 還原 + section 錨點重建。
- **追加（手繪箭頭）**：way 區塊 h2（「我們試著將看不見的熱度與香氣視覺化…」）整合 sukima arrow-recruit-svg 手繪箭頭（cometTailRevealMask/clip、comet-tail-reveal-stream、雙 #BFFF00 箭頭、cometTailReveal 4s、dasharray 500/offset 500→0、位置 left:50 bottom:-39 translate(-100%) width:191 + 1920/2560 media）；bc-series.js 加 initArrowReveal（IO 監測 .col-main.way 加 .show）。版號 ?v=20260824l/c。驗證：show 觸發、箭頭 bbox 224×63、行動端無溢出、無 id 衝突。
- **追加（手繪圓圈）**：summary 第一個 p「那股香不只是味道…」整合 sukima title-office-svg 手繪圓圈（organicFingerprintRevealMask/clip、fingerprint-reveal-flow、#BFFF00 圓圈、fingerprintReveal 1.11s=速度+80%、dasharray 700/offset 700→0、位置 top34/left172 + 834/1920 media）；共用 way .show 觸發 + `.productFv .title-office-svg path` 覆蓋。版號 ?v=20260824r。驗證：fingerprintReveal 1.11s、圓圈 bbox 71×85、圓圈區域綠色 1730、行動端無溢出。
- **追加（手繪山形）**：h1 morphing「世界太快」整合 sukima footer-arrow-svg 手繪山形（organicMountainRevealMask/clip、mountain-range-reveal-tracer、14 個 #BFFF00 山形、revealFooterSvg 3.33s=速度+80%、dasharray 1000/offset 1000→0）。**兩次修復**：① SVG 誤放 morphing .word 內被 `contrast(25) blur(1px)` 濾鏡扭曲+淡出 → 移到 h1 內（morphing 外、h1 relative）；② blobs.css `.productFv.style_01 h1 svg{width:83vw}` 覆蓋尺寸 → `.productFv .footer-arrow-svg{width:259px!important}`。版號 ?v=20260824z。驗證：SVG 259×115、svgFilter none、山形不疊文字。
- **追加（手繪箭頭：這就是起點）**：summary 第二行「這就是起點」整合 sukima who-arrow-svg（arm-arrowwwa/mcarrowwwa、reveal-brush-arrow-wwa、#bfff00 箭頭、organicRevealAnimation 1.19s=先+80%後減慢30%、dasharray 300/offset 300→0）。移除 tracer inline `stroke-dashoffset:0px`。版號 ?v=20260824ad。驗證：organicRevealAnimation 1.19s、path bbox 146×79、行動端無溢出。
- **追加（手繪圓形 + 他にもいます！）**：topConcept 區塊 h2「為什麼，Between Coffee…」整合 sukima other-members-svg（organicRevealMaskMembersTitle/organicClip333、organic-reveal-brush444、#BFFF00 圓形、organicRevealAnimation 1.5s、dasharray 800/offset 784→0）+「他にもいます！」文字（.bc-other-members 容器含 span+svg，span scale 0→1 延遲 1s）。bc-series.js 加 initTopConceptReveal（IO 監測 .bc-top-concept）。**修復**：容器 translateX 滑入造成左移 89px → 移除滑入（固定 rotate -10deg）；容器移到「一杯好咖啡。」後（inline-block）；圓形 140/190/240px、文字 16/20/26px。版號 ?v=20260824aj。驗證：容器位置固定（起始=結束）、span scale(1)、圓形 190×121。

### 2026-08-24：Sticker 貼紙模組化（sticker-box 資料驅動）🏷️ ✅

- **需求**：① 並非所有咖啡都能看到 sticker（A 咖啡 Sticker 1、B 咖啡 Sticker 2、留空=不顯示）；② admin 自訂 sticker 功能；③ 不需複製 8 個模組（資料驅動模組化）。
- **架構**：新增 `Sticker` 模型（eshop/models/sticker.py）——背景款式（內建 4 款）+ 前圖（內建 4 款 preset 或上傳自訂 ImageField，上傳優先）+ text_en/text_zh（`\n` 換行）+ is_active + sort_order；CoffeeItem/BeanItem 各加 `sticker` FK（留空=不顯示）。
- **migration**：0064（CreateModel Sticker + FK + **pickup_time drift 修復**）、0065（seed 4 款 Sticker：8 咖啡→S1、6 咖啡豆→S2 維持現況）。
- **pickup_time drift**：`ordermodel.pickup_time` 資料庫欄位已存在但 state 被 0052 移除、model 又加回 → makemigrations 誤判 AddField。0064 沿用 0052 SeparateDatabaseAndState 手法修復，`--check` 從此 No changes。
- **模板**：sticker-box 包 `{% if xxx.sticker %}`；背景圖 inline style、前圖/文字資料驅動（`|linebreaksbr`）。
- **CSS**：`.sticker .bg` 移除硬編碼背景圖；`.sticker .front img` 加 `object-fit: contain`。
- **Admin**：StickerAdmin（縮圖預覽/文字/啟用/排序）+ 兩商品 Admin 加 Sticker fieldset。
- **驗證**：migrate/check/makemigrations No changes；Test client（含留空不渲染 + transaction 回滾）；Chrome DevTools（coffee/1=S1、coffee/9 臨時換 S3 顯示不同款式、admin 列表與選單）；上傳前圖 property 優先。
- **備註**：Render 免費方案上傳的自訂前圖重新部署後可能遺失（與現有商品圖限制相同）；內建款式不受影響。

### 2026-08-24：浮動購物車按鈕修復 🛒 ✅

- **問題 1（按鈕疊在購物車頂部）**：`.bc-floating-cart.hide` 只有 `pointer-events:none` + `animation:none`（2026-08-14 移除動畫）→ `_hideFloatingCart()` 移除 show 加 hide 後**按鈕仍顯示**（無 display none）→ 疊在購物車頂部（DOM 在購物車後、同 z-index 9999）。修復：`.bc-floating-cart.hide` 加 `display: none !important`。
- **問題 2（點擊瞬間右側位移）**：`open()` 先 `_lockScroll()`（對浮動按鈕設 `right: 40+scrollbarWidth` → 按鈕左移）之後才 `_hideFloatingCart()`。修復：調整順序——先 `_cartOpenHiddenFloating=true` + `_hideFloatingCart()`，再 `_lockScroll()`。
- **追加（恢復加入購物車滑入動畫）**：`.bc-floating-cart.show` 恢復 `animation: bcFloatingIn 0.4s ease-out forwards`；補回遺失的 `.bc-floating-cart.no-anim.show { animation: none }`（初始載入靜默）。
- **追加（頁面跳轉靜默）**：頁面載入 async fetch 同步 >500ms 時 `_initialBadgeSync` 已 false → 每次跳頁滑入。修復：`_updateBadge(count, animatedOverride)` 加覆寫參數，`_syncBadgeFromServer`（載入/bfcache 恢復）傳 `false` 強制靜默。
- **追加（已有商品再次加入不重播）**：`_showFloatingCart` 的 `toggle('no-anim')` 在 `if(contains('show')) return` 之前 → 加入時移除 no-anim 觸發動畫重播。修復：先檢查 `show` 再 return。
- **版號**：bc-components.css ?v=20260824a、bc-slideout-cart.js ?v=20260824c。
- **驗證**：按鈕打開購物車時 display none、無位移；跳頁載入靜默；加入購物車滑入（僅首次）；已有商品再次加入不重播（badge 5→6 無動畫）。


### 2026-08-22~23：MCP 配置修復 + rotate-mau 整合 + 多項 UI 整合 ✅

#### MCP 伺服器配置（2026-08-22）
- **mcp-server-fetch 修復**：Cline 4.1.11 實際讀取 `~/.cline/data/settings/cline_mcp_settings.json`（非 globalStorage）；uv/uvx 因 snap 更新遺失 → 重裝至 `~/.local/bin/uvx`（穩定路徑）；新增 context7、chrome-devtools、supabase-postgres、supabase-mcp、django-manager、@21st-dev/magic、sequential-thinking、playwright（Playwright MCP 需 `--executable-path` 指向 `~/.cache/ms-playwright/chromium-1234/`）。

#### mauinterview rotate-mau 整合（about.html，2026-08-22~23）
- **需求**：將 https://mauinterview.musabi.ac.jp/ 首頁 `.rotate-mau` 整合到 about.html（圓形路徑排列的環形文字標誌 + 緩慢旋轉）。
- **實作**：`bc-rotate-mau.css` 新建；HTML 4 層巢狀 div（block content 首個位置）；純 CSS 動畫 `kf__spin__re` 36s/50s；**z-index 99→-1**（背景層）。
- **mask 文字**：原「美はつづく」是 SVG path 圖形 → 用 fontTools + 字型轉 path。**文字沿圓周排列**（radial 像素分析證實：墨水全在圓周、中心空洞、8 方向均勻）。
- **字型歷程**：Mogra → Playfair Display → **Roboto**（cap/asc 校準：font-size 100 維持 cap 77px）。
- **間隙統一（重要）**：scale 必須 = `2πR/total_step`（字元 ink 弧長 = 步長弧長）否則 Ti/Ri 間隙大、me 重疊；字元中心 = `xMin + inkW/2`（path translate 校正）；`--gap` 控制間隙。最終：兩組「Taste Right Taste Time」44 字元繞滿 360°、間隙統一 1.06 viewBox。
- **工具**：`scripts/generate_rotate_mau_mask.py`（可重用產生器：--text/--font-size/--gap/--span-degree/--font）。

#### bc-series-list 咖啡名稱/Highlight（2026-08-23）
- 名稱改 **Josefin Sans 26px uppercase**（coffee_menu 風格，base.html 補載 Josefin Sans）、highlight **18px 500**；letter-spacing normal（與 coffee_menu 一致）。

#### bean 烘焙程度 5 顆咖啡豆 SVG（2026-08-23）
- 5 個 roastrange-item 各加咖啡豆 SVG（5 種造型：經典橢圓/圓/細長/淚滴/雙瓣）、5 級咖啡色階（#E3C29E→#5A3822）、旋轉 55°、行動端縮小 16px。

#### kariomons .staff 整合（bean.html 賞味期限下方，2026-08-23）
- **需求**：整合 kariomons.com/onlineshop/1377 的 `.staff`（2 個 inner：圓形照片 + 名字 + 評論）到賞味期限下方，UI 完全一樣。
- **實作**：`.bc-staff` 系列（flex、虛線分隔、86px 圓形照片）；員工頭像（staff_ito/staff_natsu.png 深藍線稿）；寬度 = `.block-23`（100%）；title-sub 置頂；文字全寬。
- **懸停邊框根因**：`class="staff bc-staff"` 觸發 style-bootstrap 既有 `.staff`（團隊成員卡片）樣式（border #1d150b、hover 金色）→ **移除 `.staff` class** 解決。
- **figure 瀏覽器默認 margin（1em 40px）** → 照片被壓到 6px，需 `margin: -10px 0 0`。
- **頭像 PNG 深藍線稿 + 90% 透明** → 黑底看不見（曾加米色圓底 #F3EEE2 後依用戶要求移除）。
- **版號**：bc-rotate-mau.css ?v=20260822p、bc-components.css ?v=20260823o、bc-series.css ?v=20260823b。



### 2026-08-21：SERIES 照片修復 + 平板基於桌面縮小 + caption 加大 ✅

- **需求（用戶）**：修改後 1) 照片消失無顯示；2) 平板仍無響應式（應基於桌面布局縮小尺寸）；3) 咖啡名稱與 Highlight 文字加大。
- **根因（照片消失）**：上一輪 python 批次加入 caption 時，img src 從 `{% static 'images/coffee_01.png' %}` 誤改為 `{% static 'coffee_01.png' %}`（少 `images/` 前綴）→ /static/coffee_01.png 不存在 → 照片消失。
- **實作**：
  - **照片修復**：12 個 SERIES img src 加回 `images/` 前綴 → 照片恢復（CDP imgLoaded=true）。
  - **平板基於桌面縮小**：768-1199 照片 `420/280px → 300/200px`、滑桿 padding `calc((100%−280px)/2) → (100%−200px)/2`、pager bottom 30px；標題維持 52px（右緣 < 照片左緣，不重疊）。
  - **caption 加大**：名稱 `15 → 20px`、highlight `12 → 14px`。
- **驗證**：CDP 1280/1024/768/375 照片 imgLoaded=true、src=coffee_01.png；平板 slideW 300px（桌面 420px 縮小）、標題 52px；caption 名稱 20px/highlight 14px；`node --check` + `manage.py check` 通過；版號 `?v=20260821i`。

### 2026-08-21：SERIES 每種咖啡名稱 + Highlight 高亮 + 平板標題響應式 ✅

- **需求（用戶）**：1) bc-series-hero 添加每種咖啡名稱和 Highlight 高亮文本在底部；2) bc-series-heading 平板端沒有響應式設計，文本疊加在照片下層。
- **實作**：
  - **名稱 + Highlight**：兩組 SERIES 滑桿（第一組 + 括號組）各 6 張照片底部添加 `.bc-series-caption`（名稱 + 金色 highlight）。名稱/highlight 取自資料庫 `eshop_coffeeitem`（依序：WakeMeup「雙產區，喚醒一天」、Sunshine「陽光果香，清新明亮」、Flat White「馥芮白，綿密奶咖」、Black Blend「黑金拼配，醇厚相伴」、Nice Step「果香清爽，活力滿點」、Butter King「大師拼配，順滑日常」）。
  - **CSS**：`.bc-series-caption`（名稱白色 600 粗體 15px、highlight 品牌金 300 12px）位於照片下方。
  - **平板響應式**：768-1199 `bc-series-heading` font `140→52px`、padding `40→15px` → 標題右緣（217px）< 照片左緣（768 為 237px、1024 為 365px）**不再與照片重疊**；1280 維持 140px。
- **驗證**：CDP 確認 caption 12 個（兩組）、內容正確；平板 1024/768 標題與第一張照片 overlap=False；桌面 1280 標題 140px 維持；行動 375 標題 50px；`node --check`（bc-series.js）+ `manage.py check` 通過；verify scroll-scrub 200/200、198/198 不受影響；版號 `?v=20260821h`（bc-series.css）。

### 2026-08-21：行動端文字加大（參考 hakujuji）+ 照片縮小 ✅

- **需求（用戶）**：「在行動端文字加大，參考 https://www.hakujuji-g.co.jp/」。
- **參考值**：hakujuji 行動版字級 `5.0666666667vw`（19px）；我們行動版受限於 15 字長行 + 照片避讓空間。
- **實作**：
  - **文字加大**：行動版字級 `2.6 → 3.8vw`（14.3px，hakujuji 的 75%）。
  - **照片縮小**（騰出文字空間）：thum--1 `18→16vw`、thum--2/3 `15→12vw`、thum--4 `16→8vw`、thum--6 `13→11vw`、thum--7 `16→13vw`；高度依新行距（3.8vw 字級）校準：2 行 `13.3→13.0vw`、3 行 `19.9→19.7vw`。
  - 縮排/避讓配合：li1-3 `18vw`、li5/6 `14vw`、li11/12 `14vw`、li13-15 `10vw`、li16-18 `13vw`、li17/18 `15vw`。
- **驗證**：clearance（SP_FIXED 新尺寸 + 不重疊）1280/1024/768/375 全 PASS；行動版照片覆蓋 thum--1/2/3/4/7 2 行、thum--6 3 行；layout（行動偏移更新）PASS；**justify 字距縮小**（15 字行自然寬接近容器 → spread ~0、avg ~5，文字填滿右緣 textW=W）；verify scroll-scrub 200/200、198/198；`manage.py check` 通過；版號 `?v=20260821ag`。
- **取捨**：照片縮小（thum--4 16→8vw 最明顯）換取文字加大；字級 3.8vw 為照片行文字容納的上限（thum--4 需 8vw）。

### 2026-08-21：行動端 thum--2/3/7 佔 2 行 + 文本縮小字距 ✅

- **需求（用戶）**：行動端 1) csBlock__leaderThum--2/3/7 更改為佔用 2 行文字；2) 文本縮小字距。
- **實作**：
  - **thum--2/3/7 佔 2 行**：行動版高度 `3 → 10.8vw`（=2 行）、`top → 0`（貼 li 頂，避免覆蓋第 3 行）；寬度維持（thum--2/3 `15vw`、thum--7 `16vw`）；實測覆蓋行數 `[5,6]/[11,12]/[17,18]`（2 行）。
  - **文本縮小字距**：行動版欄位 `topConcept__tobContents 100% → 90%` → justify 字距 avg `12.8 → 9.8`（長行 15 字 `(265−153)/14 ≈ 8px`）。
- **驗證**：clearance（SP_FIXED thum--2/3/7 高 10.8 期望 + 不重疊）1280/1024/768/375 全 PASS；行動版照片覆蓋行數 thum--1/2/3/4/7 `[1,2]/[5,6]/[11,12]/[13,14]/[17,18]`（2 行）、thum--6 `[16,17,18]`（3 行）；layout PASS；375/414 無重疊；verify scroll-scrub 200/200、198/198；`manage.py check` 通過；版號 `?v=20260821af`。
- **取捨**：行動版欄位縮小 90% → 右側留白 ~37px（375 螢幕）；短行（li18 7 字）justify 字距仍較大（15.2px）。

### 2026-08-21：topConcept thum--4/6 加寬 + 文字縮小 4px ✅

- **需求（用戶）**：「csBlock__leaderThum--4 和 csBlock__leaderThum--6 增加寬度，文字可移除 1-8 個相對調整」（文字縮小 1-8px 配合）。
- **實作**：
  - **thum--4 加寬**：桌面 `4→8vw`（768-1023 `3.4→6vw`、行動版 `12→16vw`）；避讓 li6/7 `4.6→8.6vw`（768-1023 `6.6vw`、行動版 li13-15 `14→18vw`）。
  - **thum--6 加寬**：桌面 `6→10vw`（768-1023 `5→8vw`、行動版 `9→13vw`）；縮排 li11-13 `6.6→10.6vw`（768-1023 `8.6vw`、行動版 li16-18 `11→15vw`）。
  - **文字縮小**：桌面 `2→1.7vw`（~4px）、窄桌面 `1.75→1.5vw`、行動版 `3→2.6vw`。
  - 照片高度校準（字級縮小 → 行距變小）：≥1024 thum--1/4 `5.5vw`、thum--6 `8.7vw`；768-1023 `5.3/8.0vw`、thum--2/3/5/7 `2.0vw`；行動版 thum--1/4 `10.8vw`、thum--6 `16.2vw`。
- **驗證**：clearance（thum--4/6 新尺寸期望 + 不重疊）1280/1024/768/375 全 PASS；照片覆蓋行數：thum--1/4 2 行、thum--6 3 行、thum--2/3/5/7 1 行；layout PASS；justify spread 1280 avg 12.0、375 avg 12.8（文字縮小後字距略增）；1440/414 無重疊；verify scroll-scrub 200/200、198/198；`manage.py check` 通過；版號 `?v=20260821ae`。
- **取捨**：thum--4/6 加寬讓照片更顯眼；文字縮小 4px 後 justify 字距略增（1280 avg 12.0）。

### 2026-08-21：topConcept 欄位左移 + 所有照片改 placeholder 加寬 + 文字縮小 ✅

- **需求（用戶）**：1) 欄位左移；2) 所有照片更改為使用 placeholder（偽造照片）方法和增加寬度；3) 文字大小相對縮小調整。
- **實作**：
  - **欄位左移**：`topConcept__tob` `justify-content: space-between → flex-start`（col 靠左貼標題，右側留白；li 起點回 367）。
  - **所有照片 → placeholder 加寬**：thum--1/2/3/4/5/6/7 全部改為深色底 + 金色細邊框 + 咖啡 SVG 佔位框；寬度增加（桌面 thum--1 `12vw`、--2/3/4/5 `4vw`、--6 `6vw`、--7 `3.5vw`；行動版 --1 `18vw`、--2/3 `15vw`、--4 `12vw`、--6 `9vw`、--7 `16vw`）。thum--1/4 佔 2 行、thum--6 佔 3 行、thum--2/3/5/7 佔 1 行內。
  - **文字縮小**：桌面 `2.25→2vw`、窄桌面 `1.75vw`、行動版 `3.5→3vw`（照片加寬後文字空間縮小）。
  - 照片高度校準（字級縮小後行距變小）：≥1024 thum--1/4 `6.3vw`、thum--6 `9.6vw`、thum--2/3/5 `2.3vw`；768-1023 `5.7/8.6/2.2vw`；行動版 `11.6/17.6/3vw`。
- **驗證**：clearance（全部 placeholder 固定框期望 + 不重疊）1280/1024/768/375 全 PASS；照片覆蓋行數 thum--1/4 `[1,2]/[6,7]`（2 行）、thum--6 `[11,12,13]`（3 行）、thum--2/3/5/7 `[3]/[6]/[9]/[13]`（1 行）；layout（欄位左移後 li 起點 367）PASS；justify spread 1280 avg 9.3、375 avg 11.7；1440/414 無重疊；verify scroll-scrub 200/200、198/198；`node --check` + `manage.py check` 通過；版號 `?v=20260821ad`。
- **取捨**：所有照片改為偽造照片（placeholder）——hakujuji 實際照片不再顯示；照片加寬讓文字空間變小 → 文字縮小（桌面 2vw）；欄位左移後右側留白（col 55.5% 靠左）。

### 2026-08-21：topConcept 整體縮小 25% + thum--4/6 改 placeholder（2/3 行）✅

- **需求（用戶，plan 確認後）**：1) csBlock__leader--list 文本和照片區域整體縮小（縮小 25%）；2) hakujuji_leader_4 不使用，改 placeholder 偽造照片填滿佔 2 行；3) hakujuji_leader_6 不使用，改 placeholder 偽造照片填滿佔 3 行。
- **實作**：
  - **整體縮小 25%**：col `74.01→55.5%`（欄位 content 818→613px）、字級 `3→2.25vw`（桌面）、照片 ×0.75（thum--1 9.79vw、thum--2/3/5 2.63vw、thum--7 2.18vw 等）；行距縮小 → 固定框照片（2/3 行）依實際行距校準（≥1024 2 行 6.6vw、3 行 10.0vw；768-1023 6.0/8.9vw；行動版 11.6/17.6vw）。
  - **placeholder（偽造照片）**：thum--4（li6/li13 右側）`3×6.6vw`（桌面）`10×11.6vw`（行動）佔 2 行；thum--6（li11/li16 左側）`4.5×10.0vw`/`7.5×17.6vw` 佔 3 行；樣式 = 深色底（rgba 白 4%）+ 金色細邊框（rgba 金 0.4）+ 居中品牌簡約咖啡杯 SVG（`leader-placeholder`，about.html 內嵌 4 處）。
  - **字距收斂**：僅縮字級會讓 justify 字距暴增（22.6px）→ 同步縮小 col（55.5%）→ 1280 spread 回歸 `7.0`；行動版字級 `3.5vw`（spread 10.2）。
  - li7 補右避讓（thum--4 placeholder 覆蓋 li6-7）。
- **驗證**：clearance（placeholder 固定框新期望 + 不重疊）1280/1024/768/375 全 PASS；照片覆蓋行數：thum--1 `[1,2]`、thum--4 `[6,7]`（2 行）、thum--6 `[11,12,13]`（3 行）、行動版 `[13,14]`/`[16,17,18]`；layout（col 縮小後 li 起點 586）PASS；1440/414 無重疊；verify scroll-scrub 200/200、198/198；`node --check` + `manage.py check` 通過；版號 `?v=20260821ac`。
- **取捨**：col 縮小 → 文字區塊偏右、左側（標題與欄位間）留白較多；行動版字距 10.2px（較桌面大，因行動版欄位全寬）。

### 2026-08-21：topConcept thum--1/6 固定框 cover 填滿 2 行（消除照片下方間隙）✅

- **需求（用戶）**：「hakujuji_leader_6 與 hakujuji_leader_1 照片下方有間隙，可以強制填滿，或者使用另一張照片適配高度填滿」。
- **根因**：照片高度（vw 比例固定）與行距（受字級影響）不同步——thum--1（橫式 0.682）與 thum--6（直式 0.749）的照片高在部分寬度小於 2 行文字空間 → 下方間隙；放大後又在 768-1023 超過 2 行 → 覆蓋第 3 行（壓字）。
- **實作**：
  - **thum--1/6 改固定框 + cover 填滿 2 行**（強制填滿，無間隙、不覆蓋 3 行）：桌面 ≥1024 高 `8.85vw`、768-1023 `7.8vw`、行動版 `13.72vw`（=2 行實際空間，逐寬度校準避免覆蓋第 3 行）。
  - 桌面 thum--1 `13.05×8.85vw`、thum--6 `6.66×8.85vw`（≥1024）；11.9/6.13×7.8vw（768-1023）；行動版 thum--1 `20×13.72vw`、thum--6 `10.3×13.72vw`（cover）。
  - 768-1023 降字級 `2.5vw`（thum--1 縮排吃空間）+ thum--1/6 縮小（media query 移於 thum 規則之後避免被覆蓋）。
- **驗證**：clearance（照片固定框新期望 + 不重疊）1280/1024/768/375 全 PASS；thum--1/6 覆蓋行數皆 `[1,2]`/`[11,12]`（2 行，bottom 貼齊下一文字頂、無間隙）；layout PASS；justify spread 維持（1280 avg 10.9、375 avg 6.5）；1440/414 無重疊；verify scroll-scrub 200/200、198/198；`manage.py check` 通過；版號 `?v=20260821ab`。
- **取捨**：thum--1/6 以 cover 填滿（照片被裁切——thum--1 橫式裁左右、thum--6 直式裁極少），但無間隙、照片佔 2 行完整。

### 2026-08-21：topConcept 所有照片稍微加大 ✅

- **需求（用戶）**：「所有照片稍微加大」。
- **實作**：
  - 桌面加大 +10~15%：thum--1 `6→7vw`、--2/3/5 `3→3.5vw`、--4 `4→4.6vw`、--6 `6→6.5vw`、--7 `2.5→2.9vw`；縮排/避讓配合（li1/2 7.6vw、li6 4.1+5.2vw、li11-13 7.1vw 等）。
  - 行動版加大 +5~8%（受限 ≤2 行）：thum--1 `12→13vw`、--2/3 `17.5vw`、--4 `13→14vw`、--6 高 `12vw`（寬 14.5）、--7 `19.5×13.5vw`；thum--3 top 微調 `2.13→1.5vw`（避免覆蓋 li13）。
  - 照片垂直居中維持（thum--1 top 0.22vw、thum--2/3/5 1.1vw、thum--4 0.74vw、thum--7 1.05vw）。
- **驗證**：clearance（照片尺寸新期望 + 不重疊）1280/1024/768/375 全 PASS；照片覆蓋行數：桌面 thum--1 `[1,2]`、thum--6 `[11,12]`（2 行）、行動版 thum--2/3 `[5,6]/[11,12]`、thum--6 `[16,17]`（2 行）；layout PASS；justify spread 維持（1280 avg 11.9、375 avg 6.4）；1440/414 無重疊；verify scroll-scrub 200/200、198/198；`node --check` + `manage.py check` 通過；版號 `?v=20260821z`。

### 2026-08-21：topConcept 照片垂直居中 + 縮小行動版 thum--1/6（佔 ≤2 行）✅

- **需求（用戶）**：1) 右側照片向上方位移；2) hakujuji_leader_6 佔用 3 行；3) hakujuji_leader_1 佔用 3 行。
- **根因**：
  - **向上位移**：照片縮小後（矮於行高）top 仍固定 `0.37vw`（li padding 內）→ 照片貼行頂，視覺偏上。
  - **佔 3 行**：行動版 thum--6 固定高 `20vw`（75px）÷ 行動行距 25px = **3 行**；行動版 thum--1 `15vw`（38px）覆蓋 2 行。
- **實作**：
  - **照片垂直居中於行**（桌面）：thum--1 `top 0.26vw`、thum--2/3/5 `1.28vw`、thum--4 `0.94vw`、thum--7 `1.22vw`（=(行高−照片高)/2）；thum--6 高於行高維持 `0.37vw`。
  - **行動版縮小**：thum--1 `15→12vw`（31px→1.2 行）、thum--6 高 `20→12vw`（45px→1.8 行）；li1-3 縮排 `17→14vw`。
- **驗證**：照片覆蓋行數：行動版 thum--6 `[16,17]`（2 行，原 3 行）、thum--1 `[1,2]`（2 行）、桌面 thum--1 `[1]`、thum--6 `[11,12]`（2 行）；右側照片垂直居中（thum--2 等 top 在行中部）；clearance/layout 全 PASS；無重疊；spread 維持（1280 avg 12.3、375 avg 6.6）；verify scroll-scrub 200/200、198/198；`manage.py check` 通過；版號 `?v=20260821y`。

### 2026-08-21：topConcept 全部文字 justify 填滿右緣 + 字級 3vw + 照片縮小 ✅

- **需求（用戶）**：「文字沒有填滿欄位右緣」。詢問後選**「justify 填滿 + 放大字級至 3vw（字距降為 ~14px、文字更大更滿），照片行溢出則縮小照片」**。
- **實作**：
  - **全部文字 justify 填滿**（`text-align: justify` + `text-align-last: justify` + inter-character）：非照片行填滿欄位右緣（818px）、照片行填滿到照片前。
  - **字級放大**：桌面統一 `3vw`（1280→38px，原 2.5/2.75vw）；行動版維持 `4vw`。
  - **照片縮小**（照片行文字需容納 15 字 3vw=605px）：桌面 thum--1 `6vw`、--2/3/5 `3vw`、--4 `4vw`、--6 `6vw`、--7 `2.5vw`（原 11.35/5.12/11.49/9.37/3.95vw）；行動版維持 15/17.33/17.07/13vw。
  - 縮排/避讓配合：桌面 li1/2/11/12/13 `6.6vw`、li6 `3.6vw`；右避讓 li3/li9 `3.6vw`、li6 `4.6vw`、li13 `3.1vw`；行動版不變。
- **驗證**：clearance（照片尺寸新期望 + 全域照片×文字不重疊）1280/1024/768/375 全 PASS；layout（期望值更新）PASS；justify spread：1280 avg 12.3（非照片行 13.5-17.1，li13 短行 21.2）、375 avg 6.4；1440/414 無重疊；verify scroll-scrub 200/200、198/198 PASS；`node --check` + `manage.py check` 通過；版號 `?v=20260821x`。
- **取捨**：文字填滿欄位右緣 → 非照片行字距 ~14-17px（使用者接受，比自然寬右側留白更「滿」）；照片縮小（偏離原站尺寸）；li13（12 字短行）填滿後字距 21.2px（短行 justify 本質）。

### 2026-08-21：topConcept 照片不壓字（照片與文字分離）+ 縮小文字 ✅

- **需求（用戶）**：「不要照片壓字，調整文字大小」——照片不再蓋住文字，照片與文字分離。
- **實作**：
  - **照片與文字分離**：照片垂直覆蓋的每一行文字都水平避讓（左側照片→縮排、右側照片→右避讓），全域照片×文字不重疊。
  - **文字縮小**：桌面 `2.75vw`（≥1024）/ `2.5vw`（768-1023）、行動 `4vw`——使各照片行文字完整容納在避讓後的空間。
  - **桌面照片維持原站尺寸**（thum--1 11.35vw、--4 11.49vw 等）；**行動版 thum--1/4 縮小**（28→15vw、27.73→13vw）以容納 15 字長行（li4/li14）。
  - 縮排/避讓：桌面 li1-3 `12.5vw`、li6/7 `6.44vw`、li11-13 `10.61vw`；右避讓 li3/li9 `5.7vw`、li6/7/8 `12.1vw`、li13 `4.6vw`。
  - li7 letter-spacing `0.11→0.05em`（原站值致文字過寬，在雙避讓窄空間溢出）；行動版 li6/7 覆蓋桌面縮排為 0。
- **驗證**：clearance（加入全域照片×文字不重疊檢查）1280/1024/768/375 全 PASS；layout（期望值更新）PASS；measure 無溢出行；verify scroll-scrub 200/200、198/198 PASS；1440/414 補測無重疊；`node --check` + `manage.py check` 通過；版號 `?v=20260821w`。
- **取捨**：照片與文字並排（不壓字）→ 文字可用空間受限 → 桌面字級 2.5-2.75vw（32-35px）、行動 4vw（15px）；**行動版 thum--1/4 縮小**（偏離原站行動版尺寸）；li7 字距縮小（偏離原站 0.11em）。

### 2026-08-21：topConcept 回歸 hakujuji 原站樣式（照片尺寸、字級、無 justify）✅

- **需求（用戶）**：「照片尺寸使用 https://www.hakujuji-g.co.jp/，最終結果/顯示必須與該網站 UI 和動畫完全一樣」。
- **調查（CDP 實測原站）**：hakujuji 原站字級 `3.2942898975vw`（1280→42px）、照片「width 固定 + 高度自然」（default.css 全局 `img{width:100%;height:auto}`）、文字無 justify（自然寬左對齊）、照片壓字（z-index 在上）、行動版 thum--6/7 固定框 + cover。原站桌面行長 15-21 字（715-892px 寬），**文字本身也溢出容器**（被照片壓/延伸）——Between 中文 15 字（647-720px）比原站更短，溢出更少。
- **實作**：
  - 照片尺寸回歸原站：thum--1 `11.35vw`、--2/3/5 `5.12vw`、--4 `11.49vw`、--6 `9.37vw`、--7 `3.95vw`（桌面）；thum--1 `28vw`、--2 `17.33vw`、--3 `17.07vw`、--4 `27.73vw`、--6 `13.87×20vw`、--7 `18.67×12.53vw`（行動，6/7 固定框 cover）。img `width:100%;height:auto;display:block`。
  - 字級回歸：桌面 `3.2942898975vw`、行動 `5.0666666667vw`。
  - 縮排回歸原站：桌面 li1/2 `13.18vw`、li6 `6.44vw`、li11~13 `10.61vw`；行動 li1~3 `31.2vw`、li11/12 `22.67vw`、li16~18 `17.33vw` + 照片行避讓。
  - 移除 justify（`text-align:left`）、移除統右緣、移除 2 行高框與 cover（桌面）。
  - 深色適配保留（白字）、scroll-scrub 動畫（bc-top-concept.js）不變；版號 `?v=20260821v`。
- **驗證**：clearance（重寫：照片尺寸=原站 vw 值 + 高度自然比例）1280/1024/768/375 全 PASS；layout（期望值回原站縮排）PASS；measure 無 justify（spread 0）；verify scroll-scrub 200/200、198/198 PASS；原站 CDP 比對：原站 li1 715px（溢出 66px）、Between li1 647px（溢出 0）→ Between 溢出更少；`manage.py check` 通過。
- **取捨**：照片壓字是本設計核心——桌面 li6 文字被 thum--4 蓋 58px（與原站一致）；行動版 li14（15 字中文，比原站 11 字日文長）被 thum--4 蓋 104px（35%），為「照片壓字」+ 中文較長的自然結果，若嫌多可縮短行動版文案拆行。

### 2026-08-21：topConcept 照片換為 hakujuji 原站照片（維持優化佈局）✅

- **需求（用戶）**：「照片使用 https://www.hakujuji-g.co.jp/，最終結果必須與該網站 UI 和動畫完全一樣」。
- **調查**：hakujuji-g.co.jp 是岡山甜點品牌「白十字」；topConcept 照片為 `/assets/img/contents/concept/leader__img--1~7.jpg`（橫式暖色照片，比例 ~1.46；僅 img--6 直式 0.749）。原站字級 3.29vw、文字左對齊（無 justify）、照片壓字、scroll-scrub 動畫——與目前優化版差異大。詢問後使用者選**「只換照片，其餘維持優化（2 行高小字距統右緣）」**。
- **實作**：
  - 下載 7 張照片至 `static/images/hakujuji_leader_N.jpg`（thum--1~7 對應 leader__img--1~7）。
  - `about.html` topConcept 的 7 個 thum img 替換（**SERIES 滑桿兩組維持 coffee PNG，不受影響**）；CSS 版號 `?v=20260821u`。
  - CSS `object-fit: contain → cover`：橫式照片填滿 2 行高框（3.44×4.4vw / 6.57×8.4vw），中央裁切、不變形；縮排/避讓、統右緣、字距**零變動**。
- **驗證**：7 張照片伺服器 200 + CDP natural 尺寸正確（310×212 等）；clearance/layout/measure 全 PASS（佈局與字距維持：1280 avg 2.6、375 avg 4.5）；verify scroll-scrub 200/200、198/198；`manage.py check` 通過。
- **注意**：hakujuji 照片為橫式（1.46），cover 於 2 行高框裁切兩側（保留中央 ~53%，主體保留）；直式 img--6 幾乎不裁。照片為第三方網站素材（使用者指定使用），若需 hakujuji 完整橫式照片顯示需放寬佈局（字距回歸 ~12px）。

### 2026-08-21：topConcept 統右緣 + 全照片 2 行高 + 縮小左側照片（方案 C）✅

- **需求（用戶回饋）**：上一版「逐列收斂」字距雖小但「階梯狀太明顯」「文字不再統一填滿欄位右緣」，完全不理想。詢問後採**方案 C：統右緣 + 深度收斂（字距 ~7px）+ 縮小桌面左側照片 coffee_01/03/08 與 coffee_04 至 2 行高**。
- **數學限制（關鍵）**：
  - justify 字距 = (容器寬 − 自然寬) ÷ 字間數。「填滿右緣」與「小字距」在桌面欄位（818px）與每行 15 字（自然寬 ~440px）下互斥；統右緣 + 小字距只能靠縮小欄位（右側留白）。左側照片縮排是統右緣的最大瓶頸（縮排列容不下窄欄位）。
  - **CJK 字體實際渲染高度 > font-size**（Noto Sans TC ≈ 1.45×）→ 文字行視覺高度超出 li 內容區。照片 2 行高（56px）必然垂直覆蓋相鄰行文字，解法是「被覆蓋的行水平縮排避讓」（照片壓字 = coffee_01 方法，垂直重疊允許）。
- **實作**：
  - **統右緣**：非照片列填滿同一右緣；右 padding 隨斷點加深（768→13vw、940→19vw、≥1200→22.5vw），確保雙照片列 li06 在窄桌面容納；右側照片 right 同步（貼統右緣）。
  - **全照片 2 行高**：桌面 3.44×4.4vw、行動 6.57×8.4vw（PNG 0.7818）、bean_01 4.4×8.4vw（正方）。coffee_04 桌面縮至 2 行高（不再大尺寸）。
  - **左側照片縮排避讓**：coffee_01（li1，top 0.37 覆蓋 li1+li2）、coffee_03（li6，top −1.28 上移覆蓋 li5+li6——因 li7 有 coffee_04 右避讓放不下左縮排）、coffee_08（li11，top 0.37 覆蓋 li11+li12）；被覆蓋行 li2/li5/li12 桌面縮排 4vw。
  - **行動版**：coffee_01/03/08 top 0 覆蓋自己行+下一行（li2/li12/li17 縮排 8.2vw）；coffee_04 上移（top −5.53vw）覆蓋 li12+li13（行動版 li14 是 15 字長行，無法避讓 2 行高照片）；coffee_02/bean_01 覆蓋兩行（li5+li6、li17+li18，皆避讓）。
  - **字距**：桌面 15 字列 ~7px、行動 ~6-8px；照片避讓/縮排列自然更小；li13（12 字短行）與行動版 li12/li18 額外右縮收斂。
- **驗證**：clearance（重寫：全域照片×文字不重疊 + 照片高=2×font-size + 統右緣 ±3px + 字距 ≤9px）1280/1024/768/375 全 PASS；layout（期望值更新）PASS；verify scroll-scrub 200/200、198/198 PASS；字距 avg 2.6/3.0/3.6/4.5、max 6.8/6.8/6.8/8.1；1440/414 補測 avg 3.9/5.8、max 8.8/9.9；`node --check` + `manage.py check` 通過；CSS `?v=20260821t`。
- **取捨**：右側留白較大（桌面 1280 文字右緣 ~897、欄位右緣 ~1185）；li6 的 coffee_03（上移）與 coffee_04（居中）垂直位置不同（li7 無法縮排的數學限制）；文字右緣統一無階梯（照片行因避讓右縮 ~照片寬）。

### 2026-08-21：照片 2 行高 + 桌面/平板文字縮小 + 各列容器收斂字距 ✅

- **需求（用戶）**：1) coffee_02/coffee_04/bean_01 照片太小 → 改為佔用 2 行文字尺寸（所有響應端）；2) 平板和桌面端縮小文字；3) 所有響應端字距仍太大，問「縮小容器」或「縮小字級」能否解決。
- **分析（字距公式）**：justify 字距 ≈ (容器寬 − 自然寬) ÷ 字間數。①縮小容器 → 分子變小，直接有效；②單獨縮小字級 → 自然寬也縮小但容器不變 → px 字距反而變大；須「縮小容器 + 縮小字級」並用，文字區塊才能同時更精簡且字距收斂。
- **實作**：
  - 桌面/平板（≥768）字級 `2.6 → 2.2vw`；移除 768–939 降字級例外與 ≥1200 全域右 padding 70px。
  - 桌面各列右 padding 依字數收斂（li-1/2:10.5、li-3/4/5/8/10:24.2、li-6:17.2、li-7:20.8、li-9:18.4、li-11/12:9.2、li-13:21.8vw）→ 字距目標 ~6px。
  - 行動各列右 padding（li-4:8.8、li-5:14.1、li-6~10:16.8、li-12:4.5、li-13:22.9、li-15:8.5、li-17:13.3、li-18:22.4vw）→ 字距目標 ~5px。
  - 右側照片 2 行高（height=2×font-size）：桌面 `4.4vw`（coffee_02/05 寬 3.44vw、bean_01 4.4×4.4vw），行動 `8.4vw`（coffee_02/04 寬 6.57vw、bean_01 8.4×8.4vw）；寬度依 PNG 長寬比（咖啡杯 0.782、豆袋 1.0）；coffee_04 桌面維持原大尺寸（11.49×7.83vw，不縮小）。
- **驗證**：CDP 1280/1024/768/375 字距 avg 5.6/2.9/0.4/3.8px（原 11.8/9.6/5.3/7.2px，最大 20.5→7.7）；照片高 44×56/35×45/26×34/25×32（=2 行高）；文字尾 875–1067 < 照片左 1038–1141（無重疊）；clearance/layout/verify 全 PASS（clearance 已改寫為「2 行高 + 不重疊 + 字距≤8px」）；`node --check` + `manage.py check` 通過；curl 確認伺服器提供新版 CSS（?v=20260821s）。
- **取捨（新布局）**：文字不再統一填滿欄位右緣——各列依字數在 ~875–1067（桌面）/ ~217–335（行動）收斂右緣，呈階梯狀；文字與右側照片間距 19–266px（不重疊）。此為縮小容器換取小字距的必然結果。

### 2026-08-21：行動版文字 justify 填滿右緣（修正右側縮入）✅

- **需求（用戶）**：行動端右側文本區域沒有 justify，右側縮進去 → 要文字填滿右側。
- **根因**：桌面的照片行 padding-right（li-3: 5.72vw、li-6/7: 12vw、li-9: 5.72vw）在行動版仍生效（桌面區規則非 media query 內）——但行動版這些行沒有照片 → justify 文字被限制在較窄內容區，右側縮入。
- **實作（行動 ≤767px）**：行動版文字改 justify（`text-align`/`text-align-last: justify` + inter-character，與桌面一致）；重置 li-3/6/7/9 的 padding-right 為 0；照片行 li-5/13/17 維持 padding-right（39/50.5/33vw）讓 justify 文字停在照片前（6px）。
- **驗證**：CDP 375px 全部非照片行 justify 填滿到右緣（文字尾 335 = li 右緣）；照片行文字尾 227/184/250、照片 233/190/256（6px 間距）；clearance/layout/verify 全 PASS；scroll-scrub 200/200、198/198；`node --check` + `manage.py check` 通過。
- **注意（justify 特性）**：行動版短行（7–11 字）justify 填滿 295px 時字距會拉開（如 li-18 恰度好的一杯），這是 justify 填滿的本質；桌面行較長所以相對不那麼開。若覺得太開可再縮小字級或改部分 justify。

### 2026-08-21：行動版修復（文字縮小 + 右側照片縮小至行內）✅

- **需求（用戶）**：行動端 1a) 右側文本超出容器；1b) coffee_04 與文字疊加下層；1c) coffee_02 下方文字未覆蓋一行有間隙；2) 縮小文字。
- **根因**：行動版沿用原站 base-sp 的 5.07vw 文字與大照片——我們的中文文案較長 → 溢出（1a）；先前把右側照片移到行尾與原站 padding 設計衝突 → 疊加/間隙（1b/1c）。
- **實作（行動 ≤767px）**：字級 `5.07 → 4.2vw`（15.75px，縮小文字）；右側照片（coffee_02/04/bean_01）縮小至 `7.4×5vw` 並貼齊各自文字行尾（間距 6px）——不再向下重疊（1b/1c）；移除多餘的 padding-right 保留區（li-5/6、li-13/14/15、li-17/18）。左側照片（coffee_01/03/08）維持 coffee_01 方法（行有左縮排避開）。
- **驗證**：CDP 375px 最大文字尾端 339<375（無溢出）；右側照片距文字 6px、完整在行內；clearance/layout/verify 全 PASS；scroll-scrub 正常（198/198）；`node --check` + `manage.py check` 通過。

### 2026-08-21：coffee_04 恢復大尺寸（coffee_01 方法：右側照片 + 重疊行右縮排）✅

- **需求（用戶）**：coffee_01（高 ~2 行）與 coffee_08（高 ~3 行）顯示良好，能否用這個方法解決 coffee_04？
- **根因**：coffee_04 與 coffee_01 其實同尺寸（11.49×7.83vw vs 11.35×7.76vw）；coffee_01 在左側、被覆蓋的行有左縮排故不撞字；coffee_04 在右側、被覆蓋的 li--7 文字 justify 填滿到右緣 → 撞上照片（「a(photo)b」）。
- **實作（coffee_01 方法套用右側）**：coffee_04 恢復 `11.49×7.83vw`；li--7 加 `padding-right: 12vw`（照片寬+間距）→ 被照片覆蓋的 li--7 文字停在照片前；li--6 維持 padding-right 12vw。照片重疊 li6+li7 兩行但兩行文字都避開它（1280 文字尾 1001 vs 照片左 1008，7px）。
- **驗證**：CDP 1280/1024/768 照片 147×100/118×80/88×60（原尺寸）、li6+li7 文字停在照片前 3–7px、無夾字、無空白行；像素確認文字尾 998、杯身自 1014（16px）；clearance/layout/verify 全 PASS；`node --check` + `manage.py check` 通過。

### 2026-08-21：coffee_04 縮小至行內（解決「兩字中間 / 空白行」）✅

- **需求（用戶）**：1) 不是兩行文字中間，是兩個文字中間（a (photo) b，照片水平夾在文字間）；2) 先前加高行後出現空白行。
- **根因**：coffee_04 照片高 7.83vw（1280→100px）是文字行（~52px）的 2 倍——放行內溢到下一行（「a(photo)b」：照片上方 li--6 文字、下方 li--7 右緣文字露出在照片右側）；加高 li--6 行則產生空白帶。
- **實作**：coffee_04 縮小至 `5.1×3.5vw`（與其他右側小照片同級，完全容納在 li--6 行內）；li--6 右 padding `12.09→5.7vw`（配合縮小後的照片寬，文字停在照片前 5–9px）；移除 768–940px 的 2.5vw 例外（li--6 已有餘裕，全寬度統一 2.6vw）。照片尺寸變更是唯一能同時消除「夾字」與「空白行」的方案。
- **驗證**：CDP 1440/1280/1024/900/768 照片在行內、文字距照片 5–9px、與下行間距 0（無空白行）；clearance/layout/verify 全 PASS；scroll-scrub 正常；`node --check` + `manage.py check` 通過。

### 2026-08-21：coffee_04 卡在兩行文字中間 → li--6 行加大底部間距容納照片 ✅

- **需求（用戶）**：coffee_04 不再被文字疊加，但照片在兩行文字中間，顯示異常。
- **根因**：coffee_04 照片高 7.83vw（1280→100px），但 li--6 文字行僅 ~52px 高 → 照片往下溢出到 li--7 文字行（li--7 justify 填滿到右緣正好在照片下方）→ 照片看似卡在 li--6/li--7 兩行文字之間。
- **實作**：`.csBlock__leaderTarget--6` 加 `padding-bottom: 5.2vw`（1280→67px），使 li--6 行高 ≥ 照片高；照片完整容納在自己的行內（維持原尺寸），與 li--7 文字保持 2–5px 間距。
- **驗證**：CDP 1440/1280/1024/768 照片在行內（photoInRow=True）、與 li--7 間距 2–5px；clearance/layout/verify 全 PASS；scroll-scrub 正常；`node --check` + `manage.py check` 通過。

### 2026-08-21：coffee_04 文字疊加下層（三修）→ 字級降至 2.6vw 給 li--6 充足餘裕 ✅

- **需求（用戶）**：coffee_04 照片區域文字疊加在下層，文字無法自動換行（nowrap 設計，溢出的文字延伸到照片下方）。
- **根因**：li--6（coffee_04 行）在 2.8vw 時內容僅比自然文字寬多 ~3px 餘裕——真實瀏覽器捲軸使內容窄 ~15px、或 fallback 字型略寬時，文字即溢出到照片下方。
- **實作**：字級 `2.8vw → 2.6vw`（桌面全部；768–940 維持 2.5vw）。slack（內容−自然寬）1280:+55 / 1024:+35 / 768:+20px，可吸收捲軸與字型差異；設計間距（文字停在照片前）維持 5–9px。加 z-index:1（照片在前）保險。
- **驗證**：CDP 各寬度文字距照片 +5~9px；clearance/layout/verify 全 PASS；scroll-scrub 正常；`node --check` + `manage.py check` 通過。
- **代價**：li--3 字距 11→14px（spacing 略回彈，換取照片不再被文字疊加）。

### 2026-08-21：coffee_04 被文字覆蓋（二修）→ 照片 z-index 置前 ✅

- **需求（用戶）**：coffee_04.png 顯示仍然異常，文字覆蓋在前面。
- **診斷**：DOM 掃描 768–1920（每 40px）文字與照片零重疊（1280 全亮狀態文字至 997、杯身自 1054 起，間距 57px）——使用者環境（字型 fallback 寬度 / 捲軸寬度）可能有微差。
- **實作**：`.csBlock__leaderThum` 加 `z-index: 1` → 照片永遠在文字前面（原站拼貼視覺：照片在上），即使任何環境下文字碰到照片也不會蓋住照片。加上先前的 768–940px 字級 2.5vw + ≥1200px padding 70px 修正。
- **驗證**：clearance/layout/verify 全 PASS；1280 全亮像素確認文字距杯身 57px；`node --check` + `manage.py check` 通過。
- **提示使用者**：若仍看到舊樣式請強制重新整理（Ctrl+F5 / Cmd+Shift+R），WHITENOISE 長快取靠 ?v=20260821g 更新。

### 2026-08-21：coffee_04 被文字覆蓋 → 防止 li--6 文字溢出到照片 ✅

- **需求（用戶）**：coffee_04.png 顯示異常，文字覆蓋在前面。
- **根因**：li--6（coffee_04 行，左右照片夾 15 字）在窄寬度（768–940px）內容不足自然文字寬 → justify 無法收縮 → 文字溢出到照片；且文字在 DOM 中位於照片之後 → 文字壓在照片前面。
- **實作**：768–939.98px 字級降至 `2.5vw`（此區間 li--6 內容放不下 2.8vw 自然文字）；≥1200px leader 右 padding `80→70px`（給 li--6 文字與照片 8px 間距，不再頂到照片）。media query 置於基底 font-size 規則之後（避免被覆蓋）。
- **驗證**：CDP 各寬度 li--6 文字停在照片前（1280:+8 / 1024:+6 / 900:+6 / 768:+5px）；768 像素驗證字形至 580、杯身自 592 起（12px 間隔）；clearance/layout/verify 全 PASS；`node --check` + `manage.py check` 通過。

### 2026-08-21：justify 字距 → 縮小文字區域容器（分析 + 極限實作）✅

- **需求（用戶）**：字距仍太大；詢問縮小容器或縮小文字能否解決。
- **分析**：justify 字距 = (欄位寬 − 文字自然寬)/字數。縮小容器 → 字距收斂（有效）；縮小文字 → 自然寬變小 → 相對字距更大（無效）。**硬限制**：li--6（coffee_04 行，左+右照片夾 15 字）內容空間在窄寬度已無餘裕，容器最多只能縮 40px（1280 下）；再縮文字會碰到杯身。
- **實作**：≥1200px 時 leader 右 padding `40px → 80px`（1280 實測 li--6 內容 540 ≥ 自然 537，恰為極限）；1024 實測 li--6 內容僅 403 < 自然 440 → 維持 40px。字距改善：li--3 13.9→11.2px；li--13（12 字短行）維持 ~13px。
- **驗證**：clearance/layout/verify 全 PASS（各寬度文字不遮杯身、照片清出按鈕）；`node --check` + `manage.py check` 通過。
- **結論（固有權衡）**：在現有文案（12-15 字/行）與照片佈局下，justify 字距有 ~11-13px 的地板（受 li--6 照片行限制）。若要真正的自然字距，需：1) 加長文案讓行自然填滿（原站行長 16-19 字），或 2) 取消 justify 接受右側留白。此變更採「縮小容器」極限方案。

### 2026-08-21：topConcept justify 字距過寬 → 字級調整至 2.8vw 平衡 ✅

- **需求（用戶）**：文字填滿後字距太大。
- **實作**：字級 `2.30600292825vw → 2.8vw`（1280 → 35.8px，仍小於原 3.2943vw；2.306vw 在填滿下每字間距過寬，2.8vw 收斂至合理範圍）。justify + 照片 right:0 + 每行右 padding 保持不變。
- **驗證**：CDP 1280/1024/768 字級 35.8/28.7/21.5px、照片右緣 vs 按鈕 13px、字形不遮杯（像素驗證 768 字形至 580、杯身自 584 起）；768 li--6 最後字元 advance box 進入照片透明邊距 -21px（實際字形有間隔，clearance 容差調整為 -25~25 並註明）；行動版左對齊不變；全部腳本 PASS。
- **說明（固有權衡）**：文案長度固定，寬欄填滿必然有字距；2.8vw 為「縮小」與「字距」的平衡點，可再調。

### 2026-08-21：行動版右側照片貼齊右緣（消除照片縮入）✅

- **需求（用戶）**：文字 justify 填滿後，行動版右側照片（coffee_02/coffee_04/bean_01）看起來「縮進去了」。
- **根因**：上一輪「右側照片縮小至行內」把行動版 thum--2/4/7 從 `right: 0` 改為 `left: 51.5/40/57.6vw`（避開當時左對齊的短文字）。文字 justify 填滿至右緣（335）後，照片停在 233/190/256 → 離右緣 100+px，明顯內縮。
- **實作（bc-top-concept.css 行動 ≤767px）**：
  - 右側照片 thum--2/4/7 改回 `right: 0`（與桌面一致），貼齊 li 右緣（375 下 307-335）
  - 照片行右 padding 縮為 `li--5/13/17: 9.2vw`（39/50.5/33vw → 9.2vw）→ justify 文字填滿至照片左緣前 ~7px
  - 非照片行維持 padding-right 0（填滿右緣）不變
- **驗證**：CDP 375px 右側照片 [307,335] = li 右緣、文字尾 300/301（gap 7px）、非照片行全填滿 335（li-1 尾 339 為既有 trailing letter-space，非本次變更）；桌面 1280 回歸：照片仍在右緣、gap 7-8px 不變；`cdp_leader_clearance.py` 四寬度 PASS、`node --check` + `manage.py check` 通過。
- **檔案**：`about.html`（?v=20260821q）、`static/css/bc-top-concept.css`。

### 2026-08-21：topConcept 右側文字 justify 填滿（消除右側縮入）✅

- **需求（用戶）**：右側文字區域文本內容沒有 justify，右側縮進去 → 要文字填滿右側。
- **實作（bc-top-concept.css 桌面）**：
  - `.csBlock__leaderTarget--text--p` 加 `text-align: justify; text-align-last: justify; text-justify: inter-character`（CJK 均分字距填滿）
  - 右側照片（coffee_02/04/05/bean_01）改 `right: 0`（原站樣式），照片右緣 = 欄位右緣
  - 照片行加右 padding（li--3/9: 5.72vw、li--6: 12.09vw、li--13: 4.65vw）→ 該行文字 justify 停在照片前（5–9px gap，杯身不遮字）
  - leader 右 padding `0 → 40px` → 文字/照片在固定 Order/profile 按鈕前停下（間距 13px）
  - 行動版（≤767px）維持左對齊（media query 重置 text-align: left）
- **驗證**：CDP 1280/1024/768 文字填滿（非照片行至 li 右緣、照片行停於照片前 5–9px）、照片右緣 vs 按鈕 13px、杯身不遮字；行動版左對齊不變；verify/layout/clearance 腳本全 PASS；`node --check` + `manage.py check` 通過。
- **檔案**：`about.html`（?v=20260821c）、`static/css/bc-top-concept.css`。

### 2026-08-21：topConcept 右側文字縮小 30%（照片不調整）✅

- **需求（用戶）**：右側文字縮小 30%，照片不調整大小。
- **實作（bc-top-concept.css 桌面）**：`.csBlock__leaderTarget--text--p` 字級 `3.2942898975vw → 2.30600292825vw`（×0.7）；照片尺寸/高度全部維持原樣；右側照片（coffee_02/04/05/bean_01）的 `left` 重新量測並貼齊**縮小後**的各自文字行尾（36.4/42.3/37.5/38.8vw），coffee_04 不再延伸到欄位右緣、改貼行尾（清出 Order 按鈕 143px）。行動版（≤767px）維持 5.07vw 不變。
- **驗證**：CDP 桌面 1280/1024/768 字級 29.5/23.6/17.7px（=70%）、照片尺寸不變（66/147/66/51px）、照片左緣−行尾 4–6px、與 profile 按鈕間距 47–300px 全 PASS；行動版 19px 不變；layout/clearance/verify 腳本全 PASS；sticky 仍 105px；`node --check` + `manage.py check` 通過。
- **已知觀察（未改，照片不縮前提下無乾淨解法）**：行動版 bean_01/coffee_02 右緣與固定 profile/Order 按鈕在捲動帶上重疊（topConcept grid 40px 使照片右移所致，非本次文字縮小造成）。若需處理可另行調整。

### 2026-08-21：hakujuji topConcept 整合（取代 bc-leader，scroll-scrub 逐字點亮）✅

- **需求（用戶）**：將 https://www.hakujuji-g.co.jp/ 首頁的 `.boxBottomLine article.topConcept` 整合到 about.html；**取代現有 bc-leader**；忠實原站（全寬 + 原始 vw 尺寸 + sticky 標題 26%/leader 74% + 了解按鈕）；無額外 UI/css。
- **HTML（about.html）**：`<section class="boxBottomLine article topConcept bc-top-concept">` > `.grid` > `.topConcept__tob`（`tobLeader` sticky 標題「為什麼，Between Coffee／會如此堅持／一杯好咖啡。」+ `cateBtn allBtn`「了解更多」→ `{% url 'coffee_menu' %}`；`tobContents` 74% 含原 13+18 行中文 leader）。移除 `.container`。
- **CSS（新 `bc-top-concept.css`）**：1:1 複製 top.css/base.css/top-sp.css/base-sp.css（boxBottomLine 55px+底線、grid 40px、tob 26/74 flex、tobLeader sticky top:105px、articleTitle min(2.196vw,30px)、cateBtn 152px 深灰底白字圓點+hover 圓點放大、leader 原始 vw 3.2943vw 等）；深色適配（文字 #fff、底線 var(--bc-border)、hover 品牌金）；照片貼齊行尾（桌面 coffee_02/05/bean_01 於行尾、coffee_04 右緣對齊欄位右緣 55.6vw 以清出固定 Order 按鈕；行動 left 62.3/48.4/66vw）。刪除 bc-leader.css。
- **JS（新 `bc-top-concept.js`）**：複製 top.js `wrapCharSpan` + **scroll-scrub 逐字點亮**（ScrollTrigger trigger `.bc-top-concept`、start 'top 60%'、end 'bottom 50%'、scrub 0.2、onUpdate 已捲過 opacity 1 / 未捲 0.4；與 /concept/ 的一次性 stagger 不同）；spFlg 以 ≤767 對齊 CSS。刪除 bc-leader.js。
- **全域修復（bc-components.css）**：`html,body { overflow-x: hidden }` 會建立 scroll container 破壞 `position:sticky`（topConcept 標題欄無法固定）→ 改為 `overflow-x: hidden; overflow-x: clip`（clip 剪裁不建立 scroll container，防護效果相同，舊瀏覽器 fallback hidden）。
- **驗證**：CDP 桌面（13 li、7 縮圖、200 span、opacity 0.3→捲到底全 1、sticky 105px、26/74 欄、文字 42.17px）+ 行動（18 li、6 縮圖、198 span、全 1、標題 18px、按鈕 91px）+ 行偏移桌面 [535,…,503]/行動 [157,…,105] PASS + 照片貼齊行尾四寬度 PASS + 無水平捲軸 + `node --check` + `manage.py check`。
- **檔案**：`about.html`、`base.html`（bc-components ?v=20260821a）、新 `static/css/bc-top-concept.css` + `static/js/bc-top-concept.js`、刪除 `bc-leader.css`/`bc-leader.js`、更新 3 個 verify 腳本。

### 2026-08-20：bc-leader 容器化 + 縮小 30% + 右側照片改貼齊行尾 ✅

- **需求（用戶）**：1) bc-leader 目前全寬，加容器包住；2) 整個 UI 縮小 30%（文字+照片）；3) 右側全部照片（coffee_04/coffee_02/coffee_05/bean_01）「位移」。
- **根因（第 3 點，二修確認）**：原站 hakujuji 文字行很長、會延伸到貼右緣（right:0）的照片；我們的中文文案較短（~15 字），照片仍 `right:0` → 文字與照片間出現 **~500px 空曠**（桌面），照片孤獨浮在容器右緣，看起來「位移」。與固定 Order/profile 按鈕無關（前次誤判已修正）。
- **容器（HTML）**：`<section class="bc-leader">` 內包一層 Bootstrap `.container`（1140 max）。行動版 `.bc-leader > .container { padding: 0 }` 維持貼齊螢幕。
- **縮小 30%（CSS 桌面）**：`--luv: min(0.7vw, 13.44px)`（=0.7vw，上限 0.7vw@1920），所有桌面 vw 尺寸改 `calc(var(--luv) * N)`。1280 字級 42.2→29.5px（=70%）。行動版（≤767px）維持原尺寸不縮。
- **右側照片定位（本次核心）**：coffee_02/04/05/bean_01 由 `right: 0` 改為 `left: calc(var(--luv) * K)`（桌面，K=51.3/57.9/53.8/51.1，依各行列尾實測 vw 比例推導）+ 行動版 `left: 62.3/48.4/66vw` → 照片貼齊各自文字行尾端（間距 5–9px）。移除先前多餘的 768–1199px 按鈕避讓 media query。
- **驗證**：CDP 四寬度（1280/1024/768/375）照片左緣 − 該行文字尾端 = 5–9px（`cdp_leader_clearance.py` 改為檢查此條件，全 PASS）；動畫 opacity 0.3→1、13/18 li、7/6 縮圖不變；像素分析確認 7 張杯身都在新位置；`node --check` + `manage.py check` 通過。
- **檔案**：`about.html`（container + css?v=20260820a）、`static/css/bc-leader.css`、`docs/verify/cdp_leader_clearance.py`（改為行尾貼齊檢查）、`docs/verify/cdp_leader_layout.py`（桌面期望值 [218,…,195]）。

### 2026-08-19：about.html hakujuji `csBlock__leader--list` 整合（逐字亮起動畫）✅

- **需求**：將 https://www.hakujuji-g.co.jp/concept/ 的 `csBlock__leader--list` 整合到 about.html，UI/動畫 100% 複製、無額外 UI/css、不與其他區塊衝突。
- **內容決策（用戶確認）**：中文咖啡品牌文案 + 咖啡去背圖（coffee_01~05/08 + bean_01），結構/動畫不變。
- **HTML（about.html）**：新 `<section class="bc-leader">`（括號滑桿後、`ftco-section-blank` 前）；內含 `partsPc`（桌面 13 行）+ `partsSp`（行動 18 行）兩份 `.csBlock__leader`；縮圖 7 個（桌：li-1/3/6(×2)/9/11/13，行動：li-1/5/11/13/16/17）。
- **CSS（新 `bc-leader.css`）**：100% 複製原站（base.css 桌面 3.29vw + base-sp.css 行動 5.07vw、逐行 letter-spacing、縮圖 vw 定位）+ `default.css` 的 `partsPc/partsSp` 斷點切換（767px）；深色主題必要適配：文字 `#fff`、行動 border-bottom `var(--bc-border)`；`ul` reset（瀏覽器預設 padding-left 40px 會使全行偏移）；咖啡直式圖以原站縮圖足跡高度 + `object-fit: contain`。
- **JS（新 `bc-leader.js`）**：複製 concept.js `wrapCharSpan`（逐字元包 `<span>`、`ー` 加 tb-elm）；依 viewport（≤768）選 `partsPc`/`partsSp` 的 span；GSAP `opacity 0.3→1`、`duration 0.1`、`stagger 0.02`（與原站相同）；以 `ScrollTrigger`（`top 85%`、`once`）在區塊進入視窗時觸發（原站為載入觸發，但本區塊在頁面下方，載入觸發看不到動畫）；GSAP defer 時序保護沿用 bc-attract.js 輪詢模式。
- **驗證**：CDP 桌面（partsPc 顯示/partsSp 隱藏、13 li、7 縮圖、opacity 0.3→1）+ 行動（partsSp 顯示、18 li、6 縮圖、opacity 0.3→1）+ 行偏移與原站 CSS 完全一致（桌面 [187,187,19,…155] / 行動 [137,…] PASS）+ 無文字/縮圖水平溢出 + `node --check` + `manage.py check`。
- **檔案**：`templates/.../about.html`、`static/css/bc-leader.css`、`static/js/bc-leader.js`、`docs/verify/cdp_verify_leader.py`、`docs/verify/cdp_leader_layout.py`。

### 2026-08-18：about.html SERIES 滑桿 + 括號滑桿（完全複製 designing.jp/series）✅

- **需求**：將 https://designing.jp/series/ `container_3HNAz` 滑桿整合到 about.html；後續新增第二組括號滑桿 + 兩行標題。
- **第一組 SERIES 滑桿**：`bc-series-hero`（100vh flex）；標題「SERIES」140px 左側（photos 後方 z-index 0）+ 兩行文字（副標題「一種興奮感, 超越一杯的沉默」18px）；6 張咖啡去背圖（coffee_01~05/08）+ 左右箭頭 pager；照片間距（桌面 padding-right 140px、行動 margin 48px）；第一張照片頁面居中（標題改 absolute 脫離流 + 照片容器全寬 + padding-left calc((100%-280px)/2)）。
- **拖動機制**：桌面 `--js-x` transform 拖動（非原生捲動）；`pointerdown/move/up` + `setPointerCapture`（滑鼠+觸控皆可）；拖動時標題 `filter: blur(10px)` 模糊（原 backdrop-filter 有矩形裁切問題 → 改 filter 直接模糊文字）；過渡 1.8s `cubic-bezier(0.22,1,0.36,1)`（拖動時 0.15s 跟手）；F12 響應式測試修復（移除原生捲動、全用 --js-x、不依 pointerType 判斷）。
- **第二組括號滑桿（`bc-series-bracket`）**：`coffee_border_02.svg` 括號框居中固定（600×480、absolute、z-index 2、pointer-events:none）+ `noise-img noise_animation` 噪點效果（同 index.html）；每張照片一格滾動（鬆開依拖動方向吸附一格、未達門檻回彈）；修復第四張照片後卡住（maxLeft 改 `-(slideCount-1)*step`）。
- **productFv「US」blob 遮罩修復**：about.html 補載 `blobs.css` + `loadEnd`；修復 `.blobsItem>.inner` scale(0)、`.blobsBg` 桌面 0 尺寸；blob 尺寸 102vw×69vw 過大改 640×433/290×242 + 圖片 880/840px 填滿。
- **驗證**：CDP 多輪（拖動 -400/-2100px、吸附一格、括號居中 x=633、模糊 blur(4.17px)、noise desktop_noise_animation、照片居中、兩行標題 140/18px）+ node --check + CSS 括號平衡 35/35。

### 2026-08-17：WhatsApp 就緒通知失效診斷 + Render token 更新 ✅

- **問題**：客戶訂單「已就緒」狀態，發送 WhatsApp 取貨訊息不起作用，用戶懷疑 API/token 過期。
- **診斷（唯讀驗證）**：① Token **未過期**（本地 Graph API `/me` HTTP 200、`whatsapp_business_messaging` 權限完整）；② 發送功能**正常**（實際發送測試訊息 HTTP 200 成功、`send_order_ready_notification(訂單#2852)` 返回 True）；③ **真正原因** = WhatsApp 帳號仍在「測試模式」（`display_phone_number=+1 555-139-6249` Meta 預設測試號碼、`code_verification_status=NOT_VERIFIED`）→ 24h 會話窗口限制（客戶未先主動發訊息則主動推送被拒，錯誤 131030）；④ ready 訂單 10 個僅 2 個有 phone。
- **修復**：更新 Render 環境變數 `WHATSAPP_TOKEN`/`WHATSAPP_PHONE_NUMBER_ID`/`WHATSAPP_BUSINESS_ACCOUNT_ID`（Render MCP update_environ，觸發部署 dep-da1d0n7qj5pc73col130）。
- **template 程式碼準備**：`settings.py` 加 `WHATSAPP_TEMPLATE_NAME`/`WHATSAPP_TEMPLATE_LANGUAGE`（zh_HK）；`whatsapp_notifier.py` 加 `send_whatsapp_template_message()` + `_normalize_phone()`；`send_order_ready_notification` 設定了 NAME 就走 template，否則 fallback 自由格式；驗證 py_compile/check/15 tests OK + mock 切換。
- **待辦（用戶手動 Meta 平台）**：換真實香港號碼 + 號碼驗證 + template message 審核（解決 24h 窗口限制）。

### 2026-08-16：bc-welcome-panel 平板/手機右側圖片與文字溢出修復 ✅

- **問題**：使用者反饋平板/手機端 `.bc-welcome-panel` 右側圖片與文字超出容器外部。
- **診斷（CDP 768/375px）**：文字溢出為根因——`.bc-last-order`「按照之前口味落單?」`white-space: nowrap` 溢出 imgbox（平板 scrollWidth **115px** > imgbox **92px**、手機 **72px** > **62px**）；根因是 2026-08-13 縮小 imgbox（119→92→62px）讓出左側文字空間，但 last-order 文字未相應處理。圖片 absolute `top:-50/-29px` 浮出 panel 頂部為既有設計（保留）。水平方向量測皆在 panel 內（-12/-8px）。
- **修復（`bc-components.css`）**：`.bc-last-order` 平板/手機加 `white-space: normal + line-height: 1.25`（換行 2 行不再溢出）；圖片縮小避免與換行文字重疊（平板 img/img-link 92→**76px**、手機 58/62→**55px**、手機 img-link top -35→**-29px** 對齊）；`base.html` → `bc-components.css?v=20260816z`。
- **✅ 驗證（CDP 768/375/1280px）**：平板 scrollW **92 = clientW 92**（不溢出）、2 行、imgTextGap -2px（與桌面 -6px 視覺連續一致）、未溢出 panel；手機 scrollW **62 = clientW 62**、imgTextGap 1px；桌面 1280px 不變。

### 2026-08-16：navbar-brand「｛ Between ｝」移至最左 + 響應式縮小 + CSS 覆蓋修復 ✅

- **需求**：navbar-brand 移到瀏覽器最左；縮小尺寸（各端響應）；與漢堡選單水平對齊；離頂部有距離（統一響應）
- **最終方案**：container 改全寬（max-width:100% + padding 15px）→ brand 貼左、menu 靠右；navbar `padding-top` 統一離頂（桌面 30/平板 24/手機 18/小手機 14）；brand 字體響應縮小（桌面 36/平板 30/手機 24/小手機 20）；桌面 brand `margin-top:12px + margin-left:22px`；toggler `margin-left:auto` 靠右（修疊加）
- **CSS 順序修復（兩次）**：① `font-size` 寫在 media query 之後覆蓋了斷點縮小 → 改 `min-width:992px` 限定桌面；② `margin-top` 寫在 media query（前面）被 brand 區塊 `margin:0`（後面）覆蓋 → 移到 `margin:0` 之後
- **歷程**：absolute left 方案（漢堡疊加/離頂不統一）→ 回 container 內 flex + container 全寬（最乾淨）；離頂多次微調（12→20→24px）→ 改 navbar padding-top 統一

### 2026-08-16：首頁 SERIES 滑桿（完全一致複製 designing.jp/series）✅

- **需求**：用戶要求與 https://designing.jp/series/ `container_3HNAz` **完全一致**（左側文字 + 照片滑桿水平滾動時標題模糊 + 滑桿底部 + 無背景）；標題「SERIES」；獨立 `<section>` 標籤
- **規格提取**（網站 CSS）：容器 100vh flex 無背景；heading 140px `::before` `backdrop-filter:blur(10px)` `[data-blurred]` 切換；scrolling `padding-left:15.46vw` 橫向捲動；slide 350px/69.33vw；picture 280/374 375px/92.8vw 無邊框柔陰影 cover hover scale(1.03)
- **實作**：`bc-series-hero`（獨立 section、flex column 標題左上 + 滑桿 margin-top:auto 貼底、100vh 無背景）；heading「SERIES」140px（行動 50px）+ blur(10px)；6 張咖啡去背圖（coffee_01~05/08）無邊框；`bc-series.js` scroll 事件 → data-blurred；行動 scroll-snap 69.33vw；`bc-welcome-section` 覆蓋 margin-top:0（避免疊加）
- **驗證**：test client（結構/6 圖/css/js 載入/位置/welcome 相容）+ manage.py check 0 issues + bc-series.js 語法 OK；布局/CSS 數值與先前 CDP 驗證版一致（標題 140px 左、滑桿貼底、blurOpacity 1、無邊框/背景、行動 scroll-snap 無溢出）

### 2026-08-16：首頁 BETWEEN SERIES（完全複製 designing.jp/series container_3HNAz）✅

- **需求**：用戶要求**完全相同的效果**（首次整合誤加內容/布局偏離，重做）：左側文字 + 照片滑桿水平滾動時左側文字模糊（backdrop blur）+ 滑桿在底部 + 無背景 + 照片無邊框
- **結構分析**（designing.jp）：`.container_3HNAz` = fixed 100vh flex；`.heading_3yyjd` 140px 大字 `::before` backdrop-filter blur(10px) 由 `data-blurred` 切換；`.scrolling_iC60P` 橫向捲動 `padding-left:15.46vw`；`.slide_2tGjp` 350px `translate3d(var(--js-x))`；`.picture_29AE2` aspect 280/374 height 375px 無邊框柔陰影 `object-fit:cover`
- **實作**：`bc-series-hero`（height:100vh flex column，標題左上 + scrolling 底部 margin-top:auto）標題「BETWEEN/SERIES」140px 白；`::before` blur(10px) data-blurred 切換；`bc-series-scrolling` 全寬水平捲動 15.46vw；6 張咖啡去背圖 `bc-series-picture`（280/374 375px、無邊框、box-shadow、hover scale 1.03）；`bc-series.js` scroll 事件 → heading data-blurred；行動 ≤767.98 標題 50px + scrolling scroll-snap 69.33vw
- **驗證**：CDP 桌面（標題 140px 左上、滑桿貼底 gap 0、scroll→blurOpacity 1、pic 281×375 無邊框/背景、無溢出）/ 行動（50px、scroll-snap、69vw、無邊框、無溢出）

### 2026-08-16：首頁 BETWEEN SERIES 橫向滑動系列（參考 designing.jp/series）✅

- **需求**：參考 https://designing.jp/series/ 的 `container_3HNAz`（桌面固定 100vh 橫向滑動系列 + 行動 scroll-snap），以**普通區塊**形式整合到 index.html home-slider 之後
- **內容**：大標題「Between / Series」（Playfair 6rem 兩行垂直）+ 6 個系列卡片（咖啡豆/手沖/冷萃/季節限定/特調/烘焙，既有去背圖）+ 桌面箭頭/pager
- **修改**：index.html 新增 `.bc-series-hero`（home-slider 後、bc-welcome 前）；`bc-series.css` 新建（大字標題、卡片 hover、箭頭/pager、≤767.98 scroll-snap 響應）；`bc-series.js` 新建（桌面 `--bc-series-x` 位移 + 箭頭/pager、resize 重算、行動原生捲動）
- **驗證**：CDP 桌面 1280（標題 96px、箭頭點擊 translateX(-326px)、5 dots、無溢出）/ 行動 375（scroll-snap x mandatory、slide 72vw=270px、pager/箭頭隱藏、無溢出）

### 2026-08-16：首頁輪播第 3 格整合 magasinn 風格動畫區塊 ✅

- **需求**：參考 https://magasinn.xyz/ `top-main-sec-logo-inner`，整合到 index.html home-slider 第 3 個橫幅（保留咖啡機影片背景，內容層整個替換）
- **內容**：logo 動畫文字「A Craft Roastery」+ catch「Brewed / With / Soul」+ 6 張咖啡去背圖輪播（`coffee_01~05/08.png`）
- **修改**：index.html 第 3 橫幅 `.bc-slider3-magasin`（修正 magasinn 未閉合 span 語法；響應式 hidden-sp/pc → 行動「Cra─金色線─ft」跨行）；`bc-magasin.css` 新建（anime fade-up + delay1-22 + 品牌樣式 + ≤767.98 響應）；`main.js` 新增 translated/changed 事件 + setTimeout(0) 觸發 `.is-anime`（滑走重播）+ `.js-bc-magasin-slider` owlCarousel 初始化
- **驗證**：CDP 桌面「A CRAFT ROASTERY」/ 行動「A CRA─線─FT ROASTERY」、動畫 8 元素最終 opacity 1、圖片輪播 6 dots、無水平溢出

### 2026-08-16：首頁 bc-search lead SVG 文字圖 → CSS 小文本 ✅

- **需求**：首頁 SALON/STORE SEARCH 區塊的 `bc_search_txt_pc.svg`（DEMI DO 白色 SVG 字形文字圖）改為 CSS 小文本並刪除 SVG
- **文字**：「隱藏在工廠區只有百餘呎的咖啡店，每位員工必須先從自己開始了解咖啡，讓 {BETWEEN} 連接深愛著咖啡的人需求與喜好。」（`BETWEEN` 金色強調）
- **修改**：index.html 移除 `<picture>`（pc/sp 兩 SVG）→ `.bc-search-lead` 文本 + `.bc-search-lead-brand` 金色 span；bc-search.css `.bc-search-lead` 改文字樣式（Noto Sans TC、0.8rem、line-height 1.9、rgba 白 0.72）+ 響應式（≤768 0.9rem、≤575 0.85rem、寬 100%）；css `?v=20260816a`；**git rm 兩 SVG**
- **驗證**：CDP 實測文本顯示/金色 BETWEEN/無破圖/無溢出（width 187、font 12.6px）；manage.py check 0 issues

### 2026-08-16：profile 頁新增登出按鈕 ✅

- **需求**：`/profile/` 個人資料頁新增「登出」按鈕
- **修改**：socialuser/urls.py 新增 `path("logout/", LogoutView.as_view(next_page="index"))`（Django 內建、POST + CSRF）；profile.html 底部操作區新增登出 form（確認對話框）+ `.profile-logout-btn` 金色系樣式（profile.css，與品牌一致、與紅色刪除帳戶區分）；登出後回首頁 `/`
- **驗證**：profile 含按鈕 + `action=/profile/logout/`；POST logout → 302 `/`；登出後訪 profile → 302 登入頁

### 2026-08-15：coffee 自訂選項組功能（16 組）+ Admin 排序/UI 合併 + 顯示修復 🛠 ✅

- **功能**：每種咖啡在 Admin 勾選啟用「自訂選項組」（16 組：杯量/濃度/奶量/奶類/焦糖/黃油/椰奶/香草/特調/烏龍/茉莉/抹茶/綠茶/焙茶/面層配料/配豆），詳情頁依排序渲染供客戶選擇（單選、點擊清除、last-order 預選、杯量含 oz/icon 特殊結構、兩行布局）
- **資料流**：add_to_cart 收集 `option_<key>` → `extra_options`（依咖啡排序）→ cart key 含選項 → CartItem.options_json 同步 → 訂單 items.extra_options → `translate_option` → 各顯示端（order_confirm/checkout/fps/cash/order_history/滑出購物車/員工端 renderers）
- **模型/遷移**：`option_definitions.py`（16 組定義）、CoffeeItem +16 `option_*` toggles + 16 `option_order_*` 排序數字欄位、CartItem.options_json JSONField；Migrations 0058-0063（每支手動移除誤含 pickup_time）
- **Admin**：自訂選項組 UI 合併（OptionGroupConfigWidget 每組「勾選 + 排序數字」一行、option-group-config-grid）；後去除白色背景、邊框改深灰 #555
- **排序**：`sort_option_keys_for_coffee` helper（數字小在前、0=預設順序）；add_to_cart / cart_count API / `_add_chinese_options` 皆依咖啡排序（修正 PostgreSQL jsonb 重排 dict 順序問題）
- **顯示修復**：order_confirm/checkout 的 legacy fallback（杯量「中」/濃度「預設」/奶量「正常」硬編碼）移除；有 extra_options 只顯示新選項；`_add_chinese_options` 有選項時 pop legacy 欄位（舊訂單無選項保留 legacy 顯示）
- **preselect 修復**：詳情頁 query 預選（首頁復購連結）原只對匹配按鈕 `add('active')` 未清除同組其他按鈕 → default+query 同時已選（杯量「正常」+「追加」）；改 `toggle` 後 CDP 實測帶 query/無 query 每組皆恰 1 個 active
- **員工端 waiting 卡片修復**：`queue-manager.js renderWaitingOrderItems` 缺 `extra_options_cn` 顯示 → 等待中標籤卡片咖啡自訂選項（杯量/濃度/配豆）不顯示；補上迴圈（與 base renderer 一致）+ 重量改 `weight_cn` 優先（200克）；CDP 實測含杯量/配豆/濃度 + Kenya 研磨/重量正常
- **驗證**：verify_all_options.py（31 項）+ verify_cup_strength/bean_blend/milk_level/option_display/group_order 共 6 腳本全 PASS、`manage.py check` 0 issues

### 2026-08-15：coffee 詳情頁杯量 oz 標籤/文字加大 🎨 ✅

- **需求**：`/coffee/x/` 杯量按鈕右上角盎司標籤（`.bc-option-oz` 金色 chip）與盎司文字「相應加大」，含每個響應狀態處理；第二輪只加大標籤（padding）文字維持
- **修改**（bc-components.css + coffee.html inline，純 CSS）：
  - 桌面/平板（≥768px）：基底 `.bc-option-oz` font-size **0.72rem→0.85rem**（1280px ≈ 13.6px）、padding **4px8px→6px12px**（chip 56×26）
  - 行動端（≤767.98px）：font-size **8px→11px**、padding **5px10px**（chip 47×21）；`.product-details #cup-level-group .bc-option-oz` (1,2,0)!important 勝過 coffee.html inline (1,1,0)!important
  - `base.html` → `bc-components.css?v=20260814y`
- ✅ 驗證（CDP 1280/1024/768/375/320px）：全斷點 chip 右上角貼齊、按鈕內、無水平溢出、文字與內容零/輕微重疊

### 2026-08-15：全模板 HTML 結構/語法檢查 + 修正 + 冗餘清除 🧹 ✅

- **檢查**：59 個模板全部載入（get_template 55 成功、0 TemplateSyntaxError）+ 自訂 html.parser 堆疊檢查 + view/url/include/extends 使用追蹤（關鍵交叉巢狀案例用 headless Chromium 實測真實 DOM）
- **修正 8 項結構錯誤**：
  - `coffee.html` / `bean.html`：breadcrumbs `<p><span><a>` 缺 `</span>` → 補閉合
  - `base.html`：Material Icons link **重複 rel 屬性** → 移除
  - `fps_payment.html`：商戶名稱多餘 `</b>` → 移除
  - `order_confirm.html`：**`<form>` 交叉巢狀**（form 開於 col-xl-7 內、閉於 sidebar 後，實測 `#payment-button` 真實 DOM 在 `#payment-form` 外）→ 修正後 form 還原 col-xl-7 內 + sidebar button 用 HTML5 `form="payment-form"` 屬性關聯；後續使用者回報佈局回歸（flex 破壞）→ 已修復（col-xl-7/5 皆 row 子元素、寬度 58/42、`btn.form.id==='payment-form'`、圖示順序正確）
  - `index.html` / `landing_v3.html`：SVG `<clipPath>`/`<path>` 未閉合 → 補 `/>` + `</clipPath>`
  - `profile.html`：缺 1 個 `</div>`（container 未閉合）；`order_history.html`：缺 2 個 `</div>`（row+container 未閉合）
- **補建缺失模板**（view 已接線但檔案不存在，原 500）：`socialuser/reactivate.html`、`socialuser/activity_history.html`、`socialuser/points_summary.html`
- **刪除 15 個孤兒/死檔模板（git rm）**：`index_backup.html`、`landing_new.html`、`landing_v2.html`、`layouts/rightcorner_menu.html`、`layouts/box.html`、`layouts/content.html`、`admin/websocket_monitor.html`、`cart/templates/cart/cart_detail.html`、`eshop/.../queue_dashboard.html`、`queue_statistics.html`、`customer_queue_status.html`、`restaurant/templates/*`（4 個，app 已移除）
- **冗餘清除**：重複 `noise-filiter` SVG（index/landing_v3 各有副本，base 全域已有 → DOM 重複 id）、order_confirm debug 隱藏欄位去重、coffee_menu/bean_menu 卡片無用 `<form>`、nav.html hidden 死碼 -53 行（保留 `#bc-cart-toggle`）、base.html 註解掉的 rightcorner_menu include
- ✅ 驗證：get_template **47/47 成功**、html.parser 結構檢查歸零（僅餘條件式 group div 靜態誤判）、`manage.py check` 0 issues、全頁 HTTP 200、CDP 實測 order_confirm form/button 關聯 + 圖示順序 + 無溢出
- 模板數：**59 → 44**

### 2026-08-14（追加）：.cart-popup 響應式設計修復（bean/coffee 詳情頁加入購物車 Toast）🎨 ✅

- **問題**：`.cart-popup`（style-utilities.css，bean/coffee 詳情頁共用）只有容器寬度一層響應式（唯一 `@media ≤575.98px`）：
  - 🔴 手機 320/375px 商品資訊區（`.popup-product-info` flex-shrink:0 + max-width:260px）溢出被 `overflow:hidden` 裁切 → 名稱截斷、**價格/數量完全看不見**
  - 🔴 576~599.98px 斷層：media 只覆蓋 ≤575.98 → 576px 視窗時 popup min-width:600px 突出視窗 12px
  - 🔴 平板 576~991.98 維持桌面尺寸塞進 92vw → **整個 UI 太大不平衡**（使用者回饋）
  - 🟠 `.popup-product-price` 完全無 CSS 樣式
- **修復**（純 CSS，不改 HTML/JS）：
  - 全寬範圍 575.98 → **991.98px**（消除斷層）
  - **三層級響應式**：平板級（≤991.98：padding 12/20、gap 12、字體 14/18/14、img 40）+ 手機級（≤575.98：padding 10/12、字體 12/15/12、icon 34、img `display:none !important` 讓名稱空間）→ popup 高度 **56/65/88px** 三層和諧遞進
  - `.popup-product-info` 改 `flex:1 + min-width:0`（名稱 ellipsis 生效）
  - 補上 `.popup-product-price` base 樣式
- ✅ 驗證：CDP 量測 320~1280px × bean/coffee 全通過（無溢出/無裁切/無突出）；375px 名稱 88px（約 7 字）、價格/數量完整可見；平板 768px 543px 居中不再桌面尺寸；1280px 無回歸
- 版本：`style-utilities.css?v=20260814b`

### 2026-08-14（追加 2）：coffee_menu / bean_menu 平板端保留不對稱網格 🎨 ✅

- **問題**：`.bean-mix-*` 網格（兩頁共用）平板（768~1079.98px）降級為**對稱 2 欄**（大卡整行全寬 + 兩小卡並排）→ 失去桌面不對稱瀑布感，使用者要求平板仍用不對稱網格
- **修復**（bc-components.css，純 CSS）：
  - `≤1079.98px` 改為不對稱瀑布：`2fr 1fr`、大卡跨 2 行（`grid-row: 1/3` + 內容垂直置中）、兩小卡上下排
  - flip 組鏡像：`.bean-mix-flip { grid-template-columns: 1fr 2fr }`（原 flip 大卡落 1fr 小欄反了）
  - 圖片縮小加 **`!important`**（覆蓋桌面 340/280 的 !important）：大卡 `min(280px,100%)`、小卡 `min(200px,100%)`
- ✅ 驗證：CDP 768~1280px × 兩頁，平板全斷點大卡:小卡 = **2:1 不對稱**、flip 鏡像正確、小卡上下排、無溢出；桌面 1080+ 維持 340/280 無回歸
- 版本：`bc-components.css?v=20260814a`

### 2026-08-14（追加 3）：bean/coffee 詳情頁一般文字統一 #ccc + 建立 --bc-text-ccc 變數 🎨 ✅

- **問題**：詳情頁一般文字原有 **8+ 種顏色**（#eee/#adadad/#666/#aaa/rgb(108)/rgba(0.7)/橘黃價格/金 active），視覺雜亂
- **需求**：一般文字統一 #ccc、建立變數供後續引用；**品牌金（價格、active 狀態）保留**；咖啡/咖啡豆圖片顏色不更動
- **修復**（bc-components.css，純 CSS）：
  - `:root` 新增 **`--bc-text-ccc: #ccc`** 變數
  - 詳情頁一般文字全部設 `color: var(--bc-text-ccc)`：商品名（含 inner span，需同級覆寫 style-bootstrap `.product-details span{color:#eee}`）、描述、標籤、內容值 `.pl-3`、資訊圖示、烘焙選項（`:not(.bc-roast-active)` 排除 active）、表單標籤 `.form-group p`、數量輸入框
  - 保留品牌金：價格橘黃、選項按鈕、烘焙 active、oz、按鈕
- ✅ 驗證：CDP 掃描 bean/8 + coffee/8，一般文字全部 #ccc（bean 19 / coffee 14 個）、金色 8/7 個與價格橘黃保留
- 版本：`bc-components.css?v=20260814c`

### 2026-08-14（追加 4）：coffee_menu / bean_menu 行動端「大卡/小卡並排瀑布」佈局 🎨 ✅

- **需求演進**：行動端原本單欄堆疊 → 2 欄等大 + 錯落 → 「大卡全寬橫幅 + 小卡並排」→ **最終「大卡/小卡相同並排、大卡不需全寬、像桌面端處理方法」**
- **修復**（bc-components.css，純 CSS）：
  - 改寫 ≤767.98px：**大卡 2fr 跨 2 行**（內容垂直置中）+ **兩小卡 1fr 上下排**（與平板/桌面同構）
  - **組間 flip 鏡像**（`.bean-mix-flip { grid-template-columns: 1fr 2fr }` + 大卡 col2 / 小卡 col1）
  - **第二小卡 `translateY(1rem)` 微錯落**（`!important` 覆蓋 `.coffee-mix-grid` transform:none）
  - 尺寸縮小：大卡圖 `min(200px,100%)`、小卡圖 `min(130px,100%)`、小卡文字 12/11px；描述隱藏保留
  - **平衡調整（追加）**：比例 2fr 1fr → **`1.5fr 1fr`**（flip `1fr 1.5fr`）、大卡圖 180 → 375px 大卡 **187**（原 208）/小卡 **125**（原 104），比例 2:1→**1.5:1** 更平衡；**名稱 19.4→13px、價格 15→12px**（大小卡統一，高 specificity 覆蓋）
  - **按鈕統一 + 錯落加大（追加 2）**：大小卡按鈕**固定相同寬度 96px**（字體 12px、padding 6px 12px）；第二小卡錯落 `translateY(1rem→2rem) !important` 階梯感更明顯
  - **按鈕居中修復（追加 3）**：按鈕 `display:block` 不受 text-align:center 影響 → 靠左偏（大卡 45px）；加 `margin: 0 auto` 強制居中 → CDP 驗證 btnCx=cardCx 完全對稱
  - **平衡微調（追加 4）**：大卡照片 `min(180→150px,100%)`、大小卡間距 gap `1rem→0.5rem`（8px 更緊湊）——375px 大卡圖 150、間距 7-8px
  - **平衡微調（追加 5）**：大卡圖 `150→130px`、小卡圖 `130→110px`、間距 `0.5rem→0.25rem`（4px）
  - **三端錯落加大（追加 6）**：行動端 `2rem→3rem`、平板 `none→2rem !important`、桌面 bean `4rem→5rem`/coffee `-6rem→-7rem`
  - **同行橫向錯落（追加 7）**：小卡1 內容 `margin-top` 12px（行動端）/24px（平板、桌面）——與大卡頂部錯開
- ✅ 驗證：CDP 320~1280px × 兩頁，行動端大卡 1.5fr 並排（375px 187px）、小卡 1fr（125px）、flip 鏡像正確、名稱/價格 13/12px 縮小生效、**按鈕大小卡 96px 一致且居中**、**三端錯落加大（行動 44/平板 32/桌面 80px + 同行橫向 12/24px）**、大卡圖 130px/間距 4px、無溢出；平板/桌面無回歸
- 版本：`bc-components.css?v=20260814s`

### 2026-08-14（追加 5）：咖啡/咖啡豆 highlight 亮點標語（菜單卡片名稱下方）🎨 ✅

- **需求**：添加咖啡/咖啡豆 highlight 中文亮點（12-15 字），顯示在 coffee_menu / bean_menu 卡片名稱下方
- **實作**：
  - 模型：`CoffeeItem`/`BeanItem` 加 `highlight` 欄位 + **Migration 0057**（移除誤含的 ordermodel.pickup_time——DB 已存在，既有 model/migration 不同步）
  - 文案：8 咖啡 + 6 咖啡豆依特性填寫 12-15 字中文（shell 依 name 更新）
  - Admin list_display/search_fields/fieldsets 加 highlight；模板名稱 `<h5>` 下方加 `.bc-menu-highlight`
  - CSS：品牌金 12px（行動端 11px），覆蓋 style-bootstrap `.menu-wrap p`（16px/#ccc/line-clamp 截斷）
  - **單行 + 響應式修正（追加）**：重新建立精簡文案（12-15→8-9 字）；CSS 加 nowrap+ellipsis → 行動端單行；三級響應式字體（行動端 11 / 平板 16 / 桌面 18px + **font-weight 500**——使用者指定 600→500）
- ✅ 驗證：test client（8+6 highlight、200）+ CDP 320~1280px（belowName、品牌金 #c49b63、字體 11/16/18px、全斷點單行、無溢出）
- 版本：`bc-components.css?v=20260814o`

### 2026-08-14（追加 6）：bean/coffee 詳情頁隱藏右側 Buy & Order 按鈕 🎨 ✅

- **需求**：詳情頁無需顯示右側懸浮按鈕（Buy & Order）；**保留**懸浮購物車按鈕與右側虛線（使用者指定）
- **實作**：bean.html / coffee.html 頁面級 style `.bc-attract-nav { display: none !important }`（不隱藏 .bc-floating-cart 與 #borders）
- ✅ 驗證：CDP 375/1280px，詳情頁 Buy & Order=none、虛線/浮動購物車保留；coffee_menu 對照 flex 正常

### 2026-08-14（追加 7）：首頁 .mid-banner 響應式 🎨 ✅

- **問題**：`.mid-banner` 全固定值（min-height 620px/span 48px/lg_message 6em）無響應式，手機 620px 高、84px 文字，375px 寬度 423px 溢出
- **修復**（style-custom.css）：三級響應式——手機 ≤575.98（300px/28px/2.6em）、平板 ≤991.98（460px/40px/4.5em）、桌面維持；加 max-width:100%
- ✅ 驗證：CDP 320~1280px，320px 寬 242 不再溢出、全斷點 hScroll=False、桌面無回歸
- **行距加大（追加）**：`.lg_message` line-height 0.8→1.15（手機 42px/桌面 97px）；`style-custom.css?v=20260814b`

### 2026-08-14（追加 8）：菜單頁隱藏右側 Buy & Order 按鈕 🎨 ✅

- **需求**：bean_menu / coffee_menu 無需顯示右側 Buy & Order（coffee_menu 自指冗餘、bean_menu nav 可替代）；保留懸浮購物車與虛線
- **實作**：兩菜單頁頁面級 style `.bc-attract-nav { display: none !important }`（與詳情頁一致）
- ✅ 驗證：CDP 375/1280px，兩頁 Buy & Order=none、虛線/浮動購物車保留

### 2026-08-14（追加 9）：浮動購物車初始載入靜默顯示（修正每次跳轉彈出）🛠 ✅

- **問題**：購物車有商品時每次頁面跳轉浮動購物車滑入彈出一次（視覺幹擾）
- **根因**：`_syncBadgeFromServer` 被呼叫兩次（constructor + rAF），第二次移除 no-anim → 動畫觸發
- **修復**：JS 傳 animated 參數（初始 false 加 `.no-anim`）+ `_initialBadgeSync` 延遲 500ms 切換；CSS `.bc-floating-cart.no-anim.show { animation: none }`
- ✅ 驗證：CDP 真實 session（有商品），三頁載入皆 `no-anim`+`animation:none`；加入購物車路徑維持動畫
- 版本：`bc-components.css?v=20260814u`、`bc-slideout-cart.js?v=20260814b`

### 2026-08-14（追加 10）：完全移除滑入動畫 + 伺服器端初始渲染 🎨 ✅

- **需求**：加入購物車時的滑入動畫也是視覺幹擾 → 完全移除；數量增減維持顯示；切換頁面不閃出
- **修復**：CSS `.bc-floating-cart.show/hide` 改 `animation: none`；base.html 浮動購物車伺服器端渲染（`{% if not cart_count %}` + badge `{{ cart_count }}`）→ 有商品載入即顯示無閃出
- ✅ 驗證：CDP 無商品 none、有商品兩頁 block+animation:none、模擬加入後 animation:none
- 版本：`bc-components.css?v=20260814v`

### 2026-08-14（追加 11）：數量徽章文字閃爍修復 🛠 ✅

- **問題**：浮動購物車數量徽章文字閃爍
- **根因**：徽章用 webfont（Noto Sans TC）字體載入延遲（FOUT）；`_updateBadge` 相同值仍重設 textContent 觸發重繪
- **修復**：徽章 `font-family: Arial`（數字立即渲染）；`_updateBadge` 值相同不重設
- ✅ 驗證：CDP 徽章 font=Arial、animation=none、更新正常
- 版本：`bc-components.css?v=20260814w`、`bc-slideout-cart.js?v=20260814c`

### 2026-08-14（追加 12）：右側虛線加深灰色 🎨 ✅

- 全域右側點線 `#borders .bc-borders__right` 背景改 **`rgba(128,128,128,0.6)`**（原白 `rgba(255,255,255,0.5)`）
- 版本：`bc-attract.css?v=20260814a`

### 2026-08-13（追加 3）：首頁 bc-welcome-panel 最後訂單連結咖啡豆選項修復 🛠 ✅

- **問題**：首頁「按照之前口味落單?」連結（`.bc-welcome-img-link`）本應記錄客戶上次訂單的咖啡與咖啡豆選項，但咖啡豆部分失效：
  - 後端 `_get_last_order_link()`（views.py）只處理 `cup_level`/`milk_level`/`strength_level` 三個咖啡選項；咖啡豆訂單 item 中這三個 key 皆為 `null` → 連結退化成 `/bean/{id}/`，上次的重量/研磨度選項被丟棄
  - 前端 `bean.html` 完全沒有 query 預選 JS（coffee.html 有、bean 沒有）→ 即使帶 query 也不會預選
- **修復**：
  - `views.py` `_get_last_order_link()`：依商品類型分流 → 咖啡豆（bean）取 `weight` + `grinding_level`；咖啡維持 cup/milk/strength
  - `bean.html`：DOMContentLoaded 內新增 `preselectLastOrderOptions`（與 coffee.html 同風格）→ 讀取 `weight`→`#weight-group`、`grinding_level`→`#grinding-group`，同步 active 按鈕 + hidden input；重量預選後 `updatePriceDisplay()` 同步價格
- ✅ 驗證：Django test client（真實 coffee `/coffee/8/?cup_level=Medium&milk_level=Medium&strength_level=Normal`、模擬 bean `/bean/8/?weight=500g&grinding_level=Medium`、無選項 `/bean/3/`）+ CDP 真實瀏覽器（bean 500g/Medium/$119 預選、無 query 對照 200g/Non/$59、coffee 回歸正常）

### 2026-08-13（追加 4）：bc-welcome-panel 行動端文字錯亂 + bc-search hover 動畫反應慢 修復 🛠 ✅

- **bc-welcome-panel 行動端文字錯亂**（CDP 375px 登入量測）：文字區僅 126px 寬（imgbox 94px + avatar 44px + gaps 擠壓）→ greeting「歡迎回來!fb_kei, 喝返杯先~~」與 points「當前積分可減免 -5 訂單及帳戶詳情」被迫換行 2 行、字體縮至 10px
  - 修復（bc-components.css ≤768/≤480）：text gap 18→10px、avatar 51→38px、imgbox 119→62px、img 83→58px、greeting 10→11px、`.bc-welcome-info` 加 `flex:1` → 文字區 **126→173px**，greeting/points **單行**完整顯示
  - ✅ 驗證：375px 單行無錯亂；768/1280px 無回歸
- **bc-search hover 動畫反應慢**（CDP 追蹤）：
  - 快速 hover 進出時 `is-on`+`is-out` 同時存在 → CSS is-out 後定義勝出 → hover 中背景圖反向移出
  - `hide()` 的 1500ms setTimeout 強制移除 `is-on` → 長時間 hover 圖會消失
  - 進入動畫 250ms delay + 1000ms = 1.25s 才完成
  - 修復：`bc-search.js` show() 取消 pending hideTimer + 移除 is-out、hide() 移除 is-on（計時器可取消）；`bc-search.css` 動畫縮短（1000→700ms、delay 250→120ms）
  - ✅ 驗證：進入動畫 **0.7s 完成**；長時間 hover is-on 保持；快速進出無 class 衝突
- 版本：`bc-components.css?v=20260813ba`、`bc-search.css/js?v=20260813a`


### 2026-08-13（追加 5）：coffee_menu 咖啡產品區域改為 A+C 混合不對稱網格（方案 A）🎨 ✅

- **需求**：coffee_menu 產品區域參考 bean_menu 的不對稱網格（`.bean-mix-grid`），改掉原本的 Z 字對角 2×2（`.coffee-menu-zgrid`）
- **方案比較與迭代**：提供 3 種方案（A：A+C 混合翻轉=bean 樣式／B：跨欄瀑布=首頁 asymmetric-grid-v1 樣式／C：雙瀑布階梯）
  1. 先實作 **C**（`.coffee-duo-*`）→ 使用者不滿意
  2. 切換 **B**（`asymmetric-grid-v1`）→ 使用者不滿意
  3. 切換 **A**（與 bean_menu 完全一致）→ 定案 ✅
- **最終實作（方案 A，左右鏡像反轉）**：
  - `coffee_menu.html`：商品區改用 **`.bean-mix-*` 共用 class**（與 bean_menu 同一套佈局）→ 每 3 個一組（大 小 小）、組間 `.bean-mix-flip` 鏡像翻轉；**flip 判斷 `forloop.counter0|divisibleby:6`** → 組1 flip（大卡右）、組2 非 flip（大卡左）、組3 flip（大卡右），與 bean_menu 成左右鏡像；8 商品 = 3 組（組3 尾組 2 個）；卡片回歸 `menu-wrap` 結構
  - **錯落**：coffee_menu 第二張小卡改為**向上錯落**（`.coffee-mix-grid` wrapper 覆蓋 `translateY(-6rem)`），bean_menu 維持向下 4rem；小卡2 頂部與大卡底部重疊約 48px（浮上效果）；響應式與 bean-mix 一致
  - `base.html` → `bc-components.css?v=20260813bi`
  - **零新增 CSS**：完全複用 bean-mix 規則（1.7fr 1.15fr 1.15fr、大卡跨 2 欄 340px、小卡 280px、第二小卡 `translateY(4rem)`、三級響應式）→ 兩頁佈局 100% 一致
  - 清理死代碼：移除方案 C `.coffee-duo-*`（134 行）+ 舊 `.coffee-menu-zgrid`/`.coffee-z-*`（95 行）；保留 bean_menu 使用的 `.coffee-menu-desc`
  - `base.html` → `bc-components.css?v=20260813bc`
- ✅ 驗證：test client（3 組含 1 flip、3 main + 5 sub、8 商品、無 asymmetric/coffee-image-container 殘留）+ CDP 1280px（組1 大卡左 340px + 小卡右階梯 280px、組2 鏡像大卡右、組3 尾組 2 個）+ 1080/768/375px 無溢出、375px 單欄（`docs/verify/cdp_verify_coffee_beanmix.py`）；首頁/bean_menu/詳情頁無回歸


### 2026-08-13（追加 12）：bean 詳情頁烘焙水平 active 改金色 🎨 ✅

- **問題**：Roast level active 顯示灰色
- **根因**：`.roastrange-item span{color:#666}` specificity 勝過 `.bc-roast-active`（金色）
- **修復**：`.bc-roast-active` → `.roastrange-item span.bc-roast-active`（高 specificity）；active 圓點 `::before` 改 `--brand-primary`；`bc-components.css?v=20260813bm`
- ✅ 驗證（`docs/verify/cdp_verify_roast_active.py`）：bean/1 中浅、bean/2 中、bean/3 深 → 文字金色 rgb(196,155,99)+700、圓點金色；全頁 200


### 2026-08-13（追加 11）：付款頁 .payment-item-fps/cash 內聯 CSS 搬移 🛠 ✅

- **需求**：`.payment-item-fps` / `.payment-item-cash` 內聯 CSS 搬至 CSS 檔案
- **實作**：`bc-components.css` 新增 `.payment-item-fps, .payment-item-cash` 共用規則（與 .payment-list-simple 同風格）；fps/cash 模板移除內聯；`bc-components.css?v=20260813bl`
- ✅ 驗證（`docs/verify/cdp_verify_payment_item_style.py`）：computed style 與原內聯完全一致、inlineStyle null、無殘留、全頁 200


### 2026-08-13（追加 10）：FPS/Cash 付款頁按鈕樣式統一（參考 coffee_menu 落單）🎨 ✅

- **問題**：付款頁按鈕用 `calltoaction-btn`（固定 230×48）+ 返回灰色（btn-outline-secondary）→ 與 coffee_menu 落單（btn-primary outline、內容寬度、金色）不同
- **修改**：fps/cash 模板移除 calltoaction-btn/px-4 py-3；返回改 `btn-outline-primary`（金）+ 移除 inline 灰色 hover；`.bc-payment-actions` 移除固定寬（246/194）→ 內容寬度；`bc-components.css?v=20260813bk`
- ✅ 驗證（`docs/verify/cdp_compare_payment_buttons.py`）：FPS 主 184×45、返回 151×45 金；Cash 主 153×45、返回 151×45 金；全按鈕金邊金字 6px 圓角 45px 與 coffee_menu 一致；全頁 200 無回歸


### 2026-08-13（追加 9）：bean 詳情頁返回按鈕桌面端居中修復 🛠 ✅

- **問題**：bean/x/ 返回按鈕桌面端偏左（btnCenterVsFormCenter -193px）
- **根因**：bean.html 的 `.text-center.mt-3` 是 `.row`(flex) 直接子元素（無 coffee 的 w-100 包裝）→ flex item 寬=內容寬靠左；居中的 CSS 只在 ≤767.98px
- **修復**：bc-components.css 該規則改為全域（width:100% + flex center）；`bc-components.css?v=20260813bj`
- ✅ 驗證（`docs/verify/cdp_measure_return_btn.py`）：bean 1280 -193→0、375/coffee 維持 0；全頁 200 無回歸


### 2026-08-13（追加 8）：首頁 .feed 水平移動 SVG 蒙版動畫消失修復 🛠 ✅

- **問題**：首頁 `.feed`（branding Deco）水平移動 SVG 蒙版動畫消失
- **根因**：commit `7dad800`（CSS Phase 4 條件載入）把 `landing.css` 從 base.html 全域移除後，只在 landing_v3.html 加回，**漏加 index.html** → 首頁 .feed 失去 feedScroll 動畫樣式
- **修復**：`index.html` `{% block extra_css %}` 加載 `landing.css`
- ✅ 驗證（`docs/verify/cdp_verify_feed_animation.py`）：animation-name feedScroll（60s）、clip-path url(#mask)、transform 持續移動（-118→-199→-280px）


### 2026-08-13（追加 7）：首頁 Best Sell 咖啡卡片排序功能（hot_item_order）🛠 ✅

- **需求**：首頁 Best Sell 咖啡卡片允許管理員在 Django admin 自由排序
- **實作**：
  - `views.py`：`_build_landing_context` / `Index` 的 hot_coffees 查詢 → `.order_by("hot_item_order", "id")[:4]`（hot_item_order 欄位早已存在但從未使用）
  - `admin.py`：CoffeeItemAdmin `list_display` + `list_editable` 加 `hot_item_order`（與 menu 的 sort_order 獨立，互不干擾）
  - 零 migration（欄位已存在）
- ✅ 驗證：`tests/integration/test_home_hot_sort.py` 2 測試全過（Best Sell hot_item_order 升序前 4、非熱門不顯示、admin 有 form-N-hot_item_order）；首頁/menu/詳情頁無回歸


### 2026-08-13（追加 6）：Django 管理後台咖啡/咖啡豆卡片排序功能（方案 A：sort_order）🛠 ✅

- **需求**：管理員在 Django admin 自由修改咖啡/咖啡豆卡片排序，應用於 coffee_menu / bean_menu
- **實作**：
  - `shop_items.py`：CoffeeItem / BeanItem 加 `sort_order = PositiveIntegerField(default=0, verbose_name="菜單排序")`；**不設 Meta.ordering**（避免影響首頁 Best Sell / 搜尋）
  - `admin.py`：`list_display` + `list_editable` 加 `sort_order`（列表頁直接輸入數字即時儲存）
  - `views.py`：CoffeeMenu / BeanMenu / 搜尋視圖 → `order_by("sort_order", "id")`（id 次要排序，未設定維持現狀）
  - Migration 0056（手動移除 ordermodel.pickup_time AddField——DB 已存在，makemigrations 誤判）
- ✅ 驗證：`tests/integration/test_menu_sort_order.py` 4 測試全過（coffee/bean 頁面 sort_order 升序、全 0 維持 id 序、admin 有 form-N-sort_order 可編輯欄位）；首頁/詳情頁/admin 無回歸


### 2026-08-13：訂單流程行動端 UI 全面優化（order_confirm + payment-confirmation）🎨 ✅

- **payment-confirmation 行動端統一縮小**（bc-components.css + style-utilities.css）：
  - 修復狀態卡片被強制 25% 寬壓扁（62px 條狀 → **2 張一排 141px**）、二維碼溢出（250→170px）、提取碼 51→35px、標題/icon/摘要縮小
- **order_confirm 訂單詳情折疊面板**（全新 `.bc-order-collapse` 元件）：
  - 移除舊 Rtable/Accordion 結構（解決雙綁定點擊無效、寬度錯位）
  - **預設關閉**、「訂單詳情」+ 向下箭頭點擊展開；vanilla JS 切換（不依賴 jQuery）
  - 容器與表單 `container > row > col-12` 同 gutter 對齊；無框簡潔樣式
  - 內容縮小（商品名 0.88rem、價格 0.9rem、選項 0.72rem）+ 行距縮小 + 圖示與文字水平中心對齊；照片 70×70 contain 居中
  - meta `flex-wrap: wrap` 窄屏換行；圖片/箭頭/radio/按鈕多輪縮小與對齊
- **伺服器層防快取**：`order_views.py` `OrderConfirm`/`order_payment_confirmation` 加 `never_cache` → 訂單頁不再被瀏覽器快取（解決「行動端看不到新版」問題）
- **主因排除**：Django test client + CDP 多寬度掃描證實伺服器渲染正常，使用者問題為瀏覽器快取舊版
- ✅ 驗證：CDP 320~1280px 全寬度無溢出、功能正常；test client 結構完整
- 版本：`bc-components.css?v=20260813aa`、`style-utilities.css?v=20260813a`

### 2026-08-13（追加）：訂單流程頁懸浮元素 + 警告卡 + 付款頁響應式 🎨 ✅

- **訂單流程頁隱藏懸浮元素**：order_confirm / payment-confirmation 頁面級 style 隱藏 `.bc-attract-nav`（右側 Buy & Order）、`.bc-floating-cart`（懸浮購物車）、`#borders`（右側虛線）；其他頁面不受影響
- **pending-order-warning-card 重構**：內聯 CSS 搬移至 bc-components.css（`.pending-order-warning-*` 16 個 class）、hover 改 CSS、移除死碼 pendingPulse；行動端內容多輪縮小（標題 0.85rem/副標題 0.7rem/價格徽章倒數按鈕 0.72rem/icon 26px）；按鈕圖示與文字水平中心對齊
- **倒數計時器徽章**：行動端排列「資訊區第一行 → 待支付徽章（含倒數）第二行靠左 → 與按鈕同行（徽章左、按鈕右）」；警告卡行動端插到訂單詳情上方（matchMedia 判斷）
- **訂單詳情 header**：總價加「總計:」前綴、向下箭頭改白色；「確認並支付」按鈕改容器寬度（100%）
- **桌面支付方式**：文字加大至 1rem、圖示與文字水平中心對齊
- **FPS/Cash 付款頁行動端響應式**（原無自訂調整）：卡片 padding 1.25rem、FPS logo 72px、現金 icon 42px、總金額 1.5rem、標題 1rem、二維碼 `min(200px, 85%)`（修復溢出）、商品圖 70px、付款說明 1rem、按鈕 0.9rem
- ✅ 驗證：375px 全縮小無溢出；1280px 桌面無回歸
- 最終版本：`bc-components.css?v=20260813at`

### 2026-08-13（追加 2）：付款頁/員工頁懸浮元素 + 漢堡對齊 + 商品明細統一 🎨 ✅

- **FPS/Cash 付款頁 + 員工管理頁隱藏懸浮元素**：三個頁面加頁面級 style 隱藏 `.bc-attract-nav`/`.bc-floating-cart`/`#borders`；懸浮購物車在員工頁原已由 JS 排除，CSS 再加一層
- **漢堡選單與右側虛線中心對齊**（bc-attract.css ≤767.98px）：`.bc-attract-menu { left: 8px }`；320/375/414px 偏差 ≤1px
- **payment-confirmation 商品明細與 order_confirm 訂單詳情一致**：商品名 0.88rem（`!important` 覆蓋 `.mb-1.text-white`）、價格 0.9rem、數量 0.8rem、單價/選項 0.72rem、圖片 70px、間距 8/4px；選項 icon 0.8rem `!important`（覆蓋全域 0.9rem `!important`）
- **商品明細選項單行顯示**：`.bc-options-row { flex-wrap: nowrap; font-size: 0.65rem; icon 0.7rem; gap 3px }` → 三選項一行、不溢出
- **移除價格「HK$」**：`|cut:"HK$"` 模板 filter
- ✅ 驗證：coffee/bean 商品顯示一致、選項單行完整、各斷點無溢出
- 最終版本：`bc-components.css?v=20260813ay`、`bc-attract.css?v=20260813a`

### 2026-08-11：CSS 全域審計 + 清理重構（Phase 1-3）✅

- **Phase 1（診斷腳本）**：新增 `scripts/audit_css_references.py`（掃描所有 `*/templates` 的 CSS 引用、標記死資產/重複/條件載入、輸出 `docs/css_audit_report.md`）
- **Phase 2（清理死資產）**：刪除 animate.css、bootstrap.min.css、dist-aggressive/、bootstrap/、css/ 子目錄、fontawesome/all.min.css 等 → **移除 1288KB**
- **Phase 3（合併精簡）**：移除 Font Awesome CDN 雙載入（保留本地 all.css）、移除未用圖示字型 ionicons/open-iconic/flaticon、移除無 data-aos 的 aos.css、blobs.css 條件載入（僅首頁/landing）→ **移除 81KB + 條件化 33KB**
- **修復**：profile.css/loyalty-table.css 被誤刪（審計腳本遺漏 app templates）→ git 恢復 + 腳本改掃所有 templates；移除 member-nav.css 死引用
- ✅ 驗證：審計死資產 0、CDP 首頁/菜單/詳情/profile/loyalty 無 404 無溢出
- ⚠️ 教訓：審計腳本需涵蓋所有 app templates 目錄

### 2026-08-11：首頁 bc-welcome-panel 桌面端崩潰修復（@media 未閉合）🚨 ✅

- **現象**：首頁桌面端 bc-welcome-panel 變滿寬 block（w=1265/h=1201/img 860×1100）、所有 bc-welcome-* 樣式失效
- **根因**：`.product-details .w-100.form-group` 規則的閉合 `}` 被註解（`/* margin-right: 15px;\n} */`）→ `@media (max-width: 767.98px)`（bc-components.css 2405）**未閉合** → 吞掉後續全部規則（含 .bc-welcome-panel 2883）→ 桌面 1280 不匹配 media → 樣式全失效
- **修復**：恢復 `.w-100.form-group` 正常結構（margin-left/right: 15px + 閉合 `}`）；CSSOM 驗證規則回到 (none)、規則總數 357→521
- **✅ 驗證**（CDP）：panel **599×106 flex**、avatar 50×50、imgbox 160×82、無溢出

### 2026-08-11：詳情頁行動端 UI 整體縮小與對齊（多輪調整）✅

- **需求**：coffee/bean 詳情頁行動端整個 UI 太大不平衡（文字、圖示、按鈕），且多處未對齊
- **實作**（bc-components.css 新增 `@media ≤767.98px` 區塊）：
  - 文字：名稱 20、價格 17、描述/資訊 13、表單標籤 13px（多輪縮小）
  - 按鈕：選項/數量/購買 36px、杯量 44px（含 oz+icon+label 三層）、返回 32px；文字 10px、圖示 11/8px
  - 對齊：標籤文字與按鈕文字水平中心對齊（覆蓋 label `align-self: flex-end` → center）；數量行與選項行左對齊（w-100.form-group margin 15px）；navbar logo/漢堡中心點對齊（brand padding-top 8→4px）；bean 返回按鈕居中（.text-center flex）
  - Footer 響應式：跑馬燈 14px/max-content 單行、social 圖示 34px、文字 13/12px
- **⚠️ 教訓**：覆蓋 style-bootstrap 需 `.product-details` 前綴提高 specificity；Bootstrap .px-4/.py-3 帶 !important；coffee.html inline `<style>` 的 id 選擇器需 (1,2,0)!important 才能覆蓋

### 2026-08-11：sticker-box 重構（容器塌陷 + clamp 響應式 + 名稱右側）✅

- **問題**：詳情頁 sticker-box 容器塌陷（h=0）、冗餘背景圖、無響應式、位置錯亂
- **實作**（style-custom.css）：
  - 容器 `clamp(109px, 28.16vw, 208px)`（行動端自動縮小、桌面 208px），移除 transform scale（transform 不改 layout、會使 background-size:contain 計算錯誤）
  - `.sticker .bg` 加 `background-size: contain`（手機縮放時隨容器縮小）
  - HTML 移入名稱 `.block-23` 內、absolute 錨定名稱右側（top:-124/right:-50）
  - 內部文字響應式 class：`.bc-sticker-text`（10-20px）、`.bc-sticker-text-sub`（7-14px）

### 2026-08-11：bc-welcome-panel avatar +10% + 積分 -5 金色粗體 ✅

- avatar 桌面 45→50px、≤768 46→51px、≤480 40→44px（+10%，icon 隨比例）；容器高度保持 106/85/70px
- 積分「-5」包 `<strong class="bc-welcome-discount">`（金色粗體）；連結間距 4→16px

### 2026-08-11：home-slider 橫幅停留 7→10 秒 + coffee_border_02 +5% ✅

- main.js `autoplayTimeout: 7000→10000`（每張橫幅 10 秒）；`?v=20260811b`
- 首頁第 1 個 slider 的 coffee_border_02.svg `.noise-img` 各斷點 ×1.05（桌面 383→402px、手機維持 92vw cap）；`style-utilities.css?v=20260811c`

### 2026-08-11：bean_menu 不對稱網格小卡組加大 + 描述平衡 + 文字加大 ✅

- 小卡組：grid `2fr 1fr 1fr`→`1.7fr 1.15fr 1.15fr`、小卡圖 260→280px（組 1 不再被壓縮）
- 描述平衡：小卡 max-width 100%（+padding 4px）、大卡 55%（差距 353→131px）
- 文字：名稱 lg→xl、價格 md→lg、描述 md→base；⚠️ 教訓：responsive-system 描述規則 (0,3,0) 需 `.menu-wrap` 前綴 (0,4,0) 才覆蓋

### 2026-08-11：詳情頁照片行動端縮小 + 直向圖限高 ✅

- 照片行動端 max-width 70%（91%→64%），媒體範圍 ≤767.98px
- coffee 直向圖（860×1100）過高 → `max-height`：手機 56vw（218px）、平板 600px、桌面 516px（各斷點 = bean 方形圖高度）
- coffee/4 圖片 404 修復（DB 指向 black_blend_Rcu39Op.png 不存在 → 更新為 black_blend.png）

### 2026-08-11：背景文字 SERVED FRESH 字距響應式 ✅

- `letter-spacing: -10px`（固定）在行動端 78px 字體 = -12.8% 文字重疊 → 改 `-0.04em`（em 相對字體）；行動端再改 0.05em（正值，分散開）
- 影響 .title-bg-head 系列 + .bc-section-with-bg-text::before（BREWED FAST 等同步受益）

### 2026-08-11：詳情頁資訊圖示顏色 ✅

- `.product-details .block-23 ul li .icon { color: rgb(108, 108, 108) }`（使用者需求，按鈕內圖示除外）

### 2026-08-10：/accounts/login/ deco_01.svg 抖動修復（追加：Stellar 視差）✅

- **抖動**：login.html deco_01 背景移除 `noise_animation` class（噪點 filter 動畫）→ 靜態
- **追加**：仍抖動 → 根因 **Stellar.js 視差**（`data-stellar-background-ratio="0.73"` 觸發 `parallaxBackgrounds`）→ 移除該屬性
- **白色**：deco_01.svg `.st1/.st2` stroke `#000→#ffffff`、根 svg `fill:#ffffff` → 深色背景可見
- **✅ 驗證**：CDP `stable: true`（background-position/left 恆定、animation none）；SVG 無 #000 殘留

### 2026-08-10：bc-welcome-greeting 登入後文案與字重調整 ✅

- **需求**：`歡迎回來 (username) , 喝返杯先!`；字重 歡迎回來(300)/username(400)/尾(300)
- **實作**：index.html 拆三 span（bc-greet-normal×2 + bc-greet-user）；bc-components.css 設定 300/400；`base.html` → `bc-components.css?v=20260810x`
- **追加**：歡迎回來 與 username 之間間距 → bc-greet-user `margin-left: 6px`、移除前導空格；`?v=20260810y`
- **追加2**：文案 `歡迎回來!`（驚嘆號）與 `, 喝返杯先~~`（!→~~）
- **✅ 驗證**（test client）：文案格式正確、Hey 已移除、username 內容無前導空格

### 2026-08-10：bc-welcome-panel 容器寬度 -5% ✅

- **需求**：容器寬度 -5%（澄清：非 -15%）
- **實作**：桌面 630→**599px**、平板 92→**87%**、手機 96→**91%**（×0.95）；`base.html` → `bc-components.css?v=20260810w`
- **✅ 驗證**（CDP）：寬度 599/633/305px（約 -5%）；高度 106/85/70 保持、其他不受影響

### 2026-08-10：bc-welcome 登入後顯示 username + 積分連結 ✅

- **需求**：greeting 顯示 `Hey, (username) 歡迎回來, 喝返杯先!`；積分文字 `當前積分可以減免 -5 訂單及帳戶詳情`（連結）
- **實作**：index.html greeting 加 `{{ user.username }}`；points 加 `bc-welcome-link`（→ `socialuser:profile`）；bc-components.css 新增連結樣式（金色下底線）
- `base.html` → `bc-components.css?v=20260810u`
- **✅ 驗證**（test client 登入 kei）：username 顯示、積分文字、連結 `/profile/`、Buddy 登入後消失

### 2026-08-10：/accounts/login/ deco_01.svg 抖動修復 + 改白色 ✅

- **抖動**：login.html deco_01 背景移除 `noise_animation` class（噪點 filter 動畫）→ 靜態
- **白色**：deco_01.svg `.st1/.st2` stroke `#000→#ffffff`、根 svg `fill:#ffffff` → 深色背景可見
- **✅ 驗證**：SVG 無 #000 殘留；login deco_01 無 noise_animation；signup 同步受益

### 2026-08-10：bc-welcome-imgbox 圖片與 last-order 文字水平對齊修復 ✅

- **需求（澄清）**：圖片與 `.bc-last-order` 文字的對齊（非容器垂直位置）
- **問題**：圖片 `right: 0` 靠右 → 中心偏右（桌面 12px、手機 6px）；文字居中 → 水平不對齊
- **修復**：`.bc-welcome-img`/`.bc-welcome-img-link` 改 `left:50% + translateX(-50%)`（水平居中）；`base.html` → `bc-components.css?v=20260810t`
- **✅ 驗證**（CDP）：centerX_diff = 0（圖片中心 = 文字中心，全部斷點）

### 2026-08-10：bc-welcome-panel avatar +15%、文字加大、容器高度保持 ✅

- **需求**：avatar +15%、greeting/points 文字加大、**容器高度保持**（106/85/70）
- **實作**：avatar 39→45 / 40→46 / 35→40px（+15%，icon 隨之 1.8/1.5/1.25rem）；greeting 16/15/10px、points 15/14/10px
- **高度保持原理**：容器高由 imgbox（82/73/60）決定，左側內容（avatar+文字 ~50px）皆小於 imgbox → 不撐高
- `base.html` → `bc-components.css?v=20260810r`
- **✅ 驗證**（CDP）：容器高度 106/85/70 保持、avatar 45/46/40、文字 16/15、15/14、10/10

### 2026-08-10：全域文字穩定修復（`<html>` inline font-size clamp + 審計腳本）✅

- **審計**：`scripts/audit_text_stability.py`（可直接執行）——全域 339 個 rem font-size（11 檔案）、檢查 base.html 標記、HTTP 渲染 7 個主要頁面
- **修復**：`<html>` 加 inline `style="font-size: clamp(14px, 0.3vw+13.5px, 16px)"` → HTML 解析即設定基準，所有 rem 載入即穩定（不依賴 CSS 順序、保留響應式縮放）；清理 display=swap 死碼註解
- **✅ 審計結果**：全部通過（html inline + display=block + 無 swap 殘留 + 7 頁面渲染）

### 2026-08-10：文字抖動最終修復（Google Fonts display=block 消除 FOUT）✅

- **問題**：px 化後仍輕微抖動、bc-search-txt 也抖 → **根因 FOUT**（`display=swap` 字體交換時字寬變化）
- **修復**：base.html Google Fonts `display=swap` → `display=block`（字體載入前隱藏、載入後顯示 → 無交換抖動）
- **取捨**：首次載入字體前文字短暫空白；之後快取即時顯示
- ✅ 驗證：渲染 HTML 含 `display=block`

### 2026-08-10：bc-welcome-greeting/points 文字大小抖動修復（rem → 固定 px）✅

- **問題**：greeting/points 初始狀態文字大小抖動 → 根因 rem 單位依賴 `responsive-system.css` 的 `html { font-size: clamp() }`（最後載入覆蓋基準 → rem 重新計算跳變）
- **回答**：CSS 順序有影響（html clamp 後載入）；**!important 無法解決**（擋不住 html font-size 對 rem 的影響）
- **修復**：改固定 px（桌面 14/13、≤768 13/12、≤480 8/8）；`base.html` → `bc-components.css?v=20260810q`
- **⚠️ 若仍抖動**：可能是字體載入 FOUT（display=swap 交換 fallback）

### 2026-08-10：bc-welcome-greeting/points 縮放動畫（加入後移除）✅

- **曾實作**：greeting/points 初始縮小→放大（`transform: scale(0.5→1)`+opacity，不需 !important，順序放系列後，0.6s ease both）
- **移除**：使用者指示「不需要動畫」→ 刪除 `bcWelcomePop` 規則（無殘留）；`base.html` → `bc-components.css?v=20260810p`

### 2026-08-10：隱藏導航選單「登入」✅

- **需求**：隱藏導航選單中的「登入」
- **實作**：`nav.html` 未登入狀態的「登入」dropdown-item 加 `hidden`（與註冊一致）
- **✅ 驗證**：渲染 `<a hidden class="dropdown-item" href="/accounts/login/">`；bc-welcome-panel 登入連結保留

### 2026-08-10：bc-welcome-panel 整體高度降低 15% ✅

- **需求**：`.bc-welcome-panel` 整體高度降低 15%
- **實作**：`bc-components.css` 各斷點高度元素等比縮小 ×0.85（padding/avatar/info gap/文字/imgbox/img/img-link）
- `base.html` → `bc-components.css?v=20260810n`
- **✅ 驗證**（CDP 量測）：桌面 125→**106px**（-15.2%）、平板 100→**85px**（-15%）、手機 82→**70px**（-14.6%）

### 2026-08-10：首頁第 3 個 slider 影片更改為 coffee_machine.webm ✅

- **需求**：第 3 個輪播橫幅內影片更改為 `coffee_machine`（mp4 → 最終 **webm**）
- **實作**：`index.html` 第 3 格 `<source>` → `{% static 'images/coffee_machine.webm' %}` type="video/webm"（8.3MB、時長 20.4s）
- **✅ 驗證**（CDP）：`currentSrc: coffee_machine.webm`、`readyState: 4`、`video_error: null`、時長 20.4s

### 2026-08-10：bc-marquee 閃出修復（循環 buffer 取代模循環）✅

- **問題**：「第1段結尾有間隙、第2段閃出接1段」→ 模循環 `x += itemW` 跳變時「• 」前綴閃失
- **修復**（`bc-marquee.js` v2）：循環 buffer——item1 完全移出視窗時 `appendChild` 移到尾端 + `x += itemW` 補償 → track 成環形、視窗內容任意時刻連續；確保 ≥3 item
- `base.html` → `bc-marquee.js?v=20260810b`
- **✅ 驗證**（CDP）：`continuous: true`（buffer 前後視窗內容一致）、transform 整數無跳變

### 2026-08-10：bc-marquee 抖動終極修復（JS rAF 整數像素驅動）✅

- **問題**：CSS animation 線性插值非整數位移 → 文字子像素渲染 → 仍見「一段接一段」抖動
- **終極方案**：新增 `static/js/bc-marquee.js`——JS rAF 每幀位移累積 + `Math.round` 整數像素（物理不抖）+ 模循環（連續變數無縫）；`resize`/`fonts.ready` 重算；reduced-motion 停用；CSS animation 為無 JS fallback
- `base.html` → `bc-marquee.js?v=20260810a` + `bc-components.css?v=20260810m`
- **✅ 驗證**（CDP）：JS 接管（animation none）、位移全部整數（-82,-83,-84...）、步進均勻 -1px、模循環無跳變

### 2026-08-10：bc-marquee 抖動跳動修復（移除 letter-spacing + will-change）✅

- **問題**：跑馬燈「抖動跳動、一段接一段」→ 根因 `letter-spacing: 0.5px`（亞像素字距累積）+ `will-change: transform`（合成層子像素抖動）+ `inline-flex` sub-pixel 間隙
- **修正**：移除 letter-spacing、移除 will-change、track 改 `display: flex + width: fit-content`（與 footer scroller 一致）
- `base.html` → `bc-components.css?v=20260810l`
- **✅ 驗證**（CDP）：`letter_spacing: normal`、`will_change: auto`、手機 item 完全等寬；4 次取樣位移完全均勻（每 800ms -16.4px）、`monotonic: true` 無跳動

### 2026-08-10：bc-marquee 無縫無限循環修正（移除 item padding）✅

- **問題**：跑馬燈「斷開連接、文字間斷」→ 根因 `.bc-marquee__item` 的 `padding-inline: 0.5rem` 造成接縫 1rem 空白
- **修正**：移除 item padding；HTML 內容統一 `&nbsp;` 間距；無縫保證 = 2 item 等寬 + track 2×item + gap 0 + `translateX(-50%)`
- `base.html` → `bc-components.css?v=20260810k`
- **✅ 驗證**（CDP 1280/375px）：item 等寬、接縫 gap 0、padding 0px、動畫連續位移（-74→-128）無跳動

### 2026-08-10：bean_menu banner 跑馬燈換新（移除 .scroller-box → 自訂 .bc-marquee）✅

- **需求**：移除 banner 內 .scroller-box，相同位置新增水平跑馬燈（使用者選 **Mogra 品牌字 20px、右→左、精簡 padding**）
- **實作**：`bean_menu.html` 換 `.bc-marquee`；`bc-components.css` 新增 `.bc-marquee` 系列（Mogra 20px、`bcMarqueeScroll 28s` 右→左無縫、`padding-block 0.75rem`、純 CSS 不依賴 main.js）；`base.html` → `bc-components.css?v=20260810j`
- **✅ 驗證**（CDP 1280/375px）：scroller-box 移除、動畫執行中、banner 高度降低（701→654px、482→438px）、跑馬燈 60px（原 107px）、footer 不受影響、無溢出

### 2026-08-10：bean_menu banner 內複製 footer 的 .scroller-box 水平遮罩動畫 ✅

- **需求**：使用 footer 內的水平遮罩動畫 `.scroller-box`，複製到 bean_menu 的 `ftco-subpage-banner` container 內
- **實作**（`bean_menu.html`）：banner container 內（icon_text 後）加入 `.scroller-box > .scroller > ul.tag-list.scroller__inner > 2×li`；文案品牌化「ROASTED FRESH・BREWED FAST・SERVED FRESH・HUG IN A CUP」
- **零新增 CSS/JS**：複用 `.scroller-box` 樣式（style-utilities.css）；main.js `querySelectorAll('.scroller')` 全域初始化（`data-animated=true` + 複製 li 無縫循環）
- **注意**：banner 高度被內容自然撐高（桌面 500→701px、手機 82vw→482px），非 overflow，視覺可接受
- **✅ 驗證**（CDP 1280/375px）：`data-animated=true`、li 複製 4 個、`animation: scroll 60s` transform 位移中、footer 不受影響、無水平溢出

### 2026-08-10：首頁第 1 個輪播橫幅 coffee_border_01.svg 增大（×1.61）+ 改白色 ✅

- **需求**：第 1 個 slider 內的 `coffee_border_01.svg` 增大（40% → 再 +15% = ×1.61）、改為白色
- **SVG**（`static/images/coffee_border_01.svg`）：兩個 path 加 `fill="#ffffff"`（原無 fill = 預設黑色，在深色背景不可見）
- **CSS**（`style-utilities.css`）：`.slider-item.slider-first .noise-img`（index.html 第 1 個 slider 加 `slider-first` class）各斷點 ×1.61（17vw→27.4vw/min 238→383px、55→88.6vw、65→104.7vw、75→120.8vw；手機維持 92vw cap = container 滿寬）
- **⚠️ 教訓**：不用 `.slider-item:first-child`——owl 結構中每個 `.slider-item` 都是其 `.owl-item` 父的 `:first-child`，會誤匹配全部 slider；用明確 class 標記
- `base.html` → `style-utilities.css?v=20260810f`
- **✅ 驗證**（CDP 1280/768/375/320px）：slider1 = 383/383/345/294px；slider3 對照不受影響（238/422/281/240px 原尺寸）；`svg_white: true`、全斷點無溢出

### 2026-08-10：bean_menu 產品區域 A+C 混合不對稱網格（瀑布 × 棋盤翻轉）✅

- **需求**：bean_menu 咖啡豆產品區改為不對稱網格；提供 3 方案（瀑布 A / 蛇形 B / 棋盤 C），使用者選 **A+C 混合**
- **布局**：每 3 個一組（DOM = 大 小 小），6 商品 = 2 組：
  - A 瀑布：大卡左側跨 2 欄（`grid-column 1/3`，圖片 340px）+ 小卡右側上下、第二張 `translateY(4rem)` 錯落
  - C 棋盤：組 2 翻轉（`.bean-mix-flip`：大卡右側 `2/4`、小卡左側）
- **實作**：`bean_menu.html` + `bc-components.css` 新增 `.bean-mix-*`（獨立 class，不影響 coffee_menu `.coffee-menu-zgrid`）；響應式 ≤1080px 大卡整行+小卡並排、≤768px 單欄
- **⚠️ 教訓**：小卡定位用 **sibling 選擇器**（`.bean-mix-main + .bean-mix-sub`）；`nth-of-type` 依賴 div 類型計數（main 也是 div）會錯位
- `base.html` → `bc-components.css?v=20260810i`
- **✅ 驗證**（CDP 375/768/1280px）：組 1 大左小右、組 2 翻轉大右小左、小卡錯落 64px、平板大卡整行、手機單欄、全斷點無溢出；coffee_menu 不受影響

### 2026-08-10：首頁第 3 個輪播橫幅背景圖片 → 全幅背景影片（無橢圓遮罩）✅

- **需求**：第 3 個橫幅整面背景圖片（`bg_3.jpg`）改為影片容器填滿整個橫幅，**無橢圓形遮罩**（不同於第 2 個的 blobsVideo 橢圓 morph 呈現）；影片與第 2 個相同 `roasting.webm`
- **實作**：
  - `index.html`：移除 inline `background-image: bg_3.jpg`，改為 `<div class="bc-banner-video loadEnd">` + `<video>`（`data-lazy-video` 延遲載入，main.js 通用處理）
  - `style-utilities.css`：複用 `.bc-banner-video` 基礎樣式（`position:absolute` 全幅 + `video object-fit:cover` 鋪滿）；**移除** `.bc-banner-video-3 / .banner-stage-3 / .inner-3 / morph-3` 橢圓系列死碼
  - 保留 `.overlay`（黑 0.6）蓋影片 → 暗色調；`base.html` → `style-utilities.css?v=20260810c`
- **✅ 驗證**（CDP 375px/1280px）：`background-image: none`、容器填滿橫幅（375×480 / 1265×750）、`borderRadius: 0px`、`animationName: none`、切到該格 `paused:false` 正常播放

### 2026-08-10：cheesetart.com c-attract 流動選單整合 ✅

#### 1. 流動選單（c-attract）整合至全站 ✅
- **需求**：參考 cheesetart.com 的 `<div class="c-attract">` 流動選單（Buy & Order 按鈕 + 漢堡選單動畫）整合到全站
- **逆向分析**（cheesetart core.css / core.min.js）：
  - `.c-attract`：動畫容器（負 margin 擴展 hover 熱區 + `perspective:87rem` 3D 透視）
  - `.c-attract__layer`：`preserve-3d` 內層（GSAP tilt 動畫目標）
  - UnifiedEffect：hover 圖層跟隨滑鼠 3D 傾斜（rotateX/rotateY ±24°）+ 位移 + 縮放，釋放時 elastic.out 回彈
- **新增**：
  - `static/css/bc-attract.css`：c-attract 容器 + Buy 按鈕（垂直長條、透明背景→黑底、白邊框、垂直文字 `writing-mode:vertical-lr`）+ 漢堡選單三條線 + `#borders` 全屏虛線
  - `static/js/bc-attract.js`：AttractEffect（UnifiedEffect 精簡版，proximity 熱區吸引 + elastic 回彈）
  - `static/images/dots_40.svg`（下載自 cheesetart，虛線 mask）
- **修改**：
  - `base.html`：GSAP 全域化（head defer）、bc-attract.css/js 引用、`#borders` HTML、`.bc-page-content` wrapper
  - `nav.html`：漢堡選單套用三條線 c-attract + Buy & Order 按鈕（`position:fixed` 右側）
  - `index.html`：移除重複 GSAP CDN
- **✅ 驗證**：hover 吸引位移正常、響應式、無溢出

#### 2. 多次視覺調整（多輪反饋）✅
- **按鈕 hover「吸引」動畫**：移除 rotate/scale 變形，改純位移跟隨游標（`translate3d 48px`）；proximity 60px 熱區（滑鼠靠近即吸引）；修復 `navigator.maxTouchPoints>0` 誤停用（觸控筆電）
- **按鈕樣式**：右側浮動（`right:17px` 中心對齊虛線）、垂直長條 50×225、透明→純黑 `#000000` 背景、白色 1px 邊框、垂直文字、hover 邊框不變色
- **按鈕 z-index**：`99999`（最頂，高於虛線 9999）
- **#borders 右側虛線**：全高（top 0 → 100%）、`z-index:9999`、`dots_40.svg` mask 點狀、灰色 `rgba(255,255,255,0.5)`、`pointer-events:none`、中心對齊 Buy 按鈕；左側虛線已隱藏
- **浮動購物車**（`bc-components.css`）：縮小 15%（68→58px、58→49px）、透明背景→黑底、移除陰影/backdrop-filter、白色邊框、徽章縮小 10%（24→22px）、金色背景、白色文字
- **浮動購物車細部調整（2026-08-10 追加）**：徽章 `.bc-floating-cart-badge` 上移 3px（`top:-3px → -6px`）；圖示 `.bc-floating-cart-btn .material-icons` 縮小 10%（桌面 `1.5rem → 1.35rem`、手機 `1.3rem → 1.17rem`）；`base.html` → `bc-components.css?v=20260810g`
- **z-index 層級修復（2026-08-10 追加）**：`#ftco-navbar`（position:absolute + z-index:3）建立 stacking context，`.bc-attract-buy`（z-index:99999）在 nav 內被鎖在層級 3、低於 `#borders`(9999) 被虛線蓋住 → 移到 `</nav>` 外、body 直接子層（`nav.html`），`99999 > 9999` 按鈕最頂、虛線在下
- **✅ 驗證**：CDP 各斷點位置/顏色/z-index/動畫均正確；全站 6 頁面渲染 DOM 順序 `#borders < </nav> < .bc-attract-buy`

#### 3. 涉及檔案
- 新增：`static/css/bc-attract.css`、`static/js/bc-attract.js`、`static/images/dots_40.svg`
- 修改：`static/css/bc-components.css`、`static/css/style-utilities.css`、`templates/betweencoffee_delivery/base.html`、`index.html`、`layouts/nav.html`

### 2026-08-10：SALON SEARCH 區塊 + 菜單網格響應式全面優化

#### 6. SALON SEARCH 滑鼠移出動畫修復 ✅
- **問題**：滑鼠移出時無動畫，產品圖瞬間跳走（消失）
- **根因**（重新比對 demido 原始 `common.css`）：
  - `.is-out` 缺少 transform（demido 每個 is-out 都有明確移出目標：`-60%/-60%/-150%`）→ 我的舊版只有 transition 無 transform → 移出時 transform 不變
  - JS 等待時機錯誤：`getComputedStyle(img03).transitionDuration` 無 class 時為 `0s` → 立即執行移除 → 中斷 is-out
- **修復**（`bc-search.css` + `bc-search.js` + `index.html?v=20260810b`）：
  - 桌面版補上三圖 `.is-out` transform（-60%/-60%/-150%）、手機版補上 SP 位移（-140%/-95%/-160%）
  - JS `hide()` 改為監聽 `img-03` 的 `transitionend`（等 1000ms+300ms 完成）+ `setTimeout(1500ms)` 保險 + `done` 旗標
- **✅ 驗證**（CDP 追蹤 transform 序列）：mouseenter→is-on 浮入原位→mouseleave→is-out 向上移出（-1.45px 持續變化）→1.3s 後 class 清除回底部；桌面/手機均完整播放

#### 5. demido.jp SALON SEARCH aside 整合至首頁 ✅（2026-08-10）
- **需求**：參考 demido.jp/products/assetspamilk2.html 的 `<aside class="search">` 加入 index.html（保留原樣風格 + hover 浮動動畫，引入 GSAP）
- **新增**：
  - `static/css/bc-search.css`（品牌化：黑底 `--bc-bg`、金色圓形 icon `--bc-gold`、demido is-on/is-out 動畫 + floating keyframes、斷點 ≤768/≤575.98）
  - `static/js/bc-search.js`（桌面 hover→is-on/is-out；行動端 GSAP ScrollTrigger 進入/離開 50%）
  - `static/images/search_img01/02/03.png`（咖啡主題圖替代：coffee_01/coffee_04/float_bean 複製）
  - `static/images/bc_search_txt_pc/sp.svg`（下載自 demido）
- **修改** `index.html`：GSAP CDN（defer）、`<aside class="bc-search">` 置於 branding Deco 之後（連結→`{% url 'coffee_menu' %}`、文字品牌化）、extra_css/extra_scripts 引用
- **保留原樣**：SALON_SEARCH SVG 標題（PC/SP path 從 demido 抓取嵌入、白色 fill）、圓形箭頭 icon
- **✅ 驗證**：1200/769px 桌面 480px + PC 標題、768px 手機 1160px + SP 標題、480/375/320px 900px；GSAP/ScrollTrigger 載入、無溢出、hover class 切換正常

#### 4. ani_bean_line_il 動畫全頁面橫跨修復 ✅（2026-08-10）
- **問題**：bean_menu 的 `ani_bean_line_il` 動畫線只顯示約 2/3 螢幕寬（1280px 時 x=-82、右邊只到 1179）
- **根因**：`position:absolute` 無 `left/top`，位於 `.post_archive`（Bootstrap container + flex row-reverse）內 → static position 偏移
- **修復**（`bean_menu.html` + `animate-custom.css`）：
  - `.ani_bean_line_il` 移到 `.ftco-subpage-section` 直接子層 + `left:0; width:100vw`（原 98.5vw）
  - `:after` 動畫規則 selector 增加 `.ftco-subpage-section > .ani_bean_line_il:after`
  - `ani_coffee_line_il` 同步修正；`base.html` 版本 → `animate-custom.css?v=20260810a`
- **✅ 驗證**：1280/768/390px 均 x=0、w=視窗全寬、`:after` 動畫正常、無溢出

#### 3. 移除「所有咖啡/所有烘焙豆」section ✅（2026-08-10）
- `coffee_menu.html`：移除「所有咖啡」`.bc-coffee-all-grid` section
- `bean_menu.html`：移除「所有烘焙豆」section
- `responsive-system.css`：清理 `.bc-coffee-*` 系列（-46 行，僅保留 Z 網格規則）
- `base.html`：`responsive-system.css?v=20260809l`
- **✅ 驗證**：兩頁無 bc-coffee 殘留、Z 網格保留（coffee 8 cell / bean 6 cell）、無溢出

#### 2. title_bg_img_02.svg 行動端裁切修復 ✅（2026-08-10）
- **問題**：bean_menu banner 的 `title_bg_img_02.svg` 行動端被裁切
- **根因**：`.svg-bg-2` 基礎規則 `background-size:cover` + 手機 `width:300px/top:-150px` → 直式 SVG(540×700) 放大裁切；coffee 的 `.svg-bg` 用 `auto`+650px 無此問題
- **修復**（`responsive-system.css` + `base.html?v=20260809k`）：≤767px 手機 `.svg-bg-2` → `background-size:auto; width:650px; top:-20px; left:-18em`（與 `.svg-bg` 一致）
- **✅ 驗證**：375/767px 兩頁一致 `auto` 無裁切；768/1200px 桌面維持 `cover` 不受影響

#### 1. bean_menu 使用 Z 字對角網格（與 coffee_menu 相同）✅（2026-08-10）
- **需求**：bean_menu 咖啡豆商品區改用與 coffee_menu 相同的不對稱網格（此頁面與 coffee_menu HTML 結構幾乎相同）
- **修改**（`bean_menu.html`）：extends 改 `layouts/blank.html`、商品區替換為 `.coffee-menu-zgrid`（每 4 個一組 = 大 小 小 大）、保留 bean 資料與 `ani_bean_line_il`
- **零新增 CSS**：完全複用 `.coffee-z-*`（bc-components.css）與響應式規則
- **✅ 驗證**：cell 結構與 coffee_menu 逐標籤一致、375/480/576/768/992/1200/1440px 響應式狀態完全一致、無溢出

### 2026-08-09：響應式系統分支（feat/responsive-system）完成並合併

- **分支**：`feat/responsive-system`（9 commits）Fast-forward 合併回 main
- **核心成果**：
  1. **全域響應式設計尺度系統**（`responsive-system.css`，最後載入）：`--bc-fs-*`/`--bc-space-*` 變數 + `html` 基準 + `img max-width`
  2. **高影響元件套用變數**：heading-section、menu-wrap、btn、詳情頁、coffee-menu-desc
  3. **全站驗證腳本** `scripts/audit_responsive.py`（9 頁 × 3 斷點無溢出）
  4. **後續修復**：subpage-banner 手機 padding（heading 101→269px）、「所有咖啡」卡片網格、Z 卡片按鈕 inline-block、Z 卡片圖片手機 180px、coffee-menu-desc 改 --bc-fs-md
- **使用者並行**：subpage-banner 手機高度 82vw、背景位置、bc-welcome 字體等
- **合併推送**：`263b052..e28fb94 main -> main`
- **驗證**：9 頁面 × 375/768/1200 無溢出、字體響應式縮放

### 2026-08-09：heading-section 手機寬度修復 + 所有咖啡卡片網格

- **問題 1**：`.ftco-subpage-banner` 手機左右 padding `7em`（112px）擠壓內容 → heading-section 375px 只剩 101px、文字換行
  - 修復（`responsive-system.css`）：≤767.98 `padding 6em 1.5em`、≤575.98 `5em 1em` → heading-section 375px **269px**（+166%）
- **問題 2**：coffee_menu Z 網格下方新增「所有咖啡」卡片網格（`.bc-coffee-all-grid` / `.bc-coffee-card`）
  - 小卡片：名稱（`--bc-fs-lg`）+ 描述（3 行截斷）+ 落單按鈕（`.bc-btn-sm`）
  - 響應式：桌面 3 欄、≤768 2 欄、≤576 1 欄；hover 上浮 + 陰影
- `base.html`：`responsive-system.css?v=20260809g`
- **✅ 驗證**：heading 375px 269px、新區塊 32 卡片、btn 12.1/13.7/15.4px、無溢出

### 2026-08-09：全域響應式設計尺度系統（P1-P3 完成）

#### 📐 方案（使用者認可：字體/間距變數 + html 基準 + 高影響覆蓋）
- **P1 系統建立**（`responsive-system.css`，最後載入）：`--bc-fs-*` 響應式字體變數（clamp，375px→~75%、1440px→100%）、`--bc-space-*` 間距變數、`html` 基準 font-size clamp（rem 自動縮放）、全域 `img max-width:100%`
- **P2 高影響元件套用**：`.heading-section h2/subheading/p`、`.menu-wrap .text h3/h5/price/desc`、`.btn/.bc-btn` 系列
  - ⚠️ 教訓：`.coffee-menu-desc` 需高 specificity（`.menu-wrap .text .coffee-menu-desc`）才覆蓋成功
- **P3 全站驗證矩陣**：375/768/1200 × 9 頁面（/、/coffee_menu/、/bean_menu/、/coffee/4/、/bean/8/、/checkout/、/cart/、/about/、/accounts/login/）全部無橫向溢出
- `base.html`：`responsive-system.css?v=20260809d`
- **✅ 驗證**：375px headingH2=31px（原40）、btn=12.1px、商品名=15px；桌面近原尺寸；全站無溢出

### 2026-08-09：首頁 Bean 區塊隱藏 + 分支合併推送

- **Bean 區塊隱藏**：`index.html` `<section class="ftco-section overflow-hidden">` → `<section hidden>`（articleStyle_08 咖啡豆區，使用者並行修改）
- **分支合併**：`fix/responsive-breakpoints`（7 commits，含本次 session 全部響應式任務）**Fast-forward 合併回 main**
- **推送**：`547abc5..263b052 main -> main`（GitHub）
- **目前狀態**：工作樹乾淨、main 與分支對齊、Render autoDeploy 已觸發

### 2026-08-09：隱藏 home-slider 橫幅內按鈕

- **需求**：隱藏 home-slider 三個 slider 的「立即落單/我們的配方/了解更多」按鈕
- **修改**（`bc-components.css`）：`.owl-carousel.home-slider .slider-item .btn { display: none }`
- **順帶修復**：先前編輯 navbar-brand 註解時 `/*` 丟失造成無效 CSS，已修復（CSS 括號 578/578 平衡）
- `base.html`：版本參數 → v=20260808h
- **✅ 驗證**（headless iframe 測量）：7 個按鈕（含 owl clone）皆 `display:none`、`visible=false`

### 2026-08-09：navbar logo「｛ Between ｝」略高修正（glyph 垂直補償）

- **反饋**：行動端/平板端 logo 仍略高（視覺中心偏上 ~4px）
- **根因**：Mogra 字體 glyph ascent 較大，`line-height:1` 下文字視覺中心偏上行盒中心上方
- **精確測量**（headless 截圖 + PIL）：375px logo 視覺中心 Y=43 vs navbar 中心 47（偏移 +4px）
- **修改**（`bc-components.css`）：`.navbar-brand` `padding-top 0.3125→0.5625rem`（+4px 下移）、`padding-bottom 0.3125→0.0625rem`（總和維持 box 高）
- `base.html`：版本參數 → v=20260808g
- **✅ 驗證**：375px logo 中心 47=navbar 47（完美）、768px logo 52/hamburger 53≈navbar 54、1200px logo 73≈navbar 71

### 2026-08-09：navbar logo 與菜單垂直居中強化

- **需求**：navbar-brand「｛ Between ｝」及菜單需垂直居中對齊（含行動/平板）
- **修改**（`bc-components.css`）：`.ftco_navbar .container { align-items:center }`；brand/toggler/nav/nav-item `align-self:center`；`.nav-link` 改 flex + `align-items:center; gap:6px`（icon 與文字垂直對齊）
- `base.html`：版本參數 → v=20260808f
- **✅ 驗證**（headless iframe 測量）：375px logo center 46.5 = toggler 46；1200px logo center 70 = 菜單 70.5；nav-link 內 icon 與所在項對齊（center 195）
- ⚠️ 注意：使用者並行把 navbar-brand 手機字體 22px 調整為 25px（保留）

### 2026-08-09：導覽列 logo（navbar-brand）手機響應式縮小

- **需求**：首頁行動端 navbar-brand「｛ Between ｝」過大需相應縮小
- **修改**（`bc-components.css`）：`.navbar-brand` ≤767.98 `30px`、≤575.98 `22px`（桌面 40px）
- `base.html`：版本參數 → v=20260808e
- **✅ 驗證**（headless iframe 測量）：375/390/430px font-size=22px、700px=30px；與 hamburger 無重疊

### 2026-08-09：首頁第一個 slider 手機響應式調整（方案 A：照片+文字相應縮小）

- **需求**：使用者指出 home-slider 第一格（「恰度好的一杯」）手機上照片（GIF/咖啡杯）沒有相應縮小、與文字重疊、顯示不理想；SVG（.noise-img）不動
- **調整**：
  - `style-utilities.css`：GIF 縮小 — ≤575.98 `90%→55%`、≤767.98 `80%→65%`
  - `bc-components.css`：
    - 咖啡杯縮小 — ≤575.98 `min(200px,60vw)→min(150px,45vw)`
    - 文字讓位 — `.slider-first-text` ≤575.98 `max-width:100%→65%`
    - 文字縮小 — ≤575.98 subheading `28→20px`、h2 `30→22px`、p `18→14px`、按鈕 `padding 0.5rem 1rem`
    - **根因**：`.slider-text { height:750px }`（桌面值）手機未縮小 → 照片偏下與文字重疊 → ≤575.98 `height:480px`、576~767.98 `height:560px`（=橫幅高）
  - `base.html`：版本參數 → v=20260808d
- **✅ 驗證**（headless iframe 測量 375px）：咖啡杯 `y=144~336`（上移居中，原 279~471）、GIF `y=134~346`；文字與照片重疊從 191px 降至 148px；視覺截圖確認縮小後整體協調
- **備註**：殘餘重疊為「左下文字 + 居中照片」佈局特性（PNG 去背透明，視覺影響有限）；若仍需完全分離可做「照片上移/上下分區」進階調整

### 2026-08-09：全域響應式審計與修復（右側漏邊 / 橫向溢出 / 斷點統一）

#### 🔬 診斷方法（headless + 同源 iframe 掃描）
- 建立臨時同源診斷頁（iframe 掃描 `documentElement.scrollWidth` vs `innerWidth`、所有 `right > innerWidth` 且無 overflow 裁剪祖先的元素），診斷完成後已刪除
- 斷點矩陣 375/390/414/480/576/768/992/1200/1440 × 頁面 /、/coffee_menu/、/bean_menu/、/coffee/4/、/bean/8/、/about/、/checkout/、/cart/、/accounts/login/
- ⚠️ 教訓：headless `--window-size` 最小 500px（375/390 測量失真），需用 iframe 指定寬度測真實手機；X-Frame-Options DENY 需臨時 SAMEORIGIN（已恢復）

#### 🚨 根因（實際測量定位）
1. **首頁**：`.playfair_deco .lg_message { display:flex; font-size:6em }` flex 下長文字不換行 → 撐開 `.mid-banner` 到 423px（viewport 375）→ 頁面橫向捲動 462px
2. **咖啡豆詳情**：`.img-box .img-4` 寬圖 455px（height:56vh 自動寬度）> 手機容器 → 溢出 408px

#### 🛠️ 修復
- `style-custom.css`：`.lg_message` 加 `flex-wrap: wrap`；`.img-box .img-4` 加 `max-width:100%; object-fit:contain`
- `bc-components.css`：全域防護 `html, body { overflow-x: hidden }`（最後防線）
- `style-utilities.css`：`.cart-popup` ≤575.98 移除 `min-width:600px`（fixed 雖不捲動但顯示時超寬）
- **斷點統一**：578→575.98（Rtable）、1196/1197→1200/1199.98（flexable-vh-20）；建立「品牌響應式斷點基準」文件（bc-components.css 頂部：480/575.98/767.98/991.98/1199.98/1200；880/1024/1250/1920 保留為兼容斷點）
- `base.html`：三個 CSS 版本參數 → v=20260808b

#### ✅ 驗證
- 所有頁面 × 所有斷點：`scrollWidth < innerWidth`，**無橫向捲動**（修復前首頁 375px 溢出 87px、bean/8 溢出 33px）
- 視覺截圖 375px 確認 iframe 邊框內無內容溢出



- **需求**：使用者指示移除載入遮罩的文字，只保留遮罩動畫與邏輯。
- **修改**（`static/css/bc-components.css`）：
  - `.home-slider::before`：`content: "Brewing... 沖泡中"` → `content: ""`，移除 flex 置中/Mogra 字型/金色文字，**僅保留深黑遮罩**（#0e0e0e）與淡出 transition
  - `.home-slider::after`：spinner `margin: -38px`（偏上給文字空間）→ `-22px`（**精確置中**）
  - 響應式 ≤575：spinner 36px 置中（`-18px`），移除 `::before` 文字樣式
  - `is-loaded` 淡出邏輯完整保留
- `base.html`：`bc-components.css?v=20260807p → q`
- **✅ 驗證**（測試頁 + headless 截圖 + PIL）：spinner 置中 X=737/Y=362（橫幅正中央），深黑遮罩完整（269,867px），金色像素僅 40 個（= spinner 圓環，**無文字**）

### 2026-08-08：home-slider 首屏跳動根因修復（bc-welcome-panel 被推下）

#### 🚨 根因（首次發現）
- **現象**：`bc-welcome-panel` 比 home-slider 先載入顯示在頁面頂部，owl 初始化後橫幅突然出現（750px），面板被向下推約 750px（首屏跳動）。
- **根因**：`static/css/owl.carousel.min.css` 標準規則 `.owl-carousel { display:none }`，只有初始化後 `.owl-loaded { display:block }`。因此 JS 執行 `owlCarousel()` 前整個橫幅高度為 0。
- **重要發現**：之前設計的「Brewing 沖泡中」載入遮罩（`.home-slider::before/::after` + `.owl-stage-outer` opacity:0）因 section `display:none` **從未真正顯示過**。

#### 🛠️ 修復（一行 CSS）
- `static/css/bc-components.css`：`.owl-carousel.home-slider { display: block }` 覆蓋 owl 預設 `display:none`，橫幅從 HTML 解析即佔 750px，載入遮罩同步顯示，`bc-welcome-panel` 全程位置穩定。
- `base.html`：`bc-components.css?v=20260807o → p`

#### ✅ 驗證（headless 截圖 + PIL）
- 無 JS（初始化前）vs 有 JS（初始化後）：`bc-welcome-panel` 深金區塊 **Y=695~819 完全一致，無跳動**
- 初始化前「Brewing 沖泡中」遮罩顯示（金色文字 + spinner，2901 金色像素）

### 2026-08-07（凌晨）：首頁 Banner 烘焙影片 + 效能優化 P0/P1 + Render 日誌診斷

#### 🎬 咖啡豆烘焙影片放入 owl-carousel Banner（完整實作）
- **實作**：`templates/betweencoffee_delivery/index.html` + `landing_v3.html`（兩者同步）
  - 第二個 slider-item（「好豆 • 造就好生活」）加入 `.bc-banner-video` 影片背景
  - `<source>` 順序：**webm 優先**（roasting.webm 2.2MB，比 mp4 6.2MB 省 65%），mp4 作 fallback
  - 移除第二個 slider 的 inline `background-image`（純深黑背景）
- **blobsVideo morph 遮罩動畫**（與咖啡豆 section 一致）：
  - `.bc-banner-video.blobsVideo` + `.inner` 結構
  - `border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%` + `animation: morph 7s infinite`
  - chrome-devtools 驗證：borderRadius 動態變形 ✅、animationName=morph ✅
- **影片尺寸調整歷程**（使用者多輪反饋）：
  1. 最初 100% 寬（1905px）→ 使用者認為過寬 → 縮小至 **1080×608 並置中**
  2. 置中用 `margin: 0 auto`（不能用 `translateX(-50%)`，會被 morph 動畫 transform 覆蓋）
  3. 拆兩層：**外層滿版深黑**（#0e0e0e）+ **內層縮小置中影片**（避免底部露出顏色）
  4. 驗證：outer 1905×750、inner 1080×608、left 413px = right 413px 完美置中 ✅
- **涉及檔案**：`landing_v3.html` / `index.html` / `static/css/style-utilities.css`

#### 📊 落地頁效能分析（chrome-devtools）— 確認過重
| 指標 | 數值 | 評估 |
|------|:----:|:----:|
| 總傳輸量 | **17.3 MB** | ❌ |
| 請求數 | **206 個** | ❌ |
| 載入時間 | **7.4 秒** | ❌ |
| video | 8.6 MB × 4 | 🔴 owl-carousel loop 複製 DOM 導致 webm 下載 4 次 |
| img | 3.6 MB × 14 | 🟡 去背 PNG 偏大 |
| css | 2.3 MB × 6 | 🟡 未合併 |
| script | 560 KB × 23 | ✅ |
| fetch | 554 KB × 136 | 🟡 WS 403 → 每 5 秒輪詢 fallback |

#### 🛠️ P0 修復：影片重複下載（8.6MB → 2.2MB）
- **根因**：無 Cache-Control header，瀏覽器不 cache 影片，owl-carousel loop 複製 DOM 導致同一 webm 下載 4 次
- **修復**：`betweencoffee_delivery/settings.py` 新增
  - `WHITENOISE_MAX_AGE = 31536000`（1 年長快取）
  - `WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ("jpg","jpeg","png","gif","ico","webm","mp4")`
- **效果**：Render 生產環境影片只實際下載 1 次（其餘由 cache 提供），節省 -6.6MB / -38% 總量

#### 🛠️ P1 修復：WebSocket 403 fallback 輪詢風暴
- **根因**：本地 runserver 不支援 WS 升級（生產 Daphne 正常），403 → fallback 每 5 秒輪詢 → 136 請求
- **修復**：`static/js/websocket-core.js` — `baseDelay: 1000→5000`、`fallbackInterval: 5000→30000`
- **效果**：每分鐘 12 次 → 2 次請求（-83%）

#### 🔍 Render 部署日誌診斷（WebSocketManager 初始化兩次）
- **現象**：日誌 12:35:18 和 12:35:29 各出現一次「✅ WebSocketManager 增強版初始化完成」
- **分析**：`eshop/websocket_manager.py` 已是單例（`__new__` + `_initialized` 保護），同進程不會重複 → Render 啟動了 **2 個 Daphne worker**
- **影響**：InMemoryChannelLayer（無 Redis）下，多 worker 的 WS group broadcast 只送達同進程連線
- **建議**：Render 儀表板設定 `WEB_CONCURRENCY=1` 消除重複初始化
- **其他日誌雜訊**（無害）：PayPal 未設定、.env not found、Could not update site（時序雜訊）、HTTP/2 not supported

#### 📂 涉及檔案（5 個）
`templates/betweencoffee_delivery/index.html` / `templates/betweencoffee_delivery/landing_v3.html` / `static/css/style-utilities.css` / `betweencoffee_delivery/settings.py` / `static/js/websocket-core.js`

### 2026-08-07（傍晚）：home-slider 抖動縮放 + 延遲顯示 + 影片自動播放全面修復（多輪迭代）

#### 🔍 背景與完整診斷歷程
本次任務從「優化首屏載入」出發，經使用者多輪反饋，最終徹底解決 home-slider 的**抖動縮放**、**延遲 1 秒顯示**、**影片無法自動播放**、**GIF 位置偏移**四大問題。

#### 🚨 最重要教訓：WHITENOISE 1 年長快取陷阱（反覆看不到修改效果的根因）
- `settings.py` 有 `WHITENOISE_MAX_AGE = 31536000`（1 年長快取）+ `WHITENOISE_USE_FINDERS = True`
- **開發時改 CSS/JS，瀏覽器永遠顯示舊版** → 所有修改「看似無效」其實是快取遮蔽
- **解法**：`base.html` 靜態資源加 `?v=` 版本參數
  - `bc-components.css?v=20260807e`
  - `main.js?v=20260807h`
- **規則**：以後每次改 CSS/JS 都要更新 `?v=` 版本參數，否則使用者看不到效果

#### 🛠️ Phase 1：消除抖動縮放
- **根因（兩層）**：
  1. owl 初始化前 `.slider-item` 高度未鎖定 → 內容堆疊塌陷
  2. `.slider-item` 有 `height:750px` 但**無 `overflow:hidden`** → 內部 GIF（725px 高）/大 SVG/內容高度達 785px → 撐破 `.owl-stage` → 高度跳動
- **修復**（`static/css/bc-components.css`）：
  - `.home-slider/.slider-item` 提前鎖定 `height: 750px`（響應式 ≤768:560px、≤576:480px）+ `overflow: hidden`
  - `.owl-stage-outer/.owl-stage/.owl-item/.slider-item` 全部 `overflow: hidden` 鎖死捲動鏈
  - 深色背景 `#0e0e0e` 佔位防白屏閃爍
- **驗證**：3 次動態測量 slider/stage/item 高度全為 750px 無跳動 ✅

#### 🛠️ Phase 2：加速載入（影片延遲 + 圖片 lazy + 首屏 preload）
- **`index.html` / `landing_v3.html`**（實際首頁是 `index.html`，非 landing_v3）：
  - 第二格烘焙影片 `preload="none"` + `data-lazy-video`（首屏不載 2.2MB）
  - 第二/三格圖片 `loading="lazy"`
- **`base.html`**：新增 `{% block extra_head %}`，`index.html` 覆寫 preload 首屏 3 資產（section_bg_01.svg / _cup_360.gif / coffee_04.png）
- **`main.js`**：新增 `loadActiveVideo()` + owl `changed.owl.carousel` 綁定

#### 🐛 多輪 bug 修復（使用者反饋驅動）

**1. GIF/SVG 尺寸縮小**
- 根因：HTML `<img width="300" height="290">` / `width="50" height="50"` 被瀏覽器當固定尺寸，覆蓋 CSS width:50%
- 修復：移除所有 HTML width/height attributes

**2. GIF 原檔縮小導致變小模糊**
- **教訓**：不要用 Pillow 把 GIF 從 1500px 縮到 750px 存檔（顯示靠 CSS width:50%，原檔解析度才是畫質）
- 修復：從 `/tmp/*_backup.gif` 恢復原檔 1500×1450

**3. 影片無法自動播放（多輪迭代）**
- 嘗試：等 canplay → play() ❌ → 僅 load() 靠原生 autoplay ❌ → **標準 `video.play()` + 移除 pause 邏輯** ✅
- **真正根因**：owl loop 會 **clone 複製影片元素**，原本的 `$el.find('video').each(pause)` 把**剛載入正要播放的那個也暫停**（監測 currentTime 0.4 被 pause 回 0 證實）
- **修復**：`loadActiveVideo()` 對 `.owl-item.active` 內影片直接 `video.play()`（muted+playsinline 下真實瀏覽器允許 autoplay），不再 pause 其他影片
- **驗證**：`activeHasVideo: true`、`activePaused: false` ✅

**4. 金色掃光佔位骨架 → 改透明**
- 使用者指定不需要金色 shimmer 掃光
- 修復：移除 `.gif-box` 的品牌金背景 + `::after` shimmer 動畫，改透明（保留 aspect-ratio）

**5. GIF 上移不居中**
- 根因：`.gif-box`（`<div>`）也被設 `aspect-ratio:1500/1450` → div 是塊級元素（寬度撐滿），div 高度 ≠ img 高度（img 寬度由 width:50% 控制）→ img 上移
- 修復：**只保留 `<img>` 上的 aspect-ratio，移除 div 上的**（div 高度由內容撐開）
- 驗證：divTop(13)=imgTop(13)、divH(725)=imgH(725)、divBottom(738)=imgBottom(738) 完全居中 ✅

#### 📂 涉及檔案（5 個）
`static/css/bc-components.css` / `static/js/main.js` / `templates/betweencoffee_delivery/base.html` / `templates/betweencoffee_delivery/index.html` / `templates/betweencoffee_delivery/landing_v3.html`

#### 🐛 DEBUG 技巧記錄（本次實用）
- owl clone 複製影片 → 網頁有 N 個同 video 元素是正常
- `activePaused` 比 `currentTime` 更可靠判斷自動播放
- 瀏覽器沿用舊 CSS/JS 時，先用 `curl` 確認伺服器回傳新版，再用 `?v=` 繞快取

### 2026-08-06：咖啡菜單 Z 字對角主副卡 + 描述 CSS 類

#### 🍽️ 咖啡菜單頁 Z 字對角主副卡網格（方案 B）
- **背景**：原咖啡菜單為傳統縱向列表，使用者要求改造
- **方案評估**：提出 3 個替代方案（A 大區塊精選、B Z 字對角主副卡、C 直排橫幅）→ 使用者選 **方案 B**
- **佈局**：每 4 個一組（DOM 順序 = 大 小 小 大），2x2 網格：
  ```
  ┌──────┬──────┐
  │ 大(1)│ 小(2)│   ← 左上大、右上小
  ├──────┼──────┤
  │ 小(3)│ 大(4)│   ← 左下小、右下大（對角反轉）
  └──────┴──────┘
  ```
- **實作**：`templates/betweencoffee_delivery/coffee_menu.html` + `static/css/bc-components.css`
  - `.coffee-menu-zgrid` / `.coffee-z-row`（2x2 grid gap 3rem）/ `.coffee-z-cell`（nth-child 指定位置）
  - 響應式 ≤768px 降為單欄堆疊
- **圖片尺寸歷程**（chrome-devtools 逐輪驗證）：
  - 最初大卡 340px 太大 → 縮小至 280px（顯示 252px）
  - 使用者要求大卡 +15%、小卡 +10% → 大 290px、小 248px
  - 使用者再要求小卡 +5% → 最終 **大卡 290px、小卡 260px**
- **位置落差**：cell2（右上小）/cell3（左下小）`margin-top: 6rem`（96px）→ 形成明顯階梯錯位
- **修正拉長問題**：強制 `height:auto !important` + `min-height:0`，避免 style-bootstrap.css 的 `height:36vh` 拉伸
- **驗證**：8 個商品圖片比例全為 1.00 ✅、落差每組精確 +96px ✅

#### 📝 咖啡描述 CSS 類 `.coffee-menu-desc`
- **問題**：描述文字無樣式控制，版面雜亂
- **方案分析**：**增加內邊距（padding）優於減少寬度（max-width）** —
  1. 不破壞卡片結構對齊（名稱/價格/按鈕保持原位）
  2. 自然縮短行長（最佳閱讀 45-75 字元）
  3. 文字與卡片邊緣留白，增加品牌呼吸感
  4. 行動版不需額外處理限寬過窄
- **最終實作**（padding 為主 + max-width 輔助）：
  ```css
  .coffee-menu-desc {
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 75%;              /* 使用者指定 */
    margin-left: auto;
    margin-right: auto;
    line-height: 1.7;
    color: rgba(255, 255, 255, 0.65);
    font-size: 1rem;             /* 使用者指定（原 0.95rem） */
  }
  ```
- **驗證**：chrome-devtools computed style = maxWidth:75%、fontSize:16px（1rem）、padding 20px ✅

#### 🎬 index.html videoWrap 分析（未實作，僅評估）
- **議題**：是否可將咖啡豆 section 的 videoWrap 放入 owl-carousel banner 內部橫幅
- **風險**：影片載入過載（heavy）可能影響著陸頁效能 → 需進行效能評估後再決定
- **狀態**：待使用者決定

#### 📂 涉及檔案（3 個）
`templates/betweencoffee_delivery/coffee_menu.html` / `static/css/bc-components.css` / `betweencoffee_delivery/views.py`（無變更，僅分析）

### 2026-08-05（深夜）：bc-welcome-panel 社交登入 + 最後訂單快速下單

#### 🔐 社交登入邏輯（登入前/登入後雙狀態）
- **後端**：`betweencoffee_delivery/views.py`
  - 新增共用 `_build_landing_context()`（商品 + `is_authenticated` + `user_avatar` + `last_order_image` + `last_order_link`）
  - 新增 `_get_user_avatar()`：**社交頭像優先**（Google 字串 URL / Facebook 巢狀 dict / Facebook Graph API），否則 Profile 頭像
  - 新增 `_get_last_order_image()`：最後訂單第一個商品圖片
  - 新增 `_get_last_order_link()`：產生最後訂單商品詳情頁連結（含 `cup_level`/`milk_level`/`strength_level` query string）
- **模板**（`index.html` + `landing_v3.html` 同步）：
  - 登入後：「Hey, 歡迎回來, 喝返杯先!」+ 社群頭像（icmoon icon 或社交照片）
  - 登入前：「Buddy! 是時間補充咖啡因!」+ 登入連結 + icon
- **首頁替換**：`index.html` 備份為 `index_backup.html`，改用 `landing_v3.html` 內容；`Index` 視圖同步使用 `_build_landing_context`

#### 👤 Facebook 頭像修復（只顯示預設頭像問題）
- **根因**：Facebook `extra_data` 無 `picture` 欄位，且 Graph API `/picture` 未帶 access token 時回傳預設/模糊頭像
- **修復**：Facebook 分支附加 `account.socialtoken_set.first().token` 作為 `access_token` query 參數
- **驗證**：下載圖片分析 = 6240 種顏色、最大顏色比例 0.93%（真實照片，非預設灰頭像）✅

#### 🖼️ 最後訂單商品圖片（wakemeup.png → 最後訂單產品圖）
- 登入且有訂單：右側顯示最後訂單咖啡/咖啡豆產品圖；未登入/無訂單：維持 wakemeup.png

#### 🎨 UI 細部調整（bc-components.css）
- 兩行文字（greeting/points）行距：`gap 5px`、greeting `line-height:1` + `inline-flex`、points `line-height:1.2`
- 頭像與兩行文字組水平居中：`.bc-welcome-text` 改 `flex-direction:row; align-items:center`；新增 `.bc-welcome-info` wrapper；移除 points 三處 `padding-left` 縮排（60/61/55px）
- **chrome-devtools 驗證**：avatarCenter 758px = infoCenter 758px、offset 0px ✅

#### 🔗 最後訂單圖片包成連結（快速一鍵下單）
- 圖片包 `.bc-welcome-img-link`，跳轉到 `/coffee/{id}/?cup_level=..&milk_level=..&strength_level=..`
- `coffee.html` JS 讀取 query 預選杯量/奶量/濃度按鈕 + 同步 hidden input
- **驗證**：`LAST ORDER LINK: /coffee/8/?cup_level=Medium&milk_level=Medium&strength_level=Normal` ✅

#### 📐 圖片位移修正
- **根因**：圖片包進 `<a>` 後絕定位基準改變導致位移
- **修復**：`.bc-welcome-img-link` 接管圖片原本的 absolute 定位（桌面 top:-92px/160px、平板 -77px/140px、手機 -55px/110px），內層 img 填滿 100%
- **檔案**：`static/css/bc-components.css`

#### 📂 涉及檔案（6 個）
`betweencoffee_delivery/views.py` / `templates/betweencoffee_delivery/index.html`（含 index_backup.html 備份）/ `templates/betweencoffee_delivery/landing_v3.html` / `templates/betweencoffee_delivery/coffee.html` / `static/css/bc-components.css`

### 2026-08-05（下午）：bc-welcome-panel 細部 + Carousel GIF 響應式放大

#### 🎨 bc-welcome-panel UI 細部
- 「Hey, 歡迎回來」文字加大 20%：桌面 `1→1.2rem`、≤768 `0.82→0.98rem`、≤480 `0.75→0.9rem`
- 兩列文字行距縮減：`.bc-welcome-text` gap `2px→1px`
- **檔案**：`static/css/bc-components.css`

#### 🎠 Carousel 兩個 GIF 響應式放大（平板/手機太小修復）
- `.gif-box img`（cup_360.gif）三級放大：≤991 `70%`、≤768 `80%`、≤576 `90%`
- `.noise-img`（SVG）三級放大：≤991 `55vw`、≤768 `65vw`、≤576 `75vw`
- **技術重點**：`!important` 置於檔案末尾，強制覆蓋既有 `.noise-img { min-width:238px }` 規則
- **chrome-devtools 驗證（768px 平板）**：noise `238→422px（+77%）`、gif `384→537px（+40%）` ✅
- **檔案**：`static/css/style-utilities.css`

### 2026-08-05：首頁 Carousel / 深金容器細部調整 + Best Sell 修正

#### 🎠 Home Slider（owl-carousel）改為左側滾動循環動畫
- **檔案**：`static/js/main.js`
- **修改**：移除 `animateOut: 'fadeOutUpBig'` / `animateIn: 'fadeInUp'`（淡入淡出）→ 使用 owl-carousel 預設 translate 水平滑動（**向左滾動**）
- **新增** `smartSpeed: 700`（滑動速度 0.7 秒）
- **新增** `autoplayTimeout: 7000`（每 7 秒換一張，原 8000）
- 搭配既有 `loop:true` + `autoplay:true` → 第一張⇄最後一張無縫左側循環

#### 🔧 Carousel 層級修復（gif / SVG 固定底層）
- **問題**：`.img-owl-bg`（gif-box z-index:1）與 `.noise-img` 無 position/z-index，蓋住資訊文字與按鈕
- **修復**（`static/css/style-utilities.css` + `static/css/bc-components.css` 最後載入）：
  - `.img-owl-bg { z-index: 0 }`（原 1）
  - `.gif-box / .gif-box img { z-index: 0 }`
  - `.noise-img { position:relative; z-index:0; pointer-events:none }`
  - `.slider-text { position:relative; z-index:10; pointer-events:auto }`（資訊+按鈕最頂層）
- **驗證**：chrome-devtools computed style = noiseZ:0, gifZ:0, imgOwlZ:0, textZ:10 ✅

#### 🎨 深金容器（.bc-welcome-panel）細部調整
- **容器**：背景改為 `#292623`（原 #774606 由使用者改動）
- **user icon**：`38px→46px`（+20%、font-size 1.8rem），響應式 ≤768 `47px`、≤480 `41px`
- **兩列文字組合模組**：新增 `.bc-welcome-text` wrapper（HTML），CSS `flex:1; flex-direction:column; gap:2px`（行距縮減）
- **對齊**：`.bc-welcome-points` padding-left 同步 = avatar + gap（桌面 60px、≤768 61px、≤480 55px）
- **文字**：「按照之前口味落單?」（使用者改動）

#### 🏆 Best Sell「最強人氣」顯示 4 件
- **檔案**：`betweencoffee_delivery/views.py`
- **修改**：`LandingNew.hot_coffees` 限制 `[:3] → [:4]`（與 `Index` 一致）
- **原因**：Best Sell 區塊渲染 `hot_coffees`，原只取 3 件

#### 📂 涉及檔案（5 個）
`static/js/main.js` / `static/css/bc-components.css` / `static/css/style-utilities.css` / `betweencoffee_delivery/views.py` / `templates/betweencoffee_delivery/landing_v3.html`

### 2026-08-04：首頁深金容器 UI 全面調整（landing_v3.html）

#### 🎨 深金容器 .bc-welcome-panel
- **顏色**: `#774606`（深金，取代原 `#6b4f2a`）
- **寬度**: `width: 54%` 已註解 → `max-width: 630px` 由內容撐開
- **高度**: 經多輪縮減約 40%（padding 12→8、avatar 36→27、內部 gap 4→2、文字逐步縮小）

#### 📐 容器中心垂直對齊 carousel banner 底部
- `.bc-welcome-section` `margin-top`: `-120px` → `-55px`（= 容器高度一半，使容器垂直中心貼齊 banner 底部）
- 響應式: ≤768px `-50px`、≤480px `-45px`（按各斷點容器高度等比）

#### 🖼️ wakemeup.png 與「上次訂單慣常口味」文字
- 圖片: `160px × 160px`、`top: -92px`（上移浮出容器）、`right: 0`
- 文字: `margin-bottom: -30px` 上移靠近照片（響應式 -22/-16px）
- `.bc-welcome-imgbox` `position: relative` + `align-items: center` → 圖片與文字共用中心軸垂直對齊

#### 📱 響應式（≤768 / ≤480 兩級漸進縮放）
- 容器: `92% / 96%`、padding 等比縮小
- 圖片: `150px / 120px`、avatar `28px / 24px`
- 文字: greeting `0.82rem / 0.75rem`、points `0.75rem / 0.68rem`
- 先前無任何響應式規則（固定寬度小螢幕會溢出），本次完整補齊

#### 🧩 全部改為 .bc-welcome-* UI 類別（bc-components.css）
- 新增: `.bc-welcome-section` / `.bc-welcome-wrap` / `.bc-welcome-panel` / `.bc-welcome-left` / `.bc-welcome-name` / `.bc-welcome-avatar` / `.bc-welcome-greeting` / `.bc-welcome-points` / `.bc-welcome-imgbox` / `.bc-welcome-img` / `.bc-last-order`
- `landing_v3.html` 完全移除深金容器區塊的內聯 CSS（符合 CSS 統一規範）

#### 📦 涉及檔案（2 個）
`landing_v3.html` / `static/css/bc-components.css`

### 2026-08-03（晚上）：訂單/付款頁面 UI 統一修復

#### 🎨 Cash 付款頁面
- `fa-money-bill-wave` 圖標：`fa-3x`（約 48px）→ 新增 `.payment-icon-cash` class（**78px** 桌面 + 行動一致）

#### 💳 訂單確認頁 4 個支付 Icon
- 新增 `.bc-payment-label-icon` 獨立 class（**1.3rem**、品牌金色 `--bc-gold`）
- 與文字**水平對齊**：`.payment-label-text { display:inline-flex; align-items:center; gap:12px }`
- 移除舊 `margin-right`，改用 flexbox gap

#### 🔤 訂單確認頁背景文字（改用 coffee.html 相同機制）
- 從 `<span class="title-bg-head-v3">`（inline 元素）→ `data-bg-text` + `.bc-section-with-bg-text`（`::before` 偽元素）
- **獨立 div** 置於 `{% block content %}` 開頭（導覽列與內容之間）
- **`.bc-bg-text-top { height:0 }`**：不佔文件流空間，主內容不再被向下推
- 參數：`top:150px`（遠離導覽列）、`font-size:16vw`、`left:1vw`、Mogra 字型、opacity .045
- ⚠️ **CSS 順序**：`.bc-bg-text-top::before` 必須在 `.bc-section-with-bg-text::before` **之後**（同 specificity，後者覆蓋前者）

#### 📐 profile 3 頁面導航列統一（與卡片同寬）
- `profile.html` / `loyalty_dashboard.html` / `order_history.html`：導航容器 `col-12` → `col-12 col-lg-8`（與下方卡片 `col-lg-8` 一致）

#### 📱 會員導航列響應式統一修復
- **移除** `member_nav.html` 的 inline `<style>`（`width:100%` + `flex:1` 對所有螢幕寫死，與全局 `@media` 衝突 → 行動螢幕縮放/文字壓縮/激活狀態異常）
- **統一在 bc-components.css 管理**：
  - `.member-nav-container { display:flex; width:100% }`（撐滿父欄與卡片對齊）
  - `a.member-nav-item { flex:1; justify-content:center; white-space:nowrap }` + span 省略號保護
  - `@media (max-width:576px)`：`flex:1 1 auto`、`padding:10px 12px`、`font-size:0.85rem`（文字不縮放、激活狀態正常）

#### 📦 涉及檔案（9 個）
`cash_payment.html` / `order_confirm.html` / `member_nav.html` / `loyalty_dashboard.html` / `order_history.html` / `profile.html` / `bc-components.css` / `style-custom.css` / `style-utilities.css`

### 2026-08-03：全站行動響應式修復 + MCP 伺服器修復 + 付款頁 UI

#### 🤖 MCP 伺服器修復（2 個）
- **django-manager MCP**：
  - 原因：設定指向 `django-mcp-server.js`，但檔案不存在（MODULE_NOT_FOUND）
  - 修復：建立新 `django-mcp-server.js`（4 個工具：django_run_command / django_order_info / django_queue_status / django_recent_orders）
  - 技術：SDK `exports` 攔截 bare specifier 導致路徑重複（`dist/cjs/dist/cjs`），改成**絕對路徑**載入 SDK 與 zod
  - 驗證：initialize + tools/list 回應成功
- **chrome-devtools MCP**：
  - 原因：預設尋找 Google Chrome stable，但系統無安裝
  - 修復：設定 `--executable-path=/snap/bin/chromium` + `--isolated`（臨時 profile 避免鎖衝突）
  - 驗證：手動啟動可開頁 `http://localhost:8081/`

#### 📱 全站行動響應式修復
- **支付確認頁 Y 軸滾動條**（`.svg-bg-4`）：容器加 wrapper 裁切 → 後發現 SVG 位移，**還原原始結構**（SVG 直接放 section 內，無覆蓋規則）
- **行動導航背景透明化**：`.navbar.ftco-navbar-light.bg-dark { background: transparent !important }`（高 specificity 覆蓋）
- **漢堡菜單圖標白色**：`.navbar-dark .navbar-toggler-icon` stroke `#ffffff`
- **profile 3 頁面 body 外部邊距**（profile / loyalty / orders）：`.svg-bg-5` 固定 680px 在行動螢幕水平溢出撐寬 body → `.svg-bg-container { overflow: hidden }` 裁切
- **`.ftco-section-blank-small` 響應式**（13 模板共用）：原 CSS 左右 `7em` 內縮 bug + `min-height: 26vh` 全螢幕相同 → 新增 991/768/480 三級漸進縮減
- **profile D 評估**: 保留 `.ftco-*` class，Phase D 暫緩

#### 💳 付款頁 UI 改良
- **FPS 付款頁 logo**：`fps-logo.png` → `fps_icon.svg`，移除 inline 100px → CSS `.payment-logo`（128px 桌面 / 110px 行動）
- **FPS/Cash 操作按鈕**：
  - 原 `mr-3`/`ml-2` 彼此抵消 → 改 `.bc-payment-actions` flex 容器（gap 12px）
  - 寬度：主要按鈕（CTA）`flex: 1.12 / max-width 246px`（+12%）、次要 `flex: 0.88 / max-width 194px`（-12%）
  - 動作螢幕（≤768px）：百分比 56%/44% + 覆寫 `.calltoaction-btn` 固定 230px 溢出
  - CTA 確認：`我已完成支付/確認訂單` 為 `btn-primary + calltoaction-btn` 金色主按鈕

#### 🔧 其他修復
- `eshop/models/order.py`：支付確認頁頂部「支付成功」圖標 `fa-badge-check`（Pro-only 顯示方塊）→ `fa-circle-check`（Free 6.0.0 可用，與已完成狀態卡一致）
- **GitHub**: 待 commit/push


---

- Migration 0001-0053 已成功應用
- Supabase 免費方案 500MB 儲存綽綽有餘

## 近期修復記錄

### 2026-08-01（下午後）：全站安全修復 + 支付寶金鑰輪換 + FPS/Cash 付款頁 UI
- **🔴 全站安全審查與修復**：
  - 從 git 追蹤移除 4 個敏感金鑰檔案（`keys/alipay_*.pem`、`betweencoffee_delivery/keys/*.key`）
  - `.gitignore` 排除 `keys/`、`*.pem`、`*.key`、`*.crt`
  - `settings.py` 移除明文密碼/API keys/資料庫憑證註釋 + 硬編碼 PayPal Client ID/Secret
  - `DebugMiddleware` 移除（不再記錄訂單 POST 個資與 Session 到日誌）
  - 加入 HSTS（`SECURE_HSTS_SECONDS=31536000` + includeSubdomains + preload）+ Referrer Policy
  - 強化密碼驗證（CommonPasswordValidator + NumericPasswordValidator）
- **🔑 支付寶金鑰輪換**：
  - openssl 生成新 RSA2 金鑰對（2048-bit）
  - 用戶在支付寶控制台完成「加簽變更」（上傳新應用公鑰 + 取得新支付寶公鑰）
  - 更新本機 `keys/` 檔案（新私鑰 + 新支付寶公鑰）
  - `settings.py` 改為 **環境變數優先** `read_alipay_key()`（Render 用環境變數，本地 fallback 到 keys/ 檔案）
  - Render 環境變數 `ALIPAY_APP_PRIVATE_KEY` / `ALIPAY_PUBLIC_KEY` 已設定為新金鑰
- **📄 FPS 付款頁面 UI**：
  - 新增「商品明細」+「訂單資訊」區域（付款說明上方）
  - 隱藏參考編號（不顯示客戶）
  - 付款說明組件全寬
  - 按鈕統一 `calltoaction-btn`：主按鈕金色、返回修改灰色
- **📄 Cash 付款頁面 UI**：
  - 付款說明組件全寬
  - 確認訂單按鈕金色、返回修改灰色
- **🛠️ 咖啡/咖啡豆詳情頁按鈕間距**（進行中）：
  - `coffee.html` / `bean.html` 立即購物與加入購物車按鈕之間加空間
  - 已嘗試 `mr-3`、`gap: 1rem`（inline），用戶反饋仍未修復，需診斷 CSS 覆蓋/順序
- **GitHub**: 安全修復已 push（commit `46fb0d3`）；FPS/Cash UI + coffee/bean 待 push

### 2026-08-01：首頁 feed 區塊兩層設計（形狀輪廓捲動 + 底部照片固定）
- **最終效果**（用戶確認）：
  - 第一層（上層 `.feed__layer-parts`）：形狀外部為**品牌深黑純色 `#0e0e0e`**（移除 bg_4.jpg），反相裁切（形狀內部是透明洞），**水平捲動動畫 feedScroll 60s**
  - 第二層（底層 `.feed`）：固定顯示 `index_feed_image.png`，**無動畫**
  - 視覺：形狀內部透出固定照片、形狀外部深黑純色捲動，形狀輪廓清晰
- **改動**：
  - `static/css/landing.css`：`.feed__layer-parts` = `#0e0e0e` + `background-image: none` + `clip-path`（反相 mask）+ `feedScroll`；`.feed` 底層 = `index_feed_image.png` 固定
- **技術關鍵**：
  - clip-path 是「反相裁切」（SVG path 先 `M2430 570H0V0H2430V570Z` 填滿矩形、再挖空咖啡形狀）→ 形狀內部是洞、透出底層
  - 蒙版是黑白邏輯（只決定顯示/隱藏，不產生顏色）；啡色是 index_feed_image.png 照片原色
  - 過程中釐清：形狀內部若完全透明＋底層也是同一張照片，形狀輪廓會消失（需深黑外部或不同背景襯托輪廓）
- **GitHub**: 待 commit（`static/css/landing.css`）

### 2026-07-31（晚）：支付寶回調 404 診斷 + 客戶端狀態卡即時更新修復 + Toast 靜默化
- **支付寶 Whitelabel 404 診斷**：
  - 確認 Whitelabel Error Page 是**支付寶 sandbox 收銀台伺服器（Java Spring Boot）自己的 404**，非我們系統
  - DevTools Network 記錄顯示 404 發生在 `cashier-sandbox.dl.alipaydev.com`，請求從未到達我們的網站
  - 修正 `.env`：原先改為 Render URL 破壞本地測試（瀏覽器跳轉機制下 `localhost:8081` 對本地測試可行），已**還原為 `http://localhost:8081/...`**
  - **Render 環境變數**：獨立設定 `ALIPAY_RETURN_URL` / `ALIPAY_NOTIFY_URL` 為 `onrender.com` 網域（部署 live）
- **支付寶簽名驗證 unquote bug 修復**（防禦性）：
  - `eshop/alipay_utils.py` — `verify_alipay_notification()` 移除重複 unquote（破壞 sign）
  - `eshop/views/payment_views.py` — `alipay_callback()` / `alipay_notify()` 移除再次 unquote
  - 原因：Django request.GET/POST 已自動解碼，二次 unquote 會把 sign 的 `+` 轉空格導致驗證失敗
- **客戶端訂單狀態卡 10-15 秒延遲修復**（兩層 bug，現已即時更新）：
  - `eshop/consumers.py` `OrderConsumer.order_update()`：將 `event['data']` 展開到 event 頂層，使 `event.get("status")` 不再為 None（原始廣播消息的資料在 `data.status`）
  - `eshop/consumers.py` `QueueConsumer.order_update()`：**保留** `queue_update` 格式給員工端，**新增**同時發送 `order_status` / `payment_status` 格式給客戶端
    - 根因：客戶端訂單狀態卡連到 `/ws/queue/`（QueueConsumer）並監聽 `order_status`，但 QueueConsumer 原本只轉發 `queue_update` → 即時更新被丟棄，只能靠 30 秒輪詢兜底
  - 驗證：`test_queue_consumer_order_update.py` 單元測試確認三種格式（queue_update / order_status / payment_status）皆送出
  - 用戶實際測試：狀態卡可即時更新 ✅
- **Toast 靜默化**：`static/js/order_status_cards.js` 的 `showToast()` 改為僅 console.log，不再呼叫 `window.toast.info()`（先前只在模板內聯 showToast 靜默，漏掉類內方法）
- **新增診斷腳本**：`verify_alipay_fix.py`、`test_ws_order_update.py`、`test_queue_consumer_order_update.py`
- **注意**：上述修改僅本地開發生效，待 commit/push 後部署 Render

### 2026-07-31：Phase 3E 測試覆蓋率提升 + 測試測試商品清理
- **測試數**: 52 → **93** 全部通過（-2 skipped）
- **新增測試**:
  - `test_audit_logger.py`（13 個，audit_logger 0%→100%）
  - `test_status_display.py`（15 個，status_display 20%→100%）
  - `test_payment_handler.py`（13 個，payment_handler 30%→90%）
- **修復既有測試**: `test_models`/`test_whatsapp_notifier`/`test_payments`/`test_queues`/`test_order_comprehensive`
  - `name` → `contact_name`（欄位 0035 已移除）
  - 訂單號斷言改為 `#<id>` 簡短格式（2026-07-28 統一）
  - 移除 `pickup_time` 過時斷言（欄位已重新加入）
- **新增工具**: `scripts/analyze_test_coverage.py`（覆蓋率分析）、`scripts/run_tests.sh`（一鍵測試）、`docs/coverage-gap-report.md`
- **清理**: 刪除測試用虛擬商品（咖啡 11/12/13、咖啡豆 9）
- **Phase D 評估**: 建立 `.bc-section`/`.bc-footer` 對應定義但發現背景重複問題，已還原 base.html footer 為原始 `ftco-*` class，Phase D 暫緩
- **GitHub**: commit `ec4b311`

### 2026-07-26：新增濃度選擇功能 + 前端渲染顯示

#### 1. 濃度選擇功能（完整端到端實作）
- **模型**: CoffeeItem + CartItem 新增 `strength_level` 欄位（Normal/Extra）
- **前端**: 咖啡詳情頁新增濃度按鈕組（預設/特濃）
- **後端**: `OrderModel.translate_option()` + `_add_chinese_options()` + `get_order_display_items()` 支援濃度翻譯與顯示
- **購物車**: `Cart.add()` + `Cart.__iter__()` 支援 `strength_level` 傳遞
- **驗證**: `verify_strength_level_comprehensive.py` 23/24 測試通過（1項為預先存在的API問題）
- **文件**: `eshop/models/shop_items.py`、`eshop/models/cart_item.py`、`cart/cart.py`、`templates/betweencoffee_delivery/coffee.html`

#### 2. 前端選項顯示統一（strength_level 顯示修復）
- **根因**: 後端 `order_views.py` 的 `items.append()` 遺漏 `strength_level` 欄位傳遞
- **修復**: `order_views.py`（get + post 共4處）、`cart/views.py` 加入 `"strength_level"` 
- **前端渲染**: `bc-slideout-cart.js` 加入濃度顯示，排序統一為 杯量→濃度→牛奶
- **所有頁面**: `order_confirm.html`、`cash_payment.html`、`order_history.html`、`order_payment_confirmation.html` 均已加入濃度顯示

#### 3. 前端 UI 調整（杯量按鈕 + feed 漏光 + 選項隱藏）

#### 3.1 首頁 feed 區塊 clip-path 漏光修復
- **問題**: `.feed__layer-parts--01` 與 `--02` 兩個 clip-path div 在 CSS 動畫中產生約 1px 合成層子像素縫隙，底層背景照片從接縫露出
- **修復**: `margin-left: -2px` 讓第二個 div 物理重疊 2px 填補縫隙
- **移除** `will-change`、`translateZ(0)`、`box-shadow`、`outline` 等干擾合成層的多餘屬性
- **文件**: `static/css/landing.css`

#### 2. 咖啡詳情頁杯量按鈕尺寸調整
- **杯量按鈕高度**: 40px → **72px**（+80%）
- **oz 標籤字體**: 0.6rem → **0.72rem**（+20%）
- **oz 標籤 padding**: 2px 5px → **3px 6px**
- **oz 標籤 margin**: 3px → **0**（貼右上角邊緣）
- **「杯量 :」文字垂直居中**: 加入 `form-group.d-flex { align-items: center; }`
- **文件**: `static/css/bc-components.css` + `templates/betweencoffee_delivery/coffee.html`

#### 3. 前端隱藏「少」杯量選項
- 在咖啡詳情頁中，Small/12oz（「少」）按鈕加上 `hidden` 屬性，前端不再顯示
- 後端資料模型 `cup_level` 邏輯完整保留不受影響
- **文件**: `templates/betweencoffee_delivery/coffee.html`

#### 4. TemplateSyntaxError 修復
- **問題**: `{% block content %}` 內嵌套了 `{% block extra_css %}`
- **修復**: 直接將 `<style>` 放在 content 區塊內
- **文件**: `templates/betweencoffee_delivery/coffee.html`

### 2026-08-02：訂單狀態卡 Icon 全面優化
- **改動**: 前後端 icon 統一（4 檔案）：
  - `eshop/models/order.py` + `order_payment_confirmation.html`（169/244）+ `order_status_cards.js`（699）
  - 已完成：`fa-trophy`/`fa-check-double` → `fa-circle-check`
  - 製作中：`fa-coffee` → `fa-mug-hot`
  - 待取餐：`fa-check-circle` → `fa-bell`
- **最終流程**: 📋 → ☕ → 🔔 → ✅
- **驗證**: grep fa-trophy 無殘留、Django check 通過

### 2026-08-01：全站安全修復 + 優先處理徽章 + WhatsApp Token
- **安全**: 修復 IDOR（api_cancel_order/OrderConsumer/QueueConsumer/ws_fallback_api）+ 4 API 權限 + 27 安全測試通過
- **徽章**: `.badge-expedited` 統一（4 JS + CSS）
- **WhatsApp**: Token 更新（過期 → HTTP 200 驗證）、新增 `test_whatsapp_diagnosis.py`

### 2026-07-24：Supabase 資料庫遷移
- **改動**: Render PostgreSQL → Supabase（新加坡節點）
- **驗證**: Migration 全部成功，2,012 筆訂單、676 筆佇列記錄完整

### 2026-07-23：models.py 拆分 + pipeline.py 拆分
- **models.py**: 1636行 → 5 個子模組（base, shop_items, cart_item, order, queue_models）
- **order_status_manager.py**: 1259行 → 4 個子模組
- **驗證**: 全面測試通過，Django 系統檢查 0 issues

### 2026-07-22：Phase 2 收尾
- 修復 2 個 URL bug（FPS/現金付款路由不匹配）
- 加上 `@staff_api_required` 裝飾器
- `cleanup` 加 try-catch 保護
- 降級方案驗證通過

### 2026-07-21：離線支付重構 + 端到端修復
- 重構 `confirm_offline_payment` 消除重複邏輯
- 新增 CoffeeQueue.coffee_count 和 preparation_time_minutes
- QueueConsumer 新增 order_update 處理器

### 2026-07-19：Render 部署 migration 修復
- 修復 0037-0046 migration（SeparateDatabaseAndState 策略）
- 新增 migration 0047 重構 Barista 模型欄位

### 2026-07-13：結帳頁面購物車清空後更新
- `window.location.reload()` → `window.location.href = '/coffee_menu/'`

### 2026-07-11：員工頁面 Bootstrap tab 改造
- SubtabManager 類別（完全接管 tab 切換邏輯）
- nav-link active 偏移修復（margin-bottom → transform）
