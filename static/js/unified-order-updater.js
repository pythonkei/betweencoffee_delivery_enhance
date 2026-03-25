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
        
        // 緩存相關屬性
        this.cache = {
            lastData: null,
            lastUpdateTime: 0,
            cacheDuration: 5000, // 5秒緩存時間
            statusCache: {} // 狀態緩存，用於檢測狀態變化
        };
        
        console.log(`🔧 創建統一的訂單更新器 #${orderId}`);
        console.log(`   WebSocket 支持: ${this.useWebSocket ? '✅ 是' : '❌ 否'}`);
        console.log(`   緩存機制: ✅ 已啟用 (${this.cache.cacheDuration}ms)`);
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
        
        // 檢查緩存：如果最近更新過且數據相同，跳過本次更新
        const now = Date.now();
        const timeSinceLastUpdate = now - this.cache.lastUpdateTime;
        
        if (timeSinceLastUpdate < this.cache.cacheDuration && this.cache.lastData) {
            console.log(`⏭️ 跳過更新，緩存有效期內 (${timeSinceLastUpdate}ms < ${this.cache.cacheDuration}ms)`);
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
            
            // 檢查數據是否有實際變化
            if (this.hasDataChanged(data)) {
                console.log('✅ API 更新成功（數據有變化）:', data);
                this.handleUpdate(data);
                
                // 更新緩存
                this.cache.lastData = data;
                this.cache.lastUpdateTime = now;
                
                // 如果訂單已完成，停止更新
                if (data.is_ready || data.status === 'completed' || data.status === 'ready') {
                    console.log('🎉 訂單已完成，停止更新器');
                    this.stop();
                }
            } else {
                console.log('⏭️ 數據無變化，跳過界面更新');
                // 仍然更新緩存時間，但不需要更新界面
                this.cache.lastUpdateTime = now;
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
        
        // ✅ 修復：添加調試日誌，顯示完整的數據結構
        console.log('📊 完整數據結構:', JSON.stringify(data, null, 2));
        
        // 提取實際的訂單數據
        const orderData = this.extractOrderData(data);
        console.log('📦 提取後的訂單數據:', orderData);
        
        // 驗證數據格式
        if (!this.validateData(orderData)) {
            console.error('❌ 數據格式無效:', orderData);
            return;
        }
        
        console.log('✅ 數據驗證通過，開始更新UI');
        
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
        
        console.log('✅ UI更新完成');
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
        
        // ✅ 修復：始終使用前端的 getStatusDisplay() 方法，忽略後端返回的 status_display
        // 這樣可以確保狀態顯示的一致性，避免後端返回「等待制作」而前端顯示「等待製作」的問題
        const statusDisplay = this.getStatusDisplay(status);
        
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
        
        console.log(`✅ 更新狀態卡片: ${status} (前端顯示: ${statusDisplay})`);
        
        // ✅ 新增：記錄後端返回的 status_display 以便調試
        if (data.status_display && data.status_display !== statusDisplay) {
            console.log(`ℹ️ 後端返回的 status_display: "${data.status_display}"，前端顯示: "${statusDisplay}"`);
        }
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
        
        // ✅ 修復：使用正確的時間戳
        // 對於 waiting 狀態，應該使用訂單創建時間或支付時間，而不是 updated_at
        // 優先級：created_at > paid_at > updated_at > 當前時間
        let timestamp = data.created_at || data.paid_at || data.updated_at;
        
        // 如果沒有時間戳，根據狀態決定是否使用當前時間
        if (!timestamp) {
            // 對於初始狀態（waiting/pending），使用訂單創建時間或當前時間
            if (status === 'waiting' || status === 'pending') {
                // 嘗試從數據中獲取創建時間
                if (data.created_at) {
                    timestamp = data.created_at;
                } else {
                    // 如果沒有創建時間，使用當前時間（至少顯示有意義的時間）
                    timestamp = new Date().toISOString();
                }
            } else {
                // 對於其他狀態，使用當前時間作為備用
                timestamp = new Date().toISOString();
            }
        }
        
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
        
        console.log(`📊 更新時間軸: status=${status}, currentStepIndex=${currentStepIndex}, timestamp=${timestamp}`);
        
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
                if (timeEl) {
                    if (timestamp) {
                        timeEl.textContent = this.formatTime(timestamp);
                    } else {
                        timeEl.textContent = '--:--';
                    }
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
    
    // ========== 緩存相關方法 ==========
    
    /**
     * 檢查數據是否有實際變化
     */
    hasDataChanged(newData) {
        const oldData = this.cache.lastData;
        
        // 如果沒有緩存數據，視為有變化
        if (!oldData) {
            console.log('🆕 首次更新，視為有變化');
            return true;
        }
        
        // 檢查關鍵字段是否有變化
        const keyFields = ['status', 'queue_position', 'progress_percentage', 'is_ready'];
        
        for (const field of keyFields) {
            const oldValue = oldData[field];
            const newValue = newData[field];
            
            // 如果字段存在且值不同
            if (newValue !== undefined && oldValue !== newValue) {
                console.log(`🔄 字段 "${field}" 有變化: ${oldValue} -> ${newValue}`);
                return true;
            }
        }
        
        // 檢查時間戳是否有顯著變化（超過30秒）
        const oldTimestamp = oldData.updated_at || oldData.timestamp;
        const newTimestamp = newData.updated_at || newData.timestamp;
        
        if (oldTimestamp && newTimestamp) {
            const oldTime = new Date(oldTimestamp).getTime();
            const newTime = new Date(newTimestamp).getTime();
            const timeDiff = Math.abs(newTime - oldTime);
            
            if (timeDiff > 30000) { // 30秒
                console.log(`🕒 時間戳有顯著變化: ${timeDiff}ms`);
                return true;
            }
        }
        
        console.log('✅ 數據無顯著變化');
        return false;
    }
    
    // ========== 輔助方法 ==========
    
    getStatusDisplay(status) {
        const map = {
            'waiting': '等待製作',      // ✅ 修復：為 waiting 狀態提供獨立的顯示文本
            'pending': '處理中',
            'preparing': '製作中',
            'ready': '待取餐',
            'completed': '已完成'
        };
        return map[status] || status;
    }
    
    getStatusDescription(status) {
        const map = {
            'waiting': '您的訂單已支付成功，正在等待咖啡師開始製作。',  // ✅ 修復：為 waiting 狀態提供獨立的描述
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
    
    // ========== 診斷方法 ==========
    
    /**
     * WebSocket診斷報告
     */
    diagnose() {
        console.group('🔍 WebSocket診斷報告');
        console.log('訂單ID:', this.orderId);
        console.log('更新器運行狀態:', this.isRunning);
        console.log('WebSocket支持:', this.useWebSocket);
        console.log('WebSocket URL:', this.socket?.url || '無連接');
        console.log('WebSocket連接狀態:', this.socket ? this.getWebSocketStateText(this.socket.readyState) : '無連接');
        console.log('重試次數:', this.reconnectAttempts);
        console.log('更新次數:', this.updateCount);
        console.log('最後緩存時間:', this.cache.lastUpdateTime ? new Date(this.cache.lastUpdateTime).toLocaleTimeString() : '無');
        console.log('最後緩存數據:', this.cache.lastData);
        console.groupEnd();
        
        // 更新頁面顯示
        this.updateDiagnosticDisplay();
    }
    
    /**
     * 獲取WebSocket狀態文本
     */
    getWebSocketStateText(state) {
        switch(state) {
            case 0: return '連接中 (CONNECTING)';
            case 1: return '已連接 (OPEN)';
            case 2: return '關閉中 (CLOSING)';
            case 3: return '已關閉 (CLOSED)';
            default: return `未知狀態 (${state})`;
        }
    }
    
    /**
     * 更新診斷顯示
     */
    updateDiagnosticDisplay() {
        const statusText = document.getElementById('connection-status-text');
        if (statusText) {
            if (this.socket) {
                const stateText = this.getWebSocketStateText(this.socket.readyState);
                statusText.textContent = `WebSocket: ${stateText}`;
            } else {
                statusText.textContent = 'API輪詢模式';
            }
        }
        
        const timestampEl = document.getElementById('last-update-timestamp');
        if (timestampEl && this.cache.lastUpdateTime) {
            timestampEl.textContent = new Date(this.cache.lastUpdateTime).toLocaleTimeString('zh-HK', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }
    
    /**
     * 手動刷新訂單狀態
     */
    manualRefresh() {
        console.log('🔄 手動刷新訂單狀態');
        
        // 強制清除緩存，確保獲取最新數據
        this.cache.lastUpdateTime = 0;
        this.cache.lastData = null;
        
        // 立即獲取訂單狀態
        this.fetchOrderStatus();
        
        // 顯示提示
        this.showManualRefreshToast();
    }
    
    /**
     * 顯示手動刷新提示
     */
    showManualRefreshToast() {
        if (window.toast) {
            window.toast.info('正在刷新訂單狀態...', '手動刷新');
        }
        
        // 更新最後更新時間顯示
        const timestampEl = document.getElementById('last-update-timestamp');
        if (timestampEl) {
            timestampEl.textContent = '刷新中...';
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
        
        // 添加手動刷新按鈕事件監聽器
        const manualRefreshBtn = document.getElementById('manual-refresh-btn');
        if (manualRefreshBtn) {
            manualRefreshBtn.addEventListener('click', () => {
                if (window.orderUpdater) {
                    window.orderUpdater.manualRefresh();
                }
            });
        }
        
        // 添加診斷按鈕（開發環境）
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            const diagnoseBtn = document.createElement('button');
            diagnoseBtn.id = 'diagnose-btn';
            diagnoseBtn.className = 'btn btn-sm btn-outline-info mt-2';
            diagnoseBtn.innerHTML = '<i class="fas fa-stethoscope mr-1"></i>診斷連線';
            diagnoseBtn.addEventListener('click', () => {
                if (window.orderUpdater) {
                    window.orderUpdater.diagnose();
                }
            });
            
            const buttonContainer = document.querySelector('.mt-4.text-center');
            if (buttonContainer) {
                buttonContainer.appendChild(diagnoseBtn);
            }
        }
        
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
        
        // 初始診斷顯示
        setTimeout(() => {
            if (window.orderUpdater) {
                window.orderUpdater.updateDiagnosticDisplay();
            }
        }, 1000);
        
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

// 全局錯誤處理（優化：過濾第三方庫錯誤）
window.addEventListener('error', function(event) {
    // ✅ 修復：過濾第三方庫錯誤（如 Bootstrap 的 Explain 錯誤）
    const errorMessage = event.error ? event.error.toString() : '';
    const errorStack = event.error ? event.error.stack : '';
    
    // 檢查是否為第三方庫錯誤
    const isThirdPartyError = 
        errorMessage.includes('Explain is not defined') ||
        errorMessage.includes('bootstrap.bundle.min.js') ||
        errorStack.includes('bootstrap.bundle.min.js');
    
    if (isThirdPartyError) {
        // 第三方庫錯誤，只記錄警告，不影響用戶體驗
        console.warn('⚠️ 第三方庫錯誤（已過濾）:', errorMessage);
        event.preventDefault();
        return true;
    } else {
        // 我們的代碼錯誤，記錄錯誤
        console.error('❌ JavaScript錯誤被捕獲:', event.error);
        event.preventDefault();
        return true;
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// 導出初始化函數
window.initUnifiedOrderUpdater = initUnifiedOrderUpdater;
