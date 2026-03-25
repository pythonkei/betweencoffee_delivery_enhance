// static/js/customer/websocket-manager.js
/**
 * 顧客端WebSocket管理器
 * 用於訂單詳情頁面的實時更新
 */
class CustomerWebSocketManager {
    constructor(orderId) {
        this.orderId = orderId;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        
        this.statusCallbacks = [];
        this.queueCallbacks = [];
        this.paymentCallbacks = [];
        
        this.init();
    }
    
    init() {
        console.log(`🔄 初始化顧客WebSocket，訂單ID: ${this.orderId}`);
        this.connect();
        this.setupEventListeners();
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/order/${this.orderId}/`;
            
            console.log(`🔗 連接顧客WebSocket: ${wsUrl}`);
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('✅ 顧客WebSocket連接成功');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.showConnectionStatus(true);
                this.sendInitialMessage();
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(event);
            };
            
            this.socket.onclose = (event) => {
                console.log('❌ 顧客WebSocket連接關閉:', event.code, event.reason);
                this.isConnected = false;
                this.showConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ 顧客WebSocket錯誤:', error);
                this.isConnected = false;
                this.showConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ 建立顧客WebSocket連接失敗:', error);
        }
    }
    
    sendInitialMessage() {
        if (this.isConnected) {
            const message = {
                type: 'handshake',
                order_id: this.orderId,
                user_type: 'customer',
                timestamp: new Date().toISOString(),
            };
            this.socket.send(JSON.stringify(message));
            console.log('🤝 發送顧客握手消息');
        }
    }
    
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 顧客收到消息:', data.type, data);
            
            // 支持多種消息類型格式
            switch(data.type) {
                case 'order_status_update':
                case 'order_status':  // ✅ 新增：支持統一更新器的消息類型
                    this.handleStatusUpdate(data);
                    break;
                case 'queue_position_update':
                case 'queue_position':  // ✅ 新增：支持隊列位置更新
                    this.handleQueueUpdate(data);
                    break;
                case 'payment_status_update':
                case 'payment_status':  // ✅ 新增：支持支付狀態更新
                    this.handlePaymentUpdate(data);
                    break;
                case 'order_ready_notification':
                case 'order_ready':  // ✅ 新增：支持訂單就緒通知
                    this.handleOrderReady(data);
                    break;
                case 'heartbeat':
                case 'pong':  // ✅ 新增：支持心跳回應
                    this.handleHeartbeat(data);
                    break;
                case 'welcome':  // ✅ 新增：支持歡迎消息
                    console.log('👋 收到歡迎消息:', data.message);
                    break;
                default:
                    console.log('❓ 未知的顧客消息類型:', data.type, data);
            }
            
        } catch (error) {
            console.error('❌ 解析顧客消息失敗:', error, event.data);
        }
    }
    
    handleStatusUpdate(data) {
        console.log(`🔄 訂單狀態更新:`, data);
        
        // ✅ 修復：處理不同格式的數據
        let statusData = data;
        
        // 格式1: 統一訂單更新器格式 {type: 'order_status', data: {...}}
        if (data.type === 'order_status' && data.data) {
            console.log('📦 檢測到統一更新器格式，提取數據');
            statusData = data.data;
        }
        
        // 格式2: 直接狀態數據 {status: 'preparing', ...}
        const status = statusData.status || data.status;
        console.log(`📊 最終狀態: ${status}`);
        
        // 執行所有回調函數
        this.statusCallbacks.forEach(callback => {
            try {
                callback(statusData);
            } catch (error) {
                console.error('狀態回調執行失敗:', error);
            }
        });
        
        // 更新UI
        this.updateStatusUI(statusData);
    }
    
    handleQueueUpdate(data) {
        console.log(`🔄 隊列位置更新: ${data.position}`);
        
        this.queueCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('隊列回調執行失敗:', error);
            }
        });
        
        this.updateQueueUI(data);
    }
    
    handlePaymentUpdate(data) {
        console.log(`💰 支付狀態更新: ${data.payment_status}`);
        
        this.paymentCallbacks.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error('支付回調執行失敗:', error);
            }
        });
        
        this.updatePaymentUI(data);
    }
    
    handleOrderReady(data) {
        console.log(`✅ 訂單就緒通知: ${data.order_id}`);
        
        // 顯示通知
        this.showNotification(`✅ 您的訂單已準備就緒！取餐碼: ${data.pickup_code || ''}`, 'success');
        
        // 播放提示音
        this.playNotificationSound();
        
        // 更新UI
        this.updateOrderReadyUI(data);
    }
    
    handleHeartbeat(data) {
        // 回應心跳
        if (this.isConnected) {
            const response = {
                type: 'heartbeat_ack',
                timestamp: new Date().toISOString(),
            };
            this.socket.send(JSON.stringify(response));
        }
    }
    
    // UI更新方法
    updateStatusUI(data) {
        const statusElement = document.getElementById('order-status-display');
        if (statusElement) {
            statusElement.textContent = this.getStatusText(data.status);
            statusElement.className = `status-badge ${this.getStatusClass(data.status)}`;
        }
        
        const progressElement = document.getElementById('order-progress');
        if (progressElement) {
            const progress = this.calculateProgress(data.status);
            progressElement.style.width = `${progress}%`;
            progressElement.setAttribute('aria-valuenow', progress);
        }
    }
    
    updateQueueUI(data) {
        const queueElement = document.getElementById('queue-position');
        if (queueElement && data.position) {
            queueElement.textContent = `隊列位置: ${data.position}`;
        }
        
        const waitElement = document.getElementById('estimated-wait');
        if (waitElement && data.estimated_time) {
            waitElement.textContent = `預計等待: ${data.estimated_time}`;
        }
    }
    
    updatePaymentUI(data) {
        const paymentElement = document.getElementById('payment-status');
        if (paymentElement) {
            paymentElement.textContent = this.getPaymentStatusText(data.payment_status);
            paymentElement.className = `payment-status ${this.getPaymentStatusClass(data.payment_status)}`;
        }
    }
    
    updateOrderReadyUI(data) {
        // 更新訂單狀態為就緒
        this.updateStatusUI({ status: 'ready' });
        
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
    
    // 輔助方法
    getStatusText(status) {
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
    
    getStatusClass(status) {
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
    
    calculateProgress(status) {
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
    
    getPaymentStatusText(status) {
        const statusMap = {
            'pending': '待支付',
            'paid': '已支付',
            'failed': '支付失敗',
            'cancelled': '已取消',
        };
        return statusMap[status] || status;
    }
    
    getPaymentStatusClass(status) {
        const classMap = {
            'pending': 'text-warning',
            'paid': 'text-success',
            'failed': 'text-danger',
            'cancelled': 'text-secondary',
        };
        return classMap[status] || 'text-secondary';
    }
    
    showConnectionStatus(connected) {
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
    
    showNotification(message, type = 'info') {
        // 使用現有的通知系統或創建簡單的通知
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 1050; max-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('音頻播放失敗:', e));
        } catch (error) {
            // 忽略音頻錯誤
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            console.log(`🔄 ${delay/1000}秒後嘗試重連 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connect();
                }
            }, delay);
        } else {
            console.error('❌ 達到最大重連次數，停止嘗試');
            this.showNotification('實時更新已斷開，請刷新頁面獲取最新狀態', 'warning');
        }
    }
    
    // 註冊回調函數
    onStatusUpdate(callback) {
        this.statusCallbacks.push(callback);
        return () => {
            const index = this.statusCallbacks.indexOf(callback);
            if (index > -1) this.statusCallbacks.splice(index, 1);
        };
    }
    
    onQueueUpdate(callback) {
        this.queueCallbacks.push(callback);
        return () => {
            const index = this.queueCallbacks.indexOf(callback);
            if (index > -1) this.queueCallbacks.splice(index, 1);
        };
    }
    
    onPaymentUpdate(callback) {
        this.paymentCallbacks.push(callback);
        return () => {
            const index = this.paymentCallbacks.indexOf(callback);
            if (index > -1) this.paymentCallbacks.splice(index, 1);
        };
    }
    
    // 清理方法
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.isConnected = false;
            console.log('🔌 手動斷開顧客WebSocket連接');
        }
    }
    
    cleanup() {
        this.disconnect();
        this.statusCallbacks = [];
        this.queueCallbacks = [];
        this.paymentCallbacks = [];
        console.log('🧹 顧客WebSocket管理器已清理');
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.CustomerWebSocketManager = CustomerWebSocketManager;
    
    // 如果頁面有訂單ID，自動初始化
    document.addEventListener('DOMContentLoaded', () => {
        const orderIdMeta = document.querySelector('meta[name="order-id"]');
        if (orderIdMeta) {
            const orderId = orderIdMeta.getAttribute('content');
            if (orderId) {
                console.log(`🔄 檢測到訂單ID: ${orderId}，初始化顧客WebSocket`);
                window.customerWebSocket = new CustomerWebSocketManager(orderId);
            }
        }
    });
}