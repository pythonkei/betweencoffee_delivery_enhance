// static/js/staff-order-management/performance-monitor.js
// ==================== 性能監控工具 ====================
// 監控 JavaScript 性能，收集性能指標

class PerformanceMonitor {
    constructor() {
        this.metrics = {
            renderTime: [],
            apiResponseTime: [],
            domUpdateTime: [],
            memoryUsage: [],
            eventHandlingTime: []
        };
        
        this.thresholds = {
            renderTime: 100, // 毫秒
            apiResponseTime: 500, // 毫秒
            domUpdateTime: 50, // 毫秒
            memoryUsage: 50, // MB
            eventHandlingTime: 100 // 毫秒
        };
        
        this.warnings = [];
        this.isEnabled = true;
        this.samplingRate = 0.1; // 10% 採樣率
        
        console.log('📊 性能監控器初始化完成');
    }
    
    /**
     * 開始性能監控
     */
    enable() {
        this.isEnabled = true;
        console.log('📊 性能監控已啟用');
    }
    
    /**
     * 停止性能監控
     */
    disable() {
        this.isEnabled = false;
        console.log('📊 性能監控已禁用');
    }
    
    /**
     * 設置採樣率
     * @param {number} rate - 採樣率 (0-1)
     */
    setSamplingRate(rate) {
        if (rate >= 0 && rate <= 1) {
            this.samplingRate = rate;
            console.log(`📊 採樣率設置為: ${rate * 100}%`);
        }
    }
    
    /**
     * 檢查是否應該採樣
     * @returns {boolean} 是否應該採樣
     */
    shouldSample() {
        return this.isEnabled && Math.random() < this.samplingRate;
    }
    
    /**
     * 測量渲染時間
     * @param {string} componentName - 組件名稱
     * @param {Function} renderFunction - 渲染函數
     * @returns {*} 渲染結果
     */
    measureRenderTime(componentName, renderFunction) {
        if (!this.shouldSample()) {
            return renderFunction();
        }
        
        const startTime = performance.now();
        const result = renderFunction();
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.metrics.renderTime.push({
            component: componentName,
            duration: duration,
            timestamp: new Date().toISOString()
        });
        
        // 檢查閾值
        if (duration > this.thresholds.renderTime) {
            this.addWarning('renderTime', `${componentName} 渲染時間過長: ${duration.toFixed(2)}ms`);
        }
        
        return result;
    }
    
    /**
     * 測量 API 響應時間
     * @param {string} apiName - API 名稱
     * @param {Promise} apiPromise - API Promise
     * @returns {Promise} API 結果
     */
    async measureApiResponseTime(apiName, apiPromise) {
        if (!this.shouldSample()) {
            return apiPromise;
        }
        
        const startTime = performance.now();
        
        try {
            const result = await apiPromise;
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            this.metrics.apiResponseTime.push({
                api: apiName,
                duration: duration,
                timestamp: new Date().toISOString(),
                success: true
            });
            
            // 檢查閾值
            if (duration > this.thresholds.apiResponseTime) {
                this.addWarning('apiResponseTime', `${apiName} 響應時間過長: ${duration.toFixed(2)}ms`);
            }
            
            return result;
        } catch (error) {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            this.metrics.apiResponseTime.push({
                api: apiName,
                duration: duration,
                timestamp: new Date().toISOString(),
                success: false,
                error: error.message
            });
            
            throw error;
        }
    }
    
    /**
     * 測量 DOM 更新時間
     * @param {string} operationName - 操作名稱
     * @param {Function} domOperation - DOM 操作函數
     * @returns {*} 操作結果
     */
    measureDomUpdateTime(operationName, domOperation) {
        if (!this.shouldSample()) {
            return domOperation();
        }
        
        const startTime = performance.now();
        const result = domOperation();
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        this.metrics.domUpdateTime.push({
            operation: operationName,
            duration: duration,
            timestamp: new Date().toISOString()
        });
        
        // 檢查閾值
        if (duration > this.thresholds.domUpdateTime) {
            this.addWarning('domUpdateTime', `${operationName} DOM 更新時間過長: ${duration.toFixed(2)}ms`);
        }
        
        return result;
    }
    
    /**
     * 測量事件處理時間
     * @param {string} eventName - 事件名稱
     * @param {Function} eventHandler - 事件處理函數
     * @returns {Function} 包裝後的事件處理函數
     */
    wrapEventHandler(eventName, eventHandler) {
        return (...args) => {
            if (!this.shouldSample()) {
                return eventHandler(...args);
            }
            
            const startTime = performance.now();
            const result = eventHandler(...args);
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            this.metrics.eventHandlingTime.push({
                event: eventName,
                duration: duration,
                timestamp: new Date().toISOString()
            });
            
            // 檢查閾值
            if (duration > this.thresholds.eventHandlingTime) {
                this.addWarning('eventHandlingTime', `${eventName} 事件處理時間過長: ${duration.toFixed(2)}ms`);
            }
            
            return result;
        };
    }
    
    /**
     * 收集內存使用情況
     */
    collectMemoryUsage() {
        if (!this.shouldSample() || !performance.memory) {
            return;
        }
        
        const memory = performance.memory;
        const usedJSHeapSize = memory.usedJSHeapSize / (1024 * 1024); // 轉換為 MB
        
        this.metrics.memoryUsage.push({
            usedJSHeapSize: usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize / (1024 * 1024),
            jsHeapSizeLimit: memory.jsHeapSizeLimit / (1024 * 1024),
            timestamp: new Date().toISOString()
        });
        
        // 檢查閾值
        if (usedJSHeapSize > this.thresholds.memoryUsage) {
            this.addWarning('memoryUsage', `內存使用過高: ${usedJSHeapSize.toFixed(2)}MB`);
        }
    }
    
    /**
     * 添加警告
     * @param {string} category - 警告類別
     * @param {string} message - 警告消息
     */
    addWarning(category, message) {
        const warning = {
            category: category,
            message: message,
            timestamp: new Date().toISOString(),
            severity: 'warning'
        };
        
        this.warnings.push(warning);
        
        // 顯示警告（可選）
        if (window.CommonUtils) {
            window.CommonUtils.showToast(`⚠️ ${message}`, 'warning');
        } else {
            console.warn(`⚠️ ${message}`);
        }
    }
    
    /**
     * 獲取性能報告
     * @returns {Object} 性能報告
     */
    getPerformanceReport() {
        const report = {
            summary: {},
            metrics: {},
            warnings: this.warnings,
            recommendations: []
        };
        
        // 計算各指標的平均值
        Object.keys(this.metrics).forEach(category => {
            const data = this.metrics[category];
            if (data.length > 0) {
                const durations = data.map(item => item.duration || 0);
                const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
                const maxDuration = Math.max(...durations);
                const minDuration = Math.min(...durations);
                
                report.metrics[category] = {
                    count: data.length,
                    average: avgDuration.toFixed(2),
                    max: maxDuration.toFixed(2),
                    min: minDuration.toFixed(2),
                    threshold: this.thresholds[category] || 'N/A'
                };
                
                // 檢查是否超過閾值
                if (avgDuration > (this.thresholds[category] || Infinity)) {
                    report.recommendations.push(`優化 ${category}: 平均 ${avgDuration.toFixed(2)}ms 超過閾值 ${this.thresholds[category]}ms`);
                }
            }
        });
        
        // 生成摘要
        report.summary = {
            totalWarnings: this.warnings.length,
            totalMetrics: Object.values(this.metrics).reduce((sum, arr) => sum + arr.length, 0),
            samplingRate: this.samplingRate,
            monitoringEnabled: this.isEnabled,
            generatedAt: new Date().toISOString()
        };
        
        return report;
    }
    
    /**
     * 導出性能數據
     * @returns {string} JSON 格式的性能數據
     */
    exportData() {
        return JSON.stringify({
            metrics: this.metrics,
            warnings: this.warnings,
            thresholds: this.thresholds,
            summary: {
                totalMetrics: Object.values(this.metrics).reduce((sum, arr) => sum + arr.length, 0),
                totalWarnings: this.warnings.length,
                generatedAt: new Date().toISOString()
            }
        }, null, 2);
    }
    
    /**
     * 重置性能數據
     */
    reset() {
        Object.keys(this.metrics).forEach(key => {
            this.metrics[key] = [];
        });
        this.warnings = [];
        console.log('📊 性能數據已重置');
    }
    
    /**
     * 自動收集性能數據（定期執行）
     */
    startAutoCollection(interval = 30000) { // 默認 30 秒
        if (this.autoCollectionInterval) {
            clearInterval(this.autoCollectionInterval);
        }
        
        this.autoCollectionInterval = setInterval(() => {
            this.collectMemoryUsage();
            
            // 定期生成報告
            if (this.shouldSample()) {
                const report = this.getPerformanceReport();
                console.log('📊 定期性能報告:', report.summary);
            }
        }, interval);
        
        console.log(`📊 自動性能數據收集已啟動，間隔: ${interval}ms`);
    }
    
    /**
     * 停止自動收集
     */
    stopAutoCollection() {
        if (this.autoCollectionInterval) {
            clearInterval(this.autoCollectionInterval);
            this.autoCollectionInterval = null;
            console.log('📊 自動性能數據收集已停止');
        }
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.PerformanceMonitor = PerformanceMonitor;
    
    // 創建默認實例
    if (!window.performanceMonitor) {
        window.performanceMonitor = new PerformanceMonitor();
        
        // 自動啟動（可選）
        setTimeout(() => {
            window.performanceMonitor.startAutoCollection();
        }, 5000);
    }
    
    console.log('✅ 性能監控器已加載');
}

// 性能監控工具函數
const PerformanceUtils = {
    /**
     * 創建性能監測點
     * @param {string} name - 監測點名稱
     */
    mark(name) {
        if (performance && performance.mark) {
            performance.mark(`start_${name}`);
        }
    },
    
    /**
     * 測量性能
     * @param {string} name - 監測點名稱
     * @returns {number} 持續時間（毫秒）
     */
    measure(name) {
        if (performance && performance.measure) {
            performance.mark(`end_${name}`);
            performance.measure(name, `start_${name}`, `end_${name}`);
            
            const entries = performance.getEntriesByName(name);
            if (entries.length > 0) {
                return entries[0].duration;
            }
        }
        return 0;
    },
    
    /**
     * 獲取頁面加載時間
     * @returns {Object} 頁面加載時間信息
     */
    getPageLoadTimes() {
        if (!performance || !performance.timing) {
            return null;
        }
        
        const timing = performance.timing;
        
        return {
            dns: timing.domainLookupEnd - timing.domainLookupStart,
            tcp: timing.connectEnd - timing.connectStart,
            request: timing.responseStart - timing.requestStart,
            response: timing.responseEnd - timing.responseStart,
            domLoading: timing.domComplete - timing.domLoading,
            domInteractive: timing.domInteractive - timing.navigationStart,
            domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
            load: timing.loadEventEnd - timing.navigationStart,
            total: timing.loadEventEnd - timing.navigationStart
        };
    },
    
    /**
     * 檢查是否支持 Performance API
     * @returns {boolean} 是否支持
     */
    isSupported() {
        return !!(performance && performance.now && performance.mark && performance.measure);
    }
};

// 全局註冊 PerformanceUtils
if (typeof window !== 'undefined') {
    window.PerformanceUtils = PerformanceUtils;
    console.log('✅ 性能工具已加載');
}