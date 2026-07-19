// static/js/staff-order-management/websocket-manager.js
// ==================== WebSocket連接管理器 - 精簡版 ====================
//
// 功能：專注於 WebSocket 通訊和業務邏輯處理
// - 橋接 WebSocketCore，處理員工頁面業務訊息
// - 訊息分發與監聽
// - 連線品質監控
// - 離線訊息佇列
//
// 已移除（由基礎服務層處理）：
// - Toast 通知 → ToastService
// - 音效播放 → 由 EventBus 觸發，外部處理
// - 連接指示器 UI → 由 EventBus 觸發，外部處理
// - 自定義通知 → ToastService
//
// 依賴：
// - WebSocketCore (websocket-core.js)
// - EventBus (services/event-bus.js)
// - ToastService (services/toast-service.js)

class WebSocketManager {
    constructor() {
        console.log('🔄 初始化WebSocket管理器（精簡版）...');
        
        // ====== 連接狀態 ======
        this.isConnected = false;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        
        // ====== 連線品質監控 ======
        this.connectionQuality = {
            score: 100,
            lastLatency: 0,
            avgLatency: 0,
            latencySamples: [],
            disconnects: 0,
            reconnectSuccess: 0,
            reconnectFailed: 0
        };
        
        // ====== 離線訊息佇列 ======
        this.messageQueue = [];
        this.maxQueueSize = 100;
        this.processingQueue = false;
        
        // ====== 訊息監聽器 ======
        this.messageListeners = new Map();
        
        // 核心實例引用
        this.core = null;
        
        // 取消註冊函數列表
        this._unsubscribers = [];
        
        // 初始化
        this._init();
        
        console.log('✅ WebSocket管理器（精簡版）初始化完成');
    }
    
    /**
     * 初始化：等待 WebSocketCore 就緒
     */
    _init() {
        const core = window.wsCore || (window.WebSocketCore && WebSocketCore.getInstance());
        
        if (core) {
            this._bindToCore(core);
        } else {
            console.log('⏳ 等待 WebSocketCore 就緒...');
            const checkInterval = setInterval(() => {
                const c = window.wsCore || (window.WebSocketCore && WebSocketCore.getInstance());
                if (c) {
                    clearInterval(checkInterval);
                    this._bindToCore(c);
                }
            }, 200);
            
            // 10秒超時
            setTimeout(() => {
                clearInterval(checkInterval);
                if (!this.core) {
                    console.error('❌ WebSocketCore 初始化超時');
                }
            }, 10000);
        }
    }
    
    /**
     * 綁定到 WebSocketCore
     */
    _bindToCore(core) {
        this.core = core;
        
        // 同步核心狀態
        this.isConnected = core.state.isConnected;
        this.isConnecting = core.state.isConnecting;
        
        // 註冊核心事件監聽
        this._unsubscribers.push(
            core.on('connected', () => this._handleCoreConnected())
        );
        this._unsubscribers.push(
            core.on('disconnected', (data) => this._handleCoreDisconnected(data))
        );
        this._unsubscribers.push(
            core.on('reconnecting', (data) => this._handleCoreReconnecting(data))
        );
        this._unsubscribers.push(
            core.on('reconnect_failed', () => this._handleCoreReconnectFailed())
        );
        this._unsubscribers.push(
            core.on('message', (data) => this._handleCoreMessage(data))
        );
        this._unsubscribers.push(
            core.on('page_visible', () => this._handleCorePageVisible())
        );
        
        // 無論核心狀態如何，都同步連接狀態
        this._syncConnectionState(core.state.isConnected);
        
        console.log('✅ WebSocketManager 已綁定到 WebSocketCore');
    }
    
    // ==================== 核心事件處理 ====================
    
    _handleCoreConnected() {
        console.log('✅ WebSocketCore 已連線（橋接）');
        this._syncConnectionState(true);
        this.processMessageQueue();
        
        // 通過 EventBus 發布事件
        if (window.eventBus) {
            window.eventBus.emit('websocket:connected', {
                timestamp: new Date().toISOString(),
                reconnectCount: this.connectionQuality.reconnectSuccess
            });
        }
    }
    
    _handleCoreDisconnected(data) {
        console.log(`❌ WebSocketCore 斷線（橋接）: ${data.reason}`);
        this._syncConnectionState(false);
        
        if (window.eventBus) {
            window.eventBus.emit('websocket:disconnected', {
                code: data.code,
                reason: data.reason,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    _handleCoreReconnecting(data) {
        console.log(`🔄 WebSocketCore 重連中（橋接）: ${data.attempt}/${data.maxRetries}`);
        this.reconnectAttempts = data.attempt;
        this.isConnecting = true;
        this.isConnected = false;
        
        if (window.eventBus) {
            window.eventBus.emit('websocket:reconnecting', {
                attempt: data.attempt,
                maxRetries: data.maxRetries,
                delay: data.delay
            });
        }
    }
    
    _handleCoreReconnectFailed() {
        console.error('❌ WebSocketCore 重連失敗（橋接）');
        this.connectionQuality.reconnectFailed++;
        this.calculateConnectionScore();
        
        if (window.eventBus) {
            window.eventBus.emit('websocket:reconnect_failed', {
                attempts: this.reconnectAttempts,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    _handleCoreMessage(data) {
        // 處理 pong（延遲數據從核心獲取）
        if (data.type === 'pong') {
            if (data.client_time) {
                const latency = Date.now() - data.client_time;
                this.recordLatency(latency);
            }
            return;
        }
        
        console.log('📨 收到WebSocket訊息（橋接）:', data.type);
        
        // 觸發監聽器
        if (this.messageListeners.has(data.type)) {
            this.messageListeners.get(data.type).forEach(callback => {
                try { callback(data); } catch (error) {
                    console.error(`❌ 監聽器錯誤 (${data.type}):`, error);
                }
            });
        }
        
        // 通過 EventBus 發布原始訊息
        if (window.eventBus) {
            window.eventBus.emit(`websocket:message:${data.type}`, data);
        }
        
        // 原有訊息處理 - 使用 DebounceCoordinator 統一調度刷新
        this.handleLegacyMessage(data);
    }
    
    _handleCorePageVisible() {
        console.log('👁️ 頁面恢復可見（橋接）');
        // 由 DebounceCoordinator 統一處理
        if (window.debounceCoordinator) {
            window.debounceCoordinator.scheduleRefresh('manual', 'page_visible', {});
        }
    }
    
    /**
     * 同步連接狀態
     */
    _syncConnectionState(connected) {
        this.isConnected = connected;
        this.isConnecting = false;
        
        if (connected) {
            this.reconnectAttempts = 0;
            this.connectionQuality.reconnectSuccess++;
            this.connectionQuality.disconnects = 0;
            this.calculateConnectionScore();
        } else {
            this.connectionQuality.disconnects++;
            this.calculateConnectionScore();
        }
    }
    
    // ==================== 兼容原有 API ====================
    
    /**
     * 建立連接（兼容舊 API，實際由核心管理）
     */
    connect() {
        console.log('ℹ️ WebSocketManager.connect() - 連接由 WebSocketCore 管理');
        if (this.core) {
            this.core.connect();
        }
    }
    
    /**
     * 斷開連接（兼容舊 API）
     */
    disconnect() {
        console.log('ℹ️ WebSocketManager.disconnect() - 斷開由 WebSocketCore 管理');
        if (this.core) {
            this.core.disconnect();
        }
    }
    
    /**
     * 重新連接（兼容舊 API）
     */
    reconnect() {
        console.log('🔄 WebSocketManager.reconnect() - 重連由 WebSocketCore 管理');
        if (this.core) {
            this.core.reconnect();
        }
    }
    
    /**
     * 發送訊息（兼容舊 API）
     */
    sendMessage(message) {
        if (this.core) {
            return this.core.send(message);
        }
        return false;
    }
    
    /**
     * 發送測試訊息（兼容舊 API）
     */
    sendTestMessage(message) {
        return this.sendMessage({
            type: 'test',
            message: message,
            timestamp: new Date().toISOString(),
            client_time: Date.now()
        });
    }
    
    /**
     * 發送連接信息（兼容舊 API）
     */
    sendConnectionInfo() {
        if (this.core && this.core.state.isConnected) {
            this.core.sendJSON({
                type: 'connect',
                user_type: 'staff',
                user_id: this.getUserId(),
                timestamp: new Date().toISOString()
            });
        }
    }
    
    /**
     * 發送 ping（兼容舊 API，由核心管理）
     */
    sendPing() {
        // 由核心管理
    }
    
    /**
     * 發送 pong（兼容舊 API，由核心管理）
     */
    sendPong() {
        // 由核心管理
    }
    
    // ==================== 保留的業務邏輯 ====================
    
    /**
     * 記錄延遲數據
     */
    recordLatency(latency) {
        this.connectionQuality.lastLatency = latency;
        this.connectionQuality.latencySamples.push(latency);
        if (this.connectionQuality.latencySamples.length > 10) {
            this.connectionQuality.latencySamples.shift();
        }
        const sum = this.connectionQuality.latencySamples.reduce((a, b) => a + b, 0);
        this.connectionQuality.avgLatency = Math.round(
            sum / this.connectionQuality.latencySamples.length
        );
        this.calculateConnectionScore();
    }
    
    /**
     * 計算連線品質分數
     */
    calculateConnectionScore() {
        let score = 100;
        if (this.connectionQuality.avgLatency > 0) {
            if (this.connectionQuality.avgLatency > 1000) score -= 30;
            else if (this.connectionQuality.avgLatency > 500) score -= 15;
            else if (this.connectionQuality.avgLatency > 200) score -= 5;
        }
        score -= Math.min(30, this.connectionQuality.disconnects * 10);
        score -= Math.min(20, this.connectionQuality.reconnectFailed * 5);
        this.connectionQuality.score = Math.max(0, Math.min(100, score));
        return this.connectionQuality.score;
    }
    
    /**
     * 將訊息加入佇列
     */
    queueMessage(message) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            this.messageQueue.shift();
        }
        this.messageQueue.push({
            message: message,
            timestamp: Date.now(),
            attempts: 0
        });
        console.log(`📦 訊息已加入佇列，當前佇列大小: ${this.messageQueue.length}`);
    }
    
    /**
     * 處理訊息佇列
     */
    async processMessageQueue() {
        if (this.processingQueue || this.messageQueue.length === 0 || !this.isConnected) {
            return;
        }
        
        this.processingQueue = true;
        console.log(`🔄 開始處理訊息佇列，共 ${this.messageQueue.length} 條訊息`);
        
        const failedMessages = [];
        
        while (this.messageQueue.length > 0) {
            const queuedMessage = this.messageQueue.shift();
            
            if (Date.now() - queuedMessage.timestamp > 300000) {
                continue;
            }
            
            queuedMessage.attempts++;
            if (queuedMessage.attempts > 3) {
                continue;
            }
            
            try {
                const success = this.sendMessage(queuedMessage.message);
                if (!success) {
                    failedMessages.push(queuedMessage);
                    await this.delay(100 * queuedMessage.attempts);
                }
            } catch (error) {
                console.error('❌ 處理佇列訊息失敗:', error);
                failedMessages.push(queuedMessage);
            }
        }
        
        failedMessages.forEach(msg => this.messageQueue.unshift(msg));
        this.processingQueue = false;
        
        console.log(`✅ 訊息佇列處理完成，剩餘: ${this.messageQueue.length} 條`);
    }
    
    // ==================== 事件監聽系統 ====================
    
    on(messageType, callback) {
        if (!this.messageListeners.has(messageType)) {
            this.messageListeners.set(messageType, []);
        }
        this.messageListeners.get(messageType).push(callback);
        return () => this.off(messageType, callback);
    }
    
    off(messageType, callback) {
        if (this.messageListeners.has(messageType)) {
            const listeners = this.messageListeners.get(messageType);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    // ==================== 訊息處理 ====================
    
    handleWebSocketMessage(event) {
        // 由核心處理
    }
    
    /**
     * 處理舊版訊息格式
     * 所有數據刷新統一交由 DebounceCoordinator 調度
     */
    handleLegacyMessage(data) {
        // 使用 DebounceCoordinator 統一調度刷新
        if (window.debounceCoordinator) {
            window.debounceCoordinator.scheduleRefresh('websocket', data.type, data);
        }
        
        switch(data.type) {
            case 'queue_update':
                this.handleQueueUpdate(data);
                break;
            case 'order_update':
                this.handleOrderUpdate(data);
                break;
            case 'new_order':
                this.handleNewOrder(data);
                break;
            case 'order_ready':
                this.handleOrderReady(data);
                break;
            case 'order_collected':
                this.handleOrderCollected(data);
                break;
            case 'payment_update':
                this.handlePaymentUpdate(data);
                break;
            case 'system_message':
                this.handleSystemMessage(data);
                break;
            case 'ping':
                break;
            default:
                this.handleGenericUpdate(data);
        }
    }
    
    /**
     * 處理隊列更新
     * 🔧 修復：收到 queue_update 後觸發 UnifiedDataManager 重新加載數據
     */
    handleQueueUpdate(data) {
        console.log('📊 隊列更新:', data);
        if (data.message && window.toast) {
            window.toast.info(`📊 ${data.message}`);
        }
        
        // 🔧 修復：觸發統一數據管理器重新加載，確保員工端即時顯示新訂單
        if (window.unifiedDataManager) {
            console.log('🔄 隊列更新，觸發統一數據重新加載');
            window.unifiedDataManager.loadUnifiedData(true);
        }
    }
    
    /**
     * 處理訂單更新
     */
    handleOrderUpdate(data) {
        console.log('📝 訂單更新:', data);
        const orderId = data.order_id || data.id;
        if (orderId && data.status && window.toast) {
            const statusMap = {
                'waiting': '等待中',
                'preparing': '製作中',
                'ready': '已就緒',
                'completed': '已提取'
            };
            const statusText = statusMap[data.status] || data.status;
            window.toast.info(`📝 訂單 #${orderId} 狀態更新: ${statusText}`);
        }
    }
    
    /**
     * 處理新訂單
     */
    handleNewOrder(data) {
        console.log('🆕 新訂單:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            if (window.toast) {
                window.toast.success(`🆕 新訂單 #${orderId} 已創建`);
            }
            // 通過 EventBus 觸發音效播放
            if (window.eventBus) {
                window.eventBus.emit('sound:play', { frequency: 660, duration: 0.3, volume: 0.2 });
            }
        }
    }
    
    /**
     * 處理訂單就緒
     */
    handleOrderReady(data) {
        console.log('✅ 訂單就緒:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            if (window.toast) {
                window.toast.success(`✅ 訂單 #${orderId} 已就緒，等待取餐`);
            }
            if (window.eventBus) {
                window.eventBus.emit('sound:play', { frequency: 880, duration: 0.3, volume: 0.3 });
            }
        }
    }
    
    /**
     * 處理訂單已提取
     */
    handleOrderCollected(data) {
        console.log('📦 訂單已提取:', data);
        const orderId = data.order_id || data.id;
        if (orderId && window.toast) {
            window.toast.info(`📦 訂單 #${orderId} 已提取`);
        }
    }
    
    /**
     * 處理支付更新
     */
    handlePaymentUpdate(data) {
        console.log('💳 支付更新:', data);
        const orderId = data.order_id || data.id;
        if (orderId && window.toast) {
            const status = data.payment_status || data.status;
            window.toast.info(`💳 訂單 #${orderId} 支付狀態: ${status}`);
        }
    }
    
    /**
     * 處理系統訊息
     */
    handleSystemMessage(data) {
        console.log('🔔 系統訊息:', data);
        const message = data.message || data.text || '系統訊息';
        const level = data.level || 'info';
        if (window.toast) {
            const toastMethod = level === 'error' ? 'error' : 
                               level === 'warning' ? 'warning' : 'info';
            window.toast[toastMethod](`🔔 ${message}`);
        }
    }
    
    /**
     * 處理通用更新
     */
    handleGenericUpdate(data) {
        console.log('🔄 通用更新:', data);
    }
    
    getUserId() {
        const userMeta = document.querySelector('meta[name="user-id"]');
        if (userMeta) {
            return userMeta.getAttribute('content');
        }
        if (window.currentUserId) {
            return window.currentUserId;
        }
        return 'unknown';
    }
    
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            readyState: this.core ? (this.core.socket ? this.core.socket.readyState : null) : null,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts,
            connectionQuality: { ...this.connectionQuality },
            messageQueueSize: this.messageQueue.length,
            lastPongTime: this.core?.heartbeat?.lastPongTime 
                ? new Date(this.core.heartbeat.lastPongTime).toLocaleTimeString() 
                : 'N/A'
        };
    }
    
    clearMessageQueue() {
        const queueSize = this.messageQueue.length;
        this.messageQueue = [];
        console.log(`🗑️ 訊息佇列已清空，共 ${queueSize} 條訊息`);
        if (window.toast) {
            window.toast.info(`📦 已清空 ${queueSize} 條待發送訊息`);
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// 暴露到全局
if (typeof window !== 'undefined') {
    window.WebSocketManager = WebSocketManager;
}
