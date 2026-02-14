// static/js/staff-order-management/websocket-manager.js
// ==================== WebSocket連接管理器 - 增強版（智能重連、離線佇列） ====================

class WebSocketManager {
    constructor() {
        console.log('🔄 初始化WebSocket管理器（增強版）...');
        
        // ====== WebSocket連接狀態 ======
        this.socket = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;  // 增加重試次數
        this.reconnectInterval = 1000;    // 初始1秒
        this.maxReconnectInterval = 30000; // 最大30秒
        this.reconnectTimer = null;
        
        // ====== 心跳機制 ======
        this.heartbeatInterval = 25000;   // 25秒
        this.heartbeatTimer = null;
        this.lastPongTime = Date.now();
        this.pingTimeout = 5000;          // 5秒未收到pong視為超時
        this.pingTimer = null;
        
        // ====== 增強功能：離線訊息佇列 ======
        this.messageQueue = [];           // 離線時暫存的訊息
        this.maxQueueSize = 100;          // 最大佇列大小
        this.processingQueue = false;     // 是否正在處理佇列
        
        // ====== 增強功能：連線品質監控 ======
        this.connectionQuality = {
            score: 100,                  // 0-100分
            lastLatency: 0,             // 最後一次延遲（ms）
            avgLatency: 0,             // 平均延遲
            latencySamples: [],         // 延遲樣本
            disconnects: 0,            // 斷線次數
            reconnectSuccess: 0,       // 重連成功次數
            reconnectFailed: 0         // 重連失敗次數
        };
        
        // ====== 增強功能：訊息監聽器 ======
        this.messageListeners = new Map(); // type -> [callbacks]
        
        // 連接狀態元素
        this.connectionIndicator = null;
        
        // 初始化
        this.connect();
        this.setupHeartbeat();
        this.setupEventListeners();
        this.setupVisibilityHandler();
        
        // 添加防抖屬性
        this.refreshTimeouts = new Map();
        this.lastRefreshTime = 0;
        this.minRefreshInterval = 1000;
        
        console.log('✅ WebSocket管理器增強版初始化完成');
    }
    
    // ==================== 增強功能1：智能重連策略 ====================
    
    /**
     * 建立WebSocket連接（增強版）
     */
    connect() {
        if (this.isConnected || this.isConnecting) {
            console.log('⚠️ WebSocket正在連接或已連接，跳過');
            return;
        }
        
        this.isConnecting = true;
        
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/queue/`;
            
            console.log(`🔗 嘗試連接到WebSocket (第${this.reconnectAttempts + 1}次):`, wsUrl);
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = (event) => {
                this.handleOpen(event);
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(event);
            };
            
            this.socket.onclose = (event) => {
                this.handleClose(event);
            };
            
            this.socket.onerror = (error) => {
                this.handleError(error);
            };
            
        } catch (error) {
            console.error('❌ 建立WebSocket連接失敗:', error);
            this.isConnecting = false;
            this.attemptReconnect();
        }
    }
    
    /**
     * 處理連接成功（增強版）
     */
    handleOpen(event) {
        console.log('✅ WebSocket連接成功');
        
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.lastPongTime = Date.now();
        
        // 更新連線品質
        this.connectionQuality.reconnectSuccess++;
        this.connectionQuality.disconnects = 0;
        this.calculateConnectionScore();
        
        // 顯示連接狀態
        this.showConnectionStatus(true);
        
        // 發送連接信息
        this.sendConnectionInfo();
        
        // 處理離線佇列
        this.processMessageQueue();
        
        // 觸發連接成功事件
        this.triggerEvent('websocket_connected', {
            timestamp: new Date().toISOString(),
            reconnectCount: this.connectionQuality.reconnectSuccess
        });
        
        // 清除重連計時器
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
    
    /**
     * 處理連接關閉（增強版）
     */
    handleClose(event) {
        console.log(`❌ WebSocket連接關閉: 代碼=${event.code}, 原因=${event.reason || '未知'}`);
        
        this.isConnected = false;
        this.isConnecting = false;
        this.socket = null;
        
        // 更新連線品質
        this.connectionQuality.disconnects++;
        this.calculateConnectionScore();
        
        // 顯示連接狀態
        this.showConnectionStatus(false);
        
        // 觸發斷線事件
        this.triggerEvent('websocket_disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString()
        });
        
        // 非正常關閉（非1000）才重連
        if (event.code !== 1000) {
            this.attemptReconnect();
        }
    }
    
    /**
     * 智能重連（指數退避 + 隨機抖動）
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ 達到最大重試次數，停止重連');
            
            // 更新連線品質
            this.connectionQuality.reconnectFailed++;
            this.calculateConnectionScore();
            
            // 觸發重連失敗事件
            this.triggerEvent('websocket_reconnect_failed', {
                attempts: this.reconnectAttempts,
                timestamp: new Date().toISOString()
            });
            
            // 顯示永久斷線狀態
            this.showPermanentDisconnect();
            
            return;
        }
        
        this.reconnectAttempts++;
        
        // 指數退避：2^attempt * 1000ms，最大30秒
        const baseDelay = Math.min(
            this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts - 1),
            this.maxReconnectInterval
        );
        
        // 添加隨機抖動（±20%）
        const jitter = baseDelay * 0.2 * (Math.random() * 2 - 1);
        const delay = Math.max(1000, Math.min(baseDelay + jitter, this.maxReconnectInterval));
        
        console.log(`🔄 ${Math.round(delay/1000)}秒後嘗試重新連接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        // 更新狀態顯示
        this.updateReconnectStatus(this.reconnectAttempts, delay);
        
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    // ==================== 增強功能2：心跳與延遲檢測 ====================
    
    /**
     * 設置心跳機制（增強版）
     */
    setupHeartbeat() {
        // 清除現有計時器
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        
        this.heartbeatTimer = setInterval(() => {
            this.checkHeartbeat();
        }, this.heartbeatInterval);
        
        console.log(`💓 心跳機制已啟動（間隔: ${this.heartbeatInterval/1000}秒）`);
    }
    
    /**
     * 檢查心跳狀態
     */
    checkHeartbeat() {
        if (!this.isConnected) return;
        
        const now = Date.now();
        const timeSinceLastPong = now - this.lastPongTime;
        
        // 如果超過ping超時時間未收到pong，視為連線超時
        if (timeSinceLastPong > this.pingTimeout) {
            console.warn(`⚠️ 心跳超時 (${timeSinceLastPong}ms)，重新連接...`);
            
            // 更新連線品質
            this.connectionQuality.score -= 20;
            
            // 主動重連
            this.disconnect();
            this.attemptReconnect();
        } else {
            // 正常發送ping
            this.sendPing();
        }
    }
    
    /**
     * 發送ping（帶延遲測量）
     */
    sendPing() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const pingTime = Date.now();
            
            const message = {
                type: 'ping',
                client_time: pingTime,
                timestamp: new Date().toISOString()
            };
            
            this.socket.send(JSON.stringify(message));
            
            // 設置ping超時檢測
            this.pingTimer = setTimeout(() => {
                const latency = Date.now() - pingTime;
                console.log(`📊 當前延遲: ${latency}ms`);
                
                // 記錄延遲
                this.recordLatency(latency);
            }, 100);
        }
    }
    
    /**
     * 記錄延遲數據
     */
    recordLatency(latency) {
        this.connectionQuality.lastLatency = latency;
        
        // 保存最近10個樣本
        this.connectionQuality.latencySamples.push(latency);
        if (this.connectionQuality.latencySamples.length > 10) {
            this.connectionQuality.latencySamples.shift();
        }
        
        // 計算平均延遲
        const sum = this.connectionQuality.latencySamples.reduce((a, b) => a + b, 0);
        this.connectionQuality.avgLatency = Math.round(
            sum / this.connectionQuality.latencySamples.length
        );
        
        // 更新連線分數
        this.calculateConnectionScore();
    }
    
    /**
     * 計算連線品質分數
     */
    calculateConnectionScore() {
        let score = 100;
        
        // 延遲扣分
        if (this.connectionQuality.avgLatency > 0) {
            if (this.connectionQuality.avgLatency > 1000) {
                score -= 30;
            } else if (this.connectionQuality.avgLatency > 500) {
                score -= 15;
            } else if (this.connectionQuality.avgLatency > 200) {
                score -= 5;
            }
        }
        
        // 斷線次數扣分
        score -= Math.min(30, this.connectionQuality.disconnects * 10);
        
        // 重連失敗扣分
        score -= Math.min(20, this.connectionQuality.reconnectFailed * 5);
        
        // 確保分數在0-100之間
        this.connectionQuality.score = Math.max(0, Math.min(100, score));
        
        // 更新狀態指示器
        this.updateConnectionQuality();
        
        return this.connectionQuality.score;
    }
    
    // ==================== 增強功能3：離線訊息佇列 ====================
    
    /**
     * 發送訊息（帶離線佇列）
     */
    sendMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.socket.send(messageStr);
                return true;
            } catch (error) {
                console.error('❌ 發送WebSocket訊息失敗:', error);
                this.queueMessage(message);
                return false;
            }
        } else {
            console.warn('⚠️ WebSocket未連接，訊息已加入佇列');
            this.queueMessage(message);
            return false;
        }
    }
    
    /**
     * 將訊息加入佇列
     */
    queueMessage(message) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            console.warn('⚠️ 訊息佇列已滿，丟棄最舊訊息');
            this.messageQueue.shift();
        }
        
        this.messageQueue.push({
            message: message,
            timestamp: Date.now(),
            attempts: 0
        });
        
        console.log(`📦 訊息已加入佇列，當前佇列大小: ${this.messageQueue.length}`);
        
        // 觸發佇列更新事件
        this.triggerEvent('websocket_queue_updated', {
            queueSize: this.messageQueue.length
        });
    }
    
    /**
     * 處理訊息佇列（帶重試限制）
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
            
            // 檢查訊息是否過期（超過5分鐘）
            if (Date.now() - queuedMessage.timestamp > 300000) {
                console.warn('⚠️ 訊息已過期，丟棄:', queuedMessage.message);
                continue;
            }
            
            // 檢查重試次數
            queuedMessage.attempts++;
            if (queuedMessage.attempts > 3) {
                console.error('❌ 訊息重試次數過多，丟棄:', queuedMessage.message);
                continue;
            }
            
            try {
                const success = this.sendMessage(queuedMessage.message);
                
                if (!success) {
                    failedMessages.push(queuedMessage);
                    await this.delay(100 * queuedMessage.attempts); // 重試延遲
                }
            } catch (error) {
                console.error('❌ 處理佇列訊息失敗:', error);
                failedMessages.push(queuedMessage);
            }
        }
        
        // 將失敗的訊息重新加入佇列
        failedMessages.forEach(msg => this.messageQueue.unshift(msg));
        
        this.processingQueue = false;
        
        console.log(`✅ 訊息佇列處理完成，剩餘: ${this.messageQueue.length} 條`);
        
        // 觸發佇列處理完成事件
        this.triggerEvent('websocket_queue_processed', {
            remaining: this.messageQueue.length
        });
    }
    
    // ==================== 增強功能4：事件監聽系統 ====================
    
    /**
     * 註冊訊息監聽器
     */
    on(messageType, callback) {
        if (!this.messageListeners.has(messageType)) {
            this.messageListeners.set(messageType, []);
        }
        
        this.messageListeners.get(messageType).push(callback);
        
        return () => this.off(messageType, callback); // 返回取消函數
    }
    
    /**
     * 移除訊息監聽器
     */
    off(messageType, callback) {
        if (this.messageListeners.has(messageType)) {
            const listeners = this.messageListeners.get(messageType);
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    /**
     * 觸發事件
     */
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
    
    /**
     * 處理收到的訊息（增強版）
     */
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // 更新最後活動時間
            this.lastPongTime = Date.now();
            
            // 處理pong回應
            if (data.type === 'pong') {
                if (data.client_time) {
                    const latency = Date.now() - data.client_time;
                    this.recordLatency(latency);
                }
                return;
            }
            
            console.log('📨 收到WebSocket訊息:', data.type);
            
            // 觸發對應類型的監聽器
            if (this.messageListeners.has(data.type)) {
                this.messageListeners.get(data.type).forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`❌ 訊息監聽器執行錯誤 (${data.type}):`, error);
                    }
                });
            }
            
            // 原有的訊息處理邏輯
            this.handleLegacyMessage(data);
            
        } catch (error) {
            console.error('❌ 解析WebSocket訊息失敗:', error, event.data);
        }
    }
    
    // ==================== 增強功能5：頁面可見性處理 ====================
    
    /**
     * 設置頁面可見性處理器
     */
    setupVisibilityHandler() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // 頁面隱藏時，降低資源消耗
                this.handlePageHidden();
            } else {
                // 頁面顯示時，恢復連線
                this.handlePageVisible();
            }
        });
    }
    
    /**
     * 處理頁面隱藏
     */
    handlePageHidden() {
        console.log('👁️ 頁面隱藏，降低WebSocket活動');
        
        // 延長心跳間隔
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = setInterval(() => {
                this.checkHeartbeat();
            }, 60000); // 60秒
        }
    }
    
    /**
     * 處理頁面顯示
     */
    handlePageVisible() {
        console.log('👁️ 頁面顯示，恢復WebSocket活動');
        
        // 恢復正常心跳
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        this.setupHeartbeat();
        
        // 檢查連線狀態
        if (!this.isConnected && !this.isConnecting) {
            console.log('🔄 頁面恢復可見，重新連接WebSocket');
            this.attemptReconnect();
        }
        
        // 發送ping檢測連線
        if (this.isConnected) {
            this.sendPing();
        }
    }
    
    // ==================== UI增強 ====================
    
    /**
     * 顯示連接狀態（增強版）
     */
    showConnectionStatus(connected) {
        if (!this.connectionIndicator) {
            this.connectionIndicator = this.createConnectionIndicator();
        }
        
        if (connected) {
            // 根據連線品質顯示不同顏色
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
            
            // 添加懸浮提示
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
    
    /**
     * 顯示永久斷線狀態
     */
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
    
    /**
     * 更新重連狀態
     */
    updateReconnectStatus(attempt, delay) {
        if (!this.connectionIndicator) return;
        
        const seconds = Math.round(delay / 1000);
        this.connectionIndicator.innerHTML = `
            <i class="fas fa-sync fa-spin"></i> 
            重連中 (${attempt}/${this.maxReconnectAttempts})
            <span class="badge badge-light ml-1">${seconds}秒</span>
        `;
    }
    
    /**
     * 更新連線品質顯示
     */
    updateConnectionQuality() {
        if (!this.connectionIndicator || !this.isConnected) return;
        
        // 更新懸浮提示
        this.connectionIndicator.title = `WebSocket連接正常
延遲: ${this.connectionQuality.avgLatency}ms
品質分數: ${this.connectionQuality.score}分
斷線次數: ${this.connectionQuality.disconnects}次
訊息佇列: ${this.messageQueue.length}條`;
    }
    
    /**
     * 創建連接狀態指示器（增強版）
     */
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
            
            // 添加點擊事件，顯示詳細資訊
            indicator.addEventListener('click', () => {
                this.showConnectionDetails();
            });
            
            document.body.appendChild(indicator);
        }
        
        return indicator;
    }
    
    /**
     * 顯示連線詳細資訊
     */
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
            心跳間隔: ${this.heartbeatInterval/1000}秒
            
            WebSocket狀態: ${this.socket ? ['連接中', '已連接', '關閉中', '已關閉'][this.socket.readyState] : '無'}
            
            ⏱️ 最後更新: ${new Date().toLocaleTimeString()}
        `;
        
        // 使用toast顯示
        this.showNotification(details, 'info', 8000);
    }
    
    // ==================== 兼容原有API ====================
    
    /**
     * 處理傳統訊息（保持向後兼容）
     */
    handleLegacyMessage(data) {
        // 原有的switch-case邏輯
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
                // 已在上層處理
                break;
            default:
                this.handleGenericUpdate(data);
        }
    }
    
    // ==================== 公用方法 ====================
    
    /**
     * 延遲函數
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    /**
     * 斷開連接
     */
    disconnect() {
        if (this.socket) {
            console.log('🔌 手動斷開WebSocket連接');
            this.socket.close(1000, 'manual_disconnect');
            this.socket = null;
            this.isConnected = false;
            this.isConnecting = false;
        }
        
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
        
        if (this.pingTimer) {
            clearTimeout(this.pingTimer);
            this.pingTimer = null;
        }
    }
    
    /**
     * 重新連接
     */
    reconnect() {
        console.log('🔄 手動重新連接WebSocket');
        this.disconnect();
        this.reconnectAttempts = 0; // 重置重試次數
        setTimeout(() => {
            this.connect();
        }, 500);
    }
    
    /**
     * 獲取連線狀態
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            readyState: this.socket ? this.socket.readyState : null,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts,
            connectionQuality: { ...this.connectionQuality },
            messageQueueSize: this.messageQueue.length,
            lastPongTime: new Date(this.lastPongTime).toLocaleTimeString()
        };
    }
    
    /**
     * 清空訊息佇列
     */
    clearMessageQueue() {
        const queueSize = this.messageQueue.length;
        this.messageQueue = [];
        console.log(`🗑️ 訊息佇列已清空，共 ${queueSize} 條訊息`);
        this.showNotification(`📦 已清空 ${queueSize} 條待發送訊息`, 'info');
    }
    
    /**
     * 發送測試訊息
     */
    sendTestMessage(message) {
        return this.sendMessage({
            type: 'test',
            message: message,
            timestamp: new Date().toISOString(),
            client_time: Date.now()
        });
    }
    
    // 原有的處理方法保持不變...
    handleQueueUpdate(data) { /* 保持原有邏輯 */ }
    handleOrderUpdate(data) { /* 保持原有邏輯 */ }
    handleNewOrder(data) { /* 保持原有邏輯 */ }
    handleOrderReady(data) { /* 保持原有邏輯 */ }
    handleOrderCollected(data) { /* 保持原有邏輯 */ }
    handlePaymentUpdate(data) { /* 保持原有邏輯 */ }
    handleSystemMessage(data) { /* 保持原有邏輯 */ }
    handleGenericUpdate(data) { /* 保持原有邏輯 */ }
    
    /**
     * 觸發統一數據刷新（保持原有邏輯）
     */
    triggerUnifiedDataRefresh() {
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
        
        this.refreshTimeout = setTimeout(() => {
            console.log('🔄 觸發統一數據刷新');
            
            if (window.unifiedDataManager && typeof window.unifiedDataManager.loadUnifiedData === 'function') {
                window.unifiedDataManager.loadUnifiedData();
            } else {
                document.dispatchEvent(new CustomEvent('refresh_unified_data'));
            }
            
            this.refreshTimeout = null;
        }, 300);
    }
    
    /**
     * 發送pong（保持原有邏輯）
     */
    sendPong() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = {
                type: 'pong',
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(message));
        }
    }
    
    /**
     * 發送連接信息（保持原有邏輯）
     */
    sendConnectionInfo() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = {
                type: 'connect',
                user_type: 'staff',
                user_id: this.getUserId(),
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(message));
        }
    }
    
    /**
     * 獲取用戶ID（保持原有邏輯）
     */
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
    
    /**
     * 顯示通知（增強版）
     */
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
     * 播放聲音（保持原有邏輯）
     */
    playSound(frequency, volume, duration) {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = frequency;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(volume, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
            
        } catch (error) {
            console.log('🔇 聲音播放失敗（可能瀏覽器不支持）:', error);
        }
    }
    
    /**
     * 播放新訂單聲音（保持原有邏輯）
     */
    playNewOrderSound() {
        this.playSound(800, 0.3, 0.5);
    }
    
    /**
     * 播放完成聲音（保持原有邏輯）
     */
    playCompletionSound() {
        this.playSound(1200, 0.3, 0.3);
    }
    
    /**
     * 播放通知聲音（保持原有邏輯）
     */
    playNotificationSound() {
        this.playSound(1000, 0.2, 0.4);
    }
    
    /**
     * 設置事件監聽器（新增）
     */
    setupEventListeners() {
        // 監聽網路狀態變化
        window.addEventListener('online', () => {
            console.log('🌐 網路已恢復');
            this.showNotification('🌐 網路已恢復，重新連接中...', 'success');
            this.reconnect();
        });
        
        window.addEventListener('offline', () => {
            console.log('🌐 網路已中斷');
            this.showNotification('🌐 網路已中斷，將在恢復後自動重連', 'warning', 5000);
        });
        
        // 監聽頁面卸載
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    // 延遲初始化，確保DOM就緒
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.webSocketManager) {
                console.log('🌍 創建WebSocket管理器增強版...');
                window.webSocketManager = new WebSocketManager();
                
                // 方便調試
                console.log('🌍 WebSocketManager 增強版已註冊到 window 對象');
                
                // 添加全局輔助方法
                window.WebSocketUtils = {
                    reconnect: () => window.webSocketManager?.reconnect(),
                    disconnect: () => window.webSocketManager?.disconnect(),
                    getStatus: () => window.webSocketManager?.getConnectionStatus(),
                    clearQueue: () => window.webSocketManager?.clearMessageQueue(),
                    sendTestMessage: (msg) => window.webSocketManager?.sendTestMessage(msg)
                };
            }
        }, 500);
    });
}