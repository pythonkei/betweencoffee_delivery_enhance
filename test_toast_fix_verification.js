// 測試多重訊息彈出問題修復
console.log('🔍 開始測試多重訊息彈出問題修復...');

// 模擬 toast-manager.js
window.toast = {
    success: function(message) {
        console.log('✅ toast.success:', message);
        incrementToastCount('success');
    },
    error: function(message) {
        console.log('❌ toast.error:', message);
        incrementToastCount('error');
    },
    info: function(message) {
        console.log('ℹ️ toast.info:', message);
        incrementToastCount('info');
    },
    warning: function(message) {
        console.log('⚠️ toast.warning:', message);
        incrementToastCount('warning');
    }
};

// 模擬 orderManager
window.orderManager = {
    showToast: function(message, type) {
        console.log(`📢 orderManager.showToast: ${message} (${type})`);
        incrementToastCount(type);
    }
};

// 計數器
let toastCounts = {
    success: 0,
    error: 0,
    info: 0,
    warning: 0,
    total: 0
};

function incrementToastCount(type) {
    toastCounts[type]++;
    toastCounts.total++;
    console.log(`📊 當前計數: ${type}=${toastCounts[type]}, 總計=${toastCounts.total}`);
}

// 模擬 queue-manager.js 中的方法
async function simulateStartPreparation(orderId = 123) {
    console.log(`🔄 模擬開始製作訂單 #${orderId}`);
    
    // 1. 調用 API（模擬）
    console.log(`🔄 調用 API: /eshop/queue/start/${orderId}/`);
    
    // 2. 顯示成功訊息
    window.toast.success(`✅ 已開始製作訂單 #${orderId}`);
    
    // 3. 觸發事件
    document.dispatchEvent(new CustomEvent('order_started_preparing', {
        detail: { 
            order_id: orderId,
            estimated_ready_time: '15:30'
        }
    }));
    
    console.log('📢 事件觸發: order_started_preparing');
}

async function simulateMarkAsReady(orderId = 123) {
    console.log(`🔄 模擬標記訂單 #${orderId} 為就緒`);
    
    // 1. 調用 API（模擬）
    console.log(`🔄 調用 API: /eshop/queue/ready/${orderId}/`);
    
    // 2. 顯示成功訊息
    window.toast.success(`✅ 訂單 #${orderId} 已標記為就緒`);
    
    // 3. 觸發事件
    document.dispatchEvent(new CustomEvent('order_marked_ready', {
        detail: { order_id: orderId }
    }));
    
    console.log('📢 事件觸發: order_marked_ready');
}

async function simulateMarkAsCollected(orderId = 123) {
    console.log(`🔄 模擬標記訂單 #${orderId} 為已提取`);
    
    // 1. 調用 API（模擬）
    console.log(`🔄 調用 API: /eshop/queue/collected/${orderId}/`);
    
    // 2. 顯示成功訊息
    window.toast.success(`✅ 訂單 #${orderId} 已標記為已提取`);
    
    // 3. 觸發事件
    document.dispatchEvent(new CustomEvent('order_collected', {
        detail: { order_id: orderId }
    }));
    
    console.log('📢 事件觸發: order_collected');
}

// 模擬 order-manager.js 中的事件處理（修改後版本）
document.addEventListener('order_started_preparing', (event) => {
    const orderId = event.detail.order_id;
    console.log(`🔄 order-manager: 訂單 #${orderId} 開始製作`);
    // 注意：不再顯示成功訊息，已在 queue-manager.js 中顯示
});

document.addEventListener('order_marked_ready', (event) => {
    const orderId = event.detail.order_id;
    console.log(`🔄 order-manager: 訂單 #${orderId} 已標記為就緒`);
    // 注意：不再顯示成功訊息，已在 queue-manager.js 中顯示
});

document.addEventListener('order_collected', (event) => {
    const orderId = event.detail.order_id;
    console.log(`🔄 order-manager: 訂單 #${orderId} 已標記為已提取`);
    // 注意：不再顯示成功訊息，已在 queue-manager.js 中顯示
});

// 測試函數
async function runTests() {
    console.log('\n🧪 ========== 開始測試 ==========\n');
    
    // 重置計數器
    toastCounts = { success: 0, error: 0, info: 0, warning: 0, total: 0 };
    
    // 測試1: 開始製作按鈕
    console.log('🧪 測試1: 開始製作按鈕');
    await simulateStartPreparation(101);
    console.log(`📊 結果: 顯示了 ${toastCounts.success} 個成功訊息`);
    console.log(`📊 預期: 應該只顯示 1 個成功訊息\n`);
    
    // 等待1秒
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 測試2: 已就緒按鈕
    console.log('🧪 測試2: 已就緒按鈕');
    await simulateMarkAsReady(102);
    console.log(`📊 結果: 顯示了 ${toastCounts.success} 個成功訊息`);
    console.log(`📊 預期: 應該只顯示 2 個成功訊息（累計）\n`);
    
    // 等待1秒
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 測試3: 客戶已提取按鈕
    console.log('🧪 測試3: 客戶已提取按鈕');
    await simulateMarkAsCollected(103);
    console.log(`📊 結果: 顯示了 ${toastCounts.success} 個成功訊息`);
    console.log(`📊 預期: 應該只顯示 3 個成功訊息（累計）\n`);
    
    // 測試4: 快速連續點擊（測試防重複機制）
    console.log('🧪 測試4: 快速連續點擊同一按鈕');
    toastCounts.success = 0; // 重置成功計數
    await simulateStartPreparation(104);
    await simulateStartPreparation(104); // 立即再次點擊
    console.log(`📊 結果: 顯示了 ${toastCounts.success} 個成功訊息`);
    console.log(`📊 預期: 應該只顯示 1 個成功訊息（防重複機制生效）\n`);
    
    // 總結
    console.log('📋 ========== 測試總結 ==========');
    console.log(`✅ 總共顯示了 ${toastCounts.total} 個訊息`);
    console.log(`✅ 成功訊息: ${toastCounts.success}`);
    console.log(`✅ 錯誤訊息: ${toastCounts.error}`);
    console.log(`✅ 信息訊息: ${toastCounts.info}`);
    console.log(`✅ 警告訊息: ${toastCounts.warning}`);
    
    // 驗證修復
    const expectedTotal = 4; // 3個正常操作 + 1個防重複測試
    if (toastCounts.total === expectedTotal) {
        console.log('\n🎉 測試通過！多重訊息彈出問題已修復。');
        console.log('✅ 每個操作只顯示一個成功訊息');
        console.log('✅ 防重複機制正常運作');
    } else {
        console.log(`\n⚠️ 測試未通過：顯示了 ${toastCounts.total} 個訊息，預期 ${expectedTotal} 個`);
        console.log('❌ 可能還有重複顯示的問題');
    }
}

// 運行測試
runTests().catch(console.error);