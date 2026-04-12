// static/js/websocket-reconnect-manager.js
// WebSocket重連管理器 - 實現指數退避算法和智能重連策略

/**
 * WebSocket重連管理器
 * 實現指數退避重連算法，包含隨機抖動和智能重連策略
 */
class WebSocketReconnectManager {
    /**
     * 創建重連管理器
     * @param {Object} options 配置選項
     * @param {number} options.baseDelay 基礎延遲（毫秒），默認1000ms
     * @param {number} options.maxDelay 最大延遲（毫秒），默認30000ms
     * @param {number} options.maxRetries 最大重試次數，默認10次
     * @param {number} options.jitterFactor 抖動因子（0-1），默認0.2（±20%）
     * @param {boolean} options.enableJitter 是否啟用抖動，默認true
     */
    constructor(options = {}) {
        this.baseDelay = options.baseDelay || 1000; // 1秒
        this.maxDelay = options.maxDelay || 30000; // 30秒
        this.maxRetries = options.maxRetries || 10;
        this.jitterFactor = options.jitterFactor || 0.2; // ±20%
        this.enableJitter = options.enableJitter !== false;
        
        this.retryCount = 0;
        this.lastRetryTime = null;
        this.retryHistory = [];
        this.isRetrying = false;
        
        // 連接質量指標
        this.connectionMetrics = {
            totalConnections: 0,
            successfulConnections: 0,
            failedConnections: 0,
            totalRetries: 0,
            avgReconnectTime: 0,
            lastConnectionTime: null,
            connectionStreak: 0, // 連續成功連接次數
            failureStreak: 0,    // 連續失敗連接次數
        };
        
        console.log("🔧 WebSocket重連管理器初始化完成");
        console.log(`  基礎延遲: ${this.baseDelay}ms, 最大延遲: ${this.maxDelay}ms`);
        console.log(`  最大重試次數: ${this.maxRetries}, 抖動因子: ${this.jitterFactor}`);
    }
    
    /**
     * 計算下一次重連延遲（指數退避 + 抖動）
     * @returns {number} 延遲時間（毫秒）
     */
    getNextDelay() {
        // 指數退避公式：delay = baseDelay * 2^retryCount
        let delay = this.baseDelay * Math.pow(2, this.retryCount);
        
        // 限制最大延遲
        delay = Math.min(delay, this.maxDelay);
        
        // 添加隨機抖動（如果啟用）
        if (this.enableJitter) {
            const jitterRange = delay * this.jitterFactor;
            delay += Math.random() * jitterRange * 2 - jitterRange;
            
            // 確保不小於100ms
            delay = Math.max(100, delay);
        }
        
        // 四捨五入到整數毫秒
        return Math.round(delay);
    }
    
    /**
     * 檢查是否應該繼續重試
     * @returns {boolean} 是否應該重試
     */
    shouldRetry() {
        return this.retryCount < this.maxRetries;
    }
    
    /**
     * 記錄重試開始
     * @returns {number} 本次重試的延遲時間
     */
    startRetry() {
        if (!this.shouldRetry()) {
            console.warn("⚠️ 已達到最大重試次數，停止重試");
            return -1;
        }
        
        this.isRetrying = true;
        this.retryCount++;
        this.connectionMetrics.totalRetries++;
        
        const delay = this.getNextDelay();
        this.lastRetryTime = new Date();
        
        // 記錄重試歷史
        this.retryHistory.push({
            attempt: this.retryCount,
            delay: delay,
            timestamp: this.lastRetryTime,
            retryCount: this.retryCount
        });
        
        // 限制歷史記錄長度
        if (this.retryHistory.length > 20) {
            this.retryHistory.shift();
        }
        
        console.log(`🔄 開始第 ${this.retryCount}/${this.maxRetries} 次重試，延遲: ${delay}ms`);
        return delay;
    }
    
    /**
     * 記錄連接成功
     */
    recordConnectionSuccess() {
        this.isRetrying = false;
        this.retryCount = 0; // 重置重試計數器
        
        this.connectionMetrics.totalConnections++;
        this.connectionMetrics.successfulConnections++;
        this.connectionMetrics.connectionStreak++;
        this.connectionMetrics.failureStreak = 0;
        this.connectionMetrics.lastConnectionTime = new Date();
        
        // 計算平均重連時間
        if (this.retryHistory.length > 0) {
            const lastRetry = this.retryHistory[this.retryHistory.length - 1];
            const reconnectTime = new Date() - lastRetry.timestamp;
            
            // 加權平均
            if (this.connectionMetrics.avgReconnectTime === 0) {
                this.connectionMetrics.avgReconnectTime = reconnectTime;
            } else {
                this.connectionMetrics.avgReconnectTime = 
                    0.8 * this.connectionMetrics.avgReconnectTime + 0.2 * reconnectTime;
            }
        }
        
        console.log("✅ 連接成功，重置重試計數器");
    }
    
    /**
     * 記錄連接失敗
     * @param {string} reason 失敗原因
     */
    recordConnectionFailure(reason = "未知原因") {
        this.connectionMetrics.totalConnections++;
        this.connectionMetrics.failedConnections++;
        this.connectionMetrics.failureStreak++;
        this.connectionMetrics.connectionStreak = 0;
        
        console.log(`❌ 連接失敗: ${reason}, 失敗連續次數: ${this.connectionMetrics.failureStreak}`);
    }
    
    /**
     * 重置重連管理器（用於手動重新連接）
     */
    reset() {
        this.retryCount = 0;
        this.isRetrying = false;
        this.retryHistory = [];
        console.log("🔄 重連管理器已重置");
    }
    
    /**
     * 獲取連接健康度評分（0-100）
     * @returns {number} 健康度評分
     */
    getHealthScore() {
        let score = 100;
        
        // 成功率權重：40%
        const successRate = this.connectionMetrics.totalConnections > 0 
            ? this.connectionMetrics.successfulConnections / this.connectionMetrics.totalConnections 
            : 1;
        score *= successRate * 0.4;
        
        // 重試率權重：30%（重試越少分數越高）
        const retryRate = this.connectionMetrics.totalConnections > 0
            ? this.connectionMetrics.totalRetries / this.connectionMetrics.totalConnections
            : 0;
        const retryScore = Math.max(0, 1 - Math.min(retryRate, 1)); // 重試率0-1，越低越好
        score *= retryScore * 0.3;
        
        // 連續失敗懲罰：30%
        const failurePenalty = Math.max(0, 1 - (this.connectionMetrics.failureStreak / 5)); // 連續5次失敗得0分
        score *= failurePenalty * 0.3;
        
        return Math.round(score);
    }
    
    /**
     * 獲取連接狀態摘要
     * @returns {Object} 狀態摘要
     */
    getStatusSummary() {
        const successRate = this.connectionMetrics.totalConnections > 0
            ? Math.round((this.connectionMetrics.successfulConnections / this.connectionMetrics.totalConnections) * 100)
            : 100;
            
        const healthScore = this.getHealthScore();
        let healthStatus = "優秀";
        if (healthScore < 60) healthStatus = "危險";
        else if (healthScore < 80) healthStatus = "警告";
        else if (healthScore < 90) healthStatus = "良好";
        
        return {
            // 當前狀態
            isRetrying: this.isRetrying,
            retryCount: this.retryCount,
            maxRetries: this.maxRetries,
            nextDelay: this.shouldRetry() ? this.getNextDelay() : 0,
            
            // 連接指標
            totalConnections: this.connectionMetrics.totalConnections,
            successfulConnections: this.connectionMetrics.successfulConnections,
            failedConnections: this.connectionMetrics.failedConnections,
            successRate: `${successRate}%`,
            
            // 重試指標
            totalRetries: this.connectionMetrics.totalRetries,
            avgReconnectTime: Math.round(this.connectionMetrics.avgReconnectTime),
            connectionStreak: this.connectionMetrics.connectionStreak,
            failureStreak: this.connectionMetrics.failureStreak,
            
            // 健康度
            healthScore: healthScore,
            healthStatus: healthStatus,
            lastConnectionTime: this.connectionMetrics.lastConnectionTime,
            
            // 配置
            baseDelay: this.baseDelay,
            maxDelay: this.maxDelay,
            jitterFactor: this.jitterFactor,
        };
    }
    
    /**
     * 獲取重試歷史
     * @returns {Array} 重試歷史記錄
     */
    getRetryHistory() {
        return this.retryHistory.map(record => ({
            attempt: record.attempt,
            delay: record.delay,
            timestamp: record.timestamp.toISOString(),
            formattedTime: record.timestamp.toLocaleTimeString('zh-TW')
        }));
    }
    
    /**
     * 生成重連建議
     * @returns {Object} 重連建議
     */
    getReconnectAdvice() {
        const summary = this.getStatusSummary();
        const advice = {
            immediate: [],
            warning: [],
            suggestion: []
        };
        
        // 立即行動建議
        if (summary.failureStreak >= 3) {
            advice.immediate.push("連續多次連接失敗，建議檢查網絡連接");
        }
        
        if (summary.healthScore < 60) {
            advice.immediate.push("連接健康度低，建議重啟應用或檢查服務器狀態");
        }
        
        // 警告
        if (summary.retryCount >= summary.maxRetries * 0.7) {
            advice.warning.push(`已重試 ${summary.retryCount} 次，接近最大重試次數`);
        }
        
        if (summary.successRate < 70) {
            advice.warning.push(`連接成功率僅 ${summary.successRate}，網絡可能不穩定`);
        }
        
        // 一般建議
        if (summary.avgReconnectTime > 5000) {
            advice.suggestion.push(`平均重連時間 ${summary.avgReconnectTime}ms 較長，考慮優化網絡`);
        }
        
        if (summary.connectionStreak >= 10) {
            advice.suggestion.push(`已連續成功連接 ${summary.connectionStreak} 次，連接穩定`);
        }
        
        return advice;
    }
    
    /**
     * 導出為JSON（用於調試）
     * @returns {string} JSON字符串
     */
    toJSON() {
        return JSON.stringify({
            config: {
                baseDelay: this.baseDelay,
                maxDelay: this.maxDelay,
                maxRetries: this.maxRetries,
                jitterFactor: this.jitterFactor,
                enableJitter: this.enableJitter
            },
            status: this.getStatusSummary(),
            retryHistory: this.getRetryHistory(),
            advice: this.getReconnectAdvice()
        }, null, 2);
    }
    
    /**
     * 從JSON恢復狀態
     * @param {string} jsonString JSON字符串
     */
    fromJSON(jsonString) {
        try {
            const data = JSON.parse(jsonString);
            
            // 恢復配置（可選）
            if (data.config) {
                this.baseDelay = data.config.baseDelay || this.baseDelay;
                this.maxDelay = data.config.maxDelay || this.maxDelay;
                this.maxRetries = data.config.maxRetries || this.maxRetries;
                this.jitterFactor = data.config.jitterFactor || this.jitterFactor;
                this.enableJitter = data.config.enableJitter !== false;
            }
            
            console.log("📥 從JSON恢復重連管理器狀態");
            return true;
        } catch (error) {
            console.error("❌ 從JSON恢復狀態失敗:", error);
            return false;
        }
    }
}

/**
 * WebSocket增強連接器
 * 封裝WebSocket連接，集成重連管理器
 */
class EnhancedWebSocketConnector {
    /**
     * 創建增強WebSocket連接器
     * @param {string} url WebSocket URL
     * @param {Object} options 配置選項
     */
    constructor(url, options = {}) {
        this.url = url;
        this.options = options;
        
        // 重連管理器
        this.reconnectManager = new WebSocketReconnectManager(options.reconnectOptions);
        
        // WebSocket實例
        this.websocket = null;
        
        // 事件監聽器
        this.eventListeners = {
            open: [],
            message: [],
            error: [],
            close: [],
            reconnect: [],
            healthChange: []
        };
        
        // 連接狀態
        this.connectionState = {
            isConnected: false,
            isConnecting: false,
            lastError: null,
            connectionStartTime: null,
            lastMessageTime: null,
            messageCount: 0
        };
        
        // 心跳配置
        this.heartbeatConfig = {
            enabled: options.heartbeatEnabled !== false,
            interval: options.heartbeatInterval || 30000, // 30秒
            timeout: options.heartbeatTimeout || 10000,   // 10秒
            lastPingTime: null,
            lastPongTime: null,
            pingTimeoutId: null
        };
        
        console.log(`🔌 增強WebSocket連接器創建: ${url}`);
    }
    
    /**
     * 連接WebSocket
     */
    connect() {
        if (this.connectionState.isConnecting || this.connectionState.isConnected) {
            console.log("ℹ️ 已在連接或已連接，跳過");
            return;
        }
        
        this.connectionState.isConnecting = true;
        this.connectionState.connectionStartTime = new Date();
        this.connectionState.lastError = null;
        
        try {
            console.log(`🔗 連接WebSocket: ${this.url}`);
            this.websocket = new WebSocket(this.url);
            
            // 設置事件監聽器
            this.websocket.onopen = this._handleOpen.bind(this);
            this.websocket.onmessage = this._handleMessage.bind(this);
            this.websocket.onerror = this._handleError.bind(this);
            this.websocket.onclose = this._handleClose.bind(this);
            
        } catch (error) {
            console.error("❌ 創建WebSocket失敗:", error);
            this._handleConnectionFailure(error.message);
        }
    }
    
    /**
     * 斷開WebSocket連接
     * @param {number} code 關閉代碼
     * @param {string} reason 關閉原因
     */
    disconnect(code = 1000, reason = "正常關閉") {
        if (this.websocket) {
            console.log(`🔌 手動斷開WebSocket連接: ${reason}`);
            this.websocket.close(code, reason);
        }
        
        // 清理心跳
        this._stopHeartbeat();
        
        // 重置狀態
        this.connectionState.isConnected = false;
        this.connectionState.isConnecting = false;
        this.reconnectManager.reset();
    }
    
    /**
     * 發送消息
     * @param {any} data 要發送的數據
     * @returns {boolean} 是否成功發送
     */
    send(data) {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            console.warn("⚠️ WebSocket未連接，無法發送消息");
            return false;
        }
        
        try {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.websocket.send(message);
            this.connectionState.messageCount++;
            return true;
        } catch (error) {
            console.error("❌ 發送消息失敗:", error);
            return false;
        }
    }
    
    /**
     * 添加事件監聽器
     * @param {string} event 事件名稱
     * @param {Function} callback 回調函數
     */
    addEventListener(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
    }
    
    /**
     * 移除事件監聽器
     * @param {string} event 事件名稱
     * @param {Function} callback 要移除的回調函數
     */
    removeEventListener(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }
    
    /**
     * 獲取連接狀態
     * @returns {Object} 連接狀態
     */
    getConnectionStatus() {
        const readyStateMap = {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSING',
            3: 'CLOSED'
        };
        
        const readyState = this.websocket ? this.websocket.readyState : 3;
        
        return {
            url: this.url,
            readyState: readyState,
            readyStateText: readyStateMap[readyState],
            isConnected: this.connectionState.isConnected,
            isConnecting: this.connectionState.isConnecting,
            connectionDuration: this.connectionState.connectionStartTime 
                ? new Date() - this.connectionState.connectionStartTime 
                : 0,
            messageCount: this.connectionState.messageCount,
            lastMessageTime: this.connectionState.lastMessageTime,
            lastError: this.connectionState.lastError,
            reconnectStatus: this.reconnectManager.getStatusSummary(),
            heartbeat: {
                enabled: this.heartbeatConfig.enabled,
                lastPingTime: this.heartbeatConfig.lastPingTime,
                lastPongTime: this.heartbeatConfig.lastPongTime,
                pingLatency: this.heartbeatConfig.lastPingTime && this.heartbeatConfig.lastPongTime
                    ? this.heartbeatConfig.lastPongTime - this.heartbeatConfig.lastPingTime
                    : null
            }
        };
    }
    
    /**
     * 處理WebSocket打開事件
     * @param {Event} event 打開事件
     * @private
     */
    _handleOpen(event) {
        console.log("✅ WebSocket連接成功");
        
        this.connectionState.isConnected = true;
        this.connectionState.isConnecting = false;
        this.connectionState.lastError = null;
        
        // 記錄連接成功
        this.reconnectManager.recordConnectionSuccess();
        
        // 開始心跳
        if (this.heartbeatConfig.enabled) {
            this._startHeartbeat();
        }
        
        // 觸發事件監聽器
        this._triggerEvent('open', event);
        this._triggerEvent('healthChange', { healthScore: this.reconnectManager.getHealthScore() });
    }
    
    /**
     * 處理WebSocket消息事件
     * @param {MessageEvent} event 消息事件
     * @private
     */
    _handleMessage(event) {
        this.connectionState.lastMessageTime = new Date();
        
        try {
            // 解析消息
            let data;
            if (typeof event.data === 'string') {
                data = JSON.parse(event.data);
            } else {
                data = event.data;
            }
            
            // 處理心跳回應
            if (data.type === 'pong') {
                this._handlePong(data);
                return;
            }
            
            // 觸發消息事件監聽器
            this._triggerEvent('message', { data: data, originalEvent: event });
            
        } catch (error) {
            console.error("❌ 處理WebSocket消息失敗:", error);
        }
    }
    
    /**
     * 處理WebSocket錯誤事件
     * @param {Event} event 錯誤事件
     * @private
     */
    _handleError(event) {
        console.error("❌ WebSocket錯誤:", event);
        
        this.connectionState.lastError = event;
        this.reconnectManager.recordConnectionFailure("WebSocket錯誤");
        
        // 觸發事件監聽器
        this._triggerEvent('error', event);
        this._triggerEvent('healthChange', { healthScore: this.reconnectManager.getHealthScore() });
    }
    
    /**
     * 處理WebSocket關閉事件
     * @param {CloseEvent} event 關閉事件
     * @private
     */
    _handleClose(event) {
        console.log(`🔌 WebSocket連接關閉: code=${event.code}, reason=${event.reason}`);
        
        this.connectionState.isConnected = false;
        this.connectionState.isConnecting = false;
        
        // 停止心跳
        this._stopHeartbeat();
        
        // 觸發關閉事件監聽器
        this._triggerEvent('close', event);
        
        // 如果不是正常關閉，嘗試重連
        if (event.code !== 1000 && this.reconnectManager.shouldRetry()) {
            this._scheduleReconnect();
        }
    }
    
    /**
     * 處理連接失敗
     * @param {string} reason 失敗原因
     * @private
     */
    _handleConnectionFailure(reason) {
        console.error(`❌ 連接失敗: ${reason}`);
        
        this.connectionState.isConnecting = false;
        this.connectionState.lastError = new Error(reason);
        this.reconnectManager.recordConnectionFailure(reason);
        
        // 觸發事件監聽器
        this._triggerEvent('error', new Error(reason));
        this._triggerEvent('healthChange', { healthScore: this.reconnectManager.getHealthScore() });
        
        // 嘗試重連
        if (this.reconnectManager.shouldRetry()) {
            this._scheduleReconnect();
        }
    }
    
    /**
     * 安排重連
     * @private
     */
    _scheduleReconnect() {
        const delay = this.reconnectManager.startRetry();
        
        if (delay > 0) {
            console.log(`⏰ ${delay}ms後嘗試重新連接...`);
            
            // 觸發重連事件
            this._triggerEvent('reconnect', {
                attempt: this.reconnectManager.retryCount,
                delay: delay,
                maxRetries: this.reconnectManager.maxRetries
            });
            
            // 設置定時器重連
            setTimeout(() => {
                if (!this.connectionState.isConnected && !this.connectionState.isConnecting) {
                    this.connect();
                }
            }, delay);
        }
    }
    
    /**
     * 開始心跳
     * @private
     */
    _startHeartbeat() {
        if (!this.heartbeatConfig.enabled) return;
        
        // 清理現有心跳
        this._stopHeartbeat();
        
        // 設置定期心跳
        this.heartbeatConfig.intervalId = setInterval(() => {
            this._sendPing();
        }, this.heartbeatConfig.interval);
        
        // 立即發送第一次心跳
        setTimeout(() => this._sendPing(), 1000);
    }
    
    /**
     * 停止心跳
     * @private
     */
    _stopHeartbeat() {
        if (this.heartbeatConfig.intervalId) {
            clearInterval(this.heartbeatConfig.intervalId);
            this.heartbeatConfig.intervalId = null;
        }
        
        if (this.heartbeatConfig.pingTimeoutId) {
            clearTimeout(this.heartbeatConfig.pingTimeoutId);
            this.heartbeatConfig.pingTimeoutId = null;
        }
    }
    
    /**
     * 發送ping消息
     * @private
     */
    _sendPing() {
        if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        const pingMessage = {
            type: 'ping',
            timestamp: new Date().toISOString()
        };
        
        if (this.send(pingMessage)) {
            this.heartbeatConfig.lastPingTime = new Date();
            
            // 設置超時檢測
            this.heartbeatConfig.pingTimeoutId = setTimeout(() => {
                console.warn("⚠️ 心跳超時，未收到pong回應");
                this._handleHeartbeatTimeout();
            }, this.heartbeatConfig.timeout);
        }
    }
    
    /**
     * 處理pong回應
     * @param {Object} data pong數據
     * @private
     */
    _handlePong(data) {
        if (this.heartbeatConfig.pingTimeoutId) {
            clearTimeout(this.heartbeatConfig.pingTimeoutId);
            this.heartbeatConfig.pingTimeoutId = null;
        }
        
        this.heartbeatConfig.lastPongTime = new Date();
        
        const latency = this.heartbeatConfig.lastPingTime
            ? this.heartbeatConfig.lastPongTime - this.heartbeatConfig.lastPingTime
            : 0;
            
        console.debug(`❤️ 收到pong回應，延遲: ${latency}ms`);
    }
    
    /**
     * 處理心跳超時
     * @private
     */
    _handleHeartbeatTimeout() {
        console.warn("⚠️ 心跳超時，可能連接已斷開");
        
        // 記錄連接失敗
        this.reconnectManager.recordConnectionFailure("心跳超時");
        
        // 觸發健康度變化事件
        this._triggerEvent('healthChange', { 
            healthScore: this.reconnectManager.getHealthScore(),
            reason: 'heartbeat_timeout'
        });
        
        // 如果WebSocket仍然顯示為連接狀態，嘗試關閉它
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.close(1001, "心跳超時");
        }
    }
    
    /**
     * 觸發事件監聽器
     * @param {string} event 事件名稱
     * @param {any} data 事件數據
     * @private
     */
    _triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ 執行事件監聽器 ${event} 失敗:`, error);
                }
            });
        }
    }
    
    /**
     * 導出連接狀態為JSON
     * @returns {string} JSON字符串
     */
    toJSON() {
        return JSON.stringify({
            url: this.url,
            connectionState: this.connectionState,
            reconnectManager: this.reconnectManager.getStatusSummary(),
            heartbeatConfig: this.heartbeatConfig,
            options: this.options
        }, null, 2);
    }
}

// 全局導出
if (typeof window !== 'undefined') {
    window.WebSocketReconnectManager = WebSocketReconnectManager;
    window.EnhancedWebSocketConnector = EnhancedWebSocketConnector;
}

console.log("✅ WebSocket重連管理器加載完成");
