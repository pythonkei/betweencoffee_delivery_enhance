# 系統狀態

> 2026-11-11 複驗版（2026-10-25 版之後累積 10-28 ~ 11-11；原檔 181KB 已封存：`docs/archive/memory_bank_04_full_20261017.md`）。
> 逐筆變更細節請用 `git log`，不要回頭讀封存檔。

## 系統狀態摘要

| 維度 | 狀態 | 備註 |
|------|:----:|------|
| 資料庫（Supabase） | ✅ 正常 | 2026-09-15 專案曾消失→後台還原後恢復（pooler 約 3 分鐘註冊 tenant）；07-27 還原點與本地 08-16 落差已回補（訂單 2661／佇列 1036）。2026-10-23 曾回 `ENOTFOUND tenant/user postgres.tmxvuwadktvfjtawckib not found`（當次部署失敗），**2026-10-24 15:43Z 手動部署 `a732cc28` 成功 live ⇒ 連線已恢復** |
| 核心功能 | ✅ 完整 | 下單 → 支付 → 製作 → 取餐 |
| WebSocket | ✅ 穩定 | 三層架構（WebSocketCore → 橋接 → 業務），InMemoryChannelLayer |
| 支付 | ✅ 4 種 | PayPal / Alipay / FPS / 現金 |
| 社交登入 | ✅ 已修復 | Google / Facebook（django-allauth） |
| 忠誠度 | ✅ 基礎 | 積分 + 優惠券 |
| 員工管理 | ✅ 完整 | 隊列 + 付款確認 |
| 員工端渲染器 v2 | ✅ 完成 | BaseOrderRendererV2 + 4 個 v2 渲染器 |
| About 首屏影片 | ✅ 多層輪播 | `/about/` 的 `.mv-video` 層數＝min(片單, `views.MV_MAX`=7)、片單 `views.MV_VIDEOS`＝`hero_00`~`hero_06` **依序不洗牌**、剩 0.75s 下一層交叉淡入 0.6s；首屏輪播品項另受 `MV_EXCLUDE_IDS`（現 `{7}` → 5 張）控制（2026-11-07 定案） |
| 測試 | ⚠️ 不足 | 覆蓋率低（以 `docs/verify/` CDP 腳本補前端驗證） |
| 監控 | ⚠️ 基礎 | 無告警系統 |
| 部署（Render） | ⚠️ 部署落後 66 筆 | 現行 `live`＝commit `c3f7509c`（環形照片列 hover 徽章）／trigger `manual`／finished **2026-11-03 08:47Z**（2026-11-11 Render API 複驗）。`origin/main` 尖端＝11-11（`b78d82d1` 品牌舞台 `footer*`→`bc-stage-*` 改名）⇒ **待部署 `c3f7509c..origin/main`（66 筆 code／docs）**（11-04 ~ 11-11 累積：about 首屏 sticky 影片與三段、`bc-catch` 字輪、`bc-popeye50` 回歸、詳情頁容器加寬、環形照片列改名與徽章、首屏影片 7 支多層輪播、黑遮罩 →**75%**、製程模組移 about、首頁 hero 影片輪播與落點洗牌、who section 移首頁、浮動購物車圖示 10 款、品牌舞台 class 改名）。**autoDeploy＝off，push 不會觸發部署** |
| 版本控制 | ✅ 已推齊 | `origin/main` 尖端＝2026-11-11 品牌舞台改名 `b78d82d1`＋本檔同步（以 `git log -1` 複驗，不寫死 hash）；本機 `main`＝`origin/main`；工作區僅剩 `.gitignore` 排除的本機暫存素材（`hero_06_.webm`、`pa-3__.webp`）與已刪檔（`staff0[1-4].png`、`wakemeup.png`）尚未提交 |

## 資料庫現狀

| 面向 | 本地開發 | Render 生產 |
|------|:--------:|:-----------:|
| 資料庫 | 本地 PostgreSQL | Supabase PostgreSQL |
| 連線 | `127.0.0.1:5432` | `pooler.supabase.com:6543` |
| 認證 | `postgres/postgres` | Supabase 專案憑證 |
| Migration | 手動執行（已套用至 `0083`，`0081`–`0083` 已入版控） | 部署時自動執行（正式站 `a732cc28` 已到 `0080`；`0081`–`0083` 隨下次部署套用） |
| 管理 | psql / pgAdmin | Supabase Dashboard |

> ℹ️ 生產 DB 連線：2026-10-23 曾回 `ENOTFOUND`（tenant `postgres.tmxvuwadktvfjtawckib`）導致部署失敗，但 2026-10-24 15:43Z 的手動部署（`a732cc28`）**成功且 live** ⇒ 連線已恢復。生產 migration 進度請以該次部署後的 `eshop/migrations` 記錄為準；本機 MCP 的兩個 PostgreSQL 連線仍是同一顆本地庫（`0081`–`0083` applied 時間戳同為 `2026-10-24T06:03:31Z`），不可當作生產現況。

## 近期變更（最近 15 筆，一行式）

| 日期 | 內容 |
|---|---|
| 2026-11-11 | **品牌舞台 `#bc-brand-stage` 的 `footer*` class 全面改名為 `bc-stage-*`**（`b78d82d1`，外觀零變化）：16 組對照表寫在 `static/css/bc-brand-stage.css` 檔頭（`.footer`→`.bc-stage-content`、`.footer-time`→`.bc-stage-time`、`.footer-logo-*`→`.bc-stage-photo-*`、`.footer-socials`→`.bc-stage-socials`、`.m-footer-*`→`.bc-stage-m-*`、Webflow 拼錯的 `.foooter-mail`→`.bc-stage-marquee`…）；同步 2 partial＋CSS＋JS（`_footerLogoClick`→`_stagePhotoClick`）＋`index/about.html`（`?v=20261110c`）＋`docs/verify/` 六支 CDP 腳本 selector；**不動** `<footer>` 標籤、所有 `id`／`data-*` 與 `#bc-sticky-mv .foooter-mail`。驗證：CSS 套表後與改名前逐字元相同（245 規則）、partial 結構相同、`/` 390×844 六項幾何不變、`cdp_verify_bg_footer.py` 41/41 PASS |
| 2026-11-10 | ① **sukima「who」section 由 `/about/` 搬到首頁**「推薦頁面」雙卡下方（`15c2b93c`，只改兩個模板，CSS／JS 未動）；② **浮動購物車圖示定案 `04 手提包（線條）`**：`base.html` inline SVG 雙態（`.bc-fc-line`／`.bc-fc-solid`）＋`bc-components.css` `svg.bc-fc-icon` 尺寸，版號 `20261109a`；③ 品牌舞台子 class 改名完成並驗證（見 11-11） |
| 2026-11-09 | ① 首頁 hero 背景照片黑蒙版 40% → 50% → 60% → 70% → **75%**（`bc-photoarea.css` `--pa-dim: .6→.5→.4→.3→.25`，`?v=` 依序 `20261109c`→`d`→`e`→`f`→**`g`**→**`h`**）；② **「咖啡豆製程」模組（`.bc-home-service`）自首頁 `[2b-2]` 整組移到 `/about/` 的 `.bc-search` 正下方**（index 移除 include／CSS／JS 三處，about.html 補回同樣三處；partial／CSS／JS 檔只改檔頭註解、版號 `20261030a`→`20261109a`，邏輯未動）；③ **首頁 hero 照片落點「每次載入重排」**（比照 hicard 原站：view `_photoarea_slots()` 洗牌 → `context["pa_slots"]`，模板逐格寫 `x_{{ pa_slots.N.x\|default:舊值 }}`；x/y 各自是 1–5 排列、`data-para`／`.d_n`／`.yoko` 固定不動；伺服器端決定 ⇒ 無跳位閃動；無 `static/**` 改動、不必升 `?v=`）；④ **首頁 hero 第 3 格影片改為「可輪播容器」**（view 常數 `PA_VIDEOS`＝`hero_00`→`hero_04`→`hero_05` 依序不洗牌 → `context["pa_videos"]`；模板 `{% for %}` 長出多支 `<video>`，CSS 疊同一框＋只有 `.is-on` 可見、JS `setupVideoCarousel()` 距結束 0.75s 換片、0.6s 交叉淡入；要加片只改 `PA_VIDEOS`；`?v=` css `20261109h`／js `20261109c`） |
| 2026-11-06 | `/about/` **重新載入 `bc-popeye50` 字輪並改置於 `#bc-sticky-mv` 正下方**（11-03 起停用的模組回歸）：只改 `about.html` 三處（extra_css 連結／section markup 插在 sticky-mv 收尾之後／`defer` JS 緊接 `bc-sticky-mv.js`）；CSS／JS 檔未改 ⇒ 沿用 `?v=20261102f`／`?v=20261102c`。實測 DOM 順序 sticky-mv→popeye50→series、gap 0；1440／390 無水平溢出、字輪自動旋轉＋中心連結導頁正常、sticky 影片不受影響 |
| 2026-11-04 | `/about/` 首屏 `bc-sticky-mv` 三段（`.mv-stage`）改回品牌舞台 **7 欄 grid 明確格位**（原 flex 堆疊位置與 about 頁不同；fresh `1/3/2/6`、roasted `2/4/3/7`＋8px、marquee `2/3/3/5` 同列靠左；≤991px 6 欄覆寫），字級改原站流體公式（h1 `90vw/14.4`、p1 `14vw/14.4`）；`bc-sticky-mv.css?v=20261104c`（`0bd7172d`） |
| 2026-11-04 | 補齊 10-28 起累積未提交前端（`e9bdefdb`）：首頁「咖啡豆製程」模組（`bc-home-service.{css,js}`＋partial＋`make_hs_images.py`＋`images/home-service/*`）、`/about/` 字體輪播 `bc-catch.css` **入庫**（此檔先前只在 about.html 被引用、未 commit ⇒ 正式站 404）、品牌舞台 `.footer-time` 8→10 欄（天氣移到 `{` 左側，欄10 鏡像留白）＋天氣 `z-index:3`、capabilities `--cap-scale` 等比放大＋置中、環形照片列左右拖曳（`bc-hand-ring.js bindDrag()`）、`/bean/<id>/` `.bc-staff` 字級 17／16／16、`.gitignore` 排除 `hero_bg.mp4`（81MB 未引用）等暫存大檔 |
| 2026-11-03 | `/about/` 首屏改 **sticky 影片＋產品照弧形輪播**（移植 yurumaru.life `.page-top__mv__wrap`；`bc-sticky-mv.{css,js}`、`static/media/hk_topshot-720p.mp4` 4.4MB＋poster），取代 11-02 的 popeye50 字輪（舊檔保留、不再載入）：`--mv-len:200vh`、`--mv-text-h:64vh`、原生 JS 重寫 Splide（per 3/1、autoplay 4s、前後各一組複本無縫循環）；同日修 loop 歸位抖動（`jump()` 加 `.is-jumping` 同關過渡）與滑鼠拖曳被原生 `dragstart` 中斷（`e.preventDefault()`），並在產品列下方加品牌舞台三段（`e2a5d747`／`ef98d37e`） |
| 2026-11-03 | 首頁品牌舞台環形咖啡照列 hover 互動（移植 hub.ballaholic.jp `.embla`）：`static/js/bc-hand-hover.js`（跟隨游標圓形徽章 108px、`mouseleave` 延遲 200ms、觸控不啟動）＋ `bc-hand-ring.css` 照片 hover 放大（current 1.08／其餘 0.56，僅 `(hover:hover) and (pointer:fine)`）；`bc-hand-ring.css?v=20261103c`（`c3f7509c`，**現行 live**） |
| 2026-11-02 | 首屏字輪微調（已由 11-03 sticky mv 取代）：直徑係數 `0.92→0.86`、中心品名 13.5／13.2px、手機 `.cw-wheel` 徑向遮罩、中心圖文＋SERIES 項目連結咖啡詳情頁（`87d66040`）；另 `bc-popeye50` 移除黑底改鋪 `bg_4` 材質（`33a4c06a`） |
| 2026-10-31 | `/about/` 新增「字體輪播」（移植 eightdesign.co.jp `.PZL1xq_catch`：3 行 × 4 種字體、`.74s` step-end／每格 185ms、行相位 −0.09／−0.18s、純 CSS 無 JS＋`prefers-reduced-motion` 靜止），置於 `.bc-reviews-section` 正下方；樣式 `static/css/bc-catch.css`（本輪 `e9bdefdb` 才入庫） |
| 2026-10-30 | 首頁「咖啡豆製程」捲動模組 `[2b-2]`（移植 union-tec.jp `homeService`：clip-path 膠囊→滿版、4 段輪播＋模糊轉清晰、標籤與網格字母；原生 JS 不依賴 Alpine／Lenis／three.js／GSAP）；素材 `images/home-service/hs-{1..4}{,-sp,-blur,-clip}.webp`（`scripts/make_hs_images.py` 產生）；完整數據 → `docs/archive/task_progress_20261102_home_service.md` |
| 2026-10-28 | capabilities 模組搬家（about→首頁）＋`--cap-scale` 等比放大（≥834 1.30／≥1280 1.40／≥1920 1.60）＋頁面置中；`/bean/<id>/` `.bc-staff` 字級放大（`bc-components.css?v=20261028a`）；自架 `trade-gothic` 字型＋`.bc-series-heading` 行距／字級；bean SERIES 括號滑桿搬到商品主區下方（`29eb67d1`／`f57eb768`／`f730abab`） |
| 2026-10-24 | #61 首頁「推薦頁面」雙卡（移植 union-tec.jp `recommendedPages`）＋同日調整：① 隱藏首頁 `#bc-stage-socials`（extra_css `.bc-brand-stage-hero #bc-stage-socials{display:none}`，`hidden` 屬性會被 `.footer-socials{display:flex}` 蓋掉）② 模組由 `.feed--video` 下方搬到 `.bc-brand-stage-hero` 正下方。新版號 `?v=20261024b`（css）／`20261024a`（js）（`d27f7c90` 已 push） |
| 2026-10-24 | #60 品牌舞台環形照片列「第一張咖啡」改 goo 揭示（沿用標題文字的 `stdDeviation 50→0` 時間軸，不再 scale 0.5→1）；`bc-hand-ring.js/css`、`bc-brand-stage.js`（新增 `window.BC_MEDIA_REVEAL`）、index／about `?v=20261024a`（`7a073263` 已 push） |
| 2026-10-24 | #59 咖啡豆詳情頁「店員氣泡」：`BeanItem` 10 欄位＋`measure_bubble_geometry()`、Admin 2 fieldset、migration `0081`–`0083`（幾何／文案 seed）；`.bc-coffee-comment` 宿主 selector 改中性 `.bc-photo-comment`（`edf3e87c` 已 push） |
