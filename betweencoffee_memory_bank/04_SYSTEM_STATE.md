# 系統狀態

> 2026-10-23 精簡版（原檔 181KB 已封存：`docs/archive/memory_bank_04_full_20261017.md`）。
> 逐筆變更細節請用 `git log`，不要回頭讀封存檔。

## 系統狀態摘要

| 維度 | 狀態 | 備註 |
|------|:----:|------|
| 資料庫（Supabase） | ✅ 正常 | 2026-09-15 專案曾消失→後台還原後恢復（pooler 約 3 分鐘註冊 tenant）；07-27 還原點與本地 08-16 落差已回補（訂單 2661／佇列 1036），並以 Django 模型為準校正 |
| 核心功能 | ✅ 完整 | 下單 → 支付 → 製作 → 取餐 |
| WebSocket | ✅ 穩定 | 三層架構（WebSocketCore → 橋接 → 業務），InMemoryChannelLayer |
| 支付 | ✅ 4 種 | PayPal / Alipay / FPS / 現金 |
| 社交登入 | ✅ 已修復 | Google / Facebook（django-allauth） |
| 忠誠度 | ✅ 基礎 | 積分 + 優惠券 |
| 員工管理 | ✅ 完整 | 隊列 + 付款確認 |
| 員工端渲染器 v2 | ✅ 完成 | BaseOrderRendererV2 + 4 個 v2 渲染器 |
| 測試 | ⚠️ 不足 | 覆蓋率低（以 `docs/verify/` CDP 腳本補前端驗證） |
| 監控 | ⚠️ 基礎 | 無告警系統 |
| 部署（Render） | ✅ 已上線 | 現行 `live`＝deploy `dep-db6btj0473hc73du80hg`／commit `ec8fcadb`／trigger `manual`／2026-10-12 19:04→19:07 +08:00；migration 0074 起已套用。**autoDeploy 關閉，需手動 deploy** |
| 版本控制 | ⚠️ 本機落後 | 2026-10-14 起多個 commit 未 push（`bf495475` 之後的 `aedcf859`、`aaf7c2aa`、`28b1c322`…）；2026-10-23：#58 bc-steps 相關檔案**尚未 commit**（見 `task_progress.md`） |

## 資料庫現狀

| 面向 | 本地開發 | Render 生產 |
|------|:--------:|:-----------:|
| 資料庫 | 本地 PostgreSQL | Supabase PostgreSQL |
| 連線 | `127.0.0.1:5432` | `pooler.supabase.com:6543` |
| 認證 | `postgres/postgres` | Supabase 專案憑證 |
| Migration | 手動執行 | 部署時自動執行 |
| 管理 | psql / pgAdmin | Supabase Dashboard |

## 近期變更（最近 6 筆，一行式）

| 日期 | 內容 |
|---|---|
| 2026-10-22~23 | #58 首頁四步旅程 Rive 圖示列（`bc-steps`）：自架 Rive 2.35.2、intro/hover/rest 行為修正、桌機 4 欄／手機 2×2／reduced-motion 驗證通過（未 commit） |
| 2026-10-17 | #57 移除 hero／導覽列時鐘（`bc-weather.js` ORDER 去掉 `clock`），只留天氣圖示＋溫度（本機 `28b1c322`） |
| 2026-10-16 | #56 首頁照片格桌機（≥992px）名稱／highlight 字級 24/18px、`--bc-hero-caption-h` 68.38 |
| 2026-10-15 | #55 首頁照片格桌機照片縮小 280×400、字級 20/16px（本機 `aaf7c2aa`） |
| 2026-10-14 | #51 首頁順序反轉（GUNTE hero 回第一屏）＋ GUNTE 環形字修正（`bf495475` 已 push） |
| 2026-10-12 | hero 時鐘手機 `{ }`（9 欄）＋ `w-node-*` id 語意化（`6e29b447`，已部署） |
