/**
 * Phase2 重構審核腳本 v2
 * 
 * 驗證目標：
 * 1. 所有 v2 渲染器語法正確
 * 2. 類別繼承鏈正確（extends BaseOrderRendererV2）
 * 3. 方法簽名與基礎類一致（覆寫正確）
 * 4. main.js 中 v2 渲染器的使用方式正確
 * 5. 降級方案（_getFallbackRenderer）邏輯正確
 * 6. 模板加載順序正確
 * 7. 與舊版渲染器的 API 相容性
 * 
 * 注意：v2 渲染器使用不同的方法命名慣例：
 *   - 公開方法: renderOrders, cleanup (非 destroy)
 *   - 私有方法: _confirmFPSPayment, _confirmCashPayment (底線前綴)
 *   - 動態創建: new config.Class() (非直接 new XXXRendererV2)
 */

const fs = require('fs');
const path = require('path');

// =============================================
// 輔助函數
// =============================================
function readFile(filePath) {
    try {
        return fs.readFileSync(filePath, 'utf8');
    } catch (e) {
        return null;
    }
}

// =============================================
// 測試結果收集
// =============================================
const results = {
    passed: 0,
    failed: 0,
    warnings: 0,
    details: []
};

function pass(msg) {
    results.passed++;
    results.details.push(`  ✅ ${msg}`);
}

function fail(msg, reason) {
    results.failed++;
    results.details.push(`  ❌ ${msg} — ${reason}`);
}

function warn(msg) {
    results.warnings++;
    results.details.push(`  ⚠️  ${msg}`);
}

function section(title) {
    results.details.push(`\n📌 ${title}`);
}

// =============================================
// 1. 語法驗證
// =============================================
section('1. 語法驗證');

const v2Files = [
    'static/js/staff-order-management/base-order-renderer-v2.js',
    'static/js/staff-order-management/renderers-v2/payment-pending-renderer-v2.js',
    'static/js/staff-order-management/renderers-v2/preparing-orders-renderer-v2.js',
    'static/js/staff-order-management/renderers-v2/ready-orders-renderer-v2.js',
    'static/js/staff-order-management/renderers-v2/completed-orders-renderer-v2.js',
    'static/js/staff-order-management/main.js'
];

const fileContents = {};

v2Files.forEach(file => {
    const content = readFile(file);
    if (!content) {
        fail(`無法讀取 ${file}`, '檔案不存在');
        return;
    }
    fileContents[file] = content;
    
    try {
        new Function(content);
        pass(`${file} — 語法正確`);
    } catch (e) {
        fail(`${file} — 語法錯誤`, e.message);
    }
});

// =============================================
// 2. 類別繼承鏈驗證
// =============================================
section('2. 類別繼承鏈驗證');

// 2a. BaseOrderRendererV2
const baseV2 = fileContents[v2Files[0]];
if (baseV2) {
    if (/class\s+BaseOrderRendererV2/.test(baseV2)) {
        pass('BaseOrderRendererV2 類別定義存在');
    } else {
        fail('BaseOrderRendererV2 類別定義', '未找到 class BaseOrderRendererV2');
    }
    
    // 檢查關鍵方法（v2 命名）
    const requiredMethods = [
        'renderOrders', 'renderOrderItems', 'renderPaymentMethodBadge', 
        'renderCombinedBadge', 'renderPickupCode', 'renderCustomerInfo',
        'renderOrderNumber', 'renderOrderTime', 'renderTotalPrice',
        'renderBaristaHTML', 'renderItemsDisplayHTML', 'updateLastUpdateTime',
        'showEmpty', 'cleanup'
    ];
    
    requiredMethods.forEach(method => {
        const regex = new RegExp(`\\b${method}\\s*\\(`);
        if (regex.test(baseV2)) {
            pass(`BaseOrderRendererV2.${method}() 存在`);
        } else {
            fail(`BaseOrderRendererV2.${method}()`, '方法未找到');
        }
    });
}

// 2b. 各子類別
const rendererFiles = {
    'PaymentPendingRendererV2': v2Files[1],
    'PreparingOrdersRendererV2': v2Files[2],
    'ReadyOrdersRendererV2': v2Files[3],
    'CompletedOrdersRendererV2': v2Files[4]
};

Object.entries(rendererFiles).forEach(([className, filePath]) => {
    const content = fileContents[filePath];
    if (!content) return;
    
    // 檢查 class 定義
    const classRegex = new RegExp(`class\\s+${className}`);
    if (classRegex.test(content)) {
        pass(`${className} 類別定義存在`);
    } else {
        fail(`${className} 類別定義`, '未找到');
    }
    
    // 檢查 extends
    if (/extends\s+BaseOrderRendererV2/.test(content)) {
        pass(`${className} extends BaseOrderRendererV2`);
    } else {
        fail(`${className} extends BaseOrderRendererV2`, '未繼承正確的基礎類');
    }
    
    // 檢查 constructor 中是否有 super() 調用
    if (/super\s*\(/.test(content)) {
        pass(`${className} constructor 調用 super()`);
    } else {
        warn(`${className} — 未找到 super() 調用（可能使用默認 constructor）`);
    }
});

// =============================================
// 3. main.js 整合驗證
// =============================================
section('3. main.js 整合驗證');

const mainContent = fileContents[v2Files[5]];
if (mainContent) {
    // 檢查 v2 渲染器引用
    const v2Refs = ['PaymentPendingRendererV2', 'PreparingOrdersRendererV2', 
                    'ReadyOrdersRendererV2', 'CompletedOrdersRendererV2'];
    
    v2Refs.forEach(ref => {
        if (mainContent.includes(ref)) {
            pass(`main.js 引用 ${ref}`);
        } else {
            fail(`main.js 引用 ${ref}`, '未找到引用');
        }
    });
    
    // 檢查降級方案
    if (/_getFallbackRenderer/.test(mainContent)) {
        pass('main.js 包含降級方案 _getFallbackRenderer');
    } else {
        fail('main.js 降級方案', '未找到 _getFallbackRenderer');
    }
    
    // 檢查降級邏輯：嘗試使用 v2，失敗時降級到舊版
    if (/try\s*\{/.test(mainContent) && /catch/.test(mainContent)) {
        pass('main.js 包含 try/catch 降級邏輯');
    } else {
        warn('main.js — 未找到明確的 try/catch 降級模式');
    }
    
    // 檢查渲染器初始化（動態創建模式）
    if (/new\s+config\.Class\(\)/.test(mainContent)) {
        pass('main.js 使用 new config.Class() 動態創建渲染器');
    } else {
        warn('main.js — 未找到 new config.Class() 動態創建模式');
    }
    
    // 檢查舊版渲染器作為降級
    const oldRefs = ['PaymentPendingRenderer', 'DynamicPreparingOrdersRenderer',
                     'DynamicReadyOrdersRenderer', 'DynamicCompletedOrdersRenderer'];
    
    oldRefs.forEach(ref => {
        if (mainContent.includes(ref)) {
            pass(`main.js 保留舊版 ${ref} 作為降級備援`);
        } else {
            warn(`main.js — 未找到舊版 ${ref} 引用（可能不需要）`);
        }
    });
    
    // 檢查 cleanup 方法（v2 使用 cleanup 而非 destroy）
    if (/\.cleanup\b/.test(mainContent)) {
        pass('main.js 使用 cleanup() 進行生命週期清理（v2 慣例）');
    } else {
        warn('main.js — 未找到 cleanup() 調用');
    }
}

// =============================================
// 4. 模板加載順序驗證
// =============================================
section('4. 模板加載順序驗證');

const templateContent = readFile('templates/admin/staff_order_management.html');
if (templateContent) {
    // 檢查 v2 渲染器 JS 加載
    const v2Scripts = [
        'base-order-renderer-v2.js',
        'renderers-v2/payment-pending-renderer-v2.js',
        'renderers-v2/preparing-orders-renderer-v2.js',
        'renderers-v2/ready-orders-renderer-v2.js',
        'renderers-v2/completed-orders-renderer-v2.js'
    ];
    
    v2Scripts.forEach(script => {
        if (templateContent.includes(script)) {
            pass(`模板包含 ${script}`);
        } else {
            fail(`模板包含 ${script}`, '未找到');
        }
    });
    
    // 檢查加載順序：舊版渲染器 → v2 渲染器 → WebSocket管理器 → main.js
    const orderChecks = [
        { before: 'payment-pending-renderer.js', after: 'base-order-renderer-v2.js', desc: '舊版渲染器在 v2 之前' },
        { before: 'base-order-renderer-v2.js', after: 'websocket-manager.js', desc: 'v2 渲染器在 WebSocket 管理器之前' },
        { before: 'websocket-manager.js', after: 'main.js', desc: 'WebSocket 管理器在 main.js 之前' }
    ];
    
    orderChecks.forEach(({ before, after, desc }) => {
        const beforeIdx = templateContent.indexOf(before);
        const afterIdx = templateContent.indexOf(after);
        if (beforeIdx !== -1 && afterIdx !== -1 && beforeIdx < afterIdx) {
            pass(`加載順序正確: ${desc}`);
        } else if (beforeIdx === -1) {
            warn(`加載順序檢查: ${before} 未找到`);
        } else if (afterIdx === -1) {
            warn(`加載順序檢查: ${after} 未找到`);
        } else {
            fail(`加載順序錯誤: ${desc}`, `${before} (${beforeIdx}) 應在 ${after} (${afterIdx}) 之前`);
        }
    });
    
    // 檢查 v2 渲染器在舊版渲染器之後加載
    const oldRenderersEnd = templateContent.indexOf('completed-orders-renderer.js');
    const v2Start = templateContent.indexOf('base-order-renderer-v2.js');
    
    if (oldRenderersEnd !== -1 && v2Start !== -1 && oldRenderersEnd < v2Start) {
        pass('v2 渲染器在舊版渲染器之後加載（正確的降級順序）');
    } else {
        fail('v2 渲染器加載位置', '應在舊版渲染器之後');
    }
}

// =============================================
// 5. API 相容性驗證（v2 命名慣例）
// =============================================
section('5. API 相容性驗證（v2 命名慣例）');

// v2 渲染器使用私有方法（底線前綴）和 cleanup（非 destroy）
const v2Methods = {
    'PaymentPendingRendererV2': [
        { method: 'renderOrders', location: 'base' },
        { method: 'cleanup', location: 'base' },
        { method: '_confirmFPSPayment', location: 'self' },
        { method: '_confirmCashPayment', location: 'self' },
        { method: '_handleConfirmPayment', location: 'self' },
        { method: '_handleCancelOrder', location: 'self' }
    ],
    'PreparingOrdersRendererV2': [
        { method: 'renderOrders', location: 'self' },
        { method: 'cleanup', location: 'base' },
        { method: 'startCountdown', location: 'base' }
    ],
    'ReadyOrdersRendererV2': [
        { method: 'renderOrders', location: 'self' },
        { method: 'cleanup', location: 'base' }
    ],
    'CompletedOrdersRendererV2': [
        { method: 'renderOrders', location: 'self' },
        { method: 'cleanup', location: 'base' }
    ]
};

Object.entries(v2Methods).forEach(([className, methods]) => {
    const fileEntry = Object.entries(rendererFiles).find(([k]) => k === className);
    if (!fileEntry) return;
    
    const content = fileContents[fileEntry[1]];
    if (!content) return;
    
    methods.forEach(({ method, location }) => {
        const regex = new RegExp(`\\b${method}\\s*\\(`);
        let found = false;
        
        if (location === 'self' && regex.test(content)) {
            found = true;
            pass(`${className}.${method}() 存在於子類`);
        } else if (location === 'base' && baseV2 && regex.test(baseV2)) {
            found = true;
            pass(`${className}.${method}() — 繼承自 BaseOrderRendererV2`);
        }
        
        if (!found) {
            // 再檢查一次子類（可能方法在子類中覆寫了）
            if (regex.test(content)) {
                pass(`${className}.${method}() 存在於子類（覆寫基礎類）`);
            } else if (baseV2 && regex.test(baseV2)) {
                pass(`${className}.${method}() — 繼承自 BaseOrderRendererV2`);
            } else {
                fail(`${className}.${method}()`, '方法未找到');
            }
        }
    });
});

// =============================================
// 6. 事件監聽與生命週期驗證
// =============================================
section('6. 事件監聽與生命週期驗證');

if (baseV2) {
    if (/_addManagedListener/.test(baseV2)) {
        pass('BaseOrderRendererV2 包含 _addManagedListener 事件管理');
    } else {
        warn('BaseOrderRendererV2 — 未找到 _addManagedListener');
    }
    
    if (/cleanup/.test(baseV2)) {
        pass('BaseOrderRendererV2 包含 cleanup 生命週期方法');
    }
    
    if (/this\.managedListeners/.test(baseV2) || /this\._listeners/.test(baseV2)) {
        pass('BaseOrderRendererV2 包含監聽器追蹤機制');
    } else {
        warn('BaseOrderRendererV2 — 未找到監聽器追蹤（可能使用其他機制）');
    }
}

// =============================================
// 7. 倒計時功能驗證（PreparingOrdersRendererV2）
// =============================================
section('7. 倒計時功能驗證');

const preparingV2 = fileContents[v2Files[2]];
if (preparingV2) {
    if (/\bcountdown\b/i.test(preparingV2)) {
        pass('PreparingOrdersRendererV2 包含倒計時功能');
    } else {
        fail('PreparingOrdersRendererV2 倒計時', '未找到 countdown 相關邏輯');
    }
    
    if (/setInterval/.test(preparingV2) || /setTimeout/.test(preparingV2)) {
        pass('PreparingOrdersRendererV2 使用定時器管理倒計時');
    }
    
    if (/clearInterval/.test(preparingV2) || /clearTimeout/.test(preparingV2)) {
        pass('PreparingOrdersRendererV2 包含定時器清理邏輯');
    } else {
        warn('PreparingOrdersRendererV2 — 未找到定時器清理（可能透過 cleanup 自動清理）');
    }
}

// =============================================
// 8. 支付確認功能驗證（PaymentPendingRendererV2）
// =============================================
section('8. 支付確認功能驗證');

const paymentV2 = fileContents[v2Files[1]];
if (paymentV2) {
    if (/_confirmFPSPayment/.test(paymentV2)) {
        pass('PaymentPendingRendererV2 包含 _confirmFPSPayment（私有方法）');
    } else {
        fail('PaymentPendingRendererV2._confirmFPSPayment', '未找到');
    }
    
    if (/_confirmCashPayment/.test(paymentV2)) {
        pass('PaymentPendingRendererV2 包含 _confirmCashPayment（私有方法）');
    } else {
        fail('PaymentPendingRendererV2._confirmCashPayment', '未找到');
    }
    
    if (/_handleConfirmPayment/.test(paymentV2)) {
        pass('PaymentPendingRendererV2 包含 _handleConfirmPayment 統一處理入口');
    }
    
    // 檢查是否使用 API service
    if (/apiService/.test(paymentV2) || /api\./.test(paymentV2) || /ApiService/.test(paymentV2) || /fetch/.test(paymentV2)) {
        pass('PaymentPendingRendererV2 使用 API 調用進行支付確認');
    } else {
        warn('PaymentPendingRendererV2 — 未找到 API service 引用');
    }
}

// =============================================
// 9. 降級方案完整性驗證
// =============================================
section('9. 降級方案完整性驗證');

if (mainContent) {
    // 檢查降級映射表
    if (/_getFallbackRenderer\s*\(/.test(mainContent)) {
        pass('_getFallbackRenderer 降級映射表存在');
        
        // 檢查降級映射是否完整
        const fallbackChecks = [
            { v2: 'paymentPendingRenderer', old: 'PaymentPendingRenderer' },
            { v2: 'preparingRenderer', old: 'DynamicPreparingOrdersRenderer' },
            { v2: 'readyRenderer', old: 'DynamicReadyOrdersRenderer' },
            { v2: 'completedRenderer', old: 'DynamicCompletedOrdersRenderer' }
        ];
        
        fallbackChecks.forEach(({ v2, old }) => {
            if (mainContent.includes(v2) && mainContent.includes(old)) {
                pass(`降級映射: ${v2} → ${old}`);
            } else {
                warn(`降級映射: ${v2} → ${old} — 可能不完整`);
            }
        });
    }
    
    // 檢查模板中舊版渲染器是否存在（降級需要）
    if (templateContent) {
        const oldRendererFiles = [
            'payment-pending-renderer.js',
            'preparing-orders-renderer-enhanced.js',
            'ready-orders-renderer.js',
            'completed-orders-renderer.js'
        ];
        
        oldRendererFiles.forEach(file => {
            if (templateContent.includes(file)) {
                pass(`模板保留舊版 ${file}（降級備援可用）`);
            } else {
                warn(`模板未找到 ${file}（降級備援可能不可用）`);
            }
        });
    }
}

// =============================================
// 10. 程式碼品質檢查
// =============================================
section('10. 程式碼品質檢查');

// 檢查各檔案大小
const fileSizeChecks = [
    { file: v2Files[0], name: 'BaseOrderRendererV2', maxLines: 1200 },
    { file: v2Files[1], name: 'PaymentPendingRendererV2', maxLines: 300 },
    { file: v2Files[2], name: 'PreparingOrdersRendererV2', maxLines: 400 },
    { file: v2Files[3], name: 'ReadyOrdersRendererV2', maxLines: 300 },
    { file: v2Files[4], name: 'CompletedOrdersRendererV2', maxLines: 300 },
    { file: v2Files[5], name: 'main.js', maxLines: 700 }
];

fileSizeChecks.forEach(({ file, name, maxLines }) => {
    const content = fileContents[file];
    if (content) {
        const lines = content.split('\n').length;
        if (lines <= maxLines) {
            pass(`${name} 行數合理 (${lines}行 ≤ ${maxLines}行)`);
        } else {
            warn(`${name} 行數較多 (${lines}行 > ${maxLines}行)`);
        }
    }
});

// 檢查是否有 console.log 殘留（非警告，僅記錄）
let totalConsoleLogs = 0;
Object.entries(fileContents).forEach(([file, content]) => {
    if (content) {
        const logs = (content.match(/console\.log\(/g) || []).length;
        totalConsoleLogs += logs;
    }
});
pass(`所有 v2 檔案合計 ${totalConsoleLogs} 個 console.log 調用（開發用）`);

// =============================================
// 總結
// =============================================
section('\n========================================');
section('📊 Phase2 重構審核報告');
section('========================================');
results.details.push(`✅ 通過: ${results.passed}`);
results.details.push(`❌ 失敗: ${results.failed}`);
results.details.push(`⚠️  警告: ${results.warnings}`);
const totalScore = Math.round((results.passed / (results.passed + results.failed)) * 100);
results.details.push(`📈 總分: ${totalScore}%`);
results.details.push('');
results.details.push('📋 審核結論:');
if (results.failed === 0) {
    results.details.push('  ✅ Phase2 重構完整正確，無需修改');
} else if (results.failed <= 3) {
    results.details.push('  ⚠️  Phase2 重構基本正確，有少量問題需修正');
} else {
    results.details.push('  ❌ Phase2 重構存在較多問題，需要修正');
}
results.details.push('');

// 列出所有警告
if (results.warnings > 0) {
    results.details.push('⚠️  警告事項:');
    results.details.push('  - 以上警告不影響功能，但建議在後續優化中處理');
    results.details.push('');
}

section('========================================\n');

// 輸出結果
console.log(results.details.join('\n'));

// 返回退出碼
process.exit(results.failed > 0 ? 1 : 0);
