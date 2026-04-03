// static/js/websocket-health-monitor-enhanced.js
// WebSocket連接健康度監控增強版
// 擴展現有WebSocket重連管理器，添加健康度評分和詳細監控功能

/**
 * WebSocket連接健康度監控增強版
 * 擴展現有WebSocket重連管理器，添加：
 * 1. 實時健康度評分系統
 * 2. 詳細連接統計和分析
 * 3. 監控數據收集和上報
 */
class WebSocketHealthMonitorEnhanced {
    /**
     * 創建增強版WebSocket健康度監控器
     * @param {Object} options 配置選項
     */
    constructor(options = {}) {
        // 基礎配置
        this.options = this._mergeOptions(options);
        
        // 監控數據存儲
        this.monitoringData = {
            // 連接基本信息
            connectionId: this._generateConnectionId(),
            connectionStartTime: null,
            connectionEndTime: null,
            
            // 消息統計
            totalMessagesSent: 0,
            totalMessagesReceived: 0,
            totalBytesSent: 0,
            totalBytesReceived: 0,
            
            // 時間統計
            messageLatencies: [],      // 消息延遲記錄
            connectionDurations: [],   // 連接持續時間記錄
            reconnectTimes: [],        // 重連時間記錄
            
            // 錯誤統計
            errorHistory: [],          // 錯誤歷史
            errorCountByType: {},      // 按類型統計的錯誤數量
            
            // 事件時間線
            connectionEvents: []       // 連接事件時間線
        };
        
        // 健康度評分系統
        this.healthScore = 100;        // 初始健康度（0-100）
        this.healthMetrics = {
            stability: 100,            // 連接穩定性（40%）
            reliability: 100,          // 消息可靠性（30%）
            networkQuality: 100,       // 網絡質量（20%）
            resourceUsage: 100         // 資源使用（10%）
        };
        
        // 健康度權重配置
        this.healthWeights = {
            stability: 0.4,
            reliability: 0.3,
            networkQuality: 0.2,
            resourceUsage: 0.1
        };
        
        // 警報系統
        this.alerts = [];
        this.alertThresholds = {
            healthScore: {
                warning: 70,   // 健康度低於70發出警告
                critical: 50   // 健康度低於50發出嚴重警報
            },
            errorRate: {
                warning: 0.05,  // 錯誤率超過5%發出警告
                critical: 0.1   // 錯誤率超過10%發出嚴重警報
            },
            latency: {
                warning: 1000,  // 延遲超過1秒發出警告
                critical: 3000  // 延遲超過3秒發出嚴重警報
            }
        };
        
        // 初始化時間戳
        this.lastHealthCheckTime = null;
        this.lastDataReportTime = null;
        
        console.log("🔧 WebSocket健康度監控增強版初始化完成");
        console.log(`  連接ID: ${this.monitoringData.connectionId}`);
    }
    
    /**
     * 合併配置選項
     * @private
     */
    _mergeOptions(userOptions) {
        const defaultOptions = {
            // 監控配置
            enableDetailedMonitoring: true,
            enableHealthScoring: true,
            enableAlerts: true,
            
            // 數據上報配置
            dataReportInterval: 60000,      // 數據上報間隔（60秒）
            healthCheckInterval: 30000,     // 健康度檢查間隔（30秒）
            
            // 數據保留配置
            maxLatencyRecords: 100,
            maxErrorRecords: 50,
            maxEventRecords: 200,
            
            // 性能配置
            enablePerformanceTracking: true,
            trackResourceUsage: false,      // 注意：需要瀏覽器支持
            
            // 調試配置
            debugMode: false,
            logLevel: 'info'                // 'debug', 'info', 'warn', 'error'
        };
        
        return { ...defaultOptions, ...userOptions };
    }
    
    /**
     * 生成唯一連接ID
     * @private
     */
    _generateConnectionId() {
        const timestamp = Date.now().toString(36);
        const random = Math.random().toString(36).substr(2, 9);
        return `ws_${timestamp}_${random}`;
    }
    
    /**
     * 記錄連接開始
     */
    recordConnectionStart() {
        const eventTime = new Date();
        this.monitoringData.connectionStartTime = eventTime;
        
        this._addConnectionEvent('connection_start', {
            timestamp: eventTime.toISOString(),
            connectionId: this.monitoringData.connectionId
        });
        
        console.log(`🔗 連接開始記錄: ${this.monitoringData.connectionId}`);
        
        // 啟動定期檢查
        this._startPeriodicChecks();
    }
    
    /**
     * 記錄連接結束
     * @param {string} reason 連接結束原因
     */
    recordConnectionEnd(reason = 'normal') {
        const eventTime = new Date();
        this.monitoringData.connectionEndTime = eventTime;
        
        // 計算連接持續時間
        if (this.monitoringData.connectionStartTime) {
            const duration = eventTime - this.monitoringData.connectionStartTime;
            this.monitoringData.connectionDurations.push(duration);
        }
        
        this._addConnectionEvent('connection_end', {
            timestamp: eventTime.toISOString(),
            reason: reason,
            duration: this.monitoringData.connectionDurations.slice(-1)[0] || 0
        });
        
        console.log(`🔌 連接結束記錄: ${reason}`);
        
        // 停止定期檢查
        this._stopPeriodicChecks();
        
        // 生成最終報告
        this.generateFinalReport();
    }
    
    /**
     * 記錄消息發送
     * @param {any} message 發送的消息
     * @param {number} size 消息大小（字節）
     */
    recordMessageSent(message, size = 0) {
        this.monitoringData.totalMessagesSent++;
        this.monitoringData.totalBytesSent += size;
        
        const eventTime = new Date();
        this._addConnectionEvent('message_sent', {
            timestamp: eventTime.toISOString(),
            messageId: this._generateMessageId(),
            size: size,
            type: typeof message === 'string' ? 'text' : 'binary'
        });
        
        // 調試日誌
        if (this.options.debugMode) {
            console.debug(`📤 消息發送記錄: ${this.monitoringData.totalMessagesSent} 條`);
        }
    }
    
    /**
     * 記錄消息接收
     * @param {any} message 接收的消息
     * @param {number} size 消息大小（字節）
     * @param {number} latency 消息延遲（毫秒）
     */
    recordMessageReceived(message, size = 0, latency = 0) {
        this.monitoringData.totalMessagesReceived++;
        this.monitoringData.totalBytesReceived += size;
        
        if (latency > 0) {
            this.monitoringData.messageLatencies.push(latency);
            
            // 限制記錄數量
            if (this.monitoringData.messageLatencies.length > this.options.maxLatencyRecords) {
                this.monitoringData.messageLatencies.shift();
            }
        }
        
        const eventTime = new Date();
        this._addConnectionEvent('message_received', {
            timestamp: eventTime.toISOString(),
            size: size,
            latency: latency,
            type: typeof message === 'string' ? 'text' : 'binary'
        });
        
        // 調試日誌
        if (this.options.debugMode) {
            console.debug(`📥 消息接收記錄: ${this.monitoringData.totalMessagesReceived} 條, 延遲: ${latency}ms`);
        }
        
        // 檢查延遲警報
        this._checkLatencyAlert(latency);
    }
    
    /**
     * 記錄錯誤
     * @param {string} type 錯誤類型
     * @param {string} message 錯誤消息
     * @param {any} details 錯誤詳情
     */
    recordError(type, message, details = null) {
        const errorRecord = {
            timestamp: new Date().toISOString(),
            type: type,
            message: message,
            details: details
        };
        
        this.monitoringData.errorHistory.push(errorRecord);
        
        // 統計錯誤類型
        if (!this.monitoringData.errorCountByType[type]) {
            this.monitoringData.errorCountByType[type] = 0;
        }
        this.monitoringData.errorCountByType[type]++;
        
        // 限制錯誤記錄數量
        if (this.monitoringData.errorHistory.length > this.options.maxErrorRecords) {
            this.monitoringData.errorHistory.shift();
        }
        
        this._addConnectionEvent('error', errorRecord);
        
        console.warn(`⚠️ 錯誤記錄: ${type} - ${message}`);
        
        // 檢查錯誤率警報
        this._checkErrorRateAlert();
    }
    
    /**
     * 記錄重連事件
     * @param {number} attempt 重連嘗試次數
     * @param {number} delay 重連延遲
     * @param {boolean} success 是否成功
     */
    recordReconnect(attempt, delay, success) {
        const reconnectRecord = {
            timestamp: new Date().toISOString(),
            attempt: attempt,
            delay: delay,
            success: success
        };
        
        this.monitoringData.reconnectTimes.push(delay);
        
        this._addConnectionEvent('reconnect', reconnectRecord);
        
        console.log(`🔄 重連記錄: 第 ${attempt} 次, 延遲: ${delay}ms, 成功: ${success}`);
    }
    
    /**
     * 計算健康度評分
     * @returns {number} 健康度評分（0-100）
     */
    calculateHealthScore() {
        if (!this.options.enableHealthScoring) {
            return this.healthScore;
        }
        
        // 計算各維度分數
        this.healthMetrics.stability = this._calculateStabilityScore();
        this.healthMetrics.reliability = this._calculateReliabilityScore();
        this.healthMetrics.networkQuality = this._calculateNetworkQualityScore();
        this.healthMetrics.resourceUsage = this._calculateResourceUsageScore();
        
        // 加權計算總分
        let totalScore = 0;
        for (const [metric, weight] of Object.entries(this.healthWeights)) {
            totalScore += this.healthMetrics[metric] * weight;
        }
        
        // 確保分數在0-100範圍內
        this.healthScore = Math.max(0, Math.min(100, Math.round(totalScore)));
        
        // 記錄健康度檢查時間
        this.lastHealthCheckTime = new Date();
        
        // 檢查健康度警報
        this._checkHealthScoreAlert();
        
        return this.healthScore;
    }
    
    /**
     * 計算連接穩定性分數
     * @private
     */
    _calculateStabilityScore() {
        // 基礎分數
        let score = 100;
        
        // 減分項：錯誤數量
        const totalErrors = this.monitoringData.errorHistory.length;
        if (totalErrors > 0) {
            score -= Math.min(30, totalErrors * 5); // 每個錯誤減5分，最多減30分
        }
        
        // 減分項：重連次數
        const reconnectCount = this.monitoringData.reconnectTimes.length;
        if (reconnectCount > 0) {
            score -= Math.min(20, reconnectCount * 4); // 每次重連減4分，最多減20分
        }
        
        // 加分項：連接持續時間
        if (this.monitoringData.connectionDurations.length > 0) {
            const lastDuration = this.monitoringData.connectionDurations.slice(-1)[0];
            if (lastDuration > 300000) { // 超過5分鐘
                score += 10;
            } else if (lastDuration > 60000) { // 超過1分鐘
                score += 5;
            }
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * 計算消息可靠性分數
     * @private
     */
    _calculateReliabilityScore() {
        // 基礎分數
        let score = 100;
        
        const totalMessages = this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived;
        if (totalMessages === 0) {
            return 100; // 沒有消息時返回滿分
        }
        
        // 減分項：消息丟失率（如果發送和接收數量差異很大）
        const sent = this.monitoringData.totalMessagesSent;
        const received = this.monitoringData.totalMessagesReceived;
        if (sent > 0 && received > 0) {
            const lossRate = Math.abs(sent - received) / Math.max(sent, received);
            if (lossRate > 0.1) { // 丟失率超過10%
                score -= Math.min(40, lossRate * 100); // 按百分比減分
            }
        }
        
        // 減分項：高延遲
        if (this.monitoringData.messageLatencies.length > 0) {
            const avgLatency = this._calculateAverageLatency();
            if (avgLatency > 1000) { // 平均延遲超過1秒
                score -= Math.min(30, (avgLatency - 1000) / 100); // 每100ms減1分
            }
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * 計算網絡質量分數
     * @private
     */
    _calculateNetworkQualityScore() {
        // 基礎分數
        let score = 100;
        
        // 減分項：延遲抖動
        if (this.monitoringData.messageLatencies.length >= 5) {
            const jitter = this._calculateLatencyJitter();
            if (jitter > 200) { // 抖動超過200ms
                score -= Math.min(30, (jitter - 200) / 10); // 每10ms減1分
            }
        }
        
        // 減分項：頻繁重連
        const recentReconnects = this.monitoringData.reconnectTimes.length;
        if (recentReconnects > 3) {
            score -= Math.min(40, (recentReconnects - 3) * 10); // 超過3次後每次減10分
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * 計算資源使用分數
     * @private
     */
    _calculateResourceUsageScore() {
        // 基礎分數
        let score = 100;
        
        if (this.options.trackResourceUsage && 'performance' in window) {
            try {
                // 檢查內存使用（如果瀏覽器支持）
                if (performance.memory) {
                    const usedJSHeapSize = performance.memory.usedJSHeapSize;
                    const totalJSHeapSize = performance.memory.totalJSHeapSize;
                    
                    if (totalJSHeapSize > 0) {
                        const memoryUsage = usedJSHeapSize / totalJSHeapSize;
                        if (memoryUsage > 0.8) { // 內存使用超過80%
                            score -= Math.min(20, (memoryUsage - 0.8) * 100); // 每1%減1分
                        }
                    }
                }
            } catch (error) {
                // 忽略性能API錯誤
                console.debug('性能API不可用:', error.message);
            }
        }
        
        // 減分項：大量消息
        const totalMessages = this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived;
        if (totalMessages > 1000) {
            score -= Math.min(10, (totalMessages - 1000) / 100); // 每100條消息減1分
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    /**
     * 計算平均延遲
     * @private
     */
    _calculateAverageLatency() {
        if (this.monitoringData.messageLatencies.length === 0) {
            return 0;
        }
        
        const sum = this.monitoringData.messageLatencies.reduce((a, b) => a + b, 0);
        return sum / this.monitoringData.messageLatencies.length;
    }
    
    /**
     * 計算延遲抖動
     * @private
     */
    _calculateLatencyJitter() {
        if (this.monitoringData.messageLatencies.length < 2) {
            return 0;
        }
        
        // 計算延遲的標準差作為抖動
        const avg = this._calculateAverageLatency();
        const squareDiffs = this.monitoringData.messageLatencies.map(latency => {
            const diff = latency - avg;
            return diff * diff;
        });
        
        const avgSquareDiff = squareDiffs.reduce((a, b) => a + b, 0) / squareDiffs.length;
        return Math.sqrt(avgSquareDiff);
    }
    
    /**
     * 生成消息ID
     * @private
     */
    _generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }
    
    /**
     * 添加連接事件
     * @private
     */
    _addConnectionEvent(type, data) {
        const event = {
            type: type,
            timestamp: new Date().toISOString(),
            data: data
        };
        
        this.monitoringData.connectionEvents.push(event);
        
        // 限制事件記錄數量
        if (this.monitoringData.connectionEvents.length > this.options.maxEventRecords) {
            this.monitoringData.connectionEvents.shift();
        }
    }
    
    /**
     * 檢查健康度警報
     * @private
     */
    _checkHealthScoreAlert() {
        if (!this.options.enableAlerts) {
            return;
        }
        
        const thresholds = this.alertThresholds.healthScore;
        
        if (this.healthScore < thresholds.critical) {
            this._addAlert('critical', `連接健康度嚴重不足: ${this.healthScore}/100`, {
                healthScore: this.healthScore,
                healthMetrics: { ...this.healthMetrics }
            });
        } else if (this.healthScore < thresholds.warning) {
            this._addAlert('warning', `連接健康度偏低: ${this.healthScore}/100`, {
                healthScore: this.healthScore,
                healthMetrics: { ...this.healthMetrics }
            });
        }
    }
    
    /**
     * 檢查錯誤率警報
     * @private
     */
    _checkErrorRateAlert() {
        if (!this.options.enableAlerts) {
            return;
        }
        
        const totalMessages = this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived;
        if (totalMessages === 0) {
            return;
        }
        
        const totalErrors = this.monitoringData.errorHistory.length;
        const errorRate = totalErrors / totalMessages;
        
        const thresholds = this.alertThresholds.errorRate;
        
        if (errorRate > thresholds.critical) {
            this._addAlert('critical', `錯誤率過高: ${(errorRate * 100).toFixed(1)}%`, {
                errorRate: errorRate,
                totalErrors: totalErrors,
                totalMessages: totalMessages
            });
        } else if (errorRate > thresholds.warning) {
            this._addAlert('warning', `錯誤率偏高: ${(errorRate * 100).toFixed(1)}%`, {
                errorRate: errorRate,
                totalErrors: totalErrors,
                totalMessages: totalMessages
            });
        }
    }
    
    /**
     * 檢查延遲警報
     * @private
     */
    _checkLatencyAlert(latency) {
        if (!this.options.enableAlerts) {
            return;
        }
        
        const thresholds = this.alertThresholds.latency;
        
        if (latency > thresholds.critical) {
            this._addAlert('critical', `消息延遲過高: ${latency}ms`, {
                latency: latency,
                threshold: thresholds.critical
            });
        } else if (latency > thresholds.warning) {
            this._addAlert('warning', `消息延遲偏高: ${latency}ms`, {
                latency: latency,
                threshold: thresholds.warning
            });
        }
    }
    
    /**
     * 添加警報
     * @private
     */
    _addAlert(level, message, details = null) {
        const alert = {
            id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            timestamp: new Date().toISOString(),
            level: level, // 'info', 'warning', 'critical'
            message: message,
            details: details,
            acknowledged: false,
            resolved: false
        };
        
        this.alerts.push(alert);
        
        // 限制警報數量
        if (this.alerts.length > 50) {
            this.alerts.shift();
        }
        
        // 觸發警報事件
        this._triggerAlertEvent(alert);
        
        console.log(`🚨 ${level.toUpperCase()} 警報: ${message}`);
    }
    
    /**
     * 觸發警報事件
     * @private
     */
    _triggerAlertEvent(alert) {
        if (typeof CustomEvent !== 'undefined') {
            const event = new CustomEvent('websocket:alert', {
                detail: alert
            });
            document.dispatchEvent(event);
        }
    }
    
    /**
     * 啟動定期檢查
     * @private
     */
    _startPeriodicChecks() {
        // 健康度檢查定時器
        if (this.options.healthCheckInterval > 0) {
            this.healthCheckTimer = setInterval(() => {
                this.calculateHealthScore();
            }, this.options.healthCheckInterval);
        }
        
        // 數據上報定時器
        if (this.options.dataReportInterval > 0) {
            this.dataReportTimer = setInterval(() => {
                this.reportMonitoringData();
            }, this.options.dataReportInterval);
        }
    }
    
    /**
     * 停止定期檢查
     * @private
     */
    _stopPeriodicChecks() {
        if (this.healthCheckTimer) {
            clearInterval(this.healthCheckTimer);
            this.healthCheckTimer = null;
        }
        
        if (this.dataReportTimer) {
            clearInterval(this.dataReportTimer);
            this.dataReportTimer = null;
        }
    }
    
    /**
     * 上報監控數據
     */
    reportMonitoringData() {
        if (!this.options.enableDetailedMonitoring) {
            return;
        }
        
        const report = {
            timestamp: new Date().toISOString(),
            connectionId: this.monitoringData.connectionId,
            healthScore: this.healthScore,
            healthMetrics: { ...this.healthMetrics },
            connectionStats: {
                duration: this.getConnectionDuration(),
                messagesSent: this.monitoringData.totalMessagesSent,
                messagesReceived: this.monitoringData.totalMessagesReceived,
                bytesSent: this.monitoringData.totalBytesSent,
                bytesReceived: this.monitoringData.totalBytesReceived,
                avgLatency: this._calculateAverageLatency(),
                latencyJitter: this._calculateLatencyJitter(),
                errorRate: this.calculateErrorRate(),
                reconnectCount: this.monitoringData.reconnectTimes.length
            },
            activeAlerts: this.alerts.filter(alert => !alert.resolved).length
        };
        
        // 記錄上報時間
        this.lastDataReportTime = new Date();
        
        // 發送到監控服務（這裡可以擴展為實際的API調用）
        this._sendToMonitoringService(report);
        
        // 調試日誌
        if (this.options.debugMode) {
            console.debug('📊 監控數據上報:', report);
        }
    }
    
    /**
     * 發送到監控服務（佔位方法）
     * @private
     */
    _sendToMonitoringService(report) {
        // 這裡可以實現實際的API調用
        // 例如：fetch('/api/websocket-monitoring/', { method: 'POST', body: JSON.stringify(report) })
        
        // 當前實現：發送到控制台
        if (this.options.logLevel === 'debug') {
            console.debug('📡 監控數據發送:', report);
        }
        
        // 觸發自定義事件，讓其他組件可以處理這些數據
        if (typeof CustomEvent !== 'undefined') {
            const event = new CustomEvent('websocket:monitoring_data', {
                detail: report
            });
            document.dispatchEvent(event);
        }
    }
    
    /**
     * 計算錯誤率
     */
    calculateErrorRate() {
        const totalMessages = this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived;
        if (totalMessages === 0) {
            return 0;
        }
        
        const totalErrors = this.monitoringData.errorHistory.length;
        return totalErrors / totalMessages;
    }
    
    /**
     * 獲取連接持續時間
     */
    getConnectionDuration() {
        if (!this.monitoringData.connectionStartTime) {
            return 0;
        }
        
        const endTime = this.monitoringData.connectionEndTime || new Date();
        return endTime - this.monitoringData.connectionStartTime;
    }
    
    /**
     * 生成最終報告
     */
    generateFinalReport() {
        const report = {
            connectionId: this.monitoringData.connectionId,
            startTime: this.monitoringData.connectionStartTime?.toISOString(),
            endTime: this.monitoringData.connectionEndTime?.toISOString(),
            duration: this.getConnectionDuration(),
            finalHealthScore: this.healthScore,
            finalHealthMetrics: { ...this.healthMetrics },
            summary: {
                totalMessages: this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived,
                totalBytes: this.monitoringData.totalBytesSent + this.monitoringData.totalBytesReceived,
                totalErrors: this.monitoringData.errorHistory.length,
                totalReconnects: this.monitoringData.reconnectTimes.length,
                avgLatency: this._calculateAverageLatency(),
                maxLatency: this.monitoringData.messageLatencies.length > 0 ? 
                    Math.max(...this.monitoringData.messageLatencies) : 0,
                errorRate: this.calculateErrorRate()
            },
            errorDistribution: { ...this.monitoringData.errorCountByType },
            alertsSummary: {
                total: this.alerts.length,
                critical: this.alerts.filter(a => a.level === 'critical').length,
                warning: this.alerts.filter(a => a.level === 'warning').length,
                resolved: this.alerts.filter(a => a.resolved).length
            }
        };
        
        console.log('📋 連接最終報告:', report);
        
        // 觸發最終報告事件
        if (typeof CustomEvent !== 'undefined') {
            const event = new CustomEvent('websocket:final_report', {
                detail: report
            });
            document.dispatchEvent(event);
        }
        
        return report;
    }
    
    /**
     * 獲取監控數據摘要
     */
    getMonitoringSummary() {
        return {
            connectionId: this.monitoringData.connectionId,
            healthScore: this.healthScore,
            connectionDuration: this.getConnectionDuration(),
            messages: {
                sent: this.monitoringData.totalMessagesSent,
                received: this.monitoringData.totalMessagesReceived,
                total: this.monitoringData.totalMessagesSent + this.monitoringData.totalMessagesReceived
            },
            errors: {
                total: this.monitoringData.errorHistory.length,
                byType: { ...this.monitoringData.errorCountByType }
            },
            alerts: {
                active: this.alerts.filter(a => !a.resolved).length,
                total: this.alerts.length
            }
        };
    }
    
    /**
     * 確認警報
     */
    acknowledgeAlert(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (alert) {
            alert.acknowledged = true;
            console.log(`✅ 警報已確認: ${alertId}`);
        }
    }
    
    /**
     * 解決警報
     */
    resolveAlert(alertId) {
        const alert = this.alerts.find(a => a.id === alertId);
        if (alert) {
            alert.resolved = true;
            console.log(`✅ 警報已解決: ${alertId}`);
        }
    }
    
    /**
     * 清理監控數據
     */
    cleanup() {
        this._stopPeriodicChecks();
        
        // 生成最終報告
        if (this.monitoringData.connectionStartTime && !this.monitoringData.connectionEndTime) {
            this.recordConnectionEnd('cleanup');
        }
        
        console.log(`🧹 WebSocket健康度監控清理完成: ${this.monitoringData.connectionId}`);
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.WebSocketHealthMonitorEnhanced = WebSocketHealthMonitorEnhanced;
    console.log('✅ WebSocket健康度監控增強版已註冊到全局');
}
