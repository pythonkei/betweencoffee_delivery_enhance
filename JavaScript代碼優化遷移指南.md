# JavaScript 代碼優化遷移指南

## 概述

本指南旨在幫助開發團隊將現有的 JavaScript 代碼遷移到使用新創建的共用工具模塊，以減少代碼重複、提高性能和可維護性。

## 已創建的模塊

### 1. CommonUtils (`common-utils.js`)
**位置**: `static/js/staff-order-management/common-utils.js`
**功能**: 提供共用的工具函數，包括訂單分析、徽章生成、時間格式化、DOM 操作等。

### 2. PerformanceMonitor (`performance-monitor.js`)
**位置**: `static/js/staff-order-management/performance-monitor.js`
**功能**: 性能監控工具，收集渲染時間、API 響應時間、內存使用等指標。

### 3. 測試工具
- `test_common_utils_unit.js` - 單元測試
- `test_common_utils_simple.js` - 簡單測試
- `test_common_utils.html` - 瀏覽器測試頁面

## 遷移步驟

### 步驟 1: 檢查現有代碼

#### 識別重複代碼模式
```javascript
// 常見的重複模式：
1. 訂單類型分析邏輯
2. 徽章生成代碼
3. 時間格式化函數
4. Toast 通知顯示
5. DOM 元素創建
6. 事件處理防抖/節流
```

#### 使用搜索工具
```bash
# 搜索重複的訂單分析邏輯
grep -r "coffee_count\|bean_count\|is_mixed_order" static/js/staff-order-management/

# 搜索時間格式化代碼
grep -r "toLocaleString\|formatTime\|formatHK" static/js/staff-order-management/

# 搜索徽章生成代碼
grep -r "badge.*quickorder\|badge.*primary\|badge.*info" static/js/staff-order-management/
```

### 步驟 2: 導入 CommonUtils

#### 在 HTML 中導入
```html
<!-- 在現有 JavaScript 導入之前添加 -->
<script src="/static/js/staff-order-management/common-utils.js"></script>
<script src="/static/js/staff-order-management/performance-monitor.js"></script>
```

#### 檢查導入是否成功
```javascript
// 在瀏覽器控制台檢查
console.log('CommonUtils:', window.CommonUtils);
console.log('PerformanceMonitor:', window.PerformanceMonitor);
```

### 步驟 3: 遷移具體功能

#### 3.1 遷移訂單類型分析
**舊代碼**:
```javascript
const coffeeCount = order.coffee_count || 0;
const beanCount = order.bean_count || 0;
const hasCoffee = order.has_coffee || coffeeCount > 0;
const hasBeans = order.has_beans || beanCount > 0;
const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);
```

**新代碼**:
```javascript
const typeInfo = window.CommonUtils.analyzeOrderType(order);
// 使用 typeInfo.coffeeCount, typeInfo.beanCount, typeInfo.isMixedOrder 等
```

#### 3.2 遷移徽章生成
**舊代碼**:
```javascript
let orderTypeBadge = '';
if (order.is_quick_order) {
    orderTypeBadge = '<span class="badge badge-quickorder">快速訂單</span>';
} else if (isMixedOrder) {
    orderTypeBadge = '<span class="badge badge-primary">混合訂單</span>';
} else {
    orderTypeBadge = '<span class="badge badge-info">普通訂單</span>';
}
```

**新代碼**:
```javascript
const orderTypeBadges = window.CommonUtils.generateOrderTypeBadges(order, typeInfo);
const quantityBadges = window.CommonUtils.generateQuantityBadges(typeInfo);
```

#### 3.3 遷移時間格式化
**舊代碼**:
```javascript
const orderTime = new Date(order.created_at).toLocaleString('zh-HK', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
});
```

**新代碼**:
```javascript
const orderTime = window.CommonUtils.formatHKTime(order.created_at);
const orderTimeOnly = window.CommonUtils.formatHKTimeOnly(order.created_at);
```

#### 3.4 遷移訂單項目渲染
**舊代碼**:
```javascript
let itemsHTML = '';
items.forEach(item => {
    itemsHTML += `
        <div class="d-flex align-items-center mb-3">
            <div class="mr-3">
                <img src="${item.image}" alt="${item.name}" class="img-fluid">
            </div>
            <div class="flex-grow-1">
                <h6 class="mb-0">${item.name}</h6>
                <p class="mb-1 text-muted">數量: ${item.quantity}</p>
            </div>
        </div>
    `;
});
```

**新代碼**:
```javascript
const itemsHTML = window.CommonUtils.renderOrderItems(items);
```

#### 3.5 遷移 Toast 通知
**舊代碼**:
```javascript
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert">
            <span>&times;</span>
        </button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
```

**新代碼**:
```javascript
window.CommonUtils.showToast('操作成功', 'success');
window.CommonUtils.showToast('發生錯誤', 'error');
window.CommonUtils.showToast('提示信息', 'info');
```

#### 3.6 遷移 DOM 操作
**舊代碼**:
```javascript
const element = document.createElement('div');
element.className = 'order-item';
element.setAttribute('data-order-id', orderId);
element.innerHTML = `<h5>訂單 #${orderId}</h5>`;
```

**新代碼**:
```javascript
const element = window.CommonUtils.createElement('div', {
    className: 'order-item',
    'data-order-id': orderId,
    innerHTML: `<h5>訂單 #${orderId}</h5>`
});
```

### 步驟 4: 添加性能監控

#### 4.1 監控渲染時間
```javascript
// 舊代碼
this.renderOrders(orders);

// 新代碼（帶性能監控）
window.performanceMonitor.measureRenderTime('PreparingOrdersRenderer', () => {
    this.renderOrders(orders);
});
```

#### 4.2 監控 API 響應時間
```javascript
// 舊代碼
const response = await fetch('/api/orders');

// 新代碼（帶性能監控）
const response = await window.performanceMonitor.measureApiResponseTime(
    'getOrders',
    fetch('/api/orders')
);
```

#### 4.3 監控事件處理
```javascript
// 舊代碼
button.addEventListener('click', handleClick);

// 新代碼（帶性能監控）
button.addEventListener('click', 
    window.performanceMonitor.wrapEventHandler('buttonClick', handleClick)
);
```

### 步驟 5: 運行測試

#### 5.1 運行單元測試
```bash
cd /home/kei/Desktop/betweencoffee_delivery_enhance
node test_common_utils_unit.js
```

#### 5.2 瀏覽器測試
1. 打開 `test_common_utils.html`
2. 點擊各個測試按鈕
3. 檢查控制台輸出

#### 5.3 集成測試
```bash
# 檢查 CommonUtils 是否正確加載
node test_common_utils_simple.js
```

## 遷移示例

### 完整遷移示例：製作中訂單渲染器

**遷移前** (`preparing-orders-renderer.js` 片段):
```javascript
createOrderElement(order) {
    const orderId = order.id;
    const pickupCode = order.pickup_code;
    
    // 重複的訂單分析邏輯
    const coffeeCount = order.coffee_count || 0;
    const beanCount = order.bean_count || 0;
    const hasCoffee = order.has_coffee || coffeeCount > 0;
    const hasBeans = order.has_beans || beanCount > 0;
    const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
    
    // 重複的徽章生成邏輯
    let orderTypeBadge = '';
    if (order.is_quick_order) {
        orderTypeBadge = '<span class="badge badge-quickorder">快速訂單</span>';
    } else if (isMixedOrder) {
        orderTypeBadge = '<span class="badge badge-primary">混合訂單</span>';
    } else {
        orderTypeBadge = '<span class="badge badge-info">普通訂單</span>';
    }
    
    // 重複的時間格式化
    const orderTime = new Date(order.created_at).toLocaleString('zh-HK', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
    
    // ... 其他代碼
}
```

**遷移後** (`preparing-orders-renderer-migrated.js` 片段):
```javascript
createOrderElement(order) {
    const orderId = order.id;
    const pickupCode = order.pickup_code;
    
    // 使用 CommonUtils
    const typeInfo = window.CommonUtils.analyzeOrderType(order);
    const orderTypeBadges = window.CommonUtils.generateOrderTypeBadges(order, typeInfo);
    const quantityBadges = window.CommonUtils.generateQuantityBadges(typeInfo);
    const orderTime = window.CommonUtils.formatHKTime(order.created_at);
    
    // ... 其他使用 CommonUtils 的代碼
}
```

## 性能優化建議

### 1. 使用 DocumentFragment
```javascript
// 舊代碼（性能較差）
orders.forEach(order => {
    container.innerHTML += createOrderElement(order);
});

// 新代碼（性能較好）
const fragment = document.createDocumentFragment();
orders.forEach(order => {
    fragment.appendChild(createOrderElement(order));
});
container.appendChild(fragment);
```

### 2. 圖片懶加載
```javascript
// 在 CommonUtils.renderOrderItems 中已實現
<img src="${itemImage}" loading="lazy" ...>
```

### 3. 事件委托
```javascript
// 舊代碼（每個按鈕都綁定事件）
buttons.forEach(button => {
    button.addEventListener('click', handleClick);
});

// 新代碼（單個事件監聽器）
container.addEventListener('click', (e) => {
    if (e.target.closest('.action-button')) {
        handleClick(e);
    }
});
```

### 4. 防抖和節流
```javascript
// 使用 CommonUtils 的防抖函數
const debouncedSearch = window.CommonUtils.debounce(searchFunction, 300);
searchInput.addEventListener('input', debouncedSearch);

// 使用 CommonUtils 的節流函數
const throttledScroll = window.CommonUtils.throttle(handleScroll, 100);
window.addEventListener('scroll', throttledScroll);
```

## 常見問題解決

### 問題 1: CommonUtils 未定義
**解決方案**:
1. 檢查 `common-utils.js` 是否正確導入
2. 檢查導入順序（CommonUtils 需要在其他腳本之前導入）
3. 檢查控制台是否有 JavaScript 錯誤

### 問題 2: 性能監控影響性能
**解決方案**:
1. 調整採樣率：`window.performanceMonitor.setSamplingRate(0.05)` (5%)
2. 在開發環境啟用，生產環境禁用：`window.performanceMonitor.disable()`
3. 只監控關鍵操作

### 問題 3: 遷移後功能異常
**解決方案**:
1. 運行單元測試：`node test_common_utils_unit.js`
2. 使用瀏覽器測試頁面：`test_common_utils.html`
3. 逐步遷移，每次只遷移一個功能
4. 使用版本控制，方便回滾

## 遷移檢查清單

### 準備階段
- [ ] 備份現有代碼
- [ ] 閱讀本遷移指南
- [ ] 運行現有測試確保功能正常
- [ ] 識別需要遷移的檔案

### 實施階段
- [ ] 導入 CommonUtils 和 PerformanceMonitor
- [ ] 遷移訂單類型分析邏輯
- [ ] 遷移徽章生成代碼
- [ ] 遷移時間格式化函數
- [ ] 遷移訂單項目渲染
- [ ] 遷移 Toast 通知
- [ ] 遷移 DOM 操作
- [ ] 添加性能監控

### 測試階段
- [ ] 運行單元測試
- [ ] 進行瀏覽器測試
- [ ] 檢查控制台錯誤
- [ ] 驗證功能正常
- [ ] 性能測試

### 優化階段
- [ ] 應用性能優化建議
- [ ] 檢查內存使用
- [ ] 優化渲染性能
- [ ] 文檔更新

## 預期收益

### 代碼質量提升
- **代碼重複減少**: 預計減少 30-40% 的重複代碼
- **可維護性提高**: 統一的工具接口，清晰的函數文檔
- **錯誤減少**: 統一的錯誤處理，減少邊界情況錯誤

### 性能提升
- **渲染性能**: 使用 DocumentFragment 和懶加載
- **內存使用**: 更好的事件管理和 DOM 操作
- **響應時間**: 防抖和節流減少不必要的操作

### 開發效率提升
- **開發速度**: 重用現有工具函數
- **調試效率**: 統一的錯誤處理和日誌
- **團隊協作**: 標準化的代碼模式

## 支持與反饋

### 技術支持
- 查看 `common-utils.js` 源碼註釋
- 運行測試腳本驗證功能
- 檢查瀏覽器控制台錯誤

### 問題反饋
1. 記錄遇到的問題
2. 提供重現步驟
3. 提交問題報告

### 進一步優化
1. 創建更多專用工具模塊
2. 添加 TypeScript 類型定義
3. 集成構建工具
4. 自動化測試流程

## 總結

通過本遷移指南，您可以系統性地將現有 JavaScript 代碼遷移到使用共用工具模塊，從而提高代碼質量、性能和可維護性。建議按照步驟逐步遷移，並在每個階段進行充分的測試。

**關鍵要點**:
1. **逐步遷移**: 不要一次性遷移所有代碼
2. **充分測試**: 每個遷移步驟後都要測試
3. **性能監控**: 使用 PerformanceMonitor 監控性能變化
4. **文檔更新**: 更新相關技術文檔

祝遷移順利！