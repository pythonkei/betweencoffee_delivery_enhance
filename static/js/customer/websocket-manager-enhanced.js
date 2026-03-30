// static/js/customer/websocket-manager-enhanced.js
/**
 * 顧客端增強WebSocket管理器
 * 基於員工端增強WebSocket管理器，保持顧客端API兼容性
 * 實現智能重連、心跳檢測、連接監控等增強功能
 */

class CustomerEnhancedWebSocketManager {
    /**
     * 創建顧客端增強WebSocket管理器
     * @param {string} orderId 訂單ID
     * @param {Object} options 配置選項
     */
    constructor(orderId, options = {}) {
        this.orderId = orderId;
        this.options = this._mergeOptions(options);
        
        console.log(`🔄 初始化顧客增強WebSocket管理器，訂單ID: ${orderId}`);
        
        // 回調函數存儲（保持與舊API兼容）
        this.statusCallbacks = [];
        this.queueCallbacks = [];
        this.paymentCallbacks = [];
        this.orderReadyCallbacks = [];
        
        // 增強WebSocket連接器
        this.connector = null;
        
        // 連接狀態
        this.isConnected = false;
        this.reconnectAttempts = 0;
        
        // 初始化
        this._init();
    }
    
    /**
     * 合併配置選項
     * @private
     */
    _mergeOptions(userOptions) {
        const defaultOptions = {
            // 重連配置
            reconnect: {
                baseDelay: 1000,
                maxDelay: 30000,
                maxRetries: 10,
                jitterFactor: 0.2,
                enableJitter: true
            },
            
            // 心跳配置
            heartbeat: {
                enabled: true,
                interval: 25000,  // 25秒
                timeout: 10000    // 10秒
            },
            
            // 監控配置
            monitoring: {
                enabled: true,
                showIndicator: true,
                logLevel: 'info'
            },
            
            // 顧客端專用配置
            customer: {
                autoConnect: true,
                showNotifications: true,
                playSounds: false,
                notificationDuration: 5000
            }
        };
        
        // 深度合併配置
        return this._deepMerge(defaultOptions, userOptions);
    }
    
    /**
     * 深度合併對象
     * @private
     */
    _deepMerge(target, source) {
        const result = { ...target };
        
        for (const key in source) {
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this._deepMerge(result[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }
        
        return result;
    }
    
    /**
     * 初始化WebSocket連接
     * @private
     */
    _init() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/order/${this.orderId}/`;
            
            console.log(`🔗 創建增強WebSocket連接: ${wsUrl}`);
            
            // 創建增強WebSocket連接器
            this.connector = new EnhancedWebSocketConnector(wsUrl, {
                reconnectOptions: this.options.reconnect,
                heartbeatEnabled: this.options.heartbeat.enabled,
                heartbeatInterval: this.options.heartbeat.interval,
                heartbeatTimeout: this.options.heartbeat.timeout
            });
            
            // 設置事件監聽器
            this._setupEventListeners();
            
            // 自動連接（如果配置為true）
            if (this.options.customer.autoConnect) {
                this.connect();
            }
            
            // 顯示連接狀態指示器（如果配置為true）
            if (this.options.monitoring.showIndicator) {
                this._createConnectionIndicator();
            }
            
            console.log('✅ 顧客增強WebSocket管理器初始化完成');
            
        } catch (error) {
            console.error('❌ 初始化顧客增強WebSocket管理器失敗:', error);
            this._handleError(error);
        }
    }
    
    /**
     * 設置事件監聽器
     * @private
     */
    _setupEventListeners() {
        if (!this.connector) return;
        
        // WebSocket打開事件
        this.connector.addEventListener('open', (event) => {
            console.log('✅ 顧客WebSocket連接成功');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this._showConnectionStatus(true);
            this._sendInitialMessage();
        });
        
        // WebSocket消息事件
        this.connector.addEventListener('message', (event) => {
            this._handleEnhancedMessage(event.data);
        });
        
        // WebSocket錯誤事件
        this.connector.addEventListener('error', (error) => {
            console.error('❌ 顧客WebSocket錯誤:', error);
            this.isConnected = false;
            this._showConnectionStatus(false);
            this._handleError(error);
        });
        
        // WebSocket關閉事件
        this.connector.addEventListener('close', (event) => {
            console.log(`❌ 顧客WebSocket連接關閉: ${event.code} - ${event.reason}`);
            this.isConnected = false;
            this._showConnectionStatus(false);
        });
        
        // 重連事件
        this.connector.addEventListener('reconnect', (data) => {
            this.reconnectAttempts = data.attempt;
            console.log(`🔄 嘗試重連 (${data.attempt}/${data.maxRetries})，延遲: ${data.delay}ms`);
            this._updateReconnectStatus(data.attempt, data.maxRetries, data.delay);
        });
        
        // 健康度變化事件
        this.connector.addEventListener('healthChange', (data) => {
            this._updateConnectionQuality(data.healthScore);
        });
    }
    
    /**
     * 處理增強消息
     * @private
     */
    _handleEnhancedMessage(data) {
        try {
            console.log('📨 顧客收到增強消息:', data.type, data);
            
            // 支持多種消息類型格式
            switch(data.type) {
                case 'order_status_update':
                case 'order_status':
                    this._handleStatusUpdate(data);
                    break;
                    
                case 'queue_position_update':
                case 'queue_position':
                    this._handleQueueUpdate(data);
                    break;
                    
                case 'payment_status_update':
                case 'payment_status':
                    this._handlePaymentUpdate(data);
                    break;
                    
                case 'order_ready_notification':
                case 'order_ready':
                    this._handleOrderReady(data);
                    break;
                    
                case 'heartbeat':
                case 'pong':
                    // 心跳回應，無需特殊處理
                    break;
                    
                case 'welcome':
                    console.log('👋 收到歡迎消息:', data.message);
                    break;
                    
                default:
                    console.log('❓ 未知的顧客消息類型:', data.type, data);
            }
            
        } catch (error) {
            console.error('❌ 解析顧客消息失敗:', error, data);
        }
    }
    
    /**
     * 處理狀態更新
     * @private
     */
    _handleStatusUpdate(data) {
        console.log(`🔄 訂單狀態更新:`, data);
        
        // 提取狀態數據
        let statusData = data;
        if (data.type === 'order_status' && data.data) {
            statusData = data.data;
        }
        
        const status = statusData.status || data.status;
        console.log(`📊 最終狀態: ${status}`);
        
        // 執行所有回調函數（保持與舊API兼容）
        this.statusCallbacks.forEach(callback => {
            try {
                callback(statusData);
            } catch (error) {
                console.error('狀態回調執行失敗:', error);
            }
        });
        
        // 更新UI
        this._updateStatusUI(statusData);
    }
    
    /**
     * 處理隊列更新
     * @private
     */
    _handleQueueUpdate(data) {
        console.log(`🔄 隊列位置更新: ${data.position}`);
        
        // 執行所有回調函數（保持與舊API兼容）
        this.queueCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('隊列回調執行失敗:', error);
            }
        });
        
        // 更新UI
        this._updateQueueUI(data);
    }
    
    /**
     * 處理支付更新
     * @private
     */
    _handlePaymentUpdate(data) {
        console.log(`💰 支付狀態更新: ${data.payment_status}`);
        
        // 執行所有回調函數（保持與舊API兼容）
        this.paymentCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('支付回調執行失敗:', error);
            }
        });
        
        // 更新UI
        this._updatePaymentUI(data);
    }
    
    /**
     * 處理訂單就緒
     * @private
     */
    _handleOrderReady(data) {
        console.log(`✅ 訂單就緒通知: ${data.order_id}`);
        
        // 執行所有回調函數（保持與舊API兼容）
        this.orderReadyCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('訂單就緒回調執行失敗:', error);
            }
        });
        
        // 顯示通知
        if (this.options.customer.showNotifications) {
            this._showNotification(
                `✅ 您的訂單已準備就緒！取餐碼: ${data.pickup_code || ''}`,
                'success'
            );
        }
        
        // 播放提示音
        if (this.options.customer.playSounds) {
            this._playNotificationSound();
        }
        
        // 更新UI
        this._updateOrderReadyUI(data);
    }
    
    /**
     * 發送初始消息
     * @private
     */
    _sendInitialMessage() {
        if (this.connector && this.isConnected) {
            const message = {
                type: 'handshake',
                order_id: this.orderId,
                user_type: 'customer',
                timestamp: new Date().toISOString(),
            };
            this.connector.send(message);
            console.log('🤝 發送顧客握手消息');
        }
    }
    
    /**
     * 顯示連接狀態
     * @private
     */
    _showConnectionStatus(connected) {
        const indicator = document.getElementById('websocket-status-indicator');
        if (indicator) {
            if (connected) {
                indicator.innerHTML = '<i class="fas fa-circle text-success"></i> 實時更新已連接';
                indicator.className = 'websocket-status connected';
            } else {
                indicator.innerHTML = '<i class="fas fa-circle text-danger"></i> 連接中斷';
                indicator.className = 'websocket-status disconnected';
            }
        }
    }
    
    /**
     * 更新重連狀態
     * @private
     */
    _updateReconnectStatus(attempt, maxAttempts, delay) {
        const indicator = document.getElementById('websocket-status-indicator');
        if (indicator && !this.isConnected) {
            const seconds = Math.round(delay / 1000);
            indicator.innerHTML = `
                <i class="fas fa-sync fa-spin"></i> 
                重連中 (${attempt}/${maxAttempts})
                <span class="badge badge-light ml-1">${seconds}秒</span>
            `;
        }
    }
    
    /**
     * 更新連接質量
     * @private
     */
    _updateConnectionQuality(healthScore) {
        const indicator = document.getElementById('websocket-status-indicator');
        if (indicator && this.isConnected) {
            let statusClass = 'connected';
            let statusText = '實時連接';
            
            if (healthScore < 50) {
                statusClass = 'connected-poor';
                statusText = '連線品質不佳';
            } else if (healthScore < 80) {
                statusClass = 'connected-fair';
                statusText = '連線一般';
            }
            
            indicator.className = `websocket-status ${statusClass}`;
            indicator.innerHTML = `
                <i class="fas fa-circle"></i> 
                ${statusText}
                <span class="badge badge-light ml-1">${healthScore}分</span>
            `;
        }
    }
    
    /**
     * 創建連接狀態指示器
     * @private
     */
    _createConnectionIndicator() {
        let indicator = document.getElementById('websocket-connection-indicator-customer');
        
        if (!indicator && this.options.monitoring.showIndicator) {
            indicator = document.createElement('div');
            indicator.id = 'websocket-connection-indicator-customer';
            indicator.className = 'websocket-indicator-customer';
            indicator.style.cssText = `
                position: fixed;
                bottom: 50px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 20px;
                font-size: 12px;
                z-index: 9998;
                background: rgba(0,0,0,0.8);
                color: white;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                cursor: pointer;
                transition: all 0.3s ease;
                max-width: 200px;
            `;
            
            // 添加點擊事件，顯示詳細資訊
            indicator.addEventListener('click', () => {
                this._showConnectionDetails();
            });
            
            document.body.appendChild(indicator);
        }
        
        return indicator;
    }
    
    /**
     * 顯示連線詳細資訊
     * @private
     */
    _showConnectionDetails() {
        if (!this.connector) return;
        
        const status = this.connector.getConnectionStatus();
        const details = `
            顧客WebSocket 連線詳情
            ═══════════════════════
            訂單ID: ${this.orderId}
            連線狀態: ${this.isConnected ? '✅ 已連線' : '❌ 離線'}
            連線品質: ${status.reconnectStatus.healthScore}分
            平均延遲: ${status.heartbeat.pingLatency || 'N/A'}ms
            
            重連次數: ${this.reconnectAttempts}次
            訊息數量: ${status.messageCount}條
            
            WebSocket狀態: ${status.readyStateText}
            最後訊息: ${status.lastMessageTime ? new Date(status.lastMessageTime).toLocaleTimeString() : '無'}
            
            ⏱️ 最後更新: ${new Date().toLocaleTimeString()}
        `;
        
        this._showNotification(details, 'info', 8000);
    }
    
    /**
     * 顯示通知
     * @private
     */
    _showNotification(message, type = 'info', duration = null) {
        if (!this.options.customer.showNotifications) return;
        
        const actualDuration = duration || this.options.customer.notificationDuration;
        
        const notification = document.createElement('div');
        notification.className = `customer-websocket-notification ${type}`;
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
            z-index: 9997;
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
        }, actualDuration);
    }
    
    /**
     * 播放通知聲音
     * @private
     */
    _playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('音頻播放失敗:', e));
        } catch (error) {
            // 忽略音頻錯誤
        }
    }
    
    /**
     * 處理錯誤
     * @private
     */
    _handleError(error) {
        console.error('❌ 顧客WebSocket錯誤處理:', error);
        
        if (this.options.customer.showNotifications) {
            this._showNotification(
                `WebSocket連接錯誤: ${error.message || '未知錯誤'}`,
                'error'
            );
        }
    }
    
    // ==================== 公共API（保持與舊API兼容） ====================
    
    /**
     * 連接WebSocket
     */
    connect() {
        if (this.connector) {
            this.connector.connect();
        }
    }
    
    /**
     * 斷開WebSocket連接
     */
    disconnect() {
        if (this.connector) {
            this.connector.disconnect(1000, 'manual_disconnect');
        }
        this.isConnected = false;
        this._showConnectionStatus(false);
    }
    
    /**
     * 重新連接WebSocket
     */
    reconnect() {
        console.log('🔄 手動重新連接顧客WebSocket');
        this.disconnect();
        setTimeout(() => {
            this.connect();
        }, 500);
    }
    
    /**
     * 註冊狀態更新回調（保持與舊API兼容）
     * @param {Function} callback 回調函數
     * @returns {Function} 取消註冊函數
     */
    onStatusUpdate(callback) {
        this.statusCallbacks.push(callback);
        return () => {
            const index = this.statusCallbacks.indexOf(callback);
            if (index > -1) this.statusCallbacks.splice(index, 1);
        };
    }
    
    /**
     * 註冊隊列更新回調（保持與舊API兼容）
     * @param {Function} callback 回調函數
     * @returns {Function} 取消註冊函數
     */
    onQueueUpdate(callback) {
        this.queueCallbacks.push(callback);
        return () => {
            const index = this.queueCallbacks.indexOf(callback);
            if (index > -1) this.queueCallbacks.splice(index, 1);
        };
    }
    
    /**
     * 註冊支付更新回調（保持與舊API兼容）
     * @param {Function} callback 回調函數
     * @returns {Function} 取消註冊函數
     */
    onPaymentUpdate(callback) {
        this.paymentCallbacks.push(callback);
        return () => {
            const index = this.paymentCallbacks.indexOf(callback);
            if (index > -1) this.paymentCallbacks.splice(index, 1);
        };
    }
    
    /**
     * 註冊訂單就緒回調（新增功能）
     * @param {Function} callback 回調函數
     * @returns {Function} 取消註冊函數
     */
    onOrderReady(callback) {
        this.orderReadyCallbacks.push(callback);
        return () => {
            const index = this.orderReadyCallbacks.indexOf(callback);
            if (index > -1) this.orderReadyCallbacks.splice(index, 1);
        };
    }
    
    /**
     * 發送消息
     * @param {any} data 要發送的數據
     * @returns {boolean} 是否成功發送
     */
    send(data) {
        if (this.connector) {
            return this.connector.send(data);
        }
        return false;
    }
    
    /**
     * 獲取連接狀態
     * @returns {Object} 連接狀態
     */
    getConnectionStatus() {
        if (this.connector) {
            return this.connector.getConnectionStatus();
        }
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            orderId: this.orderId
        };
    }
    
    /**
     * 清理資源
     */
    cleanup() {
        this.disconnect();
        this.statusCallbacks = [];
        this.queueCallbacks = [];
        this.paymentCallbacks = [];
        this.orderReadyCallbacks = [];
        this.connector = null;
        console.log('🧹 顧客增強WebSocket管理器已清理');
    }
    
    // ==================== UI更新方法（保持與舊API兼容） ====================
    
    /**
     * 更新狀態UI
     * @private
     */
    _updateStatusUI(data) {
        const statusElement = document.getElementById('order-status-display');
        if (statusElement) {
            statusElement.textContent = this._getStatusText(data.status);
            statusElement.className = `status-badge ${this._getStatusClass(data.status)}`;
        }
        
        const progressElement = document.getElementById('order-progress');
        if (progressElement) {
            const progress = this._calculateProgress(data.status);
            progressElement.style.width = `${progress}%`;
            progressElement.setAttribute('aria-valuenow', progress);
        }
    }
    
    /**
     * 更新隊列UI
     * @private
     */
    _updateQueueUI(data) {
        const queueElement = document.getElementById('queue-position');
        if (queueElement && data.position) {
            queueElement.textContent = `隊列位置: ${data.position}`;
        }
        
        const waitElement = document.getElementById('estimated-wait');
        if (waitElement && data.estimated_time) {
            waitElement.textContent = `預計等待: ${data.estimated_time}`;
        }
    }
    
    /**
     * 更新支付UI
     * @private
     */
    _updatePaymentUI(data) {
        const paymentElement = document.getElementById('payment-status');
        if (paymentElement) {
            paymentElement.textContent = this._getPaymentStatusText(data.payment_status);
            paymentElement.className = `payment-status ${this._getPaymentStatusClass(data.payment_status)}`;
        }
    }
    
    /**
     * 更新訂單就緒UI
     * @private
     */
    _updateOrderReadyUI(data) {
        // 更新訂單狀態為就緒
        this._updateStatusUI({ status: 'ready' });
        
        // 顯示取餐信息
        const pickupInfo = document.getElementById('pickup-info');
        if (pickupInfo) {
            pickupInfo.innerHTML = `
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> 訂單已準備就緒！</h5>
                    <p>取餐碼: <strong class="h4">${data.pickup_code || '請詢問店員'}</strong></p>
                    <p>請前往櫃檯提取您的訂單</p>
                </div>
            `;
        }
    }
    
    // ==================== 輔助方法（保持與舊API兼容） ====================
    
    /**
     * 獲取狀態文本
     * @private
     */
    _getStatusText(status) {
        const statusMap = {
            'pending': '待支付',
            'waiting': '等待製作',
            'preparing': '製作中',
            'ready': '已就緒',
            'completed': '已完成',
            'cancelled': '已取消',
        };
        return statusMap[status] || status;
    }
    
    /**
     * 獲取狀態類名
     * @private
     */
    _getStatusClass(status) {
        const classMap = {
            'pending': 'badge-secondary',
            'waiting': 'badge-warning',
            'preparing': 'badge-info',
            'ready': 'badge-success',
            'completed': 'badge-primary',
            'cancelled': 'badge-danger',
        };
        return classMap[status] || 'badge-secondary';
    }
    
    /**
     * 計算進度
     * @private
     */
    _calculateProgress(status) {
        const progressMap = {
            'pending': 10,
            'waiting': 25,
            'preparing': 60,
            'ready': 90,
            'completed': 100,
            'cancelled': 0,
        };
        return progressMap[status] || 0;
    }
    
    /**
     * 獲取支付狀態文本
     * @private
     */
    _getPaymentStatusText(status) {
        const statusMap = {
            'pending': '待支付',
            'paid': '已支付',
            'failed': '支付失敗',
            'cancelled': '已取消',
        };
        return statusMap[status] || status;
    }
    
    /**
     * 獲取支付狀態類名
     * @private
     */
    _getPaymentStatusClass(status) {
        const classMap = {
            'pending': 'text-warning',
            'paid': 'text-success',
            'failed': 'text-danger',
            'cancelled': 'text-secondary',
        };
        return classMap[status] || 'text-secondary';
    }
}

// ==================== 全局註冊和兼容性層 ====================

if (typeof window !== 'undefined') {
    // 導出增強管理器
    window.CustomerEnhancedWebSocketManager = CustomerEnhancedWebSocketManager;
    
    // 兼容性層：如果舊API被調用，使用增強版本
    const originalCustomerWebSocketManager = window.CustomerWebSocketManager;
    
    // 創建兼容性包裝器
    window.CustomerWebSocketManager = function(orderId) {
        console.log('🔄 使用增強版顧客WebSocket管理器（兼容模式）');
        
        // 創建增強管理器實例
        const enhancedManager = new CustomerEnhancedWebSocketManager(orderId, {
            customer: {
                showNotifications: false, // 兼容模式下關閉通知
                playSounds: false
            }
        });
        
        // 返回兼容性包裝對象
        return {
            // 保持原有API
            onStatusUpdate: (callback) => enhancedManager.onStatusUpdate(callback),
            onQueueUpdate: (callback) => enhancedManager.onQueueUpdate(callback),
            onPaymentUpdate: (callback) => enhancedManager.onPaymentUpdate(callback),
            disconnect: () => enhancedManager.disconnect(),
            cleanup: () => enhancedManager.cleanup(),
            
            // 內部引用（用於調試）
            _enhancedManager: enhancedManager
        };
    };
    
    // 保留對原始管理器的引用
    window.CustomerWebSocketManager.Original = originalCustomerWebSocketManager;
    window.CustomerWebSocketManager.Enhanced = CustomerEnhancedWebSocketManager;
    
    console.log('✅ 顧客增強WebSocket管理器加載完成，兼容性層已啟用');
}

// CSS動畫定義
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .websocket-status {
        transition: all 0.3s ease;
    }
    
    .websocket-status.connected {
        color: #28a745;
    }
    
    .websocket-status.connected-poor {
        color: #ffc107;
    }
    
    .websocket-status.connected-fair {
        color: #fd7e14;
    }
    
    .websocket-status.disconnected {
        color: #dc3545;
    }
    
    .customer-websocket-notification {
        animation: slideIn 0.3s ease-out;
    }
`;
document.head.appendChild(style);

console.log('🎉 顧客端增強WebSocket管理器實現完成');
