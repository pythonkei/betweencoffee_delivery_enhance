# 系統狀態

> 2026-10-25 複驗版（2026-10-23 精簡版；原檔 181KB 已封存：`docs/archive/memory_bank_04_full_20261017.md`）。
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
| 測試 | ⚠️ 不足 | 覆蓋率低（以 `docs/verify/` CDP 腳本補前端驗證） |
| 監控 | ⚠️ 基礎 | 無告警系統 |
| 部署（Render） | ⚠️ 部署落後 3 筆 | 現行 `live`＝deploy `dep-dbed2vm7bikc73825md0`／commit `a732cc28`／trigger `manual`／finished 2026-10-24 15:43Z（2026-10-25 Render API 複驗）。2026-10-23 的 `56c1bcc9` 失敗（`dep-dbde3rpsrm7s73beap6g`／Supabase pooler ENOTFOUND）已由 10-24 成功部署排除 ⇒ **DB 可連**（該次資料庫狀態現為 `deactivated`）。仍落後 3 個 code commit：`edf3e87c`（#59）、`7a073263`（#60）、`d27f7c90`（#61）＋文件提交。**autoDeploy＝off，push 不會觸發部署** |
| 版本控制 | ✅ 已推齊 | `origin/main`＝`7230896b`（code 尖端 `d27f7c90`＋文件 `f597e259`／`7230896b`；2026-10-25 推 `a732cc28..d27f7c90`、`d27f7c90..7230896b`），本機 `main`＝`origin/main`、工作區乾淨 |

## 資料庫現狀

| 面向 | 本地開發 | Render 生產 |
|------|:--------:|:-----------:|
| 資料庫 | 本地 PostgreSQL | Supabase PostgreSQL |
| 連線 | `127.0.0.1:5432` | `pooler.supabase.com:6543` |
| 認證 | `postgres/postgres` | Supabase 專案憑證 |
| Migration | 手動執行（已套用至 `0083`，`0081`–`0083` 已入版控） | 部署時自動執行（正式站 `a732cc28` 已到 `0080`；`0081`–`0083` 隨下次部署套用） |
| 管理 | psql / pgAdmin | Supabase Dashboard |

> ℹ️ 生產 DB 連線：2026-10-23 曾回 `ENOTFOUND`（tenant `postgres.tmxvuwadktvfjtawckib`）導致部署失敗，但 2026-10-24 15:43Z 的手動部署（`a732cc28`）**成功且 live** ⇒ 連線已恢復。生產 migration 進度請以該次部署後的 `eshop/migrations` 記錄為準；本機 MCP 的兩個 PostgreSQL 連線仍是同一顆本地庫（`0081`–`0083` applied 時間戳同為 `2026-10-24T06:03:31Z`），不可當作生產現況。

## 近期變更（最近 9 筆，一行式）

| 日期 | 內容 |
|---|---|
| 2026-10-25 | 版控收尾：`a732cc28..d27f7c90` 推上 `origin/main`（`#59 edf3e87c`、`#60 7a073263`、`#61 d27f7c90`），本機與遠端一致；原始 APNG 素材 `static/images/ani_{coffee,bean}_apng.png`（12.8MB）加 `.gitignore` 不入庫。同日 Render API 複驗：正式站 live＝`a732cc28`（`dep-dbed2vm7bikc73825md0`，2026-10-24 15:43Z 手動部署成功）⇒ 10-23 的 DB ENOTFOUND 已排除 |
| 2026-10-24 | #61 首頁「推薦頁面」雙卡（移植 union-tec.jp `recommendedPages`）＋同日調整：① 隱藏首頁 `#bc-stage-socials`（extra_css `.bc-brand-stage-hero #bc-stage-socials{display:none}`，`hidden` 屬性會被 `.footer-socials{display:flex}` 蓋掉）② 模組由 `.feed--video` 下方搬到 `.bc-brand-stage-hero` 正下方。新版號 `?v=20261024b`（css）／`20261024a`（js）（`d27f7c90` 已 push） |
| 2026-10-24 | #60 品牌舞台環形照片列「第一張咖啡」改 goo 揭示（沿用標題文字的 `stdDeviation 50→0` 時間軸，不再 scale 0.5→1）；`bc-hand-ring.js/css`、`bc-brand-stage.js`（新增 `window.BC_MEDIA_REVEAL`）、index／about `?v=20261024a`（`7a073263` 已 push） |
| 2026-10-24 | #59 咖啡豆詳情頁「店員氣泡」：`BeanItem` 10 欄位＋`measure_bubble_geometry()`、Admin 2 fieldset、migration `0081`–`0083`（幾何／文案 seed）；`.bc-coffee-comment` 宿主 selector 改中性 `.bc-photo-comment`（`edf3e87c` 已 push） |
| 2026-10-22~23 | #58／#58b 首頁四步旅程 Rive 圖示列（`bc-steps`）：自架 Rive 2.35.2、intro/hover/rest 修正、靜止 4s 自動循環、圖示純白；桌機 4 欄／手機 2×2／reduced-motion 驗證通過（已 push `a732cc28`） |
| 2026-10-17 | #57 移除 hero／導覽列時鐘（`bc-weather.js` ORDER 去掉 `clock`），只留天氣圖示＋溫度（`28b1c322` 已 push） |
| 2026-10-16 | #56 首頁照片格桌機（≥992px）名稱／highlight 字級 24/18px、`--bc-hero-caption-h` 68.38（`71018e97` 已 push） |
| 2026-10-15 | #55 首頁照片格桌機照片縮小 280×400、字級 20/16px（`aaf7c2aa` 已 push） |
| 2026-10-14 | #51 首頁順序反轉（GUNTE hero 回第一屏）＋ GUNTE 環形字修正（`bf495475` 已 push） |
| 2026-10-12 | hero 時鐘手機 `{ }`（9 欄）＋ `w-node-*` id 語意化（`6e29b447`，已部署） |
