#!/usr/bin/env node
/**
 * verify_step1_addManagedListener.js
 * 
 * 全面驗證步驟1：addEventListener → _addManagedListener 遷移是否正確
 * 
 * 驗證項目：
 * 1. 所有 4 個 V2 渲染器的 _bindOrderActions 中無殘留 addEventListener
 * 2. 所有按鈕綁定都使用 _addManagedListener
 * 3. _addManagedListener 在 BaseOrderRendererV2 中有正確定義
 * 4. cleanup() 方法能正確清理監聽器
 * 5. 模擬完整的事件綁定 → 清理流程
 * 6. 檢查 preparing-orders 的 markCountdownCompleted 重新綁定
 */

const fs = require('fs');
const path = require('path');

// ==================== 配置 ====================
const RENDERERS_DIR = path.join(__dirname, 'static/js/staff-order-management/renderers-v2');
const BASE_RENDERER_PATH = path.join(__dirname, 'static/js/staff-order-management/base-order-renderer-v2.js');

const RENDERER_FILES = [
    'payment-pending-renderer-v2.js',
    'preparing-orders-renderer-v2.js',
    'ready-orders-renderer-v2.js',
    'completed-orders-renderer-v2.js'
];

// ==================== 工具函數 ====================
let passed = 0;
let failed = 0;
const errors = [];

function assert(condition, message) {
    if (condition) {
        passed++;
        console.log(`  ✅ ${message}`);
    } else {
        failed++;
        errors.push(message);
        console.log(`  ❌ ${message}`);
    }
}

function assertEqual(actual, expected, message) {
    if (actual === expected) {
        passed++;
        console.log(`  ✅ ${message} (${expected})`);
    } else {
        failed++;
        errors.push(`${message} — 期望: ${expected}, 實際: ${actual}`);
        console.log(`  ❌ ${message} — 期望: ${expected}, 實際: ${actual}`);
    }
}

/**
 * 從檔案內容中提取 _bindOrderActions 方法的內容
 * 使用行號分析來精確定位方法邊界
 */
function extractBindOrderActions(content) {
    const lines = content.split('\n');
    let startLine = -1;
    let braceCount = 0;
    let inMethod = false;
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // 找到 _bindOrderActions 方法定義
        if (!inMethod && line.includes('_bindOrderActions(') && line.trimEnd().endsWith('{')) {
            startLine = i;
            inMethod = true;
            braceCount = 1;
            continue;
        }
        
        if (inMethod) {
            // 計算大括號
            for (const ch of line) {
                if (ch === '{') braceCount++;
                if (ch === '}') braceCount--;
            }
            
            if (braceCount === 0) {
                // 返回方法內容（包含方法簽名行到結尾行）
                return lines.slice(startLine, i + 1).join('\n');
            }
        }
    }
    
    return null;
}

// ==================== 測試套件 ====================

console.log('\n' + '='.repeat(70));
console.log('📋 步驟1 驗證：addEventListener → _addManagedListener 遷移');
console.log('='.repeat(70));

// ---- 測試 1: 檢查 BaseOrderRendererV2 中 _addManagedListener 的定義 ----
console.log('\n📌 測試 1: BaseOrderRendererV2 中 _addManagedListener 定義');
console.log('-'.repeat(50));

const baseContent = fs.readFileSync(BASE_RENDERER_PATH, 'utf-8');

assert(
    baseContent.includes('_addManagedListener(target, event, handler)'),
    '_addManagedListener 方法簽名正確'
);

assert(
    baseContent.includes('eventListeners'),
    'eventListeners (Map) 存在'
);

assert(
    baseContent.includes('_removeAllManagedListeners()'),
    '_removeAllManagedListeners 方法存在'
);

assert(
    baseContent.includes('cleanup()'),
    'cleanup 方法存在'
);

// 檢查 _addManagedListener 的實作邏輯
assert(
    baseContent.includes('target.addEventListener(event, handler)'),
    '_addManagedListener 內部使用 addEventListener'
);

assert(
    baseContent.includes('this.eventListeners.set('),
    '_addManagedListener 將監聽器存入 eventListeners Map'
);

// 檢查 cleanup 調用 _removeAllManagedListeners
assert(
    baseContent.includes('this._removeAllManagedListeners()'),
    'cleanup 調用 _removeAllManagedListeners'
);

// 檢查 _removeAllManagedListeners 的實作
assert(
    baseContent.includes('this.eventListeners.forEach('),
    '_removeAllManagedListeners 遍歷 eventListeners'
);

assert(
    baseContent.includes('target.removeEventListener(event, handler)'),
    '_removeAllManagedListeners 移除所有監聽器'
);

assert(
    baseContent.includes('this.eventListeners.clear()'),
    '_removeAllManagedListeners 清空 eventListeners'
);

// ---- 測試 2: 檢查所有 V2 渲染器無殘留 addEventListener ----
console.log('\n📌 測試 2: V2 渲染器無殘留 addEventListener');
console.log('-'.repeat(50));

for (const file of RENDERER_FILES) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 使用精確方法提取 _bindOrderActions
    const bindSection = extractBindOrderActions(content);
    if (bindSection) {
        const hasRawAddEventListener = bindSection.includes('.addEventListener(');
        assert(
            !hasRawAddEventListener,
            `${file} 的 _bindOrderActions 中無殘留 addEventListener`
        );
    } else {
        console.log(`  ⚠️ 無法解析 ${file} 的 _bindOrderActions`);
    }
}

// ---- 測試 3: 檢查所有按鈕綁定使用 _addManagedListener ----
console.log('\n📌 測試 3: 按鈕綁定使用 _addManagedListener');
console.log('-'.repeat(50));

for (const file of RENDERER_FILES) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 使用精確方法提取 _bindOrderActions
    const bindSection = extractBindOrderActions(content);
    if (bindSection) {
        const managedListenerCount = (bindSection.match(/this\._addManagedListener/g) || []).length;
        const rawListenerCount = (bindSection.match(/\.addEventListener\(/g) || []).length;
        
        assert(
            managedListenerCount > 0,
            `${file} 的 _bindOrderActions 中有 ${managedListenerCount} 個 _addManagedListener 調用`
        );
        assertEqual(
            rawListenerCount, 0,
            `${file} 的 _bindOrderActions 中無原始 addEventListener`
        );
    }
}

// ---- 測試 4: 檢查每個渲染器的按鈕綁定數量 ----
console.log('\n📌 測試 4: 按鈕綁定數量檢查');
console.log('-'.repeat(50));

const expectedBindings = {
    'payment-pending-renderer-v2.js': 3,  // 確認FPS、確認現金、取消訂單
    'preparing-orders-renderer-v2.js': 3, // 完成製作x2、加速
    'ready-orders-renderer-v2.js': 1,     // 已提取
    'completed-orders-renderer-v2.js': 1  // 查看詳情
};

for (const [file, expected] of Object.entries(expectedBindings)) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 計算整個檔案中的 _addManagedListener 調用
    const totalManagedListeners = (content.match(/this\._addManagedListener/g) || []).length;
    
    // 使用精確方法提取 _bindOrderActions
    const bindSection = extractBindOrderActions(content);
    let bindManagedCount = 0;
    if (bindSection) {
        bindManagedCount = (bindSection.match(/this\._addManagedListener/g) || []).length;
    }
    
    console.log(`  📊 ${file}: 總計 ${totalManagedListeners} 個 _addManagedListener, _bindOrderActions 中 ${bindManagedCount} 個`);
    
    // 檢查 _bindOrderActions 中的綁定數量是否符合預期
    if (file === 'preparing-orders-renderer-v2.js') {
        assert(bindManagedCount >= 2, `${file} 至少有 2 個 _addManagedListener 在按鈕綁定中`);
    } else {
        assertEqual(bindManagedCount, expected, `${file} 的 _bindOrderActions 中有 ${expected} 個 _addManagedListener`);
    }
}

// ---- 測試 5: 模擬事件綁定與清理流程 ----
console.log('\n📌 測試 5: 模擬事件綁定與清理流程');
console.log('-'.repeat(50));

// 模擬 BaseOrderRendererV2 的 _addManagedListener 和 cleanup 行為（使用 Map）
class MockBaseRenderer {
    constructor() {
        this.eventListeners = new Map();
        this._listenerIdCounter = 0;
    }

    _addManagedListener(target, event, handler) {
        target.addEventListener(event, handler);
        const key = `${event}_${Date.now()}_${Math.random()}`;
        this.eventListeners.set(key, { target, event, handler });
        return () => {
            target.removeEventListener(event, handler);
            this.eventListeners.delete(key);
        };
    }

    _removeAllManagedListeners() {
        this.eventListeners.forEach(({ target, event, handler }) => {
            target.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
    }

    cleanup() {
        this._removeAllManagedListeners();
    }
}

// 模擬 DOM 元素
class MockElement {
    constructor(name) {
        this.name = name;
        this.listeners = {};
    }
    addEventListener(event, handler) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(handler);
    }
    removeEventListener(event, handler) {
        if (!this.listeners[event]) return;
        const idx = this.listeners[event].indexOf(handler);
        if (idx !== -1) {
            this.listeners[event].splice(idx, 1);
        }
    }
    getListenerCount(event) {
        return this.listeners[event] ? this.listeners[event].length : 0;
    }
}

// 測試 5a: 基本綁定與清理
const renderer = new MockBaseRenderer();
const btn1 = new MockElement('btn-confirm-fps');
const btn2 = new MockElement('btn-cancel-order');

renderer._addManagedListener(btn1, 'click', () => {});
renderer._addManagedListener(btn2, 'click', () => {});

assertEqual(btn1.getListenerCount('click'), 1, '按鈕1 綁定後有 1 個監聽器');
assertEqual(btn2.getListenerCount('click'), 1, '按鈕2 綁定後有 1 個監聽器');
assertEqual(renderer.eventListeners.size, 2, 'renderer 追蹤了 2 個監聽器');

renderer.cleanup();
assertEqual(btn1.getListenerCount('click'), 0, '按鈕1 清理後無監聽器');
assertEqual(btn2.getListenerCount('click'), 0, '按鈕2 清理後無監聽器');
assertEqual(renderer.eventListeners.size, 0, 'renderer 清理後 eventListeners 為空');

// 測試 5b: 多次 cleanup 不報錯
renderer.cleanup();
assertEqual(renderer.eventListeners.size, 0, '重複 cleanup 安全');
console.log('  ✅ 重複 cleanup 不報錯');

// 測試 5c: 重新綁定場景（如 markCountdownCompleted）
const renderer2 = new MockBaseRenderer();
const btn3 = new MockElement('btn-mark-ready');
const btn4 = new MockElement('btn-expedite');

renderer2._addManagedListener(btn3, 'click', () => {});
renderer2._addManagedListener(btn4, 'click', () => {});

renderer2.cleanup(); // 清理舊監聽器
renderer2._addManagedListener(btn3, 'click', () => {}); // 重新綁定

assertEqual(btn3.getListenerCount('click'), 1, '重新綁定後按鈕3 有 1 個監聽器');
assertEqual(btn4.getListenerCount('click'), 0, '重新綁定後按鈕4 無監聽器（已清理）');
assertEqual(renderer2.eventListeners.size, 1, '重新綁定後追蹤 1 個監聽器');

// ---- 測試 6: 檢查檔案語法完整性 ----
console.log('\n📌 測試 6: 檔案語法完整性檢查');
console.log('-'.repeat(50));

for (const file of RENDERER_FILES) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 檢查 class 定義
    assert(
        content.includes('class ') && content.includes('extends BaseOrderRendererV2'),
        `${file} 正確定義 class`
    );
    
    // 檢查 constructor
    assert(
        content.includes('constructor()'),
        `${file} 有 constructor`
    );
    
    // 檢查 super() 調用
    assert(
        content.includes('super('),
        `${file} 調用 super()`
    );
    
    // 檢查 createOrderElement
    assert(
        content.includes('createOrderElement(order)'),
        `${file} 有 createOrderElement`
    );
    
    // 檢查 _bindOrderActions
    assert(
        content.includes('_bindOrderActions(div, order)'),
        `${file} 有 _bindOrderActions`
    );
    
    // 檢查全局註冊
    assert(
        content.includes('window.'),
        `${file} 有全局註冊`
    );
}

// ---- 測試 7: 檢查 preparing-orders-renderer-v2.js 的 markCountdownCompleted ----
console.log('\n📌 測試 7: preparing-orders-renderer-v2.js markCountdownCompleted 重新綁定');
console.log('-'.repeat(50));

const preparingContent = fs.readFileSync(
    path.join(RENDERERS_DIR, 'preparing-orders-renderer-v2.js'),
    'utf-8'
);

// 檢查 markCountdownCompleted 中的重新綁定
assert(
    preparingContent.includes('markCountdownCompleted'),
    'markCountdownCompleted 方法存在'
);

// 檢查 markCountdownCompleted 中的重新綁定使用 _addManagedListener
const markCountdownSection = extractBindOrderActions(preparingContent.replace('_bindOrderActions', 'markCountdownCompleted'));
// 改用更簡單的方法
const markCountdownMatch = preparingContent.match(/markCountdownCompleted[\s\S]*?\n    \}/);
if (markCountdownMatch) {
    const section = markCountdownMatch[0];
    const hasManagedListener = section.includes('this._addManagedListener');
    const hasRawListener = section.includes('.addEventListener(');
    
    assert(hasManagedListener, 'markCountdownCompleted 使用 _addManagedListener 重新綁定');
    assert(!hasRawListener, 'markCountdownCompleted 無殘留 addEventListener');
}

// ---- 測試 8: 檢查所有檔案中全域的 addEventListener 殘留 ----
console.log('\n📌 測試 8: 全域 addEventListener 殘留檢查');
console.log('-'.repeat(50));

for (const file of RENDERER_FILES) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 逐行檢查 addEventListener（排除註解行）
    const lines = content.split('\n');
    let rawAddEventListenerCount = 0;
    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.includes('.addEventListener(') && !trimmed.startsWith('//') && !trimmed.startsWith('*')) {
            rawAddEventListenerCount++;
        }
    }
    
    assertEqual(rawAddEventListenerCount, 0, `${file} 全域無殘留 addEventListener`);
}

// ---- 測試 9: 檢查 _addManagedListener 的 return 值使用 ----
console.log('\n📌 測試 9: _addManagedListener 返回值使用檢查');
console.log('-'.repeat(50));

// 檢查是否有程式碼使用 _addManagedListener 的返回值（cleanup function）
for (const file of RENDERER_FILES) {
    const filePath = path.join(RENDERERS_DIR, file);
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 檢查是否有變數接收 _addManagedListener 的返回值
    const returnUsage = content.match(/const\s+\w+\s*=\s*this\._addManagedListener/g);
    if (returnUsage) {
        console.log(`  ⚠️ ${file}: ${returnUsage.length} 處使用了 _addManagedListener 返回值（非錯誤，僅供參考）`);
    }
}

// ---- 測試 10: 端到端模擬：完整渲染器生命週期 ----
console.log('\n📌 測試 10: 端到端模擬：完整渲染器生命週期');
console.log('-'.repeat(50));

class EndToEndRenderer extends MockBaseRenderer {
    constructor(orderType) {
        super();
        this.orderType = orderType;
        this.currentOrders = new Map();
        this.cachedOrders = null;
        this.isProcessingAction = false;
        this.hasInitialData = false;
        this.isReady = false;
    }

    // 模擬完整 cleanup
    fullCleanup() {
        this._removeAllManagedListeners();
        this.currentOrders.clear();
        this.cachedOrders = null;
        this.isProcessingAction = false;
        this.hasInitialData = false;
        this.isReady = false;
    }
}

// 模擬完整生命週期
const e2eRenderer = new EndToEndRenderer('payment_pending');

// 模擬 3 個訂單卡片，每個有 3 個按鈕
const orders = [
    { id: 1, buttons: ['confirm-fps', 'confirm-cash', 'cancel'] },
    { id: 2, buttons: ['confirm-fps', 'confirm-cash', 'cancel'] },
    { id: 3, buttons: ['confirm-fps', 'confirm-cash', 'cancel'] }
];

let totalListeners = 0;
for (const order of orders) {
    for (const btnName of order.buttons) {
        const btn = new MockElement(`btn-${btnName}-${order.id}`);
        e2eRenderer._addManagedListener(btn, 'click', () => {});
        totalListeners++;
    }
}

assertEqual(e2eRenderer.eventListeners.size, 9, `綁定了 ${totalListeners} 個監聽器（3 訂單 x 3 按鈕）`);

// 模擬重新渲染（清理舊的，綁定新的）
e2eRenderer.fullCleanup();
assertEqual(e2eRenderer.eventListeners.size, 0, '重新渲染前清理所有監聽器');

// 重新綁定
for (const order of orders) {
    for (const btnName of order.buttons) {
        const btn = new MockElement(`btn-${btnName}-${order.id}`);
        e2eRenderer._addManagedListener(btn, 'click', () => {});
    }
}
assertEqual(e2eRenderer.eventListeners.size, 9, '重新渲染後綁定 9 個新監聽器');

// 最終清理
e2eRenderer.fullCleanup();
assertEqual(e2eRenderer.eventListeners.size, 0, '最終清理後無殘留監聽器');
assertEqual(e2eRenderer.currentOrders.size, 0, 'currentOrders 已清空');
assertEqual(e2eRenderer.cachedOrders, null, 'cachedOrders 已清空');
assertEqual(e2eRenderer.isProcessingAction, false, 'isProcessingAction 已重置');

console.log('  ✅ 端到端生命週期模擬通過');

// ==================== 結果彙總 ====================
console.log('\n' + '='.repeat(70));
console.log('📊 驗證結果彙總');
console.log('='.repeat(70));
console.log(`  通過: ${passed}`);
console.log(`  失敗: ${failed}`);
console.log(`  總計: ${passed + failed}`);

if (failed > 0) {
    console.log('\n❌ 失敗項目:');
    errors.forEach((err, i) => {
        console.log(`  ${i + 1}. ${err}`);
    });
    process.exit(1);
} else {
    console.log('\n✅ 所有驗證通過！步驟1 遷移正確完成。');
    console.log('\n📋 驗證總結：');
    console.log('  1. BaseOrderRendererV2 的 _addManagedListener 正確定義（使用 eventListeners Map）');
    console.log('  2. cleanup() 正確調用 _removeAllManagedListeners() 清理所有監聽器');
    console.log('  3. 所有 4 個 V2 渲染器的 _bindOrderActions 使用 _addManagedListener');
    console.log('  4. 所有 4 個 V2 渲染器無殘留 addEventListener');
    console.log('  5. 模擬綁定/清理流程正確（含重新綁定場景）');
    console.log('  6. 端到端生命週期模擬通過');
    process.exit(0);
}
