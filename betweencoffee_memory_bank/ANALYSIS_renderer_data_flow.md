# UnifiedDataManager → Renderer 資料流分析報告

> **最後更新**: 2026-07-26
> **分析範圍**: unified-data-manager.js → base-order-renderer-v2.js → 各子渲染器

---

## 一、資料流完整鏈路

```
forceRefresh / DebounceCoordinator 觸發
        │
        ▼
UnifiedDataManager.loadUnifiedData(force=false/true)
        │
        ├── fetch(/eshop/queue/unified-data/)
        │
        ├── validateDataStructure(result) ← 確保所有必要欄位存在
        │
        ├── this.currentData = result.data
        │
        └── notifyAllListeners()
                │
                ├── notifyOrder[0]: 'badge_summary'           → badge-manager.js callback
                ├── notifyOrder[1]: 'payment_pending_orders'  → PaymentPendingRendererV2
                ├── notifyOrder[2]: 'waiting_orders'           → (無對應 V2 渲染器)
                ├── notifyOrder[3]: 'preparing_orders'         → PreparingOrdersRendererV2
                ├── notifyOrder[4]: 'ready_orders'             → ReadyOrdersRendererV2
                ├── notifyOrder[5]: 'completed_orders'         → CompletedOrdersRendererV2
                └── notifyOrder[6]: 'all_data'                 → (可選全局監聽器)
```

---

## 二、DataKey 對照表

| 渲染器 | orderType | dataKey | UnifiedDataManager.listeners key | 一致性 |
|--------|-----------|---------|--------------------------------|:------:|
| `PaymentPendingRendererV2` | `payment_pending` | `payment_pending_orders` ✅ (明確指定) | `payment_pending_orders` | ✅ |
| `PreparingOrdersRendererV2` | `preparing` | `preparing_orders` (預設) | `preparing_orders` | ✅ |
| `ReadyOrdersRendererV2` | `ready` | `ready_orders` (預設) | `ready_orders` | ✅ |
| `CompletedOrdersRendererV2` | `completed` | `completed_orders` (預設) | `completed_orders` | ✅ |
| BadgeManager | -- | `badge_summary` | `badge_summary` | ✅ |
| waiting_orders | -- | 無對應 V2 渲染器 | `waiting_orders` | ⚠️ 已註冊但無監聽者 |

**結論**: 所有 V2 渲染器的 dataKey 都與 UnifiedDataManager 的 listeners key 完全一致。

---

## 三、註冊流程深度分析

### 3.1 渲染器初始化順序

```
渲染器 Constructor(options)
    │
    └── super(orderType, ...)
            │
            └── this.options.dataKey = options.dataKey || `${orderType}_orders`
                    │
                    └── 註：payment_pending 明確指定 dataKey: 'payment_pending_orders'
                        其他渲染器使用預設值 `${orderType}_orders`
```

### 3.2 建構函數延遲初始化

```
constructor() 呼叫 super()
    │
    └── setTimeout(() => this.initialize(), 100)
            │
            └── initialize()
                    ├── registerToUnifiedManager()
                    │       └── window.unifiedDataManager.registerListener(
                    │              this.options.dataKey,  // ← 資料類型 key
                    │              (data) => this.handleUnifiedData(data),  // ← callback
                    │              true  // ← immediate=true：註冊後立即回調一次
                    │       )
                    │
                    ├── bindEvents()
                    ├── checkAndLoadData()
                    └── startAutoRefresh()
```

### 3.3 registerListener 內部機制

```javascript
registerListener(dataType, callback, immediate = true) {
    // 1. 避免重複註冊（function reference 比對）
    const existingIndex = this.listeners[dataType]
        .findIndex(cb => cb === callback);
    
    // 2. 推送 callback 到 listeners[dataType]
    this.listeners[dataType].push(callback);
    
    // 3. 立即回調（如果已有數據）
    if (immediate && this.currentData && 
        this.currentData[dataType] !== undefined) {
        setTimeout(() => callback(this.currentData[dataType]), 0);
    }
    
    // 4. 返回取消函數
    return () => this.unregisterListener(dataType, callback);
}
```

---

## 四、完整推送鏈路驗證

### 4.1 正常流程（API 返回成功）

```
loadUnifiedData() 成功
    │
    ├── this.currentData = result.data
    │
    └── notifyAllListeners()
            │
            └── 按 notifyOrder 陣列順序執行：
                forEach dataType in notifyOrder:
                    notifyListeners(dataType, this.currentData[dataType])
                        │
                        └── forEach callback in listeners[dataType]:
                                callback(data)
                                    │
                                    └── handleUnifiedData(data)
                                            │
                                            └── this.orders = data  // 更新本地數據
                                                this.renderOrders()  // 觸發渲染
```

### 4.2 強制刷新流程（forceRefresh）

```
forceRefresh()
    │
    └── this.loadUnifiedData(true)
            │
            ├── this.isLoading = false  // 強制中斷當前加載
            ├── fetch(/eshop/queue/unified-data/)
            │
            └── 成功後 → notifyAllListeners()
```

### 4.3 WebSocket 觸發流程（透過 DebounceCoordinator）

```
WebSocket 事件 (queue_updated, order_status_changed, etc.)
    │
    └── document.addEventListener(eventName, ...)
            │
            └── DebounceCoordinator.scheduleRefresh('websocket', eventName, ...)
                    │
                    ├── 防抖檢查 (300ms)
                    ├── 優先級排序
                    │
                    └── executeRefresh(task)
                            │
                            └── window.unifiedDataManager.loadUnifiedData(true)
                                    │
                                    └── 成功後 → notifyAllListeners()
```

### 4.4 自動輪詢流程

```
UnifiedDataManager.startAutoRefresh()
    │
    ├── 每 10 秒執行一次
    ├── 檢查 WebSocket 是否連線（連線中跳過輪詢）
    ├── 檢查頁面是否可見（不可見暫停）
    └── 檢查網路狀態（離線暫停）
            │
            └── loadUnifiedData()
                    │
                    └── 成功後 → notifyAllListeners()
```

---

## 五、BadgeManager 資料流

### 5.1 註冊方式

```javascript
// BadgeManager 註冊 badge_summary 監聽器
window.unifiedDataManager.registerListener(
    'badge_summary',
    (badgeData) => this.updateBadges(badgeData),
    true
);
```

### 5.2 badge_summary 資料結構

```javascript
// UnifiedDataManager 確保的預設結構
badgeData = {
    payment_pending: number,  // 待確認付款
    waiting: number,          // 等待中
    preparing: number,        // 準備中
    ready: number,            // 已就緒
    completed: number         // 已完成
}
```

### 5.3 badge 更新時機

badge_summary 在 notifyOrder 陣列中排在第 0 位（最先通知），確保：
1. 徽章數字在所有子標籤頁內容渲染**之前**更新
2. SubtabManager 可以依賴 badge_summary 來設定子標籤頁 badge

---

## 六、關鍵設計決策

### 6.1 immediate=true 的作用

- 渲染器註冊時立刻獲得當前的 cached 數據
- 即使 UnifiedDataManager 尚未完成首次 API 請求，只要 currentData 存在就能拿到數據
- 避免 race condition：註冊晚於 API 返回時，仍能收到回調

### 6.2 避免重複註冊

```javascript
// 透過 function reference 比對避免同一 callback 註冊兩次
const existingIndex = this.listeners[dataType]
    .findIndex(cb => cb === callback);
if (existingIndex === -1) {
    this.listeners[dataType].push(callback);
}
```

### 6.3 100ms 延遲初始化

```javascript
constructor() {
    // 100ms 延遲確保 DOM 已準備就緒
    setTimeout(() => this.initialize(), 100);
}
```

這個 100ms 延遲的風險：
- 如果 UnifiedDataManager 的首次 API 請求在 50ms 內返回，渲染器尚未註冊
- 但 immediate=true 確保註冊後立即拿到 cached 數據，所以最終數據不會遺失

### 6.4 監聽器執行錯誤處理

```javascript
notifyListeners(dataType, data) {
    this.listeners[dataType].forEach((callback, index) => {
        try {
            callback(data);  // 單個 callback 失敗不影響其他 callback
        } catch (error) {
            console.error(...);
            errors.push({ index, error, dataType });
        }
    });
    
    // 收集所有錯誤後統一觸發事件
    if (errors.length > 0) {
        this.dispatchGlobalEvent('listener_error', { dataType, errors });
    }
}
```

---

## 七、驗證結論

| 檢查項 | 結果 | 說明 |
|--------|:----:|------|
| dataKey 一致性 | ✅ | 所有 V2 渲染器 dataKey 與 listeners key 完全匹配 |
| 推送鏈路完整性 | ✅ | forceRefresh → loadUnifiedData → notifyAllListeners → notifyListeners(dataType, data) → callback(data) 鏈路完整 |
| immediate 回調 | ✅ | 註冊時立即用 cached 數據回調一次 |
| 錯誤隔離 | ✅ | 單個監聽器異常不影響其他監聽器 |
| 防重複註冊 | ✅ | function reference 比對避免重複 |
| notifyOrder 覆蓋 | ✅ | 所有 6 個 active dataType 都在 notifyOrder 陣列中 |
| Badge 優先更新 | ✅ | badge_summary 排在第 0 位最先通知 |

**唯一注意事項**: `waiting_orders` 在 UnifiedDataManager 的 listeners 中有註冊槽位，但目前沒有 V2 渲染器監聽此 dataType。這是因為 waiting 狀態的訂單在員工後台不需要獨立子標籤頁顯示（訂單直接從 payment_pending 到 preparing 或從 paid/waiting 自動前進）。