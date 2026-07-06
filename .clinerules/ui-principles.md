# Between Coffee UI 設計原則

> 最後更新: 2026年7月6日
> 來源: 全面分析網站現有模板與 CSS 使用情況 + 品牌視覺設計風格定義

---

## 一、品牌核心訊息

```
輕鬆感 · 自由感 · 放空感
```

- 所有 UI 設計圍繞這三個關鍵詞展開
- 不花巧、無需動畫、無需漸變色
- 風格統一性：元素元件、字體、按鈕、色彩、圖標保持一致

---

## 二、品牌視覺設計風格

### 2.1 品牌視覺元素
- **SVG 插圖**: 全域網站使用具設計感的 SVG 插圖，畫風為手繪趣味性風格，帶出品牌訊息
- **黑色主題背景**: 全域為黑色 theme 背景，加強所有咖啡產品的視覺對比
- **背景裝飾**: 大多數頁面背景有透明度低的 SVG 插畫元素，附有 CSS 動畫 `noise_animation`，豐富視覺層次

### 2.2 產品照片
- 所有咖啡和咖啡豆使用**無顏色背景的 PNG 去背圖**，僅呈現產品物件本身
- 去背圖加強產品視覺焦點，讓顧客專注於產品本身

### 2.3 咖啡杯及咖啡豆包裝設計
- **設計統一性**: 所有包裝設計保持一致風格，營造獨有品牌感
- **插畫風格**: 每個包裝均帶有不同的插畫，畫風傳達「輕鬆感、自由感、放空感」
- **口味配色**: 每種咖啡及咖啡豆口味都以不同的顏色設計，便於識別

### 2.4 設計語言
- 清晰且含空間感
- 簡潔留白但不失設計感
- 字體清晰可讀

---

## 三、品牌色系統

| 用途 | 顏色值 | CSS 變數 |
|------|--------|----------|
| 品牌金色（主要強調） | `#c49b63` | `--bc-gold` |
| 金色懸浮 | `#d4ab73` | `--bc-gold-hover` |
| 金色半透明背景 | `rgba(196, 155, 99, 0.15)` | `--bc-gold-light` |
| 金色發光陰影 | `rgba(196, 155, 99, 0.3)` | `--bc-gold-glow` |
| 深黑背景 | `#0e0e0e` | `--bc-bg` |
| 卡片背景 | `rgba(255, 255, 255, 0.04)` | `--bc-bg-card` |
| 卡片懸浮 | `rgba(255, 255, 255, 0.07)` | `--bc-bg-card-hover` |
| 輸入框背景 | `rgba(255, 255, 255, 0.06)` | `--bc-bg-input` |
| 邊框 | `rgba(255, 255, 255, 0.08)` | `--bc-border` |
| 邊框聚焦（金色） | `rgba(196, 155, 99, 0.4)` | `--bc-border-focus` |
| 主要文字 | `rgba(255, 255, 255, 0.9)` | `--bc-text` |
| 次要文字 | `rgba(255, 255, 255, 0.5)` | `--bc-text-muted` |
| 暗淡文字 | `rgba(255, 255, 255, 0.3)` | `--bc-text-dim` |

---

## 四、字型系統

### 4.1 字型家族
- **標題/裝飾**: `Noto Serif TC`（weight: 400, 600, 700）
- **內文**: `Noto Sans TC`（weight: 300, 400, 500, 700）
- **Logo**: `Mogra`

### 4.2 字型大小原則
| 元素 | 大小 | 備註 |
|------|:----:|------|
| 頁面大標題 | `1.2rem ~ 1.3rem` | 區塊標題 |
| 區塊標題（結帳） | `1.15rem` | `.bc-checkout-section-title` |
| 購物車標題 | `1.2rem` | `.bc-cart-title` |
| 主要按鈕文字 | `1rem` | `.bc-btn` |
| 次要按鈕 | `0.9rem ~ 0.95rem` | `.bc-btn-secondary` |
| 購物車底部按鈕 | `0.95rem` | 白色文字 |
| 輸入框文字 | `1rem` | `.bc-input` |
| 商品名稱 | `1rem` | `.bc-product-name` |
| 商品價格 | `1.15rem` | 金色粗體 |
| 商品詳細/選項 | `0.85rem` | `.bc-product-options` |
| 欄位標籤 | `0.9rem` | `.bc-field-label` |
| 摘要行 | `1rem` | `.bc-summary-row` |
| 摘要總額 | `1.1rem`（標籤）/ `1.3rem`（金額） | 金色 |
| 購物車空狀態 | `1.1rem` | 白色 |
| 購物車小計標籤 | `0.9rem` | `.bc-cart-total-label` |
| 購物車小計金額 | `1.2rem` | 金色粗體 |
| 徽章數字 | `0.7rem` | `.bc-badge` |
| Toast 標題 | `0.9rem` | `.bc-toast-title` |
| Toast 訊息 | `0.8rem` | `.bc-toast-message` |

### 4.3 字型顏色
- 主要按鈕（金色背景上）: **白色 `#fff`**
- 次要按鈕: `var(--bc-text)`，懸浮變金色
- 價格: `var(--bc-gold)` 金色
- 一般文字: `var(--bc-text)`
- 輔助文字: `var(--bc-text-muted)`

---

## 五、間距系統

| 元素 | 內邊距 | 備註 |
|------|--------|------|
| 卡片（桌面） | `24px` | `.bc-checkout-section` |
| 卡片（手機） | `16px` | `@media max-width: 768px` |
| 一般按鈕 | `12px 24px` | `.bc-btn` |
| 購物車底部按鈕 | `12px 24px` | `.bc-cart-footer .bc-btn-lg` |
| 繼續購物按鈕 | `10px 20px` | `.bc-cart-footer .bc-btn-secondary` |
| 小按鈕 | `8px 14px` | `.bc-btn-sm` |
| 大按鈕 | `16px 32px` | `.bc-btn-lg` |
| 輸入框 | `12px 16px` | `.bc-input` |
| 區塊間距 | `16px` | margin-bottom |
| 商品間距 | `12px` | gap |
| 購物車 header/footer | `20px 24px` | padding |
| 購物車商品列表 | `16px 24px` | padding |

---

## 六、圓角系統

| 層級 | 值 | 用途 |
|:----:|:--:|------|
| 大圓角 | `12px` | 卡片、購物車抽屜、Toast |
| 中圓角 | `8px` | 商品圖片、時間選項 |
| 小圓角 | `6px` | 按鈕、輸入框、徽章 |

---

## 七、購物車規範

### 7.1 滑出購物車
- 寬度: `420px`（桌面）、`100vw`（手機）
- 動畫: `0.35s cubic-bezier(0.4, 0, 0.2, 1)`
- 遮罩: 黑色 60% + `blur(4px)`
- 關閉按鈕「X」: `font-weight: 200` 變細

### 7.2 購物車空狀態
- 顯示購物車圖示（`icon-shopping-cart`，`font-size: 3rem`，透明度 0.3）
- 文字「來一杯咖啡吧」: `1.1rem`，白色
- 不顯示「購物車是空的」

### 7.3 購物車底部
- 「前往結帳」: `0.95rem`，`color: #fff`，`padding: 12px 24px`
- 「繼續購物」: `0.95rem`，跟隨「前往結帳」大小

---

## 八、結帳頁規範

### 8.1 區塊結構
1. 訂單商品（圖示: `icon-cart-plus`）
2. 聯絡資訊（圖示: `icon-user`）
3. 預計取貨時間（圖示: `icon-clock-o`）
4. 支付方式（圖示: `icon-credit-card`）
5. 訂單摘要（圖示: `icon-list-alt`）

### 8.2 支付方式
- PayPal（圖示: `icon-paypal`）
- Alipay（圖示: `icon-mobile`）
- FPS 轉數快（圖示: `icon-camera`）
- 現金（圖示: `icon-money`）

### 8.3 取貨時間選項
- 5 分鐘（最快）、10 分鐘（推薦，預設）、15 分鐘（從容）、20 分鐘（悠閒）、30 分鐘（慢慢來）

---

## 九、圖示使用規範

### 9.1 icomoon 字型（優先使用）
| Class | 用途 |
|-------|------|
| `icon-shopping-cart` | 購物車 |
| `icon-cart-plus` | 結帳頁訂單商品標題 |
| `icon-user` | 用戶、聯絡資訊 |
| `icon-close` | 關閉按鈕（font-weight: 200） |
| `icon-clock-o` | 時間 |
| `icon-credit-card` | 支付 |
| `icon-list-alt` | 訂單摘要 |
| `icon-arrow-right` | 箭頭 |
| `icon-paypal` | PayPal |
| `icon-mobile` | Alipay |
| `icon-camera` | FPS |
| `icon-money` | 現金 |
| `icon-whatsapp` | WhatsApp |
| `icon-facebook` | Facebook |
| `icon-instagram` | Instagram |

### 9.2 Material Symbols（輔助使用）
| Class | 用途 |
|-------|------|
| `material-symbols-outlined` | 排程、undo、mobile_friendly 等 |

---

## 十、響應式斷點

| 斷點 | 調整內容 |
|:----:|----------|
| `max-width: 768px` | 購物車全寬、結帳 padding 縮小、欄位改單欄、支付 2 欄、時間選項縮小 |
| `max-width: 480px` | 支付選項改單欄 |

---

## 十一、動畫與過渡

- 預設過渡: `0.25s cubic-bezier(0.4, 0, 0.2, 1)`
- 購物車滑出: `0.35s cubic-bezier(0.4, 0, 0.2, 1)`
- Toast 進場: `bcToastIn`（0.35s，從右滑入 + 縮放）
- Toast 離場: `bcToastOut`（0.3s，向右滑出 + 縮放）
- 按鈕懸浮: `translateY(-1px)` + `box-shadow`
- 商品卡片懸浮: `translateY(-2px)`

---

## 十二、滾動條補償

當開啟購物車/Modal 鎖定滾動時：
1. `body` 設 `overflow: hidden`
2. `body` 設 `padding-right` 補償滾動條寬度
3. `position: fixed` 的 navbar 也加上 `padding-right` 補償
4. `position: absolute` 且 `right: 0` 的元素設 `right` 補償

---

## 十三、UI 開發設計注意事項

進行所有 UI 開發設計和修改時，請遵循以下原則：

### 13.1 核心原則
- **不花巧** — 功能優先，裝飾其次
- **無需動畫** — 避免不必要的 CSS/JS 動畫（品牌已有的 noise_animation 除外）
- **無需漸變色** — 使用純色，不使用 `linear-gradient`、`radial-gradient` 等

### 13.2 風格統一性
所有 UI 元素必須保持以下五個面向的統一：
1. **元素元件** — 卡片、按鈕、輸入框、列表等元件風格一致
2. **字體** — 嚴格遵循字型系統規範（Noto Serif TC / Noto Sans TC / Mogra）
3. **按鈕** — 統一使用 `.bc-btn` 系列樣式，不自行定義新按鈕風格
4. **色彩** — 嚴格使用品牌色系統中的顏色值，不引入新色
5. **圖標** — 優先使用 icomoon 字型圖標，不引入新圖標集

### 13.3 設計決策檢查清單
新增或修改 UI 元件前，請確認：
- [ ] 是否符合「輕鬆感、自由感、放空感」的品牌核心？
- [ ] 是否使用了品牌色系統中的顏色？
- [ ] 是否使用了規範中的字型？
- [ ] 是否與現有元件風格一致？
- [ ] 是否過於花巧？（如果是，簡化它）
- [ ] 是否真的需要動畫？（如果不需要，移除它）
- [ ] 是否使用了漸變色？（如果是，改用純色）
