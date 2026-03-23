// static/js/unified-order-updater.js
// ==================== 統一的訂單狀態更新器 ====================
// 功能：合併 WebSocket 和 API 輪詢，提供可靠的實時更新

/**
 * 統一的訂單狀態更新器
 * 結合 WebSocket（實時）和 API 輪詢（備用）兩種更新機制
 * 確保訂單狀態能夠實時自動更新
 */
class UnifiedOrderUpdater {
    constructor(orderId) {
        this.orderId = orderId;
        this.useWebSocket = this.checkWebSocketSupport();
        this.socket = null;
        this.updateInterval = null;
        this.isRunning = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.updateCount = 0;
        this.maxUpdates = 180; // 最多更新180次（30分鐘）
        
        console.log(`🔧 創建統一的訂單更新器 #${orderId}`);
        console.log(`   WebSocket 支持: ${this.useWebSocket ? '✅ 是' : '❌ 否'}`);
    }
    
    // ========== 核心方法 ==========
    
    /**
     * 啟動更新器
     */
    start() {
        if (this.isRunning) {
            console.warn('⚠️ 更新器已在運行中');
            return;
        }
        
        this.isRunning = true;
        console.log('🚀 啟動統一的訂單更新器');
        
        // 優先使用 WebSocket
        if (this.useWebSocket) {
            this.connectWebSocket();
        } else {
            console.log('ℹ️ WebSocket 不可用，使用 API 輪詢');
            this.startPolling();
        }
        
        // 立即更新一次
        this.fetchOrderStatus();
    }
    
    /**
     * 停止更新器
     */
    stop() {
        this.isRunning = false;
        
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        console.log('🛑 訂單更新器已停止');
    }
    
    // ========== WebSocket 方法 ==========
    
    /**
     * 檢查 WebSocket 支持
     */
    checkWebSocketSupport() {
        return 'WebSocket' in window && window.WebSocket !== null;
    }
    
    /**
     * 連接 WebSocket
     */
    connectWebSocket() {
        if (!this.useWebSocket || !this.isRunning) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/order/${this.orderId}/`;
        
        console.log(`🔗 連接 WebSocket: ${wsUrl}`);
        
        try {
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('✅ WebSocket 連接成功');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected', '即時連線中');
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('📨 收到 WebSocket 更新:', data);
                    this.handleUpdate(data);
                } catch (e) {
                    console.error('❌ 解析 WebSocket 消息失敗:', e);
                }
            };
            
            this.socket.onclose = (event) => {
                console.log('❌ WebSocket 關閉', event.code, event.reason);
                this.updateConnectionStatus('disconnected', '連線中斷');
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ WebSocket 錯誤:', error);
                this.updateConnectionStatus('disconnected', '連線錯誤');
            };
            
        } catch (error) {
            console.error('❌ WebSocket 連接失敗:', error);
            this.fallbackToPolling();
        }
    }
    
    /**
     * 嘗試重新連接 WebSocket
     */
    attemptReconnect() {
        if (!this.isRunning || this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('ℹ️ 達到最大重試次數，切換到 API 輪詢');
            this.fallbackToPolling();
            return;
        }
        
        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        
        console.log(`🔄 嘗試重新連接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})，${delay/1000}秒後`);
        this.updateConnectionStatus('reconnecting', `重新連線中 (${this.reconnectAttempts})`);
        
        setTimeout(() => {
            if (this.isRunning) {
                this.connectWebSocket();
            }
        }, delay);
    }
    
    /**
     * 回退到 API 輪詢
     */
    fallbackToPolling() {
        console.log('🔄 切換到 API 輪詢模式');
        this.updateConnectionStatus('polling', '輪詢更新中');
        this.startPolling();
    }
    
    // ========== API 輪詢方法 ==========
    
    /**
     * 啟動 API 輪詢
     */
    startPolling() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // 每10秒更新一次
        this.updateInterval = setInterval(() => {
            this.fetchOrderStatus();
        }, 10000);
        
        console.log('⏰ API 輪詢已啟動（每10秒更新一次）');
    }
    
    /**
     * 獲取訂單狀態
     */
    async fetchOrderStatus() {
        if (!this.isRunning) return;
        
        // 檢查更新次數限制
        if (this.updateCount >= this.maxUpdates) {
            console.log('ℹ️ 達到最大更新次數，停止更新');
            this.stop();
            return;
        }
        
        this.updateCount++;
        
        try {
            const apiUrl = `/eshop/order/api/order-status/${this.orderId}/`;
            console.log(`📡 調用 API: ${apiUrl} (${this.updateCount}/${this.maxUpdates})`);
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態碼: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                console.error('❌ 獲取訂單狀態失敗:', data.error);
                return;
            }
            
            console.log('✅ API 更新成功:', data);
            this.handleUpdate(data);
            
            // 如果訂單已完成，停止更新
            if (data.is_ready || data.status === 'completed' || data.status === 'ready') {
                console.log('🎉 訂單已完成，停止更新器');
                this.stop();
            }
            
        } catch (error) {
            console.error('❌ 訂單狀態更新失敗:', error);
        }
    }
    
    // ========== 更新處理方法 ==========
    
    /**
     * 處理更新數據
     */
    handleUpdate(data) {
        console.log('🔍 處理更新數據:', data);
        
        // 提取實際的訂單數據
        const orderData = this.extractOrderData(data);
        
        // 驗證數據格式
        if (!this.validateData(orderData)) {
            console.error('❌ 數據格式無效:', orderData);
            return;
        }
        
        // 更新狀態卡片
        this.updateStatusCard(orderData);
        
        // 更新進度條
        this.updateProgressBar(orderData);
        
        // 更新時間軸
        this.updateTimeline(orderData);
        
        // 更新隊列信息
        this.updateQueueInfo(orderData);
        
        // 更新支付確認頁面的特定元素
        this.updatePaymentConfirmationElements(orderData);
    }
    
    /**
     * 提取訂單數據（支持多種格式）
     */
    extractOrderData(data) {
        // 格式1: WebSocket 格式 {type: 'order_status', data: {...}, timestamp: '...'}
        if (data.type === 'order_status' && data.data) {
            console.log('📦 提取 WebSocket 格式數據:', data.data);
            return data.data;
        }
        
        // 格式2: API 格式 {success: true, order_id: ..., status: ...}
        if (data.success !== undefined) {
            console.log('📦 提取 API 格式數據');
            return data;
        }
        
        // 格式3: 直接就是訂單數據
        console.log('📦 使用原始數據格式');
        return data;
    }
    
    /**
     * 驗證數據格式
     */
    validateData(data) {
        if (!data) {
            console.error('❌ 數據為空');
            return false;
        }
        
        // 檢查是否為有效的訂單數據
        const hasStatus = data.status !== undefined;
        const hasSuccess = data.success !== undefined;
        
        if (!hasStatus && !hasSuccess) {
            console.error('❌ 數據缺少必要字段:', data);
            return false;
        }
        
        // 如果數據有 success 字段但為 false，記錄但不阻止處理
        if (data.success === false) {
            console.warn('⚠️ 數據 success 為 false:', data.error || '未知錯誤');
        }
        
        return true;
    }
    
    /**
     * 更新狀態卡片
     */
    updateStatusCard(data) {
        const status = data.status;
        const statusDisplay = data.status_display || this.getStatusDisplay(status);
        
        // 更新狀態文字
        const statusTextEl = document.getElementById('status-text');
        if (statusTextEl) {
            statusTextEl.textContent = `訂單 ${statusDisplay}`;
        }
        
        // 更新狀態圖示
        this.updateStatusIcon(status);
        
        // 更新狀態描述
        const statusDescEl = document.getElementById('status-description');
        if (statusDescEl) {
            statusDescEl.textContent = this.getStatusDescription(status);
        }
        
        console.log(`✅ 更新狀態卡片: ${status} (${statusDisplay})`);
    }
    
    /**
     * 更新狀態圖示
     */
    updateStatusIcon(status) {
        const icon = document.getElementById('status-icon-symbol');
        const iconContainer = document.getElementById('status-icon');
        
        if (!icon || !iconContainer) {
            console.warn('⚠️ 找不到狀態圖示元素');
            return;
        }
        
        // 移除所有狀態 class
        iconContainer.className = 'rounded-circle text-white d-flex align-items-center justify-content-center';
        
        switch (status) {
            case 'pending':
                icon.setAttribute('class', 'fas fa-clock fa-lg');
                iconContainer.classList.add('bg-warning');
                break;
            case 'preparing':
                icon.setAttribute('class', 'fas fa-mug-hot fa-lg');
                iconContainer.classList.add('bg-primary');
                break;
            case 'ready':
                icon.setAttribute('class', 'fas fa-bell fa-lg');
                iconContainer.classList.add('bg-success');
                break;
            case 'completed':
                icon.setAttribute('class', 'fas fa-check-double fa-lg');
                iconContainer.classList.add('bg-secondary');
                break;
            default:
                icon.setAttribute('class', 'fas fa-check fa-lg');
                iconContainer.classList.add('bg-success');
        }
    }
    
    /**
     * 更新進度條
     */
    updateProgressBar(data) {
        const progressFill = document.getElementById('progress-fill');
        if (!progressFill) return;
        
        let width = 0;
        switch (data.status) {
            case 'pending': width = 25; break;
            case 'preparing': width = 60; break;
            case 'ready': width = 90; break;
            case 'completed': width = 100; break;
            default: width = 0;
        }
        
        // 如果有後端提供的進度百分比，使用後端的值
        if (data.progress_percentage !== undefined) {
            width = Math.max(0, Math.min(100, data.progress_percentage));
        }
        
        progressFill.style.width = `${width}%`;
        console.log(`✅ 更新進度條: ${width}%`);
    }
    
    /**
     * 更新時間軸
     */
    updateTimeline(data) {
        const status = data.status;
        const timestamp = data.updated_at || new Date().toISOString();
        const steps = ['pending', 'preparing', 'ready', 'completed'];
        
        // 定義狀態順序（支持 waiting 狀態映射到 pending）
        const statusOrder = {
            'waiting': 0,    // waiting 對應到 pending
            'pending': 0,
            'preparing': 1,
            'ready': 2,
            'completed': 3
        };
        
        // 確保狀態有效
        const currentStepIndex = statusOrder[status] !== undefined ? statusOrder[status] : 0;
        
        console.log(`📊 更新時間軸: status=${status}, currentStepIndex=${currentStepIndex}`);
        
        steps.forEach((step, index) => {
            const stepEl = document.getElementById(`step-${step}`);
            const timeEl = document.getElementById(`time-${step}`);
            
            if (!stepEl) {
                console.warn(`⚠️ 找不到時間軸步驟元素: step-${step}`);
                return;
            }
            
            // 移除所有狀態類
            stepEl.classList.remove('active', 'completed');
            
            if (index < currentStepIndex) {
                // 已完成的步驟
                stepEl.classList.add('completed');
                console.log(`✅ 設置 step-${step} 為 completed (已完成，index=${index} < currentStepIndex=${currentStepIndex})`);
            } else if (index === currentStepIndex) {
                // 當前步驟
                stepEl.classList.add('active');
                if (timeEl && timestamp) {
                    timeEl.textContent = this.formatTime(timestamp);
                }
                console.log(`✅ 設置 step-${step} 為 active (當前，index=${index} = currentStepIndex=${currentStepIndex})`);
            } else {
                // 未到達的步驟
                if (timeEl) timeEl.textContent = '--:--';
                console.log(`✅ 設置 step-${step} 為 inactive (未到達，index=${index} > currentStepIndex=${currentStepIndex})`);
            }
        });
    }
    
    /**
     * 更新隊列信息
     */
    updateQueueInfo(data) {
        const queueInfo = document.getElementById('queue-info');
        if (!queueInfo) return;
        
        // 顯示/隱藏隊列信息
        if (data.status === 'pending' || data.status === 'preparing') {
            queueInfo.classList.remove('d-none');
            
            // 更新隊列位置
            const queuePosition = document.getElementById('queue-position');
            if (queuePosition && data.queue_position !== undefined) {
                queuePosition.textContent = data.queue_position;
            }
            
            // 更新預計時間
            const estimatedTime = document.getElementById('estimated-time');
            if (estimatedTime && data.estimated_time) {
                estimatedTime.textContent = data.estimated_time;
            }
            
            console.log(`✅ 顯示隊列信息 (${data.status})`);
        } else {
            queueInfo.classList.add('d-none');
            console.log(`✅ 隱藏隊列信息 (${data.status})`);
        }
    }
    
    /**
     * 更新支付確認頁面的特定元素
     */
    updatePaymentConfirmationElements(data) {
        // 更新隊列消息
        const queueMessage = document.getElementById('queue-message');
        if (queueMessage) {
            switch(data.status) {
                case 'preparing':
                    queueMessage.textContent = '您的訂單正在製作中，請耐心等候...';
                    break;
                case 'ready':
                    queueMessage.textContent = '您的訂單已準備就緒，請前往取餐！';
                    break;
                default:
                    queueMessage.textContent = data.queue_message || '';
            }
        }
        
        // 更新進度條（支付確認頁面的）
        const orderProgress = document.getElementById('order-progress');
        const progressText = document.getElementById('progress-text');
        
        if (orderProgress && progressText && data.progress_percentage !== undefined) {
            const progress = Math.max(0, Math.min(100, data.progress_percentage));
            orderProgress.style.width = `${progress}%`;
            orderProgress.setAttribute('aria-valuenow', progress);
            progressText.textContent = data.progress_display || `${progress}% 完成`;
        }
        
        // 更新完成狀態
        if (data.is_ready || data.status === 'ready') {
            const queueInfoSection = document.getElementById('queue-info-section');
            const readySection = document.getElementById('ready-section');
            
            if (queueInfoSection) queueInfoSection.style.display = 'none';
            if (readySection) readySection.style.display = 'block';
        }
    }
    
    /**
     * 更新連接狀態
     */
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
            case 'polling':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-sync mr-1"></i>';
                break;
            case 'connecting':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-spinner mr-1 fa-pulse"></i>';
                break;
        }
        
        indicator.innerHTML = icon + '<span>' + message + '</span>';
    }
    
    // ========== 輔助方法 ==========
    
    getStatusDisplay(status) {
        const map = {
            'waiting': '處理中',      // waiting 對應到 pending 的顯示
            'pending': '處理中',
            'preparing': '製作中',
            'ready': '待取餐',
            'completed': '已完成'
        };
        return map[status] || status;
    }
    
    getStatusDescription(status) {
        const map = {
            'waiting': '我們已收到您的訂單，即將開始製作。',  // waiting 對應到 pending 的描述
            'pending': '我們已收到您的訂單，即將開始製作。',
            'preparing': '您的咖啡正在用心製作中，請稍候。',
            'ready': '訂單已完成，請前往櫃檯取餐。',
            'completed': '感謝您的惠顧，歡迎再次光臨。'
        };
        return map[status] || '訂單狀態更新中...';
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
}

    // ========== 全局導出和初始化 ==========

// 全局導出
window.UnifiedOrderUpdater = UnifiedOrderUpdater;

/**
 * 初始化統一的訂單更新器
 */
function initUnifiedOrderUpdater() {
    console.log('🔧 初始化統一的訂單更新器');
    
    // 從數據屬性獲取訂單ID
    const orderId = document.body.dataset.orderId;
    const paymentStatus = document.body.dataset.paymentStatus;
    const isCoffeeOrder = document.body.dataset.isCoffeeOrder === 'true';
    const isBeansOnly = document.body.dataset.isBeansOnly === 'true';
    
    if (!orderId) {
        console.warn('⚠️ 找不到訂單ID，無法初始化更新器');
        return;
    }
    
    console.log('訂單信息:', {
        orderId,
        paymentStatus,
        isCoffeeOrder,
        isBeansOnly
    });
    
    // 檢查是否應該啟動更新器
    const shouldStartUpdater = orderId && 
        (paymentStatus === 'paid' || paymentStatus === 'pending') &&
        isCoffeeOrder && !isBeansOnly;
    
    if (shouldStartUpdater) {
        console.log('🚀 啟動條件滿足，創建更新器');
        window.orderUpdater = new UnifiedOrderUpdater(orderId);
        window.orderUpdater.start();
        
        // 添加連接狀態指示器（如果不存在）
        if (!document.getElementById('ws-connection-status')) {
            const indicator = document.createElement('div');
            indicator.id = 'ws-connection-status';
            indicator.className = 'connection-status connected';
            indicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 14px;
                display: flex;
                align-items: center;
                gap: 6px;
                background: rgba(0,0,0,0.8);
                color: white;
                z-index: 1000;
                backdrop-filter: blur(4px);
            `;
            indicator.innerHTML = '<i class="fas fa-circle mr-1" style="font-size: 10px;"></i><span>即時連線中</span>';
            document.body.appendChild(indicator);
        }
    } else {
        console.log('⏸️ 不啟動更新器，原因:', {
            hasOrderId: !!orderId,
            paymentStatus,
            isCoffeeOrder,
            isBeansOnly,
            shouldStartUpdater
        });
    }
}

// 頁面加載完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        try {
            initUnifiedOrderUpdater();
        } catch (error) {
            console.error('❌ 初始化更新器失敗:', error);
        }
    });
} else {
    // 如果DOM已經加載完成，直接初始化
    setTimeout(function() {
        try {
            initUnifiedOrderUpdater();
        } catch (error) {
            console.error('❌ 初始化更新器失敗:', error);
        }
    }, 100);
}

// 全局錯誤處理
window.addEventListener('error', function(event) {
    console.error('JavaScript錯誤被捕獲:', event.error);
    event.preventDefault();
    return true;
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// 導出初始化函數
window.initUnifiedOrderUpdater = initUnifiedOrderUpdater;
