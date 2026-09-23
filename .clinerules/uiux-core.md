# Between Coffee — UI/UX 核心規範（自動注入精簡版）

> 2026-09-06 由 `uiux-principles.md` 拆分：本檔每次自動注入（~2K tokens）。
> **完整版**：`docs/uiux-full-reference.md`（設計流程、四角色分析、審查檢查清單、附錄、SVG/HTML 範例）→ 需要時才讀。
> 所有規範源自品牌設計系統，新增/修改 UI 前先自查下方「快速檢查」。

## 一、品牌
- 核心：**輕鬆感 · 自由感 · 放空感**；不花巧、不需動畫、不需漸變色。
- 黑色 theme（`#0e0e0e`）；產品用去背 PNG；裝飾 SVG + `noise_animation`（僅此動畫）。
- 背景訊息字體 `.title-bg-head`：Mogra、20vw、opacity .05。

## 二、色系統（只用這些色）
| 用途 | 值 | CSS 變數 |
|------|------|----------|
| 品牌金 | `#c49b63` | `--bc-gold` |
| 金 hover | `#d4ab73` | `--bc-gold-hover` |
| 背景 | `#0e0e0e` | `--bc-bg` |
| 卡片 | `rgba(255,255,255,.04)` | `--bc-bg-card` |
| 輸入框 | `rgba(255,255,255,.06)` | `--bc-bg-input` |
| 邊框 | `rgba(255,255,255,.08)` | `--bc-border` |
| 主文 | `rgba(255,255,255,.9)` | `--bc-text` |
| 次文 | `rgba(255,255,255,.5)` | `--bc-text-muted` |

## 三、字型
- Noto Serif TC（標題 400/600/700）、Noto Sans TC（內文 300/400/500/700）、Mogra（Logo）。
- 主鍵：主要按鈕 1rem 白字、商品價 1.15rem 金粗體、頁標題 1.2–1.3rem、欄位標籤 .9rem。

## 四、間距 & 圓角
- 卡片 padding 24（手機 16）；按鈕 12×24；輸入框 12×16；區塊間距 16。
- 圓角：卡片/抽屜/Toast 12、圖片/選項 8、按鈕/輸入框 6。

## 五、購物車（滑出抽屜）
- 420px（手機 100vw）、0.35s cubic-bezier(.4,0,.2,1)；遮罩黑 60%+blur(4px)。
- 空態：購物車 icon 3rem（透明度 .3）+「來一杯咖啡吧」1.1rem。
- 底部：「前往結帳」.95rem 白、「繼續購物」.95rem；金額金粗體。
- 開啟時補償滾動條（body overflow hidden + padding-right；fixed navbar 同步）。

## 六、結帳頁
- 區塊順序：訂單商品 → 聯絡資訊 → 預計取貨時間 → 支付方式 → 訂單摘要（各帶 icomoon 圖示）。
- 支付：PayPal/Alipay/FPS/現金；時間預設 10 分鐘（推薦）。
- 行動端商品列表用 `.bc-order-collapse`（預設關閉、無框列表、vanilla JS 切換 aria-expanded；≥1200px 隱藏改右欄）。

## 七、圖示
- **icomoon 優先**：`icon-shopping-cart / icon-user / icon-clock-o / icon-credit-card / icon-list-alt / icon-close / icon-paypal / icon-mobile / icon-camera / icon-money / icon-whatsapp / icon-arrow-right` 等。
- Material Symbols（`material-symbols-outlined`）僅輔助。不引入新圖示集。

## 八、斷點 / 動畫 / 過渡
- 768px：購物車全寬、欄位單欄、支付 2 欄；480px：支付單欄。
- 過渡 .25s cubic-bezier(.4,0,.2,1)；購物車 .35s；僅品牌 `noise_animation` 可用，不引入其他動畫。
- 禁用漸變色（linear/radial-gradient）；按鈕 hover = translateY(-1px)+shadow。

## 九、元件統一（硬性）
- 一律使用既有 `.bc-btn`／`.bc-btn-secondary`／`.bc-btn-sm/lg`、`.bc-input`、`.bc-card` 系列，**不自行發明新樣式**。
- 顏色、字型、圖示只能取上方系統值。

## 十、快速檢查（每次動 UI 前）
1. 符合輕鬆/自由/放空？ 2. 只用品牌色？ 3. 只用規範字型？ 4. 與現有元件一致？
5. 是否過花巧？ 6. 真需要動畫？ 7. 有用漸變？（全改純色）
8. 手機與桌面都檢查？ 9. 空/錯誤/載入狀態都處理？ 10. 前端顯示與後端狀態一致？
