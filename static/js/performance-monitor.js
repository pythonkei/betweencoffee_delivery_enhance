// static/js/performance-monitor.js
// ==================== 性能監控工具 ====================

class PerformanceMonitor {
    constructor() {
        console.log('🔄 初始化性能監控工具...');
        
        // 性能數據存儲
        this.metrics = {
            httpRequests: [],
            websocketMessages: [],
            uiUpdates: [],
            operations: []
        };
        
        // 監控配置
        this.config = {
            maxEntries: 100,          // 最大記錄條數
            warningThreshold: 500,    // 警告閾值（毫秒）
            errorThreshold: 1000,     // 錯誤閾值（毫秒）
            autoCleanup: true,        // 自動清理舊數據
            enableConsoleLog: true    // 啟用控制台日誌
        };
        
        // 初始化事件監聽器
        this.initEventListeners();
        
        console.log('✅ 性能監控工具初始化完成');
    }
    
    // ==================== 事件監聽器 ====================
    
    initEventListeners() {
        // 監聽自定義性能事件
        document.addEventListener('performance:http_request', (e) => {
            this.recordHttpRequest(e.detail);
        });
        
        document.addEventListener('performance:websocket_message', (e) => {
            this.recordWebSocketMessage(e.detail);
        });
        
        document.addEventListener('performance:ui_update', (e) => {
            this.recordUiUpdate(e.detail);
        });
        
        document.addEventListener('performance:operation', (e) => {
            this.recordOperation(e.detail);
        });
        
        // 監聽頁面卸載事件，保存性能數據
        window.addEventListener('beforeunload', () => {
            this.saveMetricsToLocalStorage();
        });
        
        // 監聽頁面加載事件，恢復性能數據
        window.addEventListener('load', () => {
            this.loadMetricsFromLocalStorage();
        });
    }
    
    // ==================== 記錄方法 ====================
    
    /**
     * 記錄HTTP請求
     */
    recordHttpRequest({ url, method, startTime, endTime, status, success }) {
        const duration = endTime - startTime;
        const entry = {
            type: 'http_request',
            url,
            method,
            duration,
            status,
            success,
            timestamp: new Date().toISOString(),
            startTime,
            endTime
        };
        
        this.metrics.httpRequests.push(entry);
        
        // 檢查性能閾值
        this.checkPerformanceThreshold('HTTP請求', url, duration);
        
        // 自動清理
        if (this.config.autoCleanup) {
            this.cleanupOldEntries('httpRequests');
        }
        
        // 控制台日誌
        if (this.config.enableConsoleLog) {
            const level = duration > this.config.errorThreshold ? 'error' : 
                         duration > this.config.warningThreshold ? 'warn' : 'info';
            console[level](`📡 HTTP ${method} ${url}: ${duration}ms (${status})`);
        }
        
        return entry;
    }
    
    /**
     * 記錄WebSocket消息
     */
    recordWebSocketMessage({ type, receiveTime, serverTime, latency, size }) {
        const entry = {
            type: 'websocket_message',
            messageType: type,
            latency,
            size: size || 0,
            receiveTime,
            serverTime,
            timestamp: new Date().toISOString()
        };
        
        this.metrics.websocketMessages.push(entry);
        
        // 檢查性能閾值
        this.checkPerformanceThreshold('WebSocket消息', type, latency);
        
        // 自動清理
        if (this.config.autoCleanup) {
            this.cleanupOldEntries('websocketMessages');
        }
        
        // 控制台日誌
        if (this.config.enableConsoleLog && latency > 100) {
            console.log(`📨 WebSocket ${type}: 延遲 ${latency}ms`);
        }
        
        return entry;
    }
    
    /**
     * 記錄UI更新
     */
    recordUiUpdate({ component, action, startTime, endTime, elementsUpdated }) {
        const duration = endTime - startTime;
        const entry = {
            type: 'ui_update',
            component,
            action,
            duration,
            elementsUpdated: elementsUpdated || 0,
            timestamp: new Date().toISOString(),
            startTime,
            endTime
        };
        
        this.metrics.uiUpdates.push(entry);
        
        // 檢查性能閾值
        this.checkPerformanceThreshold('UI更新', `${component}.${action}`, duration);
        
        // 自動清理
        if (this.config.autoCleanup) {
            this.cleanupOldEntries('uiUpdates');
        }
        
        // 控制台日誌
        if (this.config.enableConsoleLog && duration > 50) {
            console.log(`🎨 UI更新 ${component}.${action}: ${duration}ms (${elementsUpdated}個元素)`);
        }
        
        return entry;
    }
    
    /**
     * 記錄操作（如按鈕點擊）
     */
    recordOperation({ operation, orderId, startTime, endTime, success, error }) {
        const duration = endTime - startTime;
        const entry = {
            type: 'operation',
            operation,
            orderId,
            duration,
            success,
            error,
            timestamp: new Date().toISOString(),
            startTime,
            endTime
        };
        
        this.metrics.operations.push(entry);
        
        // 檢查性能閾值
        this.checkPerformanceThreshold('操作', operation, duration);
        
        // 自動清理
        if (this.config.autoCleanup) {
            this.cleanupOldEntries('operations');
        }
        
        // 控制台日誌
        if (this.config.enableConsoleLog) {
            const status = success ? '✅' : '❌';
            console.log(`${status} 操作 ${operation} #${orderId}: ${duration}ms`);
        }
        
        return entry;
    }
    
    // ==================== 性能檢查 ====================
    
    /**
     * 檢查性能閾值
     */
    checkPerformanceThreshold(category, item, duration) {
        if (duration > this.config.errorThreshold) {
            this.triggerPerformanceAlert('error', category, item, duration);
        } else if (duration > this.config.warningThreshold) {
            this.triggerPerformanceAlert('warning', category, item, duration);
        }
    }
    
    /**
     * 觸發性能警報
     */
    triggerPerformanceAlert(level, category, item, duration) {
        const message = `性能${level === 'error' ? '錯誤' : '警告'}: ${category} "${item}" 耗時 ${duration}ms`;
        
        // 發送自定義事件
        document.dispatchEvent(new CustomEvent('performance:alert', {
            detail: {
                level,
                category,
                item,
                duration,
                message,
                timestamp: new Date().toISOString()
            }
        }));
        
        // 控制台日誌
        if (this.config.enableConsoleLog) {
            console[level](`🚨 ${message}`);
        }
        
        // 可選：發送到服務器
        this.sendAlertToServer(level, category, item, duration);
    }
    
    /**
     * 發送警報到服務器
     */
    sendAlertToServer(level, category, item, duration) {
        // 這裡可以實現發送到服務器的邏輯
        // 例如：fetch('/api/performance/alerts/', { method: 'POST', ... })
    }
    
    // ==================== 數據管理 ====================
    
    /**
     * 清理舊條目
     */
    cleanupOldEntries(metricType) {
        if (this.metrics[metricType].length > this.config.maxEntries) {
            const excess = this.metrics[metricType].length - this.config.maxEntries;
            this.metrics[metricType] = this.metrics[metricType].slice(excess);
        }
    }
    
    /**
     * 保存指標到本地存儲
     */
    saveMetricsToLocalStorage() {
        try {
            const data = {
                metrics: this.metrics,
                timestamp: new Date().toISOString()
            };
            localStorage.setItem('performance_metrics', JSON.stringify(data));
            console.log('💾 性能指標已保存到本地存儲');
        } catch (error) {
            console.error('❌ 保存性能指標失敗:', error);
        }
    }
    
    /**
     * 從本地存儲加載指標
     */
    loadMetricsFromLocalStorage() {
        try {
            const data = localStorage.getItem('performance_metrics');
            if (data) {
                const parsed = JSON.parse(data);
                this.metrics = parsed.metrics || this.metrics;
                console.log('📂 從本地存儲加載性能指標');
            }
        } catch (error) {
            console.error('❌ 加載性能指標失敗:', error);
        }
    }
    
    /**
     * 清除所有指標
     */
    clearAllMetrics() {
        this.metrics = {
            httpRequests: [],
            websocketMessages: [],
            uiUpdates: [],
            operations: []
        };
        console.log('🧹 所有性能指標已清除');
    }
    
    // ==================== 統計方法 ====================
    
    /**
     * 獲取性能統計
     */
    getPerformanceStats() {
        const stats = {
            totalRequests: this.metrics.httpRequests.length,
            totalWebSocketMessages: this.metrics.websocketMessages.length,
            totalUiUpdates: this.metrics.uiUpdates.length,
            totalOperations: this.metrics.operations.length,
            
            // HTTP請求統計
            httpStats: this.calculateHttpStats(),
            
            // WebSocket統計
            websocketStats: this.calculateWebSocketStats(),
            
            // UI更新統計
            uiStats: this.calculateUiStats(),
            
            // 操作統計
            operationStats: this.calculateOperationStats(),
            
            // 性能問題
            performanceIssues: this.getPerformanceIssues()
        };
        
        return stats;
    }
    
    /**
     * 計算HTTP統計
     */
    calculateHttpStats() {
        const requests = this.metrics.httpRequests;
        if (requests.length === 0) return null;
        
        const successful = requests.filter(r => r.success);
        const failed = requests.filter(r => !r.success);
        const totalDuration = successful.reduce((sum, r) => sum + r.duration, 0);
        
        return {
            total: requests.length,
            successful: successful.length,
            failed: failed.length,
            successRate: (successful.length / requests.length * 100).toFixed(1),
            averageDuration: Math.round(totalDuration / successful.length),
            minDuration: Math.min(...successful.map(r => r.duration)),
            maxDuration: Math.max(...successful.map(r => r.duration))
        };
    }
    
    /**
     * 計算WebSocket統計
     */
    calculateWebSocketStats() {
        const messages = this.metrics.websocketMessages;
        if (messages.length === 0) return null;
        
        const totalLatency = messages.reduce((sum, m) => sum + m.latency, 0);
        
        return {
            total: messages.length,
            averageLatency: Math.round(totalLatency / messages.length),
            minLatency: Math.min(...messages.map(m => m.latency)),
            maxLatency: Math.max(...messages.map(m => m.latency)),
            messageTypes: this.countMessageTypes(messages)
        };
    }
    
    /**
     * 計算UI更新統計
     */
    calculateUiStats() {
        const updates = this.metrics.uiUpdates;
        if (updates.length === 0) return null;
        
        const totalDuration = updates.reduce((sum, u) => sum + u.duration, 0);
        const totalElements = updates.reduce((sum, u) => sum + u.elementsUpdated, 0);
        
        return {
            total: updates.length,
            averageDuration: Math.round(totalDuration / updates.length),
            totalElementsUpdated: totalElements,
            averageElementsPerUpdate: Math.round(totalElements / updates.length)
        };
    }
    
    /**
     * 計算操作統計
     */
    calculateOperationStats() {
        const operations = this.metrics.operations;
        if (operations.length === 0) return null;
        
        const successful = operations.filter(o => o.success);
        const failed = operations.filter(o => !o.success);
        const totalDuration = successful.reduce((sum, o) => sum + o.duration, 0);
        
        return {
            total: operations.length,
            successful: successful.length,
            failed: failed.length,
            successRate: (successful.length / operations.length * 100).toFixed(1),
            averageDuration: Math.round(totalDuration / successful.length),
            operationTypes: this.countOperationTypes(operations)
        };
    }
    
    /**
     * 獲取性能問題
     */
    getPerformanceIssues() {
        const issues = [];
        
        // 檢查慢HTTP請求
        this.metrics.httpRequests.forEach(req => {
            if (req.duration > this.config.warningThreshold) {
                issues.push({
                    type: 'slow_http_request',
                    severity: req.duration > this.config.errorThreshold ? 'error' : 'warning',
                    item: req.url,
                    duration: req.duration,
                    timestamp: req.timestamp
                });
            }
        });
        
        // 檢查高延遲WebSocket消息
        this.metrics.websocketMessages.forEach(msg => {
            if (msg.latency > this.config.warningThreshold) {
                issues.push({
                    type: 'high_latency_websocket',
                    severity: msg.latency > this.config.errorThreshold ? 'error' : 'warning',
                    item: msg.messageType,
                    latency: msg.latency,
                    timestamp: msg.timestamp
                });
            }
        });
        
        // 檢查慢UI更新
        this.metrics.uiUpdates.forEach(update => {
            if (update.duration > this.config.warningThreshold) {
                issues.push({
                    type: 'slow_ui_update',
                    severity: update.duration > this.config.errorThreshold ? 'error' : 'warning',
                    item: `${update.component}.${update.action}`,
                    duration: update.duration,
                    timestamp: update.timestamp
                });
            }
        });
        
        return issues;
    }
    
    // ==================== 輔助方法 ====================
    
    /**
     * 計算消息類型統計
     */
    countMessageTypes(messages) {
        const types = {};
        messages.forEach(msg => {
            types[msg.messageType] = (types[msg.messageType] || 0) + 1;
        });
        return types;
    }
    
    /**
     * 計算操作類型統計
     */
    countOperationTypes(operations) {
        const types = {};
        operations.forEach(op => {
            types[op.operation] = (types[op.operation] || 0) + 1;
        });
        return types;
    }
    
    /**
     * 生成性能報告
     */
    generateReport() {
        const stats = this.getPerformanceStats();
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                totalMetrics: stats.totalRequests + stats.totalWebSocketMessages + 
                            stats.totalUiUpdates + stats.totalOperations,
                performanceIssues: stats.performanceIssues.length
            },
            detailedStats: stats,
            recommendations: this.generateRecommendations(stats)
        };
        
        return report;
    }
    
    /**
     * 生成建議
     */
    generateRecommendations(stats) {
        const recommendations = [];
        
        // HTTP請求建議
        if (stats.httpStats && stats.httpStats.averageDuration > 300) {
            recommendations.push({
                type: 'http_optimization',
                priority: 'medium',
                message: `HTTP請求平均耗時 ${stats.httpStats.averageDuration}ms，建議優化API響應時間`
            });
        }
        
        // WebSocket建議
        if (stats.websocketStats && stats.websocketStats.averageLatency > 200) {
            recommendations.push({
                type: 'websocket_optimization',
                priority: 'high',
                message: `WebSocket消息平均延遲 ${stats.websocketStats.averageLatency}ms，建議檢查網絡連接和服務器性能`
            });
        }
        
        // UI更新建議
        if (stats.uiStats && stats.uiStats.averageDuration > 100) {
            recommendations.push({
                type: 'ui_optimization',
                priority: 'low',
                message: `UI更新平均耗時 ${stats.uiStats.averageDuration}ms，建議優化DOM操作`
            });
        }
        
        return recommendations;
    }
    
    /**
     * 導出性能數據
     */
    exportData(format = 'json') {
        const data = {
            metrics: this.metrics,
            stats: this.getPerformanceStats(),
            report: this.generateReport(),
            config: this.config,
            exportTimestamp: new Date().toISOString()
        };
        
        if (format === 'json') {
            return JSON.stringify(data, null, 2);
        } else if (format === 'csv') {
            return this.convertToCsv(data);
        }
        
        return data;
    }
    
    /**
     * 轉換為CSV格式
     */
    convertToCsv(data) {
        // 簡化的CSV轉換實現
        let csv = '類型,項目,耗時(ms),時間戳,狀態\n';
        
        // HTTP請求
        data.metrics.httpRequests.forEach(req => {
            csv += `HTTP請求,${req.url},${req.duration},${req.timestamp},${req.success ? '成功' : '失敗'}\n`;
        });
        
        // WebSocket消息
        data.metrics.websocketMessages.forEach(msg => {
            csv += `WebSocket,${msg.messageType},${msg.latency},${msg.timestamp},-\n`;
        });
        
        return csv;
    }
}

// ==================== 全局註冊和工具函數 ====================

if (typeof window !== 'undefined') {
    // 創建全局實例
    window.performanceMonitor = new PerformanceMonitor();
    
    // 工具函數：記錄HTTP請求
    window.recordHttpRequest = function(url, method, startTime, endTime, status, success) {
        const detail = {
            url,
            method: method || 'GET',
            startTime,
            endTime,
            status: status || 200,
            success: success !== false
        };
        document.dispatchEvent(new CustomEvent('performance:http_request', { detail }));
    };
    
    // 工具函數：記錄WebSocket消息
    window.recordWebSocketMessage = function(type, receiveTime, serverTime, latency, size) {
        const detail = {
            type,
            receiveTime,
            serverTime,
            latency,
            size
        };
        document.dispatchEvent(new CustomEvent('performance:websocket_message', { detail }));
    };
    
    // 工具函數：記錄UI更新
    window.recordUiUpdate = function(component, action, startTime, endTime, elementsUpdated) {
        const detail = {
            component,
            action,
            startTime,
            endTime,
            elementsUpdated
        };
        document.dispatchEvent(new CustomEvent('performance:ui_update', { detail }));
    };
    
    // 工具函數：記錄操作
    window.recordOperation = function(operation, orderId, startTime, endTime, success, error) {
        const detail = {
            operation,
            orderId,
            startTime,
            endTime,
            success: success !== false,
            error
        };
        document.dispatchEvent(new CustomEvent('performance:operation', { detail }));
    };
    
    // 工具函數：獲取性能報告
    window.getPerformanceReport = function() {
        return window.performanceMonitor.generateReport();
    };
    
    // 工具函數：導出性能數據
    window.exportPerformanceData = function(format = 'json') {
        return window.performanceMonitor.exportData(format);
    };
    
    // 工具函數：清除性能數據
    window.clearPerformanceData = function() {
        window.performanceMonitor.clearAllMetrics();
    };
    
    console.log('✅ 性能監控工具已註冊到全局窗口');
}
