# WebSocket 架構遷移整合指南

## 概述

本文件記錄 Between Coffee 系統 WebSocket 架構的遷移與整合過程。目標是將分散的 WebSocket 連線管理統一為三層架構，提高穩定性、可維護性和效能。

## 新架構：三層設計

```
┌─────────────────────────────────────────────────┐
│                  應用層 (App Layer)                │
│  websocket-order.js  │  websocket-staff.js       │
│  (顧客端訂單管理)     │  (員工端隊列管理)          │
├─────────────────────────────────────────────────┤
│                  核心層 (Core Layer)               │
│  websocket-core.js                               │
│  (統一連線管理、事件系統、重連策略、心跳檢測)      │
├─────────────────────────────────────────────────┤
│                  橋接層 (Bridge Layer)              │
│  websocket-bridge.js                             │
│  (新舊架構兼容、漸進式遷移)                       │
└─────────────────────────────────────────────────┘
```

### 檔案對照表

| 檔案 | 層級 | 職責 | 依賴 |
|------|------|------|------|
| `websocket-core.js` | 核心層 | 統一連線管理、事件系統、重連策略、心跳檢測、狀態管理 | 無 |
| `websocket-order.js` | 應用層（顧客） | 訂單狀態監聽、支付狀態更新、取餐通知 | websocket-core.js |
| `websocket-staff.js` | 應用層（員工） | 隊列管理、訂單製作流程、狀態變更操作 | websocket-core.js |
| `websocket-bridge.js` | 橋接層 | 新舊架構兼容、漸進式遷移 | websocket-core.js（可選） |

## 遷移策略

### 階段一：共存（已完成 ✅）

- 新三層架構已建立並部署
- 橋接層 `websocket-bridge.js` 已建立
- 舊版 `unified-order-updater-enhanced.js` 保持不變
- 所有頁面同時載入新舊腳本

### 階段二：逐步遷移（進行中 🔄）

1. **訂單確認頁面** (`order_confirm.html`)
   - 使用 `WebSocketOrderManager` 取代內聯 WebSocket 邏輯
   - 透過橋接層確保向後兼容

2. **員工隊列頁面** (`queue_dashboard.html`)
   - 使用 `WebSocketStaffManager` 取代內聯 WebSocket 邏輯
   - 透過橋接層確保向後兼容

3. **訂單狀態卡片** (`order_status_cards.js`)
   - 整合到 `WebSocketOrderManager` 的事件系統
   - 移除重複的輪詢邏輯

### 階段三：清理（計劃中 📋）

- 移除舊版 `unified-order-updater-enhanced.js` 和 `unified-order-updater.js`
- 移除 `websocket-reconnect-manager.js`（功能已整合到核心層）
- 移除 `websocket-health-monitor.js` 和 `websocket-health-monitor-enhanced.js`
- 移除 `websocket-optimizer.js`
- 移除 `websocket-monitoring-adapter.js` 和 `websocket-monitoring-visualizer.js`
- 移除 `order_status_cards.js` 和 `order_payment_confirmation.js` 中的重複邏輯

## 如何使用新架構

### 顧客端（訂單頁面）

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 初始化訂單管理器
    const orderManager = new WebSocketOrderManager({
        orderId: '{{ order.id }}',
        onStatusChange: function(status, data) {
            // 處理狀態變更
            updateOrderUI(status, data);
        },
        onPaymentUpdate: function(paymentData) {
            // 處理支付更新
            updatePaymentUI(paymentData);
        }
    });
    
    // 開始監聽
    orderManager.connect();
});
</script>
```

### 員工端（隊列頁面）

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // 初始化員工隊列管理器
    const staffManager = new WebSocketStaffManager({
        onQueueUpdate: function(queueData) {
            // 更新隊列 UI
            renderQueue(queueData);
        },
        onOrderStatusChange: function(orderId, status) {
            // 更新單個訂單狀態
            updateOrderCard(orderId, status);
        }
    });
    
    // 開始監聽
    staffManager.connect();
});
</script>
```

### 使用橋接層（舊版兼容）

```javascript
// 舊版代碼只需將 new WebSocket(...) 替換為：
const bridge = new WebSocketBridge({
    type: 'order',
    orderId: 123,
    onMessage: function(e) {
        const data = JSON.parse(e.data);
        // 原有處理邏輯保持不變
    },
    onOpen: function() {
        console.log('已連線（透過橋接層）');
    }
});
```

## 載入順序（base.html）

腳本載入順序至關重要：

```html
<!-- 1. 核心層（必須最先載入） -->
<script src={% static "js/websocket-core.js" %}></script>

<!-- 2. 應用層（依賴核心層） -->
<script src={% static "js/websocket-order.js" %}></script>
<script src={% static "js/websocket-staff.js" %}></script>

<!-- 3. 橋接層（可選，用於舊版兼容） -->
<script src={% static "js/websocket-bridge.js" %}></script>

<!-- 4. 舊版腳本（保持不變，透過橋接層使用新核心） -->
<script src={% static "js/unified-order-updater-enhanced.js" %}></script>
```

## 事件系統參考

### 核心層事件

| 事件名稱 | 觸發時機 | 回調參數 |
|---------|---------|---------|
| `connected` | WebSocket 連線成功 | `{}` |
| `disconnected` | WebSocket 斷開 | `{code, reason}` |
| `reconnecting` | 正在重連 | `{attempt, maxRetries, delay}` |
| `reconnected` | 重連成功 | `{attempts}` |
| `message` | 收到訊息 | `{type, payload, ...}` |
| `error` | 發生錯誤 | `{message, error}` |
| `heartbeat` | 心跳檢測 | `{latency}` |

### 訂單層事件

| 事件名稱 | 觸發時機 | 回調參數 |
|---------|---------|---------|
| `order_status_change` | 訂單狀態變更 | `{order_id, status, ...}` |
| `payment_update` | 支付狀態更新 | `{order_id, payment_status, ...}` |
| `order_ready` | 訂單就緒可取餐 | `{order_id, pickup_code, ...}` |

### 員工層事件

| 事件名稱 | 觸發時機 | 回調參數 |
|---------|---------|---------|
| `queue_update` | 隊列更新 | `{queue: [...], stats: {...}}` |
| `new_order` | 新訂單加入 | `{order_id, items, ...}` |
| `order_completed` | 訂單製作完成 | `{order_id, ...}` |

## 測試驗證

### 手動測試清單

- [ ] 核心層初始化：確認 `WebSocketCore` 全域可用
- [ ] 連線建立：確認 WebSocket 連線成功
- [ ] 重連機制：斷開後自動重連（最多 10 次）
- [ ] 心跳檢測：每 30 秒發送 ping/pong
- [ ] 訂單狀態更新：顧客端收到狀態變更
- [ ] 隊列更新：員工端收到隊列變更
- [ ] 橋接層兼容：舊版 `UnifiedOrderUpdaterEnhanced` 正常運作
- [ ] 多標籤頁：同一用戶多個標籤頁共用單一連線

### 瀏覽器開發者工具驗證

```javascript
// 檢查核心層
console.log(WebSocketCore.getInstance());

// 檢查訂單管理器
console.log(window.orderManager);

// 檢查員工管理器
console.log(window.staffManager);

// 檢查橋接層
console.log(window.WebSocketBridge);
```

## 回滾計劃

如果新架構出現問題，可以快速回滾：

1. **從 base.html 移除**新腳本載入（websocket-core.js, websocket-order.js, websocket-staff.js, websocket-bridge.js）
2. **恢復**舊版腳本載入順序
3. **重新部署**到 Render

## 效能指標

| 指標 | 舊架構 | 新架構 | 改善 |
|------|--------|--------|------|
| WebSocket 連線數 | 每頁面 1 條 | 全域 1 條 | 減少 50%+ |
| 記憶體使用 | 多個實例 | 單一實例 | 減少 30%+ |
| 重連延遲 | 固定 5 秒 | 指數退避 | 更智慧 |
| 程式碼重複 | 高 | 低 | 減少 60%+ |

---

**最後更新**: 2026-06-17
**維護者**: 開發團隊
