// test_common_utils_unit.js
// CommonUtils 單元測試

const fs = require('fs');
const path = require('path');

// 模擬瀏覽器環境
global.window = {
    CommonUtils: null,
    toast: null,
    orderManager: null,
    TimeUtils: null,
    unifiedDataManager: null
};

global.document = {
    createElement: (tag) => ({ 
        className: '', 
        style: {}, 
        setAttribute: () => {}, 
        appendChild: () => {},
        querySelector: () => null,
        querySelectorAll: () => []
    }),
    createTextNode: (text) => ({ textContent: text }),
    body: {
        appendChild: () => {}
    },
    createDocumentFragment: () => ({
        appendChild: () => {},
        querySelector: () => null,
        querySelectorAll: () => []
    })
};

global.setTimeout = (fn, delay) => ({});
global.clearTimeout = () => {};

// 加載 CommonUtils
const commonUtilsPath = path.join(__dirname, 'static/js/staff-order-management/common-utils.js');
const commonUtilsContent = fs.readFileSync(commonUtilsPath, 'utf8');

// 執行 CommonUtils 代碼
eval(commonUtilsContent);

// 測試套件
class CommonUtilsTestSuite {
    constructor() {
        this.tests = [];
        this.passed = 0;
        this.failed = 0;
    }
    
    addTest(name, testFn) {
        this.tests.push({ name, testFn });
    }
    
    run() {
        console.log('🧪 開始 CommonUtils 單元測試\n');
        
        this.tests.forEach((test, index) => {
            try {
                test.testFn();
                console.log(`✅ [${index + 1}/${this.tests.length}] ${test.name}`);
                this.passed++;
            } catch (error) {
                console.log(`❌ [${index + 1}/${this.tests.length}] ${test.name}`);
                console.log(`   錯誤: ${error.message}`);
                this.failed++;
            }
        });
        
        console.log('\n📊 測試結果:');
        console.log(`   總測試數: ${this.tests.length}`);
        console.log(`   通過: ${this.passed}`);
        console.log(`   失敗: ${this.failed}`);
        console.log(`   通過率: ${((this.passed / this.tests.length) * 100).toFixed(1)}%`);
        
        return this.failed === 0;
    }
}

// 創建測試套件
const testSuite = new CommonUtilsTestSuite();

// ==================== 測試用例 ====================

// 測試 1: CommonUtils 類存在性
testSuite.addTest('CommonUtils 類存在', () => {
    if (!window.CommonUtils) {
        throw new Error('CommonUtils 未定義');
    }
    if (typeof window.CommonUtils !== 'function') {
        throw new Error('CommonUtils 不是函數');
    }
});

// 測試 2: 靜態方法存在性
testSuite.addTest('靜態方法存在', () => {
    const requiredMethods = [
        'showToast',
        'analyzeOrderType',
        'generateOrderTypeBadges',
        'generateQuantityBadges',
        'renderOrderItems',
        'formatHKTime',
        'formatHKTimeOnly',
        'debounce',
        'throttle',
        'createElement',
        'safeSetInnerHTML'
    ];
    
    requiredMethods.forEach(method => {
        if (typeof window.CommonUtils[method] !== 'function') {
            throw new Error(`方法 ${method} 不存在或不是函數`);
        }
    });
});

// 測試 3: 訂單類型分析
testSuite.addTest('訂單類型分析功能', () => {
    const testCases = [
        {
            order: { coffee_count: 2, bean_count: 0 },
            expected: { coffeeCount: 2, beanCount: 0, hasCoffee: true, hasBeans: false, isMixedOrder: false, isBeansOnly: false }
        },
        {
            order: { coffee_count: 0, bean_count: 1 },
            expected: { coffeeCount: 0, beanCount: 1, hasCoffee: false, hasBeans: true, isMixedOrder: false, isBeansOnly: true }
        },
        {
            order: { coffee_count: 1, bean_count: 1 },
            expected: { coffeeCount: 1, beanCount: 1, hasCoffee: true, hasBeans: true, isMixedOrder: true, isBeansOnly: false }
        },
        {
            order: { coffee_count: 0, bean_count: 0 },
            expected: { coffeeCount: 0, beanCount: 0, hasCoffee: false, hasBeans: false, isMixedOrder: false, isBeansOnly: false }
        }
    ];
    
    testCases.forEach((testCase, index) => {
        const result = window.CommonUtils.analyzeOrderType(testCase.order);
        
        Object.keys(testCase.expected).forEach(key => {
            if (result[key] !== testCase.expected[key]) {
                throw new Error(`測試用例 ${index + 1} 失敗: ${key} 期望 ${testCase.expected[key]}，實際 ${result[key]}`);
            }
        });
    });
});

// 測試 4: 徽章生成
testSuite.addTest('徽章生成功能', () => {
    const testCases = [
        {
            order: { is_quick_order: true },
            typeInfo: { isMixedOrder: false, isBeansOnly: false },
            expectedContains: 'badge-quickorder'
        },
        {
            order: { is_quick_order: false },
            typeInfo: { isMixedOrder: true, isBeansOnly: false },
            expectedContains: 'badge-primary'
        },
        {
            order: { is_quick_order: false },
            typeInfo: { isMixedOrder: false, isBeansOnly: false },
            expectedContains: 'badge-info'
        }
    ];
    
    testCases.forEach((testCase, index) => {
        const result = window.CommonUtils.generateOrderTypeBadges(testCase.order, testCase.typeInfo);
        
        if (!result.includes(testCase.expectedContains)) {
            throw new Error(`測試用例 ${index + 1} 失敗: 期望包含 ${testCase.expectedContains}，實際 ${result}`);
        }
    });
});

// 測試 5: 數量徽章生成
testSuite.addTest('數量徽章生成功能', () => {
    const testCases = [
        {
            typeInfo: { coffeeCount: 2, beanCount: 0 },
            expectedCoffee: '2杯',
            expectedBean: ''
        },
        {
            typeInfo: { coffeeCount: 0, beanCount: 1 },
            expectedCoffee: '',
            expectedBean: '1包咖啡豆'
        },
        {
            typeInfo: { coffeeCount: 1, beanCount: 2 },
            expectedCoffee: '1杯',
            expectedBean: '2包咖啡豆'
        }
    ];
    
    testCases.forEach((testCase, index) => {
        const result = window.CommonUtils.generateQuantityBadges(testCase.typeInfo);
        
        if (testCase.expectedCoffee && !result.includes(testCase.expectedCoffee)) {
            throw new Error(`測試用例 ${index + 1} 失敗: 期望包含 ${testCase.expectedCoffee}，實際 ${result}`);
        }
        
        if (testCase.expectedBean && !result.includes(testCase.expectedBean)) {
            throw new Error(`測試用例 ${index + 1} 失敗: 期望包含 ${testCase.expectedBean}，實際 ${result}`);
        }
    });
});

// 測試 6: 時間格式化
testSuite.addTest('時間格式化功能', () => {
    const testDate = new Date('2026-02-24T14:30:00+08:00');
    const isoString = testDate.toISOString();
    
    const formattedTime = window.CommonUtils.formatHKTime(isoString);
    const formattedTimeOnly = window.CommonUtils.formatHKTimeOnly(isoString);
    
    if (!formattedTime || formattedTime === '--:--') {
        throw new Error('formatHKTime 返回無效值');
    }
    
    if (!formattedTimeOnly || formattedTimeOnly === '--:--') {
        throw new Error('formatHKTimeOnly 返回無效值');
    }
    
    // 檢查是否包含時間部分
    if (!formattedTime.includes('14') || !formattedTime.includes('30')) {
        throw new Error('formatHKTime 格式不正確');
    }
    
    if (!formattedTimeOnly.includes('14') || !formattedTimeOnly.includes('30')) {
        throw new Error('formatHKTimeOnly 格式不正確');
    }
});

// 測試 7: 防抖函數
testSuite.addTest('防抖函數功能', () => {
    let callCount = 0;
    const increment = () => callCount++;
    
    const debouncedIncrement = window.CommonUtils.debounce(increment, 100);
    
    // 快速調用多次
    debouncedIncrement();
    debouncedIncrement();
    debouncedIncrement();
    
    if (callCount !== 0) {
        throw new Error('防抖函數不應立即執行');
    }
    
    // 注意：在 Node.js 環境中無法測試延遲執行
    console.log('   注意：防抖函數的延遲執行需要在瀏覽器環境中測試');
});

// 測試 8: 節流函數
testSuite.addTest('節流函數功能', () => {
    let callCount = 0;
    const increment = () => callCount++;
    
    const throttledIncrement = window.CommonUtils.throttle(increment, 100);
    
    // 快速調用多次
    throttledIncrement();
    throttledIncrement();
    throttledIncrement();
    
    if (callCount !== 1) {
        throw new Error('節流函數應只執行一次');
    }
});

// 測試 9: DOM 元素創建
testSuite.addTest('DOM 元素創建功能', () => {
    const element = window.CommonUtils.createElement('div', {
        className: 'test-class',
        id: 'test-id',
        textContent: '測試內容'
    });
    
    if (!element) {
        throw new Error('createElement 返回 null');
    }
    
    // 檢查屬性
    if (element.className !== 'test-class') {
        throw new Error(`className 不匹配: 期望 'test-class'，實際 '${element.className}'`);
    }
});

// 測試 10: 安全 HTML 設置
testSuite.addTest('安全 HTML 設置功能', () => {
    const element = { innerHTML: '' };
    
    // 測試安全 HTML
    window.CommonUtils.safeSetInnerHTML(element, '<span>安全內容</span>');
    
    if (!element.innerHTML.includes('<span>安全內容</span>')) {
        throw new Error('安全 HTML 設置失敗');
    }
    
    // 測試 XSS 防護
    const maliciousHTML = '<script>alert("xss")</script><span>內容</span>';
    window.CommonUtils.safeSetInnerHTML(element, maliciousHTML);
    
    if (element.innerHTML.includes('<script>')) {
        throw new Error('XSS 防護失敗，script 標籤未被過濾');
    }
});

// 測試 11: 訂單項目渲染
testSuite.addTest('訂單項目渲染功能', () => {
    const testItems = [
        {
            name: '測試咖啡',
            price: '35.00',
            total_price: '35.00',
            quantity: 1,
            cup_level_cn: '大杯',
            milk_level_cn: '無',
            type: 'coffee'
        }
    ];
    
    const result = window.CommonUtils.renderOrderItems(testItems);
    
    if (!result) {
        throw new Error('renderOrderItems 返回空值');
    }
    
    if (!result.includes('測試咖啡')) {
        throw new Error('商品名稱未正確渲染');
    }
    
    if (!result.includes('$35.00')) {
        throw new Error('價格未正確渲染');
    }
    
    if (!result.includes('大杯')) {
        throw new Error('杯型未正確渲染');
    }
});

// 測試 12: 默認圖片獲取
testSuite.addTest('默認圖片獲取功能', () => {
    const coffeeImage = window.CommonUtils.getDefaultImage('coffee');
    const beanImage = window.CommonUtils.getDefaultImage('bean');
    const defaultImage = window.CommonUtils.getDefaultImage('unknown');
    
    if (!coffeeImage.includes('default-coffee')) {
        throw new Error('咖啡默認圖片路徑不正確');
    }
    
    if (!beanImage.includes('default-beans')) {
        throw new Error('咖啡豆默認圖片路徑不正確');
    }
    
    if (!defaultImage.includes('default-product')) {
        throw new Error('默認產品圖片路徑不正確');
    }
});

// 運行測試
console.log('🚀 開始執行 CommonUtils 單元測試...\n');
const success = testSuite.run();

if (success) {
    console.log('\n🎉 所有測試通過！CommonUtils 功能正常。');
    process.exit(0);
} else {
    console.log('\n⚠️  部分測試失敗，請檢查 CommonUtils 實現。');
    process.exit(1);
}