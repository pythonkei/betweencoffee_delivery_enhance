# 專案概述

> **最後更新**: 2026年7月6日

## 開發者背景與方法論

### 開發者角色
- **新手開發者** — 使用 **Vibe Coding** 方法（跟著感覺走、邊做邊學）
- **多視角分析** — 從四個不同角色視角分析系統，產出平衡解決方案：
  1. 🛠️ **系統工程師** — 技術架構、程式碼品質、效能
  2. 🎨 **前端工程師** — 使用者體驗、互動流程、響應式設計
  3. 🖌️ **UX/UI 設計師** — 品牌調性、視覺一致性、易用性
  4. 👤 **用戶** — 實際使用情境、痛點、需求
- **目標** — 透過多視角碰撞，找到最適合小咖啡店的平衡方案

### Vibe Coding 原則
- 先讓功能跑起來，再回頭優化
- 小步迭代，每次改進一個小功能
- 遇到問題先搜尋、再問、最後才自己寫
- 保持程式碼簡單可讀，不過度工程化
- 享受開發過程，保持學習心態

## 項目信息

| 項目 | 內容 |
|------|------|
| **名稱** | Between Coffee 咖啡店外帶網站與訂單製作管理系統 |
| **技術棧** | Django + PostgreSQL + WebSocket + Bootstrap 5 |
| **核心流程** | 顧客下單 → 支付處理 → 加入製作隊列 → 員工製作 → 訂單就緒 → 顧客取餐 |
| **Live URL** | https://betweencoffee-delivery-enhance-v1.onrender.com/ |
| **GitHub** | https://github.com/pythonkei/betweencoffee_delivery_enhance |
| **部署方式** | Render（Docker 運行時），autoDeploy 啟用 |

## 品牌視覺設計風格

### 品牌核心訊息
```
輕鬆感 · 自由感 · 放空感
```

### 品牌視覺元素
- **SVG 插圖**: 全域使用手繪趣味性風格 SVG 插圖，帶出品牌訊息
- **黑色主題背景**: 全域黑色 theme 背景，加強所有咖啡產品的視覺對比
- **背景裝飾**: 多數頁面有透明度低的 SVG 插畫元素，附有 CSS 動畫 `noise_animation`，豐富視覺層次
- **產品照片**: 無顏色背景的 PNG 去背圖，僅呈現產品物件本身，加強視覺焦點
- **包裝設計**: 統一風格，每種口味不同配色，插畫傳達「輕鬆感、自由感、放空感」

### 動畫視覺元素

#### SVG 背景插畫 + noise_animation
頁面背景使用透明度低的 SVG 插畫元素，搭配 CSS `noise_animation` 動畫（1 秒循環，`will-change: filter`），透過 SVG noise filter 產生噪點抖動效果。

**應用頁面**:
| 頁面 | SVG 插畫 | 用途 |
|------|----------|------|
| 首頁 (`index.html`) | `owl_title_bg_01.svg`, `owl_title_bg_02.svg`, `product_hover.svg` | 背景裝飾、商品 hover |
| 咖啡菜單 (`coffee_menu.html`) | `title_bg_img_01.svg`, `product_hover.svg` | Banner 背景、商品 hover |
| 咖啡豆菜單 (`bean_menu.html`) | `title_bg_img_02.svg`, `product_hover.svg` | Banner 背景、商品 hover |
| 全域 (`base.html`) | — | noise-filiter SVG filter 容器 |

#### 背景訊息字體元素（title-bg-head）
頁面背景使用透明度極低的品牌字體元素（`font-family: 'Mogra'`, `font-size: 20vw`, `opacity: .05`），與頁面內容相關。

**應用頁面**:
| 頁面 | 背景文字 | 語意 |
|------|----------|------|
| 咖啡詳情 (`coffee.html`) | `｛BREWED FAST｝` | 快速沖泡 |
| 咖啡豆詳情 (`bean.html`) | `｛SERVED FRESH｝` | 新鮮供應 |
| 關於我們 (`about.html`) | `｛US｝` | 品牌故事 |

### 設計語言
- 清晰含空間感、簡潔留白、字體清晰
- 背景層次豐富：SVG 插畫 + noise_animation 動畫 + 背景訊息字體
- 所有動畫僅限品牌已有的 `noise_animation`，不引入其他 CSS/JS 動畫
- 不使用漸變色（`linear-gradient`、`radial-gradient` 等）
- 功能優先，裝飾其次，不花巧

## 完整報告

詳細的系統分析報告請參閱根目錄：

📄 **`BETWEEN_COFFEE_SYSTEM_REPORT.md`** (1185行)

涵蓋 8 大章節：系統核心價值、系統工程師視角、前端工程師視角、UX/UI 設計師視角、用戶視角、開發原則與藍圖、開發環境規則、附錄。

📄 **`.clinerules/ui-principles.md`** — UI 設計原則（品牌色、字型、間距、元件規範、動畫視覺元素）
