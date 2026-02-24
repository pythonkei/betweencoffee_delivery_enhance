// test_simple_renderer.js
// 簡化版訂單渲染器測試腳本

console.log('🚀 開始測試簡化版訂單渲染器...');

// 模擬DOM環境
if (typeof document === 'undefined') {
    const { JSDOM } = require('jsdom');
    const dom = new JSDOM('<!DOCTYPE html><html><body><div id="test-container"></div></body></html>');
    global.window = dom.window;
    global.document = dom.window.document;
    global.navigator = dom.window.navigator;
}

// 模擬統一數據管理器
window.unifiedDataManager = {
    currentData: {
        completed_orders: [],
        ready_orders: [],
        preparing_orders: []
    },
    listeners: {},
    
    registerListener: function(key, callback, immediate = false) {
        if (!this.listeners[key]) {
            this.listeners[key] = [];
        }
        this.listeners[key].push(callback);
        
        console.log(`✅ 註冊監聽器: ${key}`);
        
        if (immediate && this.currentData[key]) {
            setTimeout(() => callback(this.currentData[key]), 100);
        }
    },
    
    updateData: function(key, data) {
        this.currentData[key] = data;
        console.log(`📊 更新數據: ${key} (${data.length} 個訂單)`);
        
        if (this.listeners[key]) {
            this.listeners[key].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ 監聽器錯誤: ${error.message}`);
                }
            });
        }
        
        // 觸發全局更新事件
        const event = new window.CustomEvent('unified_data_updated');
        document.dispatchEvent(event);
    }
};

// 測試訂單數據
const testOrder = {
    id: 9999,
    created_at: new Date().toISOString(),
    pickup_code: 'TEST',
    customer_name: '測試客戶',
    customer_phone: '1234-5678',
    status: 'completed',
    total_amount: 99.99,
    payment_method: 'alipay',
    is_quick_order: true,
    items: [
        {
            name: '測試咖啡',
            price: 49.99,
            total_price: 49.99,
            quantity: 2,
            cup_level_cn: '大杯',
            milk_level_cn: '標準',
            image: '/static/images/test-coffee.jpg'
        }
    ]
};

// 創建測試容器
const container = document.createElement('div');
container.id = 'test-renderer-container';
document.body.appendChild(container);

// 動態加載簡化版渲染器
const fs = require('fs');
const path = require('path');

try {
    // 讀取簡化版渲染器文件
    const rendererPath = path.join(__dirname, 'static/js/staff-order-management/base-order-renderer-simple.js');
    const rendererCode = fs.readFileSync(rendererPath, 'utf8');
    
    // 執行代碼
    eval(rendererCode);
    
    console.log('✅ 簡化版渲染器加載成功');
    
    // 測試1: 創建渲染器實例
    console.log('\n🧪 測試1: 創建渲染器實例');
    const renderer = new BaseOrderRendererSimple('completed', 'test-renderer-container');
    
    // 等待初始化
    setTimeout(() => {
        console.log('✅ 渲染器初始化完成');
        
        // 測試2: 更新數據
        console.log('\n🧪 測試2: 更新訂單數據');
        window.unifiedDataManager.updateData('completed_orders', [testOrder]);
        
        // 檢查渲染結果
        setTimeout(() => {
            const renderedOrders = container.querySelectorAll('.card');
            console.log(`📊 渲染的訂單數量: ${renderedOrders.length}`);
            
            if (renderedOrders.length > 0) {
                console.log('✅ 訂單渲染成功');
                
                // 檢查訂單內容
                const orderCard = renderedOrders[0];
                const orderId = orderCard.querySelector('h6 strong').textContent;
                const customerName = orderCard.querySelector('.card-body p').textContent;
                
                console.log(`📋 訂單ID: ${orderId}`);
                console.log(`👤 客戶名稱: ${customerName}`);
                
                // 測試3: 空狀態顯示
                console.log('\n🧪 測試3: 空狀態顯示');
                window.unifiedDataManager.updateData('completed_orders', []);
                
                setTimeout(() => {
                    const emptyState = container.querySelector('.text-center');
                    if (emptyState) {
                        console.log('✅ 空狀態顯示正常');
                    } else {
                        console.log('⚠️ 空狀態未顯示');
                    }
                    
                    // 測試4: 銷毀渲染器
                    console.log('\n🧪 測試4: 銷毀渲染器');
                    renderer.destroy();
                    
                    if (container.innerHTML === '') {
                        console.log('✅ 渲染器銷毀成功');
                    } else {
                        console.log('⚠️ 渲染器銷毀後容器未清空');
                    }
                    
                    console.log('\n🎉 所有測試完成！');
                    process.exit(0);
                }, 500);
            } else {
                console.log('❌ 訂單渲染失敗');
                process.exit(1);
            }
        }, 500);
    }, 1000);
    
} catch (error) {
    console.error('❌ 測試失敗:', error);
    process.exit(1);
}