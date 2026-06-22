// static/js/staff-order-management/websocket-manager.js
// ==================== WebSocket連接管理器 - 橋接版（基於 WebSocketCore） ====================
//
// 此版本已遷移到 WebSocketCore 統一核心，不再自行建立 WebSocket 連接。
// 所有連接管理、心跳、重連、離線佇列等功能由 WebSocketCore 統一處理。
// 此管理器專注於員工頁面的業務邏輯：處理隊列更新、訂單通知等。
//
// 遷移日期: 2026-06-18
// 最後更新: 2026-06-21 - 修復雙重刷新路徑，統一使用 DebounceCoordinator

class WebSocketManager {
    constructor() {
        console.log('🔄 初始化WebSocket管理器（橋接版）...');
        
        // ====== 連接狀態（從核心獲取） ======
        this.isConnected = false;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        
        // ====== 連線品質監控（從核心獲取） ======
        this.connectionQuality = {
            score: 100,
            lastLatency: 0,
            avgLatency: 0,
            latencySamples: [],
            disconnects: 0,
            reconnectSuccess: 0,
            reconnectFailed: 0
        };
        
        // ====== 離線訊息佇列（本地備份） ======
        this.messageQueue = [];
        this.maxQueueSize = 100;
        this.processingQueue = false;
        
        // ====== 訊息監聽器 ======
        this.messageListeners = new Map();
        
        // 連接狀態元素
        this.connectionIndicator = null;
        
        // 核心實例引用
        this.core = null;
        
        // 取消註冊函數列表
        this._unsubscribers = [];
        
        // 初始化
        this._init();
        
        // 添加防抖屬性
        this.refreshTimeouts = new Map();
        this.lastRefreshTime = 0;
        this.minRefreshInterval = 1000;
        
        console.log('✅ WebSocket管理器橋接版初始化完成');
    }
    
    /**
     * 初始化：等待 WebSocketCore 就緒
     */
    _init() {
        const core = window.wsCore || WebSocketCore.getInstance();
        
        if (core) {
            this._bindToCore(core);
        } else {
            console.log('⏳ 等待 WebSocketCore 就緒...');
            const checkInterval = setInterval(() => {
                const c = window.wsCore || WebSocketCore.getInstance();
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
        
        // 無論核心狀態如何，都顯示連接指示器
        this._syncConnectionState(core.state.isConnected);
        
        console.log('✅ WebSocketManager 已綁定到 WebSocketCore');
    }
    
    // ==================== 核心事件處理 ====================
    
    _handleCoreConnected() {
        console.log('✅ WebSocketCore 已連線（橋接）');
        this._syncConnectionState(true);
        this.processMessageQueue();
        this.triggerEvent('websocket_connected', {
            timestamp: new Date().toISOString(),
            reconnectCount: this.connectionQuality.reconnectSuccess
        });
    }
    
    _handleCoreDisconnected(data) {
        console.log(`❌ WebSocketCore 斷線（橋接）: ${data.reason}`);
        this._syncConnectionState(false);
        this.triggerEvent('websocket_disconnected', {
            code: data.code,
            reason: data.reason,
            timestamp: new Date().toISOString()
        });
    }
    
    _handleCoreReconnecting(data) {
        console.log(`🔄 WebSocketCore 重連中（橋接）: ${data.attempt}/${data.maxRetries}`);
        this.reconnectAttempts = data.attempt;
        this.isConnecting = true;
        this.isConnected = false;
        // WebSocketCore 返回的 delay 已是毫秒單位
        this.updateReconnectStatus(data.attempt, data.delay);
    }
    
    _handleCoreReconnectFailed() {
        console.error('❌ WebSocketCore 重連失敗（橋接）');
        this.connectionQuality.reconnectFailed++;
        this.calculateConnectionScore();
        this.showPermanentDisconnect();
        this.triggerEvent('websocket_reconnect_failed', {
            attempts: this.reconnectAttempts,
            timestamp: new Date().toISOString()
        });
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
        
        this.showConnectionStatus(connected);
    }
    
    // ==================== 兼容原有 API ====================
    
    /**
     * 建立連接（兼容舊 API，實際由核心管理）
     */
    connect() {
        console.log('ℹ️ WebSocketManager.connect() - 連接由 WebSocketCore 管理');
        if (this.core) {
            this.core.connect();
        } else {
            console.warn('⚠️ WebSocketCore 未就緒，無法連接');
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
     * 發送 ping（兼容舊 API）
     */
    sendPing() {
        // 由核心管理，此處不做操作
    }
    
    /**
     * 發送 pong（兼容舊 API）
     */
    sendPong() {
        // 由核心管理，此處不做操作
    }
    
    // ==================== 原有方法保持不變 ====================
    
    /**
     * 嘗試重連（兼容舊 API，實際由核心管理）
     */
    attemptReconnect() {
        console.log('ℹ️ 重連由 WebSocketCore 管理');
        if (this.core) {
            this.core.reconnect();
        }
    }
    
    /**
     * 設置心跳（兼容舊 API，實際由核心管理）
     */
    setupHeartbeat() {
        // 由核心管理
    }
    
    /**
     * 檢查心跳（兼容舊 API）
     */
    checkHeartbeat() {
        // 由核心管理
    }
    
    /**
     * 設置頁面可見性處理器（兼容舊 API，實際由核心管理）
     */
    setupVisibilityHandler() {
        // 由核心管理
    }
    
    handlePageHidden() {
        // 由核心管理
    }
    
    handlePageVisible() {
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
        this.updateConnectionQuality();
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
        this.triggerEvent('websocket_queue_updated', {
            queueSize: this.messageQueue.length
        });
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
        this.triggerEvent('websocket_queue_processed', {
            remaining: this.messageQueue.length
        });
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
    
    triggerEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail: {
                ...detail,
                timestamp: new Date().toISOString(),
                connectionQuality: this.connectionQuality
            },
            bubbles: true
        });
        document.dispatchEvent(event);
        console.log(`📢 觸發事件: ${eventName}`, detail);
    }
    
    // ==================== 訊息處理（修復版） ====================
    
    handleWebSocketMessage(event) {
        // 由核心處理
    }
    
    /**
     * 處理舊版訊息格式 - 修復版
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
     * 處理隊列更新 - 顯示 Toast 通知
     */
    handleQueueUpdate(data) {
        console.log('📊 隊列更新:', data);
        // 隊列數據已由 UnifiedDataManager 處理，此處只做通知
        if (data.message) {
            this.showToast(`📊 ${data.message}`, 'info');
        }
    }
    
    /**
     * 處理訂單更新 - 顯示 Toast 通知
     */
    handleOrderUpdate(data) {
        console.log('📝 訂單更新:', data);
        const orderId = data.order_id || data.id;
        if (orderId && data.status) {
            const statusMap = {
                'waiting': '等待中',
                'preparing': '製作中',
                'ready': '已就緒',
                'completed': '已提取'
            };
            const statusText = statusMap[data.status] || data.status;
            this.showToast(`📝 訂單 #${orderId} 狀態更新: ${statusText}`, 'info');
        }
    }
    
    /**
     * 處理新訂單 - 顯示通知並播放音效
     */
    handleNewOrder(data) {
        console.log('🆕 新訂單:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            this.showToast(`🆕 新訂單 #${orderId} 已創建`, 'success');
            this.playSound(660, 0.3, 0.2); // 高音提示
        }
    }
    
    /**
     * 處理訂單就緒 - 顯示通知並播放音效
     */
    handleOrderReady(data) {
        console.log('✅ 訂單就緒:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            this.showToast(`✅ 訂單 #${orderId} 已就緒，等待取餐`, 'success');
            this.playSound(880, 0.3, 0.3); // 更高音提示
        }
    }
    
    /**
     * 處理訂單已提取 - 顯示通知
     */
    handleOrderCollected(data) {
        console.log('📦 訂單已提取:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            this.showToast(`📦 訂單 #${orderId} 已提取`, 'info');
        }
    }
    
    /**
     * 處理支付更新 - 顯示通知
     */
    handlePaymentUpdate(data) {
        console.log('💳 支付更新:', data);
        const orderId = data.order_id || data.id;
        if (orderId) {
            const status = data.payment_status || data.status;
            this.showToast(`💳 訂單 #${orderId} 支付狀態: ${status}`, 'info');
        }
    }
    
    /**
     * 處理系統訊息 - 顯示通知
     */
    handleSystemMessage(data) {
        console.log('🔔 系統訊息:', data);
        const message = data.message || data.text || '系統訊息';
        const level = data.level || 'info';
        this.showToast(`🔔 ${message}`, level);
    }
    
    /**
     * 處理通用更新
     */
    handleGenericUpdate(data) {
        console.log('🔄 通用更新:', data);
        // 通用更新只觸發數據刷新，不顯示通知
    }
    
    /**
     * 觸發統一數據刷新 - 已棄用，改用 DebounceCoordinator
     * @deprecated
     */
    triggerUnifiedDataRefresh() {
        // 已棄用：統一由 DebounceCoordinator 調度
        console.log('ℹ️ triggerUnifiedDataRefresh 已棄用，由 DebounceCoordinator 管理');
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
    
    // ==================== UI 方法 ====================
    
    showConnectionStatus(connected) {
        if (!this.connectionIndicator) {
            this.connectionIndicator = this.createConnectionIndicator();
        }
        
        if (connected) {
            let statusClass = 'connected';
            let statusText = '實時連接';
            
            if (this.connectionQuality.score < 50) {
                statusClass = 'connected-poor';
                statusText = '連線品質不佳';
            } else if (this.connectionQuality.score < 80) {
                statusClass = 'connected-fair';
                statusText = '連線一般';
            }
            
            this.connectionIndicator.className = `websocket-indicator ${statusClass}`;
            this.connectionIndicator.innerHTML = `
                <i class="fas fa-circle"></i> 
                ${statusText}
                <span class="badge badge-light ml-1">${this.connectionQuality.avgLatency}ms</span>
            `;
            
            this.connectionIndicator.title = `WebSocket連接正常
延遲: ${this.connectionQuality.avgLatency}ms
品質分數: ${this.connectionQuality.score}分
訊息佇列: ${this.messageQueue.length}條`;
            
        } else {
            this.connectionIndicator.className = 'websocket-indicator disconnected';
            this.connectionIndicator.innerHTML = `
                <i class="fas fa-circle"></i> 
                連接中斷
                ${this.reconnectAttempts > 0 ? 
                    `<span class="badge badge-warning ml-1">重連中 ${this.reconnectAttempts}/${this.maxReconnectAttempts}</span>` : 
                    ''}
            `;
            this.connectionIndicator.title = 'WebSocket連接中斷，嘗試重連中...';
        }
    }
    
    showPermanentDisconnect() {
        if (!this.connectionIndicator) {
            this.connectionIndicator = this.createConnectionIndicator();
        }
        
        this.connectionIndicator.className = 'websocket-indicator disconnected-permanent';
        this.connectionIndicator.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i> 
            連線失敗
            <button class="btn btn-xs btn-light ml-2" onclick="window.webSocketManager?.reconnect()">
                重試
            </button>
        `;
        this.connectionIndicator.title = '無法連接到WebSocket伺服器，請檢查網路或手動重試';
    }
    
    updateReconnectStatus(attempt, delay) {
        if (!this.connectionIndicator) return;
        
        const seconds = Math.round(delay / 1000);
        this.connectionIndicator.innerHTML = `
            <i class="fas fa-sync fa-spin"></i> 
            重連中 (${attempt}/${this.maxReconnectAttempts})
            <span class="badge badge-light ml-1">${seconds}秒</span>
        `;
    }
    
    updateConnectionQuality() {
        if (!this.connectionIndicator || !this.isConnected) return;
        
        this.connectionIndicator.title = `WebSocket連接正常
延遲: ${this.connectionQuality.avgLatency}ms
品質分數: ${this.connectionQuality.score}分
斷線次數: ${this.connectionQuality.disconnects}次
訊息佇列: ${this.messageQueue.length}條`;
    }
    
    createConnectionIndicator() {
        let indicator = document.getElementById('websocket-connection-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'websocket-connection-indicator';
            indicator.className = 'websocket-indicator';
            indicator.style.cssText = `
                position: fixed;
                bottom: 10px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 12px;
                z-index: 9999;
                background: rgba(0,0,0,0.8);
                color: white;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                cursor: pointer;
                transition: all 0.3s ease;
            `;
            
            indicator.addEventListener('click', () => {
                this.showConnectionDetails();
            });
            
            document.body.appendChild(indicator);
        }
        
        return indicator;
    }
    
    showConnectionDetails() {
        const details = `
            WebSocket 連線詳情
            ═══════════════════
            連線狀態: ${this.isConnected ? '✅ 已連線' : '❌ 離線'}
            連線品質: ${this.connectionQuality.score}分
            平均延遲: ${this.connectionQuality.avgLatency}ms
            最後延遲: ${this.connectionQuality.lastLatency}ms
            
            重連次數: ${this.connectionQuality.reconnectSuccess}次成功 / ${this.connectionQuality.reconnectFailed}次失敗
            斷線次數: ${this.connectionQuality.disconnects}次
            
            訊息佇列: ${this.messageQueue.length}條待發送
            
            ⏱️ 最後更新: ${new Date().toLocaleTimeString()}
        `;
        
        this.showNotification(details, 'info', 8000);
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
        this.showNotification(`📦 已清空 ${queueSize} 條待發送訊息`, 'info');
    }
    
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `websocket-notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 12px 18px;
            border-radius: 8px;
            background: ${type === 'success' ? '#28a745' : 
                        type === 'error' ? '#dc3545' : 
                        type === 'warning' ? '#ffc107' : '#17a2b8'};
            color: ${type === 'warning' ? '#212529' : 'white'};
            z-index: 9999;
            max-width: 350px;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
            font-size: 14px;
            line-height: 1.5;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 10px;">
                <span style="flex-grow: 1; white-space: pre-line;">${message}</span>
                <button class="close-notification" style="
                    background: none; 
                    border: none; 
                    color: ${type === 'warning' ? '#212529' : 'white'}; 
                    cursor: pointer; 
                    font-size: 18px;
                    padding: 0 4px;
                    opacity: 0.8;
                ">
                    ×
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        const closeBtn = notification.querySelector('.close-notification');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
        
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(20px)';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }
    
    /**
     * 顯示 Toast 通知（使用統一的 toast-manager.js）
     */
    showToast(message, type = 'info') {
        // 防止重複顯示相同訊息
        const now = Date.now();
        const messageKey = `${message}_${type}`;
        
        if (this.recentlyShownToasts && this.recentlyShownToasts.has(messageKey)) {
            const lastShownTime = this.recentlyShownToasts.get(messageKey);
            if (now - lastShownTime < 3000) {
                console.log(`⏭️ 跳過重複訊息: ${message} (${type})`);
                return;
            }
        }
        
        if (!this.recentlyShownToasts) {
            this.recentlyShownToasts = new Map();
        }
        this.recentlyShownToasts.set(messageKey, now);
        setTimeout(() => {
            if (this.recentlyShownToasts) {
                this.recentlyShownToasts.delete(messageKey);
            }
        }, 3000);
        
        // 優先使用統一的 toast-manager.js
        if (window.toast) {
            const toastType = type === 'success' ? 'success' : 
                             type === 'error' ? 'error' : 
                             type === 'warning' ? 'warning' : 'info';
            window.toast[toastType](message);
        } else {
            this.showNotification(message, type, 3000);
        }
    }
    
    playSound(frequency, volume, duration) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(frequency || 880, audioContext.currentTime);
            
            gainNode.gain.setValueAtTime(volume || 0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + (duration || 0.3));
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + (duration || 0.3));
            
            oscillator.onended = () => audioContext.close();
        } catch (e) {
            console.debug('🔇 音效播放失敗:', e.message);
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
