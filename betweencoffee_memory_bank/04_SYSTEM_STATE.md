# 系統狀態

> **最後更新**: 2026年9月14日（sake-mv 資源集中 + 咖啡詳情頁氣泡微調；記憶庫瘦身：歷史日誌已封存，本檔僅現況）
> **注意**: 完整變更日誌 → `docs/archive/04_SYSTEM_STATE_history_202607-202609.md`；逐筆細目 → `git log`。


## 系統狀態摘要

| 維度 | 狀態 | 備註 |
|------|:----:|------|
| 資料庫（Supabase） | ⚠️ 已還原 | 2026-09-15：專案曾消失導致部署失敗，使用者於後台還原後恢復（pooler 需約 3 分鐘註冊 tenant）；還原點資料停在 2026-07-27（訂單 2018），與本地（08-16、2661 筆）有落差，待確認是否回補 |
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
| 2026-09 前端整合 | ✅ 進行中 | yama 圓球 header（首頁）/ bean（咖啡豆）REAL 模組 / reviews 行動縮放 / **咖啡詳情頁 staff-comment 氣泡（/coffee/10/，已移到咖啡杯外）**；完成後更新本列 |
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

- 2026-09-15 部署事故排除：Supabase 專案消失（`tenant/user ... not found`、DNS NXDOMAIN）→ 使用者還原專案後，**pooler 約 3 分鐘才註冊 tenant**（連線字串不需改），觸發 Render 部署成功（0066~0069 套用、status live）
- 2026-09-14 sake-mv 資源集中（`static/images/sake-mv/*` → `static/images/*`，資料夾刪除、CSS/模板路徑同步）＋ 咖啡詳情頁氣泡微調（p-1 左 5%、p-3 上右 5%，5%＝氣泡自身尺寸）＋ 氣泡內文字垂直置中修正（對齊氣泡面積質心；pattern-1 上 1.1803fs/下 1.6497fs、pattern-5 上 0.9318fs/下 1.3972fs；4 斷點實測 ≤0.44px）＋ hero（GUNTE）第 6/7 張 slide 圖片更換（06_720.jpg / 07_1080.jpg）＋ **咖啡詳情頁氣泡文字 DB 化**（CoffeeItem `staff_comment_1/2/3` ＋ migration 0066/0067 ＋ Admin 欄位組；三顆氣泡對所有 coffee 生效、留空不顯示；新增 pattern-2（03a.svg）/p-2 位置；內距改依字數 `--bc-cb-n` 自動置中；4 斷點實測 ≤0.43px）＋ **氣泡定位幾何每款可設定**（`bubble_safe_left/right`、`bubble_photo_ratio`、`bubble_scale` ＋ migration 0068/0069；存檔時留空即以 Pillow 量測去背 PNG → Black Blend 15.08/80.25、比例 1.429、倍率 0.70；Flat White 18.1/80.71、比例 0.7；12 組 CDP 驗證氣泡皆在盒內、距內容 6~16px）
- 2026-09-13 咖啡詳情頁 staff-comment 氣泡移到咖啡杯外（對齊去背 PNG alpha bbox x 9.30%~89.53%，單一 calc 算式通吃 10 斷點、零重疊零溢出）
- 2026-09-11 咖啡詳情頁 staff-comment 氣泡建立（/coffee/10/）：長方形氣泡 + 咖啡專用 SVG + 直立文字 + 3 秒輪播彈出動畫
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
