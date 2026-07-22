// static/js/staff-order-management/benchmark-renderer.js
// ==================== Phase 3A 效能基準測試 ====================
// 用於量化渲染器優化效果
//
// 使用方式（在 Chrome DevTools Console 中）：
//   1. 打開員工端頁面
//   2. 執行: benchmarkRenderer.run()
//   3. 查看結果
//
// 或者使用 Performance 面板：
//   1. 開始 Performance 錄製
//   2. 切換到「準備中」標籤頁
//   3. 停止錄製
//   4. 檢查 FPS、Scripting、Rendering 時間

class RendererBenchmark {
    constructor() {
        this.results = {};
    }

    /**
     * 執行完整基準測試
     */
    async run() {
        console.log('%c📊 Phase 3A 效能基準測試', 'font-size: 18px; font-weight: bold;');
        console.log('%c測試時間: ' + new Date().toLocaleString('zh-HK'), 'color: #888;');
        console.log('');

        // 測試 1：渲染時間
        await this.benchmarkRenderTime();

        // 測試 2：倒數計時效能
        this.benchmarkCountdownTimers();

        // 測試 3：DOM 操作次數
        this.benchmarkDOMOperations();

        // 輸出摘要
        this.printSummary();
    }

    /**
     * 測試 1：測量各標籤頁的渲染時間
     */
    async benchmarkRenderTime(iterations = 5) {
        console.log('%c📋 測試 1：渲染時間', 'font-size: 14px; font-weight: bold;');

        const tabs = [
            { name: '待支付', key: 'payment_pending_orders' },
            { name: '準備中', key: 'preparing_orders' },
            { name: '已就緒', key: 'ready_orders' },
            { name: '已完成', key: 'completed_orders' }
        ];

        for (const tab of tabs) {
            const times = [];

            for (let i = 0; i < iterations; i++) {
                const start = performance.now();

                // 觸發統一數據管理器加載
                if (window.unifiedDataManager) {
                    await window.unifiedDataManager.loadUnifiedData(true);
                }

                // 獲取渲染器實例
                const renderer = this._findRenderer(tab.key);
                if (renderer && window.unifiedDataManager?.currentData?.[tab.key]) {
                    renderer.renderOrders(window.unifiedDataManager.currentData[tab.key]);
                }

                const end = performance.now();
                times.push(end - start);

                // 等待一下避免快取影響
                await new Promise(r => setTimeout(r, 200));
            }

            const avg = times.reduce((a, b) => a + b, 0) / times.length;
            const min = Math.min(...times);
            const max = Math.max(...times);

            this.results[`render_${tab.key}`] = { avg, min, max, times };
            console.log(`  ${tab.name}: 平均 ${avg.toFixed(2)}ms | 範圍 [${min.toFixed(2)} - ${max.toFixed(2)}]ms`);
        }
    }

    /**
     * 測試 2：檢查倒數計時 timer 數量
     */
    benchmarkCountdownTimers() {
        console.log('%c📋 測試 2：倒數計時 Timer 分析', 'font-size: 14px; font-weight: bold;');

        // 方法 1：透過 countdownTimers Map 大小
        let totalTimers = 0;
        const renderers = this._findAllRenderers();
        for (const renderer of renderers) {
            if (renderer.countdownTimers) {
                totalTimers += renderer.countdownTimers.size;
            }
        }
        console.log(`  渲染器 countdownTimers Map 總數: ${totalTimers}`);

        // 方法 2：透過 DOM 中的倒數計時 badge 數量
        const countdownBadges = document.querySelectorAll('.countdown-badge');
        console.log(`  DOM 中 .countdown-badge 元素數量: ${countdownBadges.length}`);

        // 方法 3：檢查 active 的倒數計時
        const activeBadges = document.querySelectorAll('.countdown-badge:not(.badge-success)');
        console.log(`  活躍倒數計時數量: ${activeBadges.length}`);

        this.results.countdown = {
            mapTimers: totalTimers,
            domBadges: countdownBadges.length,
            activeBadges: activeBadges.length
        };
    }

    /**
     * 測試 3：估算每次渲染的 DOM 操作次數
     */
    benchmarkDOMOperations() {
        console.log('%c📋 測試 3：DOM 操作估算', 'font-size: 14px; font-weight: bold;');

        const tabs = [
            { name: '待支付', listId: 'payment-pending-orders-list' },
            { name: '準備中', listId: 'preparing-orders-list' },
            { name: '已就緒', listId: 'ready-orders-list' },
            { name: '已完成', listId: 'completed-orders-list' }
        ];

        for (const tab of tabs) {
            const list = document.getElementById(tab.listId);
            if (list) {
                const childCount = list.children.length;
                console.log(`  ${tab.name}: ${childCount} 個訂單卡片`);
                this.results[`dom_${tab.listId}`] = childCount;
            } else {
                console.log(`  ${tab.name}: 列表容器未找到`);
            }
        }
    }

    /**
     * 輸出摘要
     */
    printSummary() {
        console.log('');
        console.log('%c📊 基準測試摘要', 'font-size: 16px; font-weight: bold;');
        console.log('========================================');

        let totalRenderTime = 0;
        let tabCount = 0;
        for (const [key, value] of Object.entries(this.results)) {
            if (key.startsWith('render_')) {
                totalRenderTime += value.avg;
                tabCount++;
            }
        }

        if (tabCount > 0) {
            console.log(`  平均渲染時間（所有標籤頁）: ${(totalRenderTime / tabCount).toFixed(2)}ms`);
        }

        if (this.results.countdown) {
            console.log(`  活躍倒數計時: ${this.results.countdown.activeBadges} 個`);
            console.log(`  countdownTimers Map: ${this.results.countdown.mapTimers} 個`);
        }

        console.log('');
        console.log('%c💡 優化後重新執行此測試以對比效果', 'color: #888;');
        console.log('========================================');

        // 將結果存到 window 供後續對比
        window.__benchmarkResults = this.results;
        console.log('✅ 結果已保存到 window.__benchmarkResults');
    }

    /**
     * 與優化後的結果對比
     * @param {Object} optimizedResults - 優化後的結果
     */
    static compare(before, after) {
        console.log('%c📊 優化前後對比', 'font-size: 16px; font-weight: bold;');
        console.log('========================================');

        for (const [key, beforeVal] of Object.entries(before)) {
            if (key.startsWith('render_') && after[key]) {
                const afterVal = after[key];
                const improvement = ((beforeVal.avg - afterVal.avg) / beforeVal.avg * 100).toFixed(1);
                console.log(`  ${key}: ${beforeVal.avg.toFixed(2)}ms → ${afterVal.avg.toFixed(2)}ms (${improvement}%)`);
            }
        }

        if (before.countdown && after.countdown) {
            const timerReduction = before.countdown.mapTimers - after.countdown.mapTimers;
            console.log(`  Timer 減少: ${before.countdown.mapTimers} → ${after.countdown.mapTimers} (減少 ${timerReduction} 個)`);
        }
    }

    // ==================== 輔助方法 ====================

    _findRenderer(dataKey) {
        // 嘗試從 window 對象查找渲染器實例
        const rendererMap = {
            'payment_pending_orders': 'paymentPendingRendererV2',
            'preparing_orders': 'preparingOrdersRendererV2',
            'ready_orders': 'readyOrdersRendererV2',
            'completed_orders': 'completedOrdersRendererV2'
        };

        const varName = rendererMap[dataKey];
        return varName ? window[varName] : null;
    }

    _findAllRenderers() {
        const names = [
            'paymentPendingRendererV2',
            'preparingOrdersRendererV2',
            'readyOrdersRendererV2',
            'completedOrdersRendererV2'
        ];

        return names
            .map(name => window[name])
            .filter(r => r != null);
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.benchmarkRenderer = new RendererBenchmark();
    console.log('🌍 RendererBenchmark 已註冊，執行 benchmarkRenderer.run() 開始測試');
}
