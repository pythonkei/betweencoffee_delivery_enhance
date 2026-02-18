// static/js/order-detail.js
// ==================== 訂單追蹤頁面 WebSocket 管理器 ====================

class OrderDetailTracker {
    constructor(orderId, token = '') {
        this.orderId = orderId;
        this.token = token;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectBaseDelay = 1000;    // 1秒
        this.reconnectMaxDelay = 30000;    // 30秒
        this.shouldReconnect = true;
        this.pingInterval = null;
        this.statusCallbacks = {
            onOpen: [],
            onMessage: [],
            onClose: [],
            onError: []
        };

        this.init();
    }

    init() {
        console.log(`🔍 初始化訂單追蹤器 #${this.orderId}`);
        this.connectWebSocket();
        this.setupEventListeners();
        this.updateConnectionStatus('connecting', '連線中...');
    }

    // ========== WebSocket 連線管理 ==========

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/order/${this.orderId}/`;
        
        console.log(`🔗 嘗試連線: ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('✅ WebSocket 連線成功');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected', '即時連線中');
            this.startHeartbeat();
            this.triggerCallbacks('onOpen');
            
            // 發送身份驗證（若需要 token）
            if (this.token) {
                this.send({ type: 'auth', token: this.token });
            }
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
                this.triggerCallbacks('onMessage', data);
            } catch (e) {
                console.error('❌ 解析訊息失敗:', e);
            }
        };

        this.socket.onclose = (event) => {
            console.log('❌ WebSocket 關閉', event.code, event.reason);
            this.isConnected = false;
            this.stopHeartbeat();
            this.updateConnectionStatus('disconnected', '連線中斷');
            this.triggerCallbacks('onClose', event);
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket 錯誤:', error);
            this.updateConnectionStatus('disconnected', '連線錯誤');
            this.triggerCallbacks('onError', error);
        };
    }

    attemptReconnect() {
        if (!this.shouldReconnect) return;
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ 已達最大重試次數，停止重連');
            this.updateConnectionStatus('disconnected', '無法連線，請重新整理頁面');
            return;
        }

        this.reconnectAttempts++;
        // 指數退避 + 抖動
        let delay = this.reconnectBaseDelay * Math.pow(1.5, this.reconnectAttempts - 1);
        delay = Math.min(delay, this.reconnectMaxDelay);
        const jitter = delay * 0.2 * (Math.random() * 2 - 1);
        const finalDelay = Math.max(1000, delay + jitter);

        console.log(`🔄 嘗試重新連線 (${this.reconnectAttempts}/${this.maxReconnectAttempts})，${Math.round(finalDelay/1000)}秒後`);
        this.updateConnectionStatus('reconnecting', `重新連線中 (${this.reconnectAttempts})`);

        setTimeout(() => {
            this.connectWebSocket();
        }, finalDelay);
    }

    disconnect() {
        this.shouldReconnect = false;
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.stopHeartbeat();
    }

    // ========== 心跳機制 ==========

    startHeartbeat() {
        this.stopHeartbeat(); // 清除舊的
        this.pingInterval = setInterval(() => {
            if (this.isConnected && this.socket?.readyState === WebSocket.OPEN) {
                this.send({ type: 'ping' });
            }
        }, 25000); // 25秒
    }

    stopHeartbeat() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    send(message) {
        if (this.socket?.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(message));
            return true;
        }
        console.warn('⚠️ WebSocket 未連線，無法發送訊息');
        return false;
    }

    // ========== 訊息處理 ==========

    handleMessage(data) {
        console.log('📨 收到訂單更新:', data);

        if (data.type === 'order_update') {
            // 統一處理 order_update
            switch (data.update_type) {
                case 'status':
                    this.updateOrderStatus(data.data);
                    break;
                case 'queue_position':
                    this.updateQueuePosition(data.data.position);
                    break;
                case 'estimated_time':
                    this.updateEstimatedTime(data.data.estimated_time);
                    break;
                default:
                    console.log('❓ 未知更新類型:', data.update_type);
            }
        } else if (data.type === 'pong') {
            // 心跳回應，忽略
        } else if (data.type === 'error') {
            console.error('伺服器錯誤:', data.message);
            this.showToast('❌ ' + data.message, 'error');
        } else {
            console.log('❓ 未知訊息類型:', data.type);
        }
    }

    // ========== UI 更新方法 ==========

    updateOrderStatus(data) {
        const status = data.status;          // pending, preparing, ready, completed
        const statusDisplay = data.status_display || this.getStatusDisplay(status);
        const updatedAt = data.updated_at || new Date().toISOString();

        // 更新狀態文字
        document.getElementById('status-text').textContent = `訂單 ${statusDisplay}`;
        
        // 更新狀態圖示與背景
        this.updateStatusIcon(status);
        
        // 更新時間軸
        this.updateTimeline(status, updatedAt);
        
        // 更新進度條
        this.updateProgressBar(status);
        
        // 顯示/隱藏排隊資訊
        const queueInfo = document.getElementById('queue-info');
        if (status === 'pending' || status === 'preparing') {
            queueInfo.classList.remove('d-none');
        } else {
            queueInfo.classList.add('d-none');
        }

        // 若訂單已完成，停止自動重連（但保留連線）
        if (status === 'completed') {
            this.shouldReconnect = false; // 完成後不需重連
        }
    }

    updateStatusIcon(status) {
        const icon = document.getElementById('status-icon-symbol');
        const iconContainer = document.getElementById('status-icon');
        
        // 移除所有狀態 class
        iconContainer.className = 'rounded-circle text-white d-flex align-items-center justify-content-center';
        
        switch (status) {
            case 'pending':
                icon.className = 'fas fa-clock fa-lg';
                iconContainer.classList.add('bg-warning');
                break;
            case 'preparing':
                icon.className = 'fas fa-mug-hot fa-lg';
                iconContainer.classList.add('bg-primary');
                break;
            case 'ready':
                icon.className = 'fas fa-bell fa-lg';
                iconContainer.classList.add('bg-success');
                break;
            case 'completed':
                icon.className = 'fas fa-check-double fa-lg';
                iconContainer.classList.add('bg-secondary');
                break;
            default:
                icon.className = 'fas fa-check fa-lg';
                iconContainer.classList.add('bg-success');
        }
    }

    updateTimeline(status, timestamp) {
        // 設定各步驟的完成狀態與時間
        const steps = ['pending', 'preparing', 'ready', 'completed'];
        let currentReached = false;
        
        steps.forEach(step => {
            const stepEl = document.getElementById(`step-${step}`);
            const timeEl = document.getElementById(`time-${step}`);
            
            if (step === status) {
                // 當前狀態：active
                stepEl.classList.add('active');
                stepEl.classList.remove('completed');
                currentReached = true;
                if (timeEl && timestamp) {
                    timeEl.textContent = this.formatTime(timestamp);
                }
            } else if (!currentReached) {
                // 已完成的狀態（在當前狀態之前）
                stepEl.classList.add('completed');
                stepEl.classList.remove('active');
                if (timeEl && timestamp) { // 這裡最好有該步驟的實際時間，但後端可能未提供全部，先以當前時間替代
                    // 若後端有提供各步驟時間，可從 data 取得，這裡先簡化
                    if (step === 'pending' && this.orderCreatedTime) {
                        timeEl.textContent = this.formatTime(this.orderCreatedTime);
                    }
                }
            } else {
                // 未到達的狀態
                stepEl.classList.remove('completed', 'active');
                if (timeEl) timeEl.textContent = '--:--';
            }
        });
    }

    updateProgressBar(status) {
        const progressFill = document.getElementById('progress-fill');
        let width = 0;
        switch (status) {
            case 'pending': width = 25; break;
            case 'preparing': width = 60; break;
            case 'ready': width = 90; break;
            case 'completed': width = 100; break;
            default: width = 0;
        }
        progressFill.style.width = width + '%';
    }

    updateQueuePosition(position) {
        const posEl = document.getElementById('queue-position');
        if (posEl) {
            posEl.textContent = position !== undefined && position !== null ? position : '-';
        }
    }

    updateEstimatedTime(timeString) {
        const estEl = document.getElementById('estimated-time');
        if (estEl) {
            if (timeString) {
                estEl.textContent = this.formatTime(timeString);
            } else {
                estEl.textContent = '--:--';
            }
        }
    }

    // ========== UI 輔助方法 ==========

    updateConnectionStatus(status, message) {
        const indicator = document.getElementById('ws-connection-status');
        if (!indicator) return;
        
        indicator.className = 'connection-status';
        let icon = '';
        switch (status) {
            case 'connected':
                indicator.classList.add('connected');
                icon = '<i class="fas fa-circle mr-1" style="font-size: 10px;"></i>';
                break;
            case 'disconnected':
                indicator.classList.add('disconnected');
                icon = '<i class="fas fa-exclamation-triangle mr-1"></i>';
                break;
            case 'reconnecting':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-sync-alt mr-1 fa-spin"></i>';
                break;
            case 'connecting':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-spinner mr-1 fa-pulse"></i>';
                break;
        }
        indicator.innerHTML = icon + '<span>' + message + '</span>';
    }

    getStatusDisplay(status) {
        const map = {
            'pending': '處理中',
            'preparing': '製作中',
            'ready': '待取餐',
            'completed': '已完成'
        };
        return map[status] || status;
    }

    formatTime(isoString) {
        if (!isoString) return '--:--';
        try {
            const date = new Date(isoString);
            return date.toLocaleTimeString('zh-HK', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return isoString;
        }
    }

    showToast(message, type = 'info') {
        // 優先使用統一的 toast-manager.js
        if (window.toast) {
            const toastType = type === 'success' ? 'success' : 
                             type === 'error' ? 'error' : 
                             type === 'warning' ? 'warning' : 'info';
            
            window.toast[toastType](message);
        } else if (window.orderManager?.showToast) {
            // 備用方案：使用 orderManager 的 showToast
            window.orderManager.showToast(message, type);
        } else {
            // 簡單實現
            alert(message);
        }
    }

    // ========== 事件系統 ==========

    on(event, callback) {
        if (this.statusCallbacks[event]) {
            this.statusCallbacks[event].push(callback);
        }
    }

    triggerCallbacks(event, data = null) {
        if (this.statusCallbacks[event]) {
            this.statusCallbacks[event].forEach(cb => cb(data));
        }
    }

    setupEventListeners() {
        // 頁面關閉前主動斷線
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }
}

// 自動初始化（如果頁面存在 order-detail-app 容器）
document.addEventListener('DOMContentLoaded', function() {
    const appContainer = document.getElementById('order-detail-app');
    if (appContainer) {
        const orderId = appContainer.dataset.orderId;
        const token = appContainer.dataset.orderToken || '';
        window.orderTracker = new OrderDetailTracker(orderId, token);
    }
});