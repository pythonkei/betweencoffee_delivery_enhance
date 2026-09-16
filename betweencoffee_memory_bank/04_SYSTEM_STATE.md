# 系統狀態

> **最後更新**: 2026年9月15日（正式庫資料回補＋統一；咖啡氣泡 6 落點、退場動畫修正、Admin 精簡；版面留白與平板端咖啡照片縮減後由使用者手動定案；記憶庫瘦身：歷史日誌已封存，本檔僅現況）
> **注意**: 完整變更日誌 → `docs/archive/04_SYSTEM_STATE_history_202607-202609.md`；逐筆細目 → `git log`。


## 系統狀態摘要

| 維度 | 狀態 | 備註 |
|------|:----:|------|
| 資料庫（Supabase） | ✅ 正常 | 2026-09-15：專案曾消失導致部署失敗，使用者於後台還原後恢復（pooler 需約 3 分鐘註冊 tenant）；還原點（07-27）與本地（08-16）的**資料落差已回補完成**——訂單 2661 / 佇列 1036 與本地一致；順帶以 **Django 模型為權威**對齊 5 個 varchar 欄位（email 80 / order_number 20 / payment_method 10 / phone 12 / pickup_code 4；本地庫才是偏離模型的一方）；同日再以 **username 為橋樑**完成**資料統一**（舊訂單歸屬 36 筆、補建 test_customer、咖啡名稱 8/9/10 覆蓋為本地版）→ 帳號 40/40、訂單歸屬與名稱 0 差異 |
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
| 2026-09 前端整合 | ✅ 進行中 | yama 圓球 header（首頁）/ bean（咖啡豆）REAL 模組 / reviews 行動縮放 / **咖啡詳情頁 staff-comment 氣泡：文字 DB 化、幾何自動量測、6 落點可選（Admin）、原地縮小退場、版面留白與平板照片縮減（2026-09-15）** |
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

- 2026-09-15 咖啡氣泡位置 6 選 1：每顆氣泡可在 Admin 各自選落點（左上／左中間／左下／右上／右中間／右下），新增 `bubble_pos_1/2/3`（migration 0070）＋ Admin 欄位組「氣泡位置（6 選 1；動畫不變）」；CSS 用 `data-pos` 選配落點（垂直 3 列、水平左右 2 側，K 依該顆圖形寬度自動縮放）→ 6 個落點都在咖啡杯外圍；彈出動畫與原站完全相同；CDP 實測預設值與改動前逐項相同（left −52.2/337.8/333.0px）、改 `bl` 確實移到左下；版號 bc-coffee-comment.css ?v=20260915d；同日 Admin 精簡：移除「氣泡定位」欄位組（幾何值仍由存檔自動量測：換圖時 save() 會偵測 image 變更並自動重新量測，不再需要手動清空）；同日三列整體向上調整（上 −2%／中 −7%／下 −10%：桌機 37.58%−0.42245fs / 57% / 70%，手機 65.42%−0.42245fs / 71% / 74%）；同日修正氣泡「退場動畫」：原本消失前會瞬間跳回入場起點（往上 40px）才縮小 → 改為加 `.is-hiding`、收縮原點改 center center，氣泡在原位置縮小消失（實測三顆中心位移 dx/dy 皆 0）；同日把氣泡與杯子的左右留白由 0.5fs 加大為 1.5fs（`--cb-gap`，桌機 +17px／手機 +13px，可單值調整）；6 個落點改為各自高度、左右刻意錯開（桌機 tl36/ml52/bl67.5、tr40/mr61/br72.5；手機 62.5/67/72、66.5/74/76）以製造自然落差；同日逐點微調：垂直 +2%（tl38/ml54/bl67.5、tr42/mr61/br74.5）＋ 新增 `--cb-out` 逐點往杯外推（tl3%/ml2%/tr2%/br2%）；落差再加大：右上 42→36%、右中間 61→64%（錨點差 28% 照片高、氣泡體重疊 19%→9%）、左上 --cb-out 3→5%（距杯 47.1px）；再逐點微調（tl38/ml55/bl70.5、tr34/mr64/br76.5；--cb-out tl4/ml2/tr1/br2）；右側三點水平錯開（--cb-out tr1/mr5/br2% → X 中心差 14.3/10.7px）；右上再左移 2%（--cb-out tr -1%，負值＝往杯內收，tr↔mr 水平差 21.5px）；右上再左移 2%＋上移 2%（top 32%、--cb-out -3%，tr↔mr 水平差 28.7px）；上列再上移（tr 30%、tl 34%；凸出照片上緣 tl 9.4~35.3px、tr 27.7~53.6px）
- 2026-09-15 `.ftco-section-blank-small` 留白縮小 30%：樣式綁 class（非標籤），故在 bc-components.css 覆蓋 8em/26vh → 5.6em/18.2vh 並同步三組 media query（×0.7）；同日再縮 20%（全面 ×0.8）→ 實測 224px → 156.8px → 125.4px（累計 −44%）；版號 ?v=20260915b；同日再分斷點微調：行動端 −20%、平板端 −10%，另平板端咖啡照片 −20%（style-custom.css 768–1079.98 區塊 max-height 532.95→426.36px、max-width 88.825→71.06%）；版號 bc-components.css ?v=20260915c、style-custom.css ?v=20260915a；同日再一輪：平板端留白再 −10%（72.6→65.3px）、行動端再 −20%（28.7→22.9px）、平板端咖啡照片再 −20%（426.3→341.1px，累計 ×0.64）；版號 bc-components.css ?v=20260915d、style-custom.css ?v=20260915b；再追加桌面端 −10%（125.4→112.9px，累計為原值 0.504 倍）；版號 bc-components.css ?v=20260915e；**使用者手動定案（同日）**：`.ftco-section-blank-small` 基礎 `padding: 2em 0; min-height: 10vh`、≤991 與 ≤768 `min-height: 2vh`、≤480 `1vh`；`.bc-page-content` 首個 section 上緣 margin `100 / 72 / 60 / 60px`（桌機／768–991.98／576–767.98／≤575.98）；另 **GUNTE hero slide 等比縮小 10%**（`bc-gunte-hero.css` 新增單一旋鈕 `--bc-gunte-scale`（試 0.9 後定案 **0.8**），驅動容器寬／`img.hide-sp`／圈圈字 SVG／hero 高／手套圓；手機 ≤767.98 全部維持不變；版號 ?v=20260915a；同日加 `--bc-gunte-top-gap: 135px` 修正桌面端投影片頂端被導覽列蓋住（−47.3→+20.2px 淨空、hero 總高不變））
（該 class 亦用於 index/bean/bean_menu/coffee_menu/checkout/landing_v3）
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
