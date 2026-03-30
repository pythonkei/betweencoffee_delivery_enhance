// static/js/unified-order-updater-enhanced.js
// ==================== 統一的訂單狀態更新器 - 增強版 ====================
// 功能：結合 WebSocket 增強連接器 + API 輪詢，提供企業級實時更新

/**
 * 統一的訂單狀態更新器 - 增強版
 * 結合 WebSocket 增強連接器（智能重連、心跳檢測、離線佇列）和 API 輪詢（備用）
 * 提供企業級的訂單狀態實時更新解決方案
 */
class UnifiedOrderUpdaterEnhanced {
    constructor(orderId, options = {}) {
        this.orderId = orderId;
        this.options = {
            // WebSocket 配置
            useWebSocket: true,
            wsUrl: null, // 自動生成
            wsReconnectOptions: {
                baseDelay: 1000,
                maxDelay: 30000,
                maxRetries: 10,
                jitterFactor: 0.2,
                enableJitter: true
            },
            
            // API 輪詢配置
            pollingEnabled: true,
            pollingInterval: 10000, // 10秒
            maxPollingUpdates: 180, // 最多180次更新（30分鐘）
            
            // 緩存配置
            cacheEnabled: true,
            cacheDuration: 5000, // 5秒緩存
            
            // 監控配置
            enableMonitoring: true,
            enableDiagnostics: true,
            
            // 事件系統
            enableEvents: true,
            
            // 兼容性配置
            legacyMode: false, // 是否啟用舊API兼容
            
            ...options
        };
        
        // 狀態管理
        this.isRunning = false;
        this.updateCount = 0;
        
        // 緩存系統
        this.cache = {
            lastData: null,
            lastUpdateTime: 0,
            statusCache: {},
            dataVersion: 0
        };
        
        // 監控指標
        this.metrics = {
            totalUpdates: 0,
            wsUpdates: 0,
            apiUpdates: 0,
            wsConnections: 0,
            wsDisconnections: 0,
            reconnectAttempts: 0,
            lastError: null,
            lastErrorTime: null,
            avgUpdateLatency: 0,
            startTime: null
        };
        
        // WebSocket 增強連接器
        this.wsConnector = null;
        
        // API 輪詢定時器
        this.pollingTimer = null;
        
        // 事件監聽器
        this.eventListeners = {
            update: [],
            statusChange: [],
            connectionChange: [],
            error: [],
            complete: []
        };
        
        // 初始化
        this.initialize();
        
        console.log(`🔧 創建統一的訂單更新器增強版 #${orderId}`);
        console.log(`   配置: WebSocket=${this.options.useWebSocket}, 輪詢=${this.options.pollingEnabled}`);
        console.log(`   緩存: ${this.options.cacheEnabled ? '✅ 已啟用' : '❌ 已禁用'}`);
        console.log(`   監控: ${this.options.enableMonitoring ? '✅ 已啟用' : '❌ 已禁用'}`);
    }
    
    // ========== 初始化方法 ==========
    
    /**
     * 初始化更新器
     */
    initialize() {
        // 設置 WebSocket URL
        if (!this.options.wsUrl) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.options.wsUrl = `${protocol}//${window.location.host}/ws/order/${this.orderId}/`;
        }
        
        // 初始化監控
        if (this.options.enableMonitoring) {
            this.metrics.startTime = Date.now();
        }
        
        // 初始化事件系統
        if (this.options.enableEvents) {
            this.setupEventSystem();
        }
        
        // 初始化診斷工具
        if (this.options.enableDiagnostics) {
            this.setupDiagnostics();
        }
    }
    
    /**
     * 設置事件系統
     */
    setupEventSystem() {
        // 創建自定義事件類型
        this.eventTypes = {
            UPDATE: 'unified_order_updater:update',
            STATUS_CHANGE: 'unified_order_updater:status_change',
            CONNECTION_CHANGE: 'unified_order_updater:connection_change',
            ERROR: 'unified_order_updater:error',
            COMPLETE: 'unified_order_updater:complete'
        };
    }
    
    /**
     * 設置診斷工具
     */
    setupDiagnostics() {
        // 創建診斷面板（開發環境）
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.createDiagnosticPanel();
        }
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
        this.metrics.startTime = Date.now();
        
        console.log('🚀 啟動統一的訂單更新器增強版');
        
        // 觸發連接變化事件
        this.triggerEvent('connectionChange', {
            status: 'starting',
            timestamp: new Date().toISOString()
        });
        
        // 優先使用 WebSocket
        if (this.options.useWebSocket && this.checkWebSocketSupport()) {
            this.connectWebSocket();
        } else if (this.options.pollingEnabled) {
            console.log('ℹ️ WebSocket 不可用或已禁用，使用 API 輪詢');
            this.startPolling();
        } else {
            console.error('❌ 無可用的更新機制');
            this.triggerEvent('error', {
                type: 'no_update_mechanism',
                message: '無可用的更新機制'
            });
        }
        
        // 立即更新一次
        this.fetchOrderStatus();
        
        // 更新連接狀態顯示
        this.updateConnectionStatus('starting', '啟動中...');
    }
    
    /**
     * 停止更新器
     */
    stop() {
        this.isRunning = false;
        
        // 停止 WebSocket
        if (this.wsConnector) {
            this.wsConnector.disconnect();
            this.wsConnector = null;
        }
        
        // 停止輪詢
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
            this.pollingTimer = null;
        }
        
        // 觸發完成事件
        this.triggerEvent('complete', {
            reason: 'manual_stop',
            timestamp: new Date().toISOString(),
            metrics: this.getMetrics()
        });
        
        console.log('🛑 訂單更新器增強版已停止');
        this.updateConnectionStatus('stopped', '已停止');
    }
    
    // ========== WebSocket 增強連接 ==========
    
    /**
     * 檢查 WebSocket 支持
     */
    checkWebSocketSupport() {
        return 'WebSocket' in window && window.WebSocket !== null;
    }
    
    /**
     * 連接 WebSocket（使用增強連接器）
     */
    connectWebSocket() {
        if (!this.options.useWebSocket || !this.isRunning) return;
        
        console.log(`🔗 連接增強 WebSocket: ${this.options.wsUrl}`);
        
        try {
            // 使用增強 WebSocket 連接器
            if (window.EnhancedWebSocketConnector) {
                this.wsConnector = new window.EnhancedWebSocketConnector(
                    this.options.wsUrl,
                    {
                        reconnectOptions: this.options.wsReconnectOptions,
                        heartbeatEnabled: true,
                        heartbeatInterval: 25000,
                        heartbeatTimeout: 10000
                    }
                );
                
                // 設置事件監聽器
                this.wsConnector.addEventListener('open', (event) => {
                    this.handleWebSocketOpen(event);
                });
                
                this.wsConnector.addEventListener('message', (event) => {
                    this.handleWebSocketMessage(event);
                });
                
                this.wsConnector.addEventListener('error', (event) => {
                    this.handleWebSocketError(event);
                });
                
                this.wsConnector.addEventListener('close', (event) => {
                    this.handleWebSocketClose(event);
                });
                
                this.wsConnector.addEventListener('reconnect', (event) => {
                    this.handleWebSocketReconnect(event);
                });
                
                this.wsConnector.addEventListener('healthChange', (event) => {
                    this.handleWebSocketHealthChange(event);
                });
                
                // 連接 WebSocket
                this.wsConnector.connect();
                
                this.metrics.wsConnections++;
                
            } else {
                console.warn('⚠️ 增強 WebSocket 連接器不可用，使用基本 WebSocket');
                this.connectBasicWebSocket();
            }
            
        } catch (error) {
            console.error('❌ WebSocket 連接失敗:', error);
            this.triggerEvent('error', {
                type: 'websocket_connection_failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
            
            this.fallbackToPolling();
        }
    }
    
    /**
     * 連接基本 WebSocket（兼容模式）
     */
    connectBasicWebSocket() {
        try {
            this.wsConnector = {
                socket: new WebSocket(this.options.wsUrl),
                isEnhanced: false
            };
            
            this.wsConnector.socket.onopen = (event) => {
                this.handleWebSocketOpen(event);
            };
            
            this.wsConnector.socket.onmessage = (event) => {
                this.handleWebSocketMessage({ data: event.data });
            };
            
            this.wsConnector.socket.onerror = (event) => {
                this.handleWebSocketError(event);
            };
            
            this.wsConnector.socket.onclose = (event) => {
                this.handleWebSocketClose(event);
            };
            
            this.metrics.wsConnections++;
            
        } catch (error) {
            console.error('❌ 基本 WebSocket 連接失敗:', error);
            this.fallbackToPolling();
        }
    }
    
    /**
     * 處理 WebSocket 打開事件
     */
    handleWebSocketOpen(event) {
        console.log('✅ WebSocket 連接成功');
        this.metrics.reconnectAttempts = 0;
        
        this.updateConnectionStatus('connected', '即時連線中');
        
        this.triggerEvent('connectionChange', {
            status: 'connected',
            type: 'websocket',
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * 處理 WebSocket 消息事件
     */
    handleWebSocketMessage(event) {
        try {
            const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
            console.log('📨 收到 WebSocket 更新:', data.type || '未知類型');
            
            this.metrics.wsUpdates++;
            this.metrics.totalUpdates++;
            
            this.handleUpdate(data);
            
        } catch (error) {
            console.error('❌ 解析 WebSocket 消息失敗:', error);
            this.triggerEvent('error', {
                type: 'websocket_message_parse_error',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    /**
     * 處理 WebSocket 錯誤事件
     */
    handleWebSocketError(event) {
        console.error('❌ WebSocket 錯誤:', event);
        
        this.metrics.lastError = event;
        this.metrics.lastErrorTime = new Date().toISOString();
        
        this.updateConnectionStatus('error', '連線錯誤');
        
        this.triggerEvent('error', {
            type: 'websocket_error',
            error: event,
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * 處理 WebSocket 關閉事件
     */
    handleWebSocketClose(event) {
        console.log(`🔌 WebSocket 關閉: code=${event.code}, reason=${event.reason}`);
        
        this.metrics.wsDisconnections++;
        
        this.updateConnectionStatus('disconnected', '連線中斷');
        
        this.triggerEvent('connectionChange', {
            status: 'disconnected',
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString()
        });
        
        // 如果不是正常關閉，嘗試回退到輪詢
        if (event.code !== 1000 && this.options.pollingEnabled) {
            this.fallbackToPolling();
        }
    }
    
    /**
     * 處理 WebSocket 重連事件
     */
    handleWebSocketReconnect(event) {
        console.log(`🔄 WebSocket 重連嘗試: ${event.attempt}/${event.maxRetries}`);
        
        this.metrics.reconnectAttempts++;
        
        this.updateConnectionStatus('reconnecting', `重新連線中 (${event.attempt})`);
        
        this.triggerEvent('connectionChange', {
            status: 'reconnecting',
            attempt: event.attempt,
            delay: event.delay,
            maxRetries: event.maxRetries,
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * 處理 WebSocket 健康度變化
     */
    handleWebSocketHealthChange(event) {
        console.log(`📊 WebSocket 健康度變化: ${event.healthScore}分`);
        
        // 更新連接狀態顯示
        let statusText = '即時連線中';
        if (event.healthScore < 50) {
            statusText = '連線品質不佳';
        } else if (event.healthScore < 80) {
            statusText = '連線一般';
        }
        
        this.updateConnectionStatus('connected', statusText);
    }
    
    /**
     * 回退到 API 輪詢
     */
    fallbackToPolling() {
        if (!this.options.pollingEnabled) {
            console.error('❌ API 輪詢已禁用，無法回退');
            return;
        }
        
        console.log('🔄 切換到 API 輪詢模式');
        
        this.updateConnectionStatus('polling', '輪詢更新中');
        
        this.triggerEvent('connectionChange', {
            status: 'polling',
            reason: 'websocket_fallback',
            timestamp: new Date().toISOString()
        });
        
        this.startPolling();
    }
    
    // ========== API 輪詢方法 ==========
    
    /**
     * 啟動 API 輪詢
     */
    startPolling() {
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
        }
        
        // 立即執行第一次輪詢
        this.fetchOrderStatus();
        
        // 設置定期輪詢
        this.pollingTimer = setInterval(() => {
            this.fetchOrderStatus();
        }, this.options.pollingInterval);
        
        console.log(`⏰ API 輪詢已啟動（每${this.options.pollingInterval/1000}秒更新一次）`);
    }
    
    /**
     * 獲取訂單狀態
     */
    async fetchOrderStatus() {
        if (!this.isRunning) return;
        
        // 檢查更新次數限制
        if (this.updateCount >= this.options.maxPollingUpdates) {
            console.log('ℹ️ 達到最大更新次數，停止更新');
            this.stop();
            return;
        }
        
        // 檢查緩存：如果最近更新過且數據相同，跳過本次更新
        if (this.options.cacheEnabled) {
            const now = Date.now();
            const timeSinceLastUpdate = now - this.cache.lastUpdateTime;
            
            if (timeSinceLastUpdate < this.options.cacheDuration && this.cache.lastData) {
                console.log(`⏭️ 跳過更新，緩存有效期內 (${timeSinceLastUpdate}ms < ${this.options.cacheDuration}ms)`);
                return;
            }
        }
        
        this.updateCount++;
        
        try {
            const apiUrl = `/eshop/order/api/order-status/${this.orderId}/`;
            console.log(`📡 調用 API: ${apiUrl} (${this.updateCount}/${this.options.maxPollingUpdates})`);
            
            const startTime = Date.now();
            const response = await fetch(apiUrl);
            const endTime = Date.now();
            
            // 計算延遲
            const latency = endTime - startTime;
            this.updateAverageLatency(latency);
            
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態碼: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                console.error('❌ 獲取訂單狀態失敗:', data.error);
                this.triggerEvent('error', {
                    type: 'api_error',
                    error: data.error,
                    timestamp: new Date().toISOString()
                });
                return;
            }
            
            this.metrics.apiUpdates++;
            this.metrics.totalUpdates++;
            
            // 檢查數據是否有實際變化
            if (!this.options.cacheEnabled || this.hasDataChanged(data)) {
                console.log('✅ API 更新成功（數據有變化）:', data);
                this.handleUpdate(data);
                
                // 更新緩存
                if (this.options.cacheEnabled) {
                    this.cache.lastData = data;
                    this.cache.lastUpdateTime = Date.now();
                    this.cache.dataVersion++;
                }
                
                // 如果訂單已完成，停止更新
                if (data.is_ready || data.status === 'completed' || data.status === 'ready') {
                    console.log('🎉 訂單已完成，停止更新器');
                    this.stop();
                    
                    this.triggerEvent('complete', {
                        reason: 'order_completed',
                        status: data.status,
                        timestamp: new Date().toISOString(),
                        data: data
                    });
                }
                
            } else {
                console.log('⏭️ 數據無變化，跳過界面更新');
                // 仍然更新緩存時間，但不需要更新界面
                if (this.options.cacheEnabled) {
                    this.cache.lastUpdateTime = Date.now();
                }
            }
            
        } catch (error) {
            console.error('❌ 訂單狀態更新失敗:', error);
            this.triggerEvent('error', {
                type: 'fetch_order_status_failed',
                error: error.message,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    // ========== 更新處理方法 ==========
    
    /**
     * 處理更新數據
     */
    handleUpdate(data) {
        console.log('🔍 處理更新數據:', data.type || '未知類型');
        
        // 提取實際的訂單數據
        const orderData = this.extractOrderData(data);
        console.log('📦 提取後的訂單數據:', orderData);
        
        // 驗證數據格式
        if (!this.validateData(orderData)) {
            console.error('❌ 數據格式無效:', orderData);
            return;
        }
        
        console.log('✅ 數據驗證通過，開始更新UI');
        
        // 觸發更新事件
        this.triggerEvent('update', {
            data: orderData,
            source: data.type === 'order_status' ? 'websocket' : 'api',
            timestamp: new Date().toISOString()
        });
        
        // 檢查狀態變化
        const oldStatus = this.cache.lastData?.status;
        const newStatus = orderData.status;
        
        if (oldStatus !== newStatus) {
            console.log(`🔄 狀態變化: ${oldStatus || '無'} -> ${newStatus}`);
            
            this.triggerEvent('statusChange', {
                oldStatus: oldStatus,
                newStatus: newStatus,
                data: orderData,
                timestamp: new Date().toISOString()
            });
        }
        
        // 更新UI（兼容舊版方法）
        this.updateUI(orderData);
        
        console.log('✅ UI更新完成');
    }
    
    /**
     * 提取訂單數據（支持多種格式）
     */
    extractOrderData(data) {
        // 格式1: WebSocket 格式 {type: 'order_status', data: {...}, timestamp: '...'}
        if (data.type === 'order_status' && data.data) {
            console.log('📦 提取 WebSocket 格式數據');
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
     * 更新UI（兼容舊版方法）
     */
    updateUI(data) {
        // 更新狀態卡片
        this.updateStatusCard(data);
        
        // 更新進度條
        this.updateProgressBar(data);
        
        // 更新時間軸
        this.updateTimeline(data);
        
        // 更新隊列信息
        this.updateQueueInfo(data);
        
        // 更新支付確認頁面的特定元素
        this.updatePaymentConfirmationElements(data);
    }
    
    /**
     * 更新狀態卡片（兼容舊版）
     */
    updateStatusCard(data) {
        const status = data.status;
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
        
        console.log(`✅ 更新狀態卡片: ${status} (顯示: ${statusDisplay})`);
    }
    
    /**
     * 更新狀態圖示（兼容舊版）
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
     * 更新進度條（兼容舊版）
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
     * 更新時間軸（兼容舊版）
     */
    updateTimeline(data) {
        const status = data.status;
        
        // 獲取時間戳
        let timestamp = data.created_at || data.paid_at || data.updated_at;
        
        if (!timestamp) {
            if (status === 'waiting' || status === 'pending') {
                timestamp = data.created_at || new Date().toISOString();
            } else {
                timestamp = new Date().toISOString();
            }
        }
        
        const steps = ['pending', 'preparing', 'ready', 'completed'];
        
        // 定義狀態順序
        const statusOrder = {
            'waiting': 0,
            'pending': 0,
            'preparing': 1,
            'ready': 2,
            'completed': 3
        };
        
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
            } else if (index === currentStepIndex) {
                // 當前步驟
                stepEl.classList.add('active');
                if (timeEl && timestamp) {
                    timeEl.textContent = this.formatTime(timestamp);
                }
            } else {
                // 未到達的步驟
                if (timeEl) timeEl.textContent = '--:--';
            }
        });
    }
    
    /**
     * 更新隊列信息（兼容舊版）
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
     * 更新支付確認頁面的特定元素（兼容舊版）
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
    
    /**
     * 更新平均延遲
     */
    updateAverageLatency(latency) {
        if (this.metrics.avgUpdateLatency === 0) {
            this.metrics.avgUpdateLatency = latency;
        } else {
            // 加權平均
            this.metrics.avgUpdateLatency = 
                0.8 * this.metrics.avgUpdateLatency + 0.2 * latency;
        }
    }
    
    // ========== 事件系統方法 ==========
    
    /**
     * 添加事件監聽器
     */
    on(eventType, callback) {
        if (this.eventListeners[eventType]) {
            this.eventListeners[eventType].push(callback);
        }
        
        return () => this.off(eventType, callback); // 返回取消函數
    }
    
    /**
     * 移除事件監聽器
     */
    off(eventType, callback) {
        if (this.eventListeners[eventType]) {
            const listeners = this.eventListeners[eventType];
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    /**
     * 觸發事件
     */
    triggerEvent(eventType, detail = {}) {
        if (!this.options.enableEvents) return;
        
        // 觸發內部監聽器
        if (this.eventListeners[eventType]) {
            this.eventListeners[eventType].forEach(callback => {
                try {
                    callback({
                        ...detail,
                        orderId: this.orderId,
                        timestamp: new Date().toISOString()
                    });
                } catch (error) {
                    console.error(`❌ 執行事件監聽器 ${eventType} 失敗:`, error);
                }
            });
        }
        
        // 觸發DOM事件
        const event = new CustomEvent(`unified_order_updater:${eventType}`, {
            detail: {
                ...detail,
                orderId: this.orderId,
                timestamp: new Date().toISOString()
            },
            bubbles: true
        });
        
        document.dispatchEvent(event);
        console.log(`📢 觸發事件: unified_order_updater:${eventType}`, detail);
    }
    
    // ========== 監控和診斷方法 ==========
    
    /**
     * 獲取監控指標
     */
    getMetrics() {
        const now = Date.now();
        const uptime = this.metrics.startTime ? now - this.metrics.startTime : 0;
        
        return {
            ...this.metrics,
            uptime: uptime,
            uptimeFormatted: this.formatDuration(uptime),
            avgUpdateLatency: Math.round(this.metrics.avgUpdateLatency),
            updateFrequency: this.metrics.totalUpdates > 0 
                ? Math.round(uptime / this.metrics.totalUpdates) 
                : 0,
            wsUpdateRatio: this.metrics.totalUpdates > 0 
                ? Math.round((this.metrics.wsUpdates / this.metrics.totalUpdates) * 100) 
                : 0,
            apiUpdateRatio: this.metrics.totalUpdates > 0 
                ? Math.round((this.metrics.apiUpdates / this.metrics.totalUpdates) * 100) 
                : 0
        };
    }
    
    /**
     * 創建診斷面板
     */
    createDiagnosticPanel() {
        const panel = document.createElement('div');
        panel.id = 'unified-order-updater-diagnostic-panel';
        panel.style.cssText = `
            position: fixed;
            bottom: 60px;
            right: 20px;
            width: 350px;
            max-height: 400px;
            background: rgba(0,0,0,0.9);
            color: white;
            border-radius: 8px;
            padding: 15px;
            z-index: 9999;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            border: 1px solid #444;
        `;
        
        panel.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; font-size: 14px;">📊 訂單更新器診斷</h4>
                <button id="close-diagnostic-panel" style="
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 16px;
                ">×</button>
            </div>
            <div id="diagnostic-content"></div>
            <div style="margin-top: 10px; display: flex; gap: 8px;">
                <button id="refresh-diagnostic" style="
                    padding: 4px 8px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                ">刷新</button>
                <button id="export-diagnostic" style="
                    padding: 4px 8px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                ">導出JSON</button>
                <button id="clear-diagnostic" style="
                    padding: 4px 8px;
                    background: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                ">清除</button>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // 設置事件監聽器
        document.getElementById('close-diagnostic-panel').addEventListener('click', () => {
            panel.remove();
        });
        
        document.getElementById('refresh-diagnostic').addEventListener('click', () => {
            this.updateDiagnosticPanel();
        });
        
        document.getElementById('export-diagnostic').addEventListener('click', () => {
            this.exportDiagnosticData();
        });
        
        document.getElementById('clear-diagnostic').addEventListener('click', () => {
            this.clearDiagnosticData();
        });
        
        // 初始更新
        this.updateDiagnosticPanel();
        
        // 定期更新
        this.diagnosticUpdateInterval = setInterval(() => {
            this.updateDiagnosticPanel();
        }, 2000);
        
        console.log('🔧 診斷面板已創建');
    }
    
    /**
     * 更新診斷面板
     */
    updateDiagnosticPanel() {
        const contentEl = document.getElementById('diagnostic-content');
        if (!contentEl) return;
        
        const metrics = this.getMetrics();
        const connectionStatus = this.getConnectionStatus();
        
        contentEl.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>訂單ID:</strong> ${this.orderId}<br>
                <strong>運行狀態:</strong> ${this.isRunning ? '✅ 運行中' : '❌ 已停止'}<br>
                <strong>運行時間:</strong> ${metrics.uptimeFormatted}<br>
                <strong>總更新次數:</strong> ${metrics.totalUpdates}
            </div>
            
            <div style="margin-bottom: 10px; padding: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
                <strong>連接狀態:</strong><br>
                <span style="color: ${connectionStatus.color}">${connectionStatus.icon} ${connectionStatus.text}</span><br>
                <strong>WebSocket:</strong> ${metrics.wsUpdates} 次<br>
                <strong>API輪詢:</strong> ${metrics.apiUpdates} 次<br>
                <strong>重連嘗試:</strong> ${metrics.reconnectAttempts} 次
            </div>
            
            <div style="margin-bottom: 10px;">
                <strong>性能指標:</strong><br>
                <strong>平均延遲:</strong> ${metrics.avgUpdateLatency}ms<br>
                <strong>更新頻率:</strong> ${metrics.updateFrequency}ms/次<br>
                <strong>WebSocket比例:</strong> ${metrics.wsUpdateRatio}%<br>
                <strong>API比例:</strong> ${metrics.apiUpdateRatio}%
            </div>
            
            <div style="margin-bottom: 10px; font-size: 11px; color: #aaa;">
                <strong>緩存信息:</strong><br>
                <strong>數據版本:</strong> ${this.cache.dataVersion}<br>
                <strong>最後更新:</strong> ${this.cache.lastUpdateTime ? new Date(this.cache.lastUpdateTime).toLocaleTimeString() : '無'}<br>
                <strong>當前狀態:</strong> ${this.cache.lastData?.status || '未知'}
            </div>
            
            ${this.metrics.lastError ? `
                <div style="margin-bottom: 10px; padding: 8px; background: rgba(220,53,69,0.2); border-radius: 4px;">
                    <strong>最後錯誤:</strong><br>
                    <span style="color: #ff6b6b;">${this.metrics.lastErrorTime ? new Date(this.metrics.lastErrorTime).toLocaleTimeString() : '未知時間'}</span><br>
                    <span style="font-size: 10px;">${this.metrics.lastError.message || this.metrics.lastError}</span>
                </div>
            ` : ''}
        `;
    }
    
    /**
     * 導出診斷數據
     */
    exportDiagnosticData() {
        const data = {
            timestamp: new Date().toISOString(),
            orderId: this.orderId,
            metrics: this.getMetrics(),
            connectionStatus: this.getConnectionStatus(),
            cache: {
                dataVersion: this.cache.dataVersion,
                lastUpdateTime: this.cache.lastUpdateTime,
                lastStatus: this.cache.lastData?.status
            },
            options: this.options
        };
        
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `order-updater-diagnostic-${this.orderId}-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('📥 診斷數據已導出');
    }
    
    /**
     * 清除診斷數據
     */
    clearDiagnosticData() {
        this.metrics = {
            totalUpdates: 0,
            wsUpdates: 0,
            apiUpdates: 0,
            wsConnections: 0,
            wsDisconnections: 0,
            reconnectAttempts: 0,
            lastError: null,
            lastErrorTime: null,
            avgUpdateLatency: 0,
            startTime: Date.now()
        };
        
        console.log('🗑️ 診斷數據已清除');
        this.updateDiagnosticPanel();
    }
    
    /**
     * 獲取連接狀態
     */
    getConnectionStatus() {
        if (!this.isRunning) {
            return { text: '已停止', color: '#6c757d', icon: '🛑' };
        }
        
        if (this.wsConnector) {
            if (this.wsConnector.isEnhanced) {
                const status = this.wsConnector.getConnectionStatus();
                if (status.isConnected) {
                    return { text: 'WebSocket已連接', color: '#28a745', icon: '✅' };
                } else if (status.isConnecting) {
                    return { text: 'WebSocket連接中', color: '#ffc107', icon: '🔄' };
                }
            } else if (this.wsConnector.socket) {
                const state = this.wsConnector.socket.readyState;
                if (state === WebSocket.OPEN) {
                    return { text: 'WebSocket已連接', color: '#28a745', icon: '✅' };
                } else if (state === WebSocket.CONNECTING) {
                    return { text: 'WebSocket連接中', color: '#ffc107', icon: '🔄' };
                }
            }
        }
        
        if (this.pollingTimer) {
            return { text: 'API輪詢中', color: '#17a2b8', icon: '⏰' };
        }
        
        return { text: '未知狀態', color: '#6c757d', icon: '❓' };
    }
    
    // ========== UI輔助方法 ==========
    
    /**
     * 更新連接狀態顯示
     */
    updateConnectionStatus(status, message) {
        const indicator = document.getElementById('ws-connection-status');
        if (!indicator) return;
        
        indicator.className = 'connection-status';
        let icon = '';
        let color = '';
        
        switch (status) {
            case 'connected':
                indicator.classList.add('connected');
                icon = '<i class="fas fa-circle mr-1" style="font-size: 10px;"></i>';
                color = '#28a745';
                break;
            case 'disconnected':
                indicator.classList.add('disconnected');
                icon = '<i class="fas fa-exclamation-triangle mr-1"></i>';
                color = '#dc3545';
                break;
            case 'reconnecting':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-sync-alt mr-1 fa-spin"></i>';
                color = '#ffc107';
                break;
            case 'polling':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-sync mr-1"></i>';
                color = '#17a2b8';
                break;
            case 'starting':
                indicator.classList.add('reconnecting');
                icon = '<i class="fas fa-spinner mr-1 fa-pulse"></i>';
                color = '#6c757d';
                break;
            case 'stopped':
                indicator.classList.add('disconnected');
                icon = '<i class="fas fa-stop-circle mr-1"></i>';
                color = '#6c757d';
                break;
            case 'error':
                indicator.classList.add('disconnected');
                icon = '<i class="fas fa-exclamation-circle mr-1"></i>';
                color = '#dc3545';
                break;
        }
        
        indicator.innerHTML = icon + '<span>' + message + '</span>';
        indicator.style.backgroundColor = color;
    }
    
    /**
     * 創建連接狀態指示器
     */
    createConnectionIndicator() {
        let indicator = document.getElementById('ws-connection-status');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'ws-connection-status';
            indicator.className = 'connection-status';
            indicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 14px;
                z-index: 1000;
                background: rgba(0,0,0,0.8);
                color: white;
                display: flex;
                align-items: center;
                gap: 6px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                cursor: pointer;
                transition: all 0.3s ease;
                backdrop-filter: blur(4px);
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
        const metrics = this.getMetrics();
        const connectionStatus = this.getConnectionStatus();
        
        const details = `
            WebSocket 連線詳情
            ═══════════════════
            訂單ID: ${this.orderId}
            連線狀態: ${connectionStatus.text}
            運行時間: ${metrics.uptimeFormatted}
            
            更新統計:
            ├─ 總更新次數: ${metrics.totalUpdates}
            ├─ WebSocket更新: ${metrics.wsUpdates} (${metrics.wsUpdateRatio}%)
            └─ API輪詢更新: ${metrics.apiUpdates} (${metrics.apiUpdateRatio}%)
            
            性能指標:
            ├─ 平均延遲: ${metrics.avgUpdateLatency}ms
            ├─ 更新頻率: ${metrics.updateFrequency}ms/次
            └─ 重連嘗試: ${metrics.reconnectAttempts}次
            
            緩存信息:
            ├─ 數據版本: ${this.cache.dataVersion}
            ├─ 最後更新: ${this.cache.lastUpdateTime ? new Date(this.cache.lastUpdateTime).toLocaleTimeString() : '無'}
            └─ 當前狀態: ${this.cache.lastData?.status || '未知'}
            
            ${this.metrics.lastError ? `
            最後錯誤:
            ├─ 時間: ${this.metrics.lastErrorTime ? new Date(this.metrics.lastErrorTime).toLocaleTimeString() : '未知'}
            └─ 錯誤: ${this.metrics.lastError.message || this.metrics.lastError}
            ` : ''}
            
            ⏱️ 最後更新: ${new Date().toLocaleTimeString()}
        `;
        
        // 使用toast顯示
        this.showNotification(details, 'info', 8000);
    }
    
    /**
     * 顯示通知
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
    
    // ========== 輔助方法 ==========
    
    getStatusDisplay(status) {
        const map = {
            'waiting': '等待製作',
            'pending': '處理中',
            'preparing': '製作中',
            'ready': '待取餐',
            'completed': '已完成'
        };
        return map[status] || status;
    }
    
    getStatusDescription(status) {
        const map = {
            'waiting': '您的訂單已支付成功，正在等待咖啡師開始製作。',
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
    
    formatDuration(ms) {
        if (ms < 1000) return `${ms}ms`;
        
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds}秒`;
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes < 60) return `${minutes}分${remainingSeconds}秒`;
        
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        
        return `${hours}時${remainingMinutes}分`;
    }
    
    // ========== 兼容性方法 ==========
    
    /**
     * 兼容舊版API
     */
    getLegacyAPI() {
        return {
            start: () => this.start(),
            stop: () => this.stop(),
            manualRefresh: () => this.manualRefresh(),
            diagnose: () => this.diagnose(),
            getStatus: () => this.getConnectionStatus(),
            getMetrics: () => this.getMetrics()
        };
    }
    
    /**
     * 手動刷新
     */
    manualRefresh() {
        console.log('🔄 手動刷新訂單狀態');
        
        // 強制清除緩存，確保獲取最新數據
        this.cache.lastUpdateTime = 0;
        this.cache.lastData = null;
        
        // 立即獲取訂單狀態
        this.fetchOrderStatus();
        
        // 顯示提示
        this.showNotification('正在刷新訂單狀態...', 'info', 2000);
    }
    
    /**
     * 診斷報告
     */
    diagnose() {
        console.group('🔍 訂單更新器診斷報告');
        console.log('訂單ID:', this.orderId);
        console.log('運行狀態:', this.isRunning ? '✅ 運行中' : '❌ 已停止');
        console.log('連接狀態:', this.getConnectionStatus().text);
        console.log('監控指標:', this.getMetrics());
        console.log('緩存信息:', {
            dataVersion: this.cache.dataVersion,
            lastUpdateTime: this.cache.lastUpdateTime ? new Date(this.cache.lastUpdateTime).toLocaleTimeString() : '無',
            lastStatus: this.cache.lastData?.status
        });
        console.log('配置選項:', this.options);
        console.groupEnd();
        
        // 更新診斷面板
        this.updateDiagnosticPanel();
        
        return this.getMetrics();
    }
    
    // ========== 全局導出和初始化 ==========
    
    /**
     * 獲取實例狀態
     */
    getState() {
        return {
            orderId: this.orderId,
            isRunning: this.isRunning,
            connectionStatus: this.getConnectionStatus(),
            metrics: this.getMetrics(),
            cache: {
                dataVersion: this.cache.dataVersion,
                lastUpdateTime: this.cache.lastUpdateTime,
                lastStatus: this.cache.lastData?.status
            },
            options: this.options
        };
    }
    
    /**
     * 導出為JSON
     */
    toJSON() {
        return JSON.stringify(this.getState(), null, 2);
    }
}

// ========== 全局導出 ==========

if (typeof window !== 'undefined') {
    window.UnifiedOrderUpdaterEnhanced = UnifiedOrderUpdaterEnhanced;
    
    // 兼容舊版API
    window.UnifiedOrderUpdater = UnifiedOrderUpdaterEnhanced;
    
    console.log('✅ 統一的訂單更新器增強版已加載');
}

/**
 * 初始化統一的訂單更新器增強版
 */
function initUnifiedOrderUpdaterEnhanced() {
    console.log('🔧 初始化統一的訂單更新器增強版');
    
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
        console.log('🚀 啟動條件滿足，創建增強版更新器');
        
        // 創建增強版更新器
        window.orderUpdater = new UnifiedOrderUpdaterEnhanced(orderId, {
            // 可選：自定義配置
            enableDiagnostics: window.location.hostname === 'localhost' || 
                              window.location.hostname === '127.0.0.1',
            legacyMode: true // 啟用舊API兼容
        });
        
        window.orderUpdater.start();
        
        // 創建連接狀態指示器
        window.orderUpdater.createConnectionIndicator();
        
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
        
        console.log('✅ 增強版訂單更新器初始化完成');
        
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

// ========== 自動初始化 ==========

// 頁面加載完成後初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        try {
            initUnifiedOrderUpdaterEnhanced();
        } catch (error) {
            console.error('❌ 初始化增強版更新器失敗:', error);
        }
    });
} else {
    // 如果DOM已經加載完成，直接初始化
    setTimeout(function() {
        try {
            initUnifiedOrderUpdaterEnhanced();
        } catch (error) {
            console.error('❌ 初始化增強版更新器失敗:', error);
        }
    }, 100);
}

// ========== 全局錯誤處理 ==========

window.addEventListener('error', function(event) {
    // 過濾第三方庫錯誤
    const errorMessage = event.error ? event.error.toString() : '';
    const errorStack = event.error ? event.error.stack : '';
    
    const isThirdPartyError = 
        errorMessage.includes('Explain is not defined') ||
        errorMessage.includes('bootstrap.bundle.min.js') ||
        errorStack.includes('bootstrap.bundle.min.js');
    
    if (isThirdPartyError) {
        console.warn('⚠️ 第三方庫錯誤（已過濾）:', errorMessage);
        event.preventDefault();
        return true;
    } else {
        console.error('❌ JavaScript錯誤被捕獲:', event.error);
        event.preventDefault();
        return true;
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('未處理的Promise拒絕:', event.reason);
    event.preventDefault();
});

// ========== 導出初始化函數 ==========

window.initUnifiedOrderUpdaterEnhanced = initUnifiedOrderUpdaterEnhanced;
window.initUnifiedOrderUpdater = initUnifiedOrderUpdaterEnhanced; // 兼容舊版

console.log('📦 統一的訂單更新器增強版加載完成');


