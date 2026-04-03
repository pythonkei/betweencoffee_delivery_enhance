// static/js/websocket-monitoring-adapter.js
// WebSocket監控適配器 - 整合現有WebSocket連接器和健康度監控

/**
 * WebSocket監控適配器
 * 將現有WebSocket連接器與健康度監控系統整合
 */
class WebSocketMonitoringAdapter {
    /**
     * 創建WebSocket監控適配器
     * @param {Object} websocketConnector 現有WebSocket連接器實例
     * @param {Object} options 配置選項
     */
    constructor(websocketConnector, options = {}) {
        if (!websocketConnector) {
            throw new Error('WebSocket連接器實例是必需的');
        }
        
        this.websocketConnector = websocketConnector;
        this.options = this._mergeOptions(options);
        
        // 創建健康度監控器
        this.healthMonitor = new WebSocketHealthMonitorEnhanced({
            enableDetailedMonitoring: true,
            enableHealthScoring: true,
            enableAlerts: true,
            debugMode: this.options.debugMode,
            logLevel: this.options.logLevel
        });
        
        // 監聽器引用（用於清理）
        this.eventListeners = new Map();
        
        // 初始化適配器
        this._initializeAdapter();
        
        console.log("🔌 WebSocket監控適配器初始化完成");
    }
    
    /**
     * 合併配置選項
     * @private
     */
    _mergeOptions(userOptions) {
        const defaultOptions = {
            // 監控配置
            monitorConnectionEvents: true,
            monitorMessageEvents: true,
            monitorErrorEvents: true,
            monitorReconnectEvents: true,
            
            // 自動化配置
            autoStartMonitoring: true,
            autoStopMonitoring: true,
            
            // 事件監聽配置
            interceptOriginalEvents: true,
            
            // 調試配置
            debugMode: false,
            logLevel: 'info'
        };
        
        return { ...defaultOptions, ...userOptions };
    }
    
    /**
     * 初始化適配器
     * @private
     */
    _initializeAdapter() {
        // 記錄連接開始
        this.healthMonitor.recordConnectionStart();
        
        // 設置事件監聽器
        this._setupEventListeners();
        
        // 設置原始連接器的事件攔截
        if (this.options.interceptOriginalEvents) {
            this._interceptOriginalEvents();
        }
        
        // 設置自定義事件監聽
        this._setupCustomEventListeners();
    }
    
    /**
     * 設置事件監聽器
     * @private
     */
    _setupEventListeners() {
        // 監聽WebSocket原生事件
        if (this.websocketConnector.ws) {
            this._attachWebSocketListeners(this.websocketConnector.ws);
        }
        
        // 監聽連接器自定義事件
        this._attachConnectorListeners();
    }
    
    /**
     * 附加WebSocket原生事件監聽器
     * @private
     */
    _attachWebSocketListeners(websocket) {
        if (!websocket) return;
        
        const listeners = {
            open: (event) => this._handleWebSocketOpen(event),
            message: (event) => this._handleWebSocketMessage(event),
            error: (event) => this._handleWebSocketError(event),
            close: (event) => this._handleWebSocketClose(event)
        };
        
        // 附加監聽器
        for (const [eventType, handler] of Object.entries(listeners)) {
            websocket.addEventListener(eventType, handler);
            this.eventListeners.set(`${eventType}_${websocket.url}`, {
                target: websocket,
                type: eventType,
                handler: handler
            });
        }
    }
    
    /**
     * 附加連接器自定義事件監聽器
     * @private
     */
    _attachConnectorListeners() {
        // 檢查連接器是否有事件發射器模式
        if (typeof this.websocketConnector.on === 'function') {
            // 如果連接器使用EventEmitter模式
            this._attachEventEmitterListeners();
        } else if (typeof this.websocketConnector.addEventListener === 'function') {
            // 如果連接器使用標準事件監聽器
            this._attachStandardListeners();
        } else {
            console.warn('⚠️ WebSocket連接器不支持標準事件監聽，部分監控功能可能受限');
        }
    }
    
    /**
     * 附加EventEmitter風格監聽器
     * @private
     */
    _attachEventEmitterListeners() {
        const eventsToMonitor = [
            'connect', 'disconnect', 'reconnect', 'message', 'error'
        ];
        
        eventsToMonitor.forEach(eventName => {
            const handler = (data) => this._handleConnectorEvent(eventName, data);
            this.websocketConnector.on(eventName, handler);
            
            this.eventListeners.set(`connector_${eventName}`, {
                target: this.websocketConnector,
                type: eventName,
                handler: handler
            });
        });
    }
    
    /**
     * 附加標準事件監聽器
     * @private
     */
    _attachStandardListeners() {
        const eventsToMonitor = [
            'open', 'close', 'message', 'error'
        ];
        
        eventsToMonitor.forEach(eventName => {
            const handler = (event) => this._handleStandardEvent(eventName, event);
            this.websocketConnector.addEventListener(eventName, handler);
            
            this.eventListeners.set(`connector_${eventName}`, {
                target: this.websocketConnector,
                type: eventName,
                handler: handler
            });
        });
    }
    
    /**
     * 攔截原始事件
     * @private
     */
    _interceptOriginalEvents() {
        // 保存原始方法
        const originalSend = this.websocketConnector.send;
        const originalClose = this.websocketConnector.close;
        
        // 攔截send方法
        if (typeof originalSend === 'function') {
            this.websocketConnector.send = (data) => {
                this._handleBeforeSend(data);
                const result = originalSend.call(this.websocketConnector, data);
                this._handleAfterSend(data);
                return result;
            };
        }
        
        // 攔截close方法
        if (typeof originalClose === 'function') {
            this.websocketConnector.close = (code, reason) => {
                this._handleBeforeClose(code, reason);
                const result = originalClose.call(this.websocketConnector, code, reason);
                this._handleAfterClose(code, reason);
                return result;
            };
        }
    }
    
    /**
     * 設置自定義事件監聽
     * @private
     */
    _setupCustomEventListeners() {
        // 監聽健康度監控器的事件
        document.addEventListener('websocket:alert', (event) => {
            this._handleHealthMonitorAlert(event.detail);
        });
        
        document.addEventListener('websocket:monitoring_data', (event) => {
            this._handleMonitoringData(event.detail);
        });
        
        document.addEventListener('websocket:final_report', (event) => {
            this._handleFinalReport(event.detail);
        });
    }
    
    /**
     * 處理WebSocket打開事件
     * @private
     */
    _handleWebSocketOpen(event) {
        if (this.options.debugMode) {
            console.debug('🔗 WebSocket連接已打開', event);
        }
        
        // 記錄連接成功
        this.healthMonitor.recordConnectionStart();
    }
    
    /**
     * 處理WebSocket消息事件
     * @private
     */
    _handleWebSocketMessage(event) {
        const messageSize = event.data ? event.data.length || 0 : 0;
        const receiveTime = Date.now();
        
        // 計算消息延遲（如果可能）
        let latency = 0;
        if (event.timeStamp) {
            latency = receiveTime - event.timeStamp;
        }
        
        // 記錄消息接收
        this.healthMonitor.recordMessageReceived(event.data, messageSize, latency);
        
        if (this.options.debugMode) {
            console.debug('📥 WebSocket消息接收', {
                size: messageSize,
                latency: latency,
                data: typeof event.data === 'string' ? event.data.substring(0, 100) : '[binary data]'
            });
        }
    }
    
    /**
     * 處理WebSocket錯誤事件
     * @private
     */
    _handleWebSocketError(event) {
        console.error('❌ WebSocket錯誤', event);
        
        // 記錄錯誤
        this.healthMonitor.recordError(
            'websocket_error',
            'WebSocket連接錯誤',
            {
                type: event.type,
                timeStamp: event.timeStamp,
                target: event.target ? event.target.constructor.name : 'unknown'
            }
        );
    }
    
    /**
     * 處理WebSocket關閉事件
     * @private
     */
    _handleWebSocketClose(event) {
        console.log('🔌 WebSocket連接已關閉', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean
        });
        
        // 記錄連接結束
        const reason = event.wasClean ? 'normal' : 'error';
        this.healthMonitor.recordConnectionEnd(reason);
    }
    
    /**
     * 處理連接器事件
     * @private
     */
    _handleConnectorEvent(eventName, data) {
        switch (eventName) {
            case 'connect':
                this.healthMonitor.recordConnectionStart();
                break;
                
            case 'disconnect':
                this.healthMonitor.recordConnectionEnd('disconnect');
                break;
                
            case 'reconnect':
                if (data && typeof data === 'object') {
                    this.healthMonitor.recordReconnect(
                        data.attempt || 1,
                        data.delay || 0,
                        data.success || false
                    );
                }
                break;
                
            case 'message':
                if (data) {
                    const messageSize = JSON.stringify(data).length;
                    this.healthMonitor.recordMessageReceived(data, messageSize);
                }
                break;
                
            case 'error':
                this.healthMonitor.recordError(
                    'connector_error',
                    '連接器錯誤',
                    data
                );
                break;
        }
        
        if (this.options.debugMode) {
            console.debug(`🔔 連接器事件: ${eventName}`, data);
        }
    }
    
    /**
     * 處理標準事件
     * @private
     */
    _handleStandardEvent(eventName, event) {
        // 轉發到相應的處理器
        switch (eventName) {
            case 'open':
                this._handleWebSocketOpen(event);
                break;
            case 'message':
                this._handleWebSocketMessage(event);
                break;
            case 'error':
                this._handleWebSocketError(event);
                break;
            case 'close':
                this._handleWebSocketClose(event);
                break;
        }
    }
    
    /**
     * 處理發送前事件
     * @private
     */
    _handleBeforeSend(data) {
        const messageSize = data ? (typeof data === 'string' ? data.length : JSON.stringify(data).length) : 0;
        
        // 記錄消息發送
        this.healthMonitor.recordMessageSent(data, messageSize);
        
        if (this.options.debugMode) {
            console.debug('📤 WebSocket消息發送', {
                size: messageSize,
                data: typeof data === 'string' ? data.substring(0, 100) : '[binary data]'
            });
        }
    }
    
    /**
     * 處理發送後事件
     * @private
     */
    _handleAfterSend(data) {
        // 可以在這裡添加發送後的處理邏輯
    }
    
    /**
     * 處理關閉前事件
     * @private
     */
    _handleBeforeClose(code, reason) {
        console.log('🔌 準備關閉WebSocket連接', { code, reason });
    }
    
    /**
     * 處理關閉後事件
     * @private
     */
    _handleAfterClose(code, reason) {
        // 連接關閉後的處理
    }
    
    /**
     * 處理健康度監控器警報
     * @private
     */
    _handleHealthMonitorAlert(alert) {
        console.log(`🚨 健康度監控警報: ${alert.level} - ${alert.message}`);
        
        // 可以根據警報級別採取不同行動
        switch (alert.level) {
            case 'critical':
                // 嚴重警報：可能需要立即採取行動
                this._handleCriticalAlert(alert);
                break;
                
            case 'warning':
                // 警告警報：可能需要監控或記錄
                this._handleWarningAlert(alert);
                break;
                
            case 'info':
                // 信息警報：僅記錄
                this._handleInfoAlert(alert);
                break;
        }
    }
    
    /**
     * 處理嚴重警報
     * @private
     */
    _handleCriticalAlert(alert) {
        // 嚴重警報處理邏輯
        // 例如：嘗試重新連接、通知用戶等
        
        if (this.websocketConnector.reconnect) {
            console.log('🔄 觸發嚴重警報，嘗試重新連接...');
            this.websocketConnector.reconnect();
        }
    }
    
    /**
     * 處理警告警報
     * @private
     */
    _handleWarningAlert(alert) {
        // 警告警報處理邏輯
        // 例如：記錄日誌、調整配置等
        
        console.warn('⚠️ 警告警報處理:', alert.message);
    }
    
    /**
     * 處理信息警報
     * @private
     */
    _handleInfoAlert(alert) {
        // 信息警報處理邏輯
        console.info('ℹ️ 信息警報:', alert.message);
    }
    
    /**
     * 處理監控數據
     * @private
     */
    _handleMonitoringData(data) {
        // 可以將監控數據發送到服務器或存儲
        if (this.options.debugMode) {
            console.debug('📊 監控數據處理:', data);
        }
        
        // 這裡可以實現數據上報邏輯
        // this._sendMonitoringDataToServer(data);
    }
    
    /**
     * 處理最終報告
     * @private
     */
    _handleFinalReport(report) {
        console.log('📋 連接最終報告已生成:', report.connectionId);
        
        // 可以將最終報告存儲或發送
        // this._storeFinalReport(report);
    }
    
    /**
     * 發送監控數據到服務器
     * @private
     */
    async _sendMonitoringDataToServer(data) {
        try {
            const response = await fetch('/api/websocket-monitoring/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            if (!response.ok) {
                console.error('❌ 監控數據上報失敗:', response.status);
            }
        } catch (error) {
            console.error('❌ 監控數據上報錯誤:', error);
        }
    }
    
    /**
     * 獲取健康度監控器實例
     */
    getHealthMonitor() {
        return this.healthMonitor;
    }
    
    /**
     * 獲取當前健康度評分
     */
    getHealthScore() {
        return this.healthMonitor.healthScore;
    }
    
    /**
     * 獲取監控摘要
     */
    getMonitoringSummary() {
        return this.healthMonitor.getMonitoringSummary();
    }
    
    /**
     * 手動觸發健康度檢查
     */
    checkHealth() {
        return this.healthMonitor.calculateHealthScore();
    }
    
    /**
     * 手動觸發數據上報
     */
    reportData() {
        this.healthMonitor.reportMonitoringData();
    }
    
    /**
     * 清理適配器
     */
    cleanup() {
        // 清理健康度監控器
        this.healthMonitor.cleanup();
        
        // 移除所有事件監聽器
        this._removeAllEventListeners();
        
        // 恢復原始方法
        this._restoreOriginalMethods();
        
        console.log('🧹 WebSocket監控適配器清理完成');
    }
    
    /**
     * 移除所有事件監聽器
     * @private
     */
    _removeAllEventListeners() {
        for (const [key, listener] of this.eventListeners.entries()) {
            try {
                if (listener.target && listener.target.removeEventListener) {
                    listener.target.removeEventListener(listener.type, listener.handler);
                } else if (listener.target && listener.target.off) {
                    listener.target.off(listener.type, listener.handler);
                }
            } catch (error) {
                console.warn(`⚠️ 移除事件監聽器失敗: ${key}`, error);
            }
        }
        
        this.eventListeners.clear();
    }
    
    /**
     * 恢復原始方法
     * @private
     */
    _restoreOriginalMethods() {
        // 注意：這裡需要根據實際情況實現
        // 由於我們是直接修改了原始對象的方法，這裡應該恢復它們
        // 但為了簡單起見，我們暫時不實現這個功能
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.WebSocketMonitoringAdapter = WebSocketMonitoringAdapter;
    console.log('✅ WebSocket監控適配器已註冊到全局');
}

// 導出適配器工廠函數
if (typeof window !== 'undefined') {
    window.createWebSocketMonitoringAdapter = (websocketConnector, options) => {
        return new WebSocketMonitoringAdapter(websocketConnector, options);
    };
}