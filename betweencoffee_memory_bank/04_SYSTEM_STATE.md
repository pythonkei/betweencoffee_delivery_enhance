# 系統狀態

> **最後更新**: 2026年9月6日（記憶庫瘦身：歷史日誌已封存，本檔僅現況）
> **注意**: 完整變更日誌 → `docs/archive/04_SYSTEM_STATE_history_202607-202609.md`；逐筆細目 → `git log`。


## 系統狀態摘要

| 維度 | 狀態 | 備註 |
|------|:----:|------|
| 核心功能 | ✅ 完整 | 下單→支付→製作→取餐 |
| WebSocket | ✅ 穩定 | 三層架構，InMemoryChannelLayer |
| 支付 | ✅ 4種 | PayPal/Alipay/FPS/現金 |
| 社交登入 | ✅ 已修復 | Google/Facebook |
| 忠誠度 | ✅ 基礎 | 積分+優惠券 |
| 員工管理 | ✅ 完整 | 隊列+付款確認 |
| 前端架構 | ✅ Sprint 1-2 | 基礎服務層 + 核心重構 |
| 員工端渲染器 v2 | ✅ Phase 2 完成 | BaseOrderRendererV2 + 4 個 v2 渲染器 |
| 測試 | ⚠️ 不足 | 覆蓋率低 |
| 監控 | ⚠️ 基礎 | 無告警系統 |
| 文檔 | ✅ 已重構 | 資訊收攏至 `.clinerules/` 目錄 |
| 2026-09 前端整合 | ✅ 進行中 | yama 圓球 header（首頁）/ bean（咖啡豆）REAL 模組 / reviews 行動縮放；完成後更新本列 |
| 記憶庫 | ✅ 已瘦身 | 2026-09-06：04 拆至 <1K、`.clinerules` 拆 core（自動注入）/完整參考（docs/uiux-full-reference.md） |

## 資料庫現狀

| 面向 | 本地開發 | Render 生產 |
|------|:--------:|:-----------:|
| 資料庫 | 本地 PostgreSQL | Supabase PostgreSQL |
| 連線 | `127.0.0.1:5432` | `pooler.supabase.com:6543` |
| 認證 | `postgres/postgres` | Supabase 專案憑證 |
| Migration | 手動執行 | 部署時自動執行 |
| 管理 | psql / pgAdmin | Supabase Dashboard |

## 近期變更（最近 10 筆標題；細節見封存檔與 git log）

- 2026-09-01 ramen→bean REAL + reviews 整合（about 頁）＋ 平板照片放大置中 ＋ sake-shirakiku product-mv 整合
- 2026-08-27 Timber Wharf 全域應用 + weekday 徽章 + SERIES 資料庫驅動（咖啡/咖啡豆）
- 2026-08-26~27 yokohama-timberwharf weather 天氣/時鐘元件整合（about 頁右上角）
- 2026-08-25 sukima row-animation + content-block-title 氣泡 + capabilities-gallery 整合（about）
- 2026-08-25 sukima who section（.section.who）整合（about）
- 2026-08-24 sukima hero-title-svg 手繪圓形畫線動畫整合（about）
- 2026-08-24 Sticker 貼紙模組化（sticker-box 資料驅動）
- 2026-08-24 浮動購物車按鈕修復
- 2026-08-22~23 MCP 配置修復 + rotate-mau 整合 + 多項 UI 整合
- 2026-08-21 SERIES 照片修復 + 平板基於桌面縮小 + caption 加大
