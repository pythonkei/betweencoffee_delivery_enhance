// static/js/staff-order-management/websocket-manager.js - 優化版
// ==================== WebSocket連接管理器 - 簡化事件處理，專注觸發統一數據刷新 ====================

class WebSocketManager {
    constructor() {
        console.log('🔄 初始化WebSocket管理器（優化版）...');
        
        // WebSocket連接狀態
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000;
        
        // 連接狀態元素
        this.connectionIndicator = null;
        
        // 初始化
        this.connect();
        this.setupHeartbeat();
        
        console.log('✅ WebSocket管理器初始化完成');
    }
    
    // ==================== WebSocket連接管理 ====================
    
    /**
     * 建立WebSocket連接
     */
    connect() {
        try {
            // 構建WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/queue/`;
            
            console.log('🔗 嘗試連接到WebSocket:', wsUrl);
            
            this.socket = new WebSocket(wsUrl);
            
            // 連接成功
            this.socket.onopen = () => {
                console.log('✅ WebSocket連接成功');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // 顯示連接狀態
                this.showConnectionStatus(true);
                
                // 發送連接信息
                this.sendConnectionInfo();
            };
            
            // 收到消息
            this.socket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
            // 連接關閉
            this.socket.onclose = (event) => {
                console.log('❌ WebSocket連接關閉:', event.code, event.reason);
                this.isConnected = false;
                this.showConnectionStatus(false);
                
                // 嘗試重新連接
                this.attemptReconnect();
            };
            
            // 連接錯誤
            this.socket.onerror = (error) => {
                console.error('❌ WebSocket錯誤:', error);
                this.isConnected = false;
                this.showConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('❌ 建立WebSocket連接失敗:', error);
        }
    }
    
    /**
     * 發送連接信息
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
            console.log('📤 發送連接信息:', message);
        }
    }
    
    /**
     * 嘗試重新連接
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 嘗試重新連接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectInterval * this.reconnectAttempts); // 指數退避
        } else {
            console.error('❌ 達到最大重試次數，停止重連');
        }
    }
    
    // ==================== 消息處理（大幅簡化） ====================
    
    /**
     * 處理WebSocket消息（簡化版）
     */
    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 收到WebSocket消息:', data.type);
            
            // 根據消息類型處理
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
                    this.handlePing(data);
                    break;
                    
                default:
                    console.log('❓ 未知的WebSocket消息類型:', data.type);
                    this.handleGenericUpdate(data);
            }
            
        } catch (error) {
            console.error('❌ 解析WebSocket消息失敗:', error, event.data);
        }
    }
    
    // ==================== 事件處理方法（全部簡化為觸發統一刷新） ====================
    
    /**
     * 處理隊列更新 - 簡化為觸發統一刷新
     */
    handleQueueUpdate(data) {
        console.log('🔄 收到隊列更新，觸發統一數據刷新');
        
        // 觸發隊列更新事件（其他組件可能監聽）
        document.dispatchEvent(new CustomEvent('queue_update_immediate', {
            detail: data
        }));
        
        // 播放通知聲音（可選）
        if (data.play_sound) {
            this.playNotificationSound();
        }
        
        // 觸發統一數據刷新（主邏輯）
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理訂單更新 - 簡化為觸發統一刷新
     */
    handleOrderUpdate(data) {
        console.log('🔄 收到訂單更新，觸發統一數據刷新');
        
        // 觸發訂單更新事件
        document.dispatchEvent(new CustomEvent('order_update_immediate', {
            detail: data
        }));
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理新訂單 - 簡化為觸發統一刷新
     */
    handleNewOrder(data) {
        console.log('🆕 收到新訂單通知:', data.order_id);
        
        // 顯示通知
        this.showNotification(`🆕 新訂單 #${data.order_id}`, 'info');
        
        // 播放新訂單聲音
        this.playNewOrderSound();
        
        // 觸發新訂單事件
        document.dispatchEvent(new CustomEvent('new_order_immediate', {
            detail: data
        }));
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理訂單就緒 - 簡化為觸發統一刷新
     */
    handleOrderReady(data) {
        console.log('✅ 收到訂單就緒通知:', data.order_id);
        
        // 顯示通知
        if (data.pickup_code) {
            this.showNotification(`✅ 訂單 #${data.order_id} 已就緒 (取餐碼: ${data.pickup_code})`, 'success');
        } else {
            this.showNotification(`✅ 訂單 #${data.order_id} 已就緒`, 'success');
        }
        
        // 播放完成聲音
        this.playCompletionSound();
        
        // 觸發訂單就緒事件
        document.dispatchEvent(new CustomEvent('order_ready_immediate', {
            detail: data
        }));
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理訂單已提取 - 簡化為觸發統一刷新
     */
    handleOrderCollected(data) {
        console.log('📦 收到訂單已提取通知:', data.order_id);
        
        // 顯示通知
        this.showNotification(`📦 訂單 #${data.order_id} 已提取`, 'info');
        
        // 觸發訂單已提取事件
        document.dispatchEvent(new CustomEvent('order_collected_immediate', {
            detail: data
        }));
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理支付更新 - 簡化為觸發統一刷新
     */
    handlePaymentUpdate(data) {
        console.log('💰 收到支付更新:', data.order_id, data.payment_status);
        
        // 觸發支付更新事件
        document.dispatchEvent(new CustomEvent('payment_update_immediate', {
            detail: data
        }));
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    /**
     * 處理系統消息 - 只顯示通知，不刷新數據
     */
    handleSystemMessage(data) {
        console.log('📢 收到系統消息:', data.message);
        
        // 顯示系統消息
        this.showNotification(`📢 ${data.message}`, data.message_type || 'info');
    }
    
    /**
     * 處理心跳 - 回應pong
     */
    handlePing(data) {
        console.log('💓 收到心跳ping');
        
        // 回應pong
        this.sendPong();
    }
    
    /**
     * 處理通用更新 - 觸發統一刷新
     */
    handleGenericUpdate(data) {
        console.log('🔄 收到通用更新，觸發統一數據刷新');
        
        // 觸發統一數據刷新
        this.triggerUnifiedDataRefresh();
    }
    
    // ==================== 核心方法：觸發統一數據刷新 ====================
    
    /**
     * 觸發統一數據刷新（防抖處理）
     */
    triggerUnifiedDataRefresh() {
        // 使用防抖避免過於頻繁的刷新
        if (this.refreshTimeout) {
            clearTimeout(this.refreshTimeout);
        }
        
        this.refreshTimeout = setTimeout(() => {
            console.log('🔄 觸發統一數據刷新');
            
            // 方法1：如果統一數據管理器存在，直接調用
            if (window.unifiedDataManager && typeof window.unifiedDataManager.loadUnifiedData === 'function') {
                window.unifiedDataManager.loadUnifiedData();
            }
            
            // 方法2：發送全局刷新事件（備用）
            else {
                document.dispatchEvent(new CustomEvent('refresh_unified_data'));
            }
            
            this.refreshTimeout = null;
        }, 300); // 300毫秒防抖
    }
    
    // ==================== 輔助方法 ====================
    
    /**
     * 設置心跳機制
     */
    setupHeartbeat() {
        // 每25秒發送一次心跳
        setInterval(() => {
            if (this.isConnected) {
                this.sendPing();
            }
        }, 25000);
        
        console.log('💓 心跳機制已啟動（每25秒一次）');
    }
    
    /**
     * 發送ping
     */
    sendPing() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = {
                type: 'ping',
                timestamp: new Date().toISOString()
            };
            this.socket.send(JSON.stringify(message));
        }
    }
    
    /**
     * 發送pong
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
     * 顯示連接狀態
     */
    showConnectionStatus(connected) {
        // 創建或獲取狀態指示器
        if (!this.connectionIndicator) {
            this.connectionIndicator = this.createConnectionIndicator();
        }
        
        if (connected) {
            this.connectionIndicator.className = 'websocket-indicator connected';
            this.connectionIndicator.innerHTML = '<i class="fas fa-circle"></i> 實時連接';
            this.connectionIndicator.title = 'WebSocket連接正常';
        } else {
            this.connectionIndicator.className = 'websocket-indicator disconnected';
            this.connectionIndicator.innerHTML = '<i class="fas fa-circle"></i> 連接中斷';
            this.connectionIndicator.title = 'WebSocket連接中斷，嘗試重連中...';
        }
    }
    
    /**
     * 創建連接狀態指示器
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
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                z-index: 9999;
                background: rgba(0,0,0,0.7);
                color: white;
                display: flex;
                align-items: center;
                gap: 5px;
            `;
            
            document.body.appendChild(indicator);
        }
        
        return indicator;
    }
    
    /**
     * 顯示通知
     */
    showNotification(message, type = 'info') {
        // 簡單的通知實現
        const notification = document.createElement('div');
        notification.className = `websocket-notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            z-index: 9999;
            max-width: 300px;
            word-wrap: break-word;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>${message}</span>
                <button class="close-notification" style="background: none; border: none; color: white; cursor: pointer; font-size: 16px;">
                    ×
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 關閉按鈕事件
        const closeBtn = notification.querySelector('.close-notification');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });
        
        // 3秒後自動消失
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.remove();
            }
        }, 3000);
    }
    
    /**
     * 播放新訂單聲音
     */
    playNewOrderSound() {
        this.playSound(800, 0.3, 0.5);
    }
    
    /**
     * 播放完成聲音
     */
    playCompletionSound() {
        this.playSound(1200, 0.3, 0.3);
    }
    
    /**
     * 播放通知聲音
     */
    playNotificationSound() {
        this.playSound(1000, 0.2, 0.4);
    }
    
    /**
     * 播放聲音（Web Audio API）
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
     * 發送消息
     */
    sendMessage(message) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('❌ 發送WebSocket消息失敗:', error);
                return false;
            }
        } else {
            console.warn('⚠️ WebSocket未連接，無法發送消息');
            return false;
        }
    }
    
    /**
     * 獲取用戶ID
     */
    getUserId() {
        // 從meta標籤或全局變量獲取用戶ID
        const userMeta = document.querySelector('meta[name="user-id"]');
        if (userMeta) {
            return userMeta.getAttribute('content');
        }
        
        // 備用方案：從全局變量獲取
        if (window.currentUserId) {
            return window.currentUserId;
        }
        
        return 'unknown';
    }
    
    /**
     * 斷開連接
     */
    disconnect() {
        if (this.socket) {
            console.log('🔌 手動斷開WebSocket連接');
            this.socket.close();
            this.socket = null;
            this.isConnected = false;
        }
    }
    
    /**
     * 重新連接
     */
    reconnect() {
        console.log('🔄 手動重新連接WebSocket');
        this.disconnect();
        setTimeout(() => {
            this.connect();
        }, 1000);
    }
    
    /**
     * 檢查連接狀態
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            readyState: this.socket ? this.socket.readyState : null,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts
        };
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    // 創建全局實例
    window.webSocketManager = new WebSocketManager();
    
    // 方便調試
    console.log('🌍 WebSocketManager 已註冊到 window 對象');
    
    // 添加一些全局輔助方法
    window.WebSocketUtils = {
        reconnect: () => window.webSocketManager?.reconnect(),
        disconnect: () => window.webSocketManager?.disconnect(),
        getStatus: () => window.webSocketManager?.getConnectionStatus(),
        sendTestMessage: (message) => {
            return window.webSocketManager?.sendMessage({
                type: 'test',
                message: message,
                timestamp: new Date().toISOString()
            });
        }
    };
}