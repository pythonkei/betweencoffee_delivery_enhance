// static/js/websocket-optimizer.js
// ==================== WebSocket優化器 - 智能連接管理 ====================
// 版本: 1.0.0
// 功能: 提供智能心跳、網絡質量檢測、優先級消息隊列等優化功能

class NetworkQualityMonitor {
    constructor() {
        console.log('📡 初始化網絡質量監控器...');
        
        // 網絡質量指標
        this.metrics = {
            latency: [],           // 延遲樣本（毫秒）
            jitter: [],            // 抖動樣本（毫秒）
            packetLoss: 0,         // 丟包率（0-1）
            bandwidth: null,       // 帶寬估計（kbps）
            connectionScore: 100,  // 連接質量分數（0-100）
            lastUpdate: Date.now()
        };
        
        // 配置
        this.config = {
            maxSamples: 20,        // 最大樣本數
            updateInterval: 5000,  // 更新間隔（毫秒）
            latencyThresholds: {
                excellent: 50,     // 優秀：<50ms
                good: 100,         // 良好：<100ms
                fair: 200,         // 一般：<200ms
                poor: 500          // 差：<500ms
            },
            jitterThresholds: {
                excellent: 10,     // 優秀：<10ms
                good: 30,          // 良好：<30ms
                fair: 50,          // 一般：<50ms
                poor: 100          // 差：<100ms
            }
        };
        
        // 初始化
        this.init();
        
        console.log('✅ 網絡質量監控器初始化完成');
    }
    
    init() {
        // 開始定期更新
        this.updateInterval = setInterval(() => {
            this.updateMetrics();
        }, this.config.updateInterval);
        
        // 監聽網絡狀態變化
        window.addEventListener('online', () => this.handleNetworkChange('online'));
        window.addEventListener('offline', () => this.handleNetworkChange('offline'));
    }
    
    /**
     * 記錄延遲樣本
     */
    recordLatency(latencyMs) {
        this.metrics.latency.push(latencyMs);
        
        // 保持最大樣本數
        if (this.metrics.latency.length > this.config.maxSamples) {
            this.metrics.latency.shift();
        }
        
        // 計算抖動（延遲變化）
        if (this.metrics.latency.length >= 2) {
            const lastLatency = this.metrics.latency[this.metrics.latency.length - 2];
            const jitter = Math.abs(latencyMs - lastLatency);
            this.metrics.jitter.push(jitter);
            
            if (this.metrics.jitter.length > this.config.maxSamples) {
                this.metrics.jitter.shift();
            }
        }
        
        // 更新連接分數
        this.updateConnectionScore();
    }
    
    /**
     * 記錄丟包
     */
    recordPacketLoss() {
        this.metrics.packetLoss = Math.min(1, this.metrics.packetLoss + 0.1);
        this.updateConnectionScore();
    }
    
    /**
     * 記錄成功傳輸
     */
    recordSuccess() {
        this.metrics.packetLoss = Math.max(0, this.metrics.packetLoss - 0.05);
        this.updateConnectionScore();
    }
    
    /**
     * 更新連接分數
     */
    updateConnectionScore() {
        let score = 100;
        
        // 延遲扣分
        const avgLatency = this.getAverageLatency();
        if (avgLatency > 0) {
            if (avgLatency > this.config.latencyThresholds.poor) {
                score -= 40;
            } else if (avgLatency > this.config.latencyThresholds.fair) {
                score -= 20;
            } else if (avgLatency > this.config.latencyThresholds.good) {
                score -= 10;
            } else if (avgLatency > this.config.latencyThresholds.excellent) {
                score -= 5;
            }
        }
        
        // 抖動扣分
        const avgJitter = this.getAverageJitter();
        if (avgJitter > 0) {
            if (avgJitter > this.config.jitterThresholds.poor) {
                score -= 30;
            } else if (avgJitter > this.config.jitterThresholds.fair) {
                score -= 15;
            } else if (avgJitter > this.config.jitterThresholds.good) {
                score -= 8;
            } else if (avgJitter > this.config.jitterThresholds.excellent) {
                score -= 3;
            }
        }
        
        // 丟包率扣分
        score -= Math.min(30, this.metrics.packetLoss * 100);
        
        // 確保分數在0-100之間
        this.metrics.connectionScore = Math.max(0, Math.min(100, Math.round(score)));
        this.metrics.lastUpdate = Date.now();
        
        return this.metrics.connectionScore;
    }
    
    /**
     * 更新所有指標
     */
    updateMetrics() {
        // 這裡可以添加更多指標更新邏輯
        // 例如：帶寬估計、網絡類型檢測等
        
        this.updateConnectionScore();
        
        // 觸發更新事件
        this.triggerUpdateEvent();
    }
    
    /**
     * 處理網絡狀態變化
     */
    handleNetworkChange(state) {
        console.log(`🌐 網絡狀態變化: ${state}`);
        
        if (state === 'online') {
            // 網絡恢復，重置部分指標
            this.metrics.packetLoss = Math.max(0, this.metrics.packetLoss - 0.3);
        } else if (state === 'offline') {
            // 網絡斷開，降低分數
            this.metrics.connectionScore = Math.max(0, this.metrics.connectionScore - 30);
        }
        
        this.updateConnectionScore();
        this.triggerUpdateEvent();
    }
    
    /**
     * 觸發更新事件
     */
    triggerUpdateEvent() {
        document.dispatchEvent(new CustomEvent('network_quality_updated', {
            detail: this.getMetrics()
        }));
    }
    
    /**
     * 獲取平均延遲
     */
    getAverageLatency() {
        if (this.metrics.latency.length === 0) return 0;
        
        const sum = this.metrics.latency.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.metrics.latency.length);
    }
    
    /**
     * 獲取平均抖動
     */
    getAverageJitter() {
        if (this.metrics.jitter.length === 0) return 0;
        
        const sum = this.metrics.jitter.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.metrics.jitter.length);
    }
    
    /**
     * 獲取網絡質量狀態
     */
    getNetworkState() {
        const score = this.metrics.connectionScore;
        const latency = this.getAverageLatency();
        
        if (score >= 90 && latency < this.config.latencyThresholds.excellent) {
            return 'excellent';
        } else if (score >= 75 && latency < this.config.latencyThresholds.good) {
            return 'good';
        } else if (score >= 50 && latency < this.config.latencyThresholds.fair) {
            return 'fair';
        } else {
            return 'poor';
        }
    }
    
    /**
     * 獲取連接質量分數
     */
    getScore() {
        return this.metrics.connectionScore;
    }
    
    /**
     * 獲取所有指標
     */
    getMetrics() {
        return {
            ...this.metrics,
            averageLatency: this.getAverageLatency(),
            averageJitter: this.getAverageJitter(),
            networkState: this.getNetworkState(),
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * 清理
     */
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

class PriorityMessageQueue {
    constructor() {
        console.log('📦 初始化優先級消息隊列...');
        
        // 消息優先級定義
        this.PRIORITY = {
            CRITICAL: 0,    // 關鍵消息：心跳、連接狀態等
            HIGH: 1,        // 高優先級：訂單狀態更新
            NORMAL: 2,      // 普通優先級：一般操作
            LOW: 3          // 低優先級：統計數據、日誌等
        };
        
        // 消息隊列
        this.queues = {
            [this.PRIORITY.CRITICAL]: [],
            [this.PRIORITY.HIGH]: [],
            [this.PRIORITY.NORMAL]: [],
            [this.PRIORITY.LOW]: []
        };
        
        // 配置
        this.config = {
            maxQueueSize: 100,          // 每個隊列最大大小
            messageTTL: 300000,         // 消息生存時間（5分鐘）
            retryLimit: 3,              // 重試次數限制
            batchSize: 5,               // 批量發送大小
            cleanupInterval: 60000      // 清理間隔（1分鐘）
        };
        
        // 統計
        this.stats = {
            totalEnqueued: 0,
            totalSent: 0,
            totalFailed: 0,
            totalExpired: 0,
            queueSizes: this.getQueueSizes()
        };
        
        // 初始化清理間隔
        this.cleanupInterval = setInterval(() => {
            this.cleanupExpiredMessages();
        }, this.config.cleanupInterval);
        
        console.log('✅ 優先級消息隊列初始化完成');
    }
    
    /**
     * 添加消息到隊列
     */
    enqueue(message, priority = this.PRIORITY.NORMAL, metadata = {}) {
        // 檢查隊列是否已滿
        const queue = this.queues[priority];
        if (queue.length >= this.config.maxQueueSize) {
            console.warn(`⚠️ 優先級 ${priority} 隊列已滿，丟棄最舊消息`);
            queue.shift();
        }
        
        // 創建隊列項目
        const queueItem = {
            id: this.generateMessageId(),
            message: message,
            priority: priority,
            metadata: {
                ...metadata,
                createdAt: Date.now(),
                attempts: 0,
                lastAttempt: null,
                expiresAt: Date.now() + this.config.messageTTL
            }
        };
        
        // 添加到隊列
        queue.push(queueItem);
        
        // 更新統計
        this.stats.totalEnqueued++;
        this.updateStats();
        
        console.log(`📥 消息已加入隊列 (優先級: ${priority}, ID: ${queueItem.id})`);
        
        // 觸發隊列更新事件
        this.triggerQueueUpdate();
        
        return queueItem.id;
    }
    
    /**
     * 從隊列獲取下一個消息
     */
    dequeue() {
        // 按優先級順序檢查隊列
        for (let priority = this.PRIORITY.CRITICAL; priority <= this.PRIORITY.LOW; priority++) {
            const queue = this.queues[priority];
            if (queue.length > 0) {
                const item = queue.shift();
                
                // 更新嘗試次數
                item.metadata.attempts++;
                item.metadata.lastAttempt = Date.now();
                
                // 更新統計
                this.stats.totalSent++;
                this.updateStats();
                
                console.log(`📤 從隊列取出消息 (優先級: ${priority}, ID: ${item.id}, 嘗試: ${item.metadata.attempts})`);
                
                return item;
            }
        }
        
        return null; // 隊列為空
    }
    
    /**
     * 批量獲取消息
     */
    dequeueBatch(maxSize = this.config.batchSize) {
        const batch = [];
        
        for (let i = 0; i < maxSize; i++) {
            const item = this.dequeue();
            if (item) {
                batch.push(item);
            } else {
                break; // 隊列為空
            }
        }
        
        return batch;
    }
    
    /**
     * 重新加入隊列（發送失敗時）
     */
    requeue(queueItem) {
        const { priority, metadata } = queueItem;
        
        // 檢查重試次數
        if (metadata.attempts >= this.config.retryLimit) {
            console.warn(`⚠️ 消息 ${queueItem.id} 重試次數過多，丟棄`);
            this.stats.totalFailed++;
            this.updateStats();
            return false;
        }
        
        // 檢查是否過期
        if (Date.now() > metadata.expiresAt) {
            console.warn(`⚠️ 消息 ${queueItem.id} 已過期，丟棄`);
            this.stats.totalExpired++;
            this.updateStats();
            return false;
        }
        
        // 重新加入隊列（根據優先級可能調整位置）
        const queue = this.queues[priority];
        
        // 如果隊列已滿，丟棄最舊消息
        if (queue.length >= this.config.maxQueueSize) {
            console.warn(`⚠️ 優先級 ${priority} 隊列已滿，丟棄最舊消息`);
            queue.shift();
        }
        
        // 重新加入隊列（放在前面，優先處理）
        queue.unshift(queueItem);
        
        console.log(`🔄 消息重新加入隊列 (ID: ${queueItem.id}, 嘗試: ${metadata.attempts})`);
        
        this.updateStats();
        this.triggerQueueUpdate();
        
        return true;
    }
    
    /**
     * 清理過期消息
     */
    cleanupExpiredMessages() {
        const now = Date.now();
        let expiredCount = 0;
        
        // 檢查所有隊列
        for (let priority = this.PRIORITY.CRITICAL; priority <= this.PRIORITY.LOW; priority++) {
            const queue = this.queues[priority];
            const validItems = [];
            
            for (const item of queue) {
                if (now > item.metadata.expiresAt) {
                    expiredCount++;
                    this.stats.totalExpired++;
                } else {
                    validItems.push(item);
                }
            }
            
            // 更新隊列
            this.queues[priority] = validItems;
        }
        
        if (expiredCount > 0) {
            console.log(`🗑️ 清理了 ${expiredCount} 個過期消息`);
            this.updateStats();
            this.triggerQueueUpdate();
        }
    }
    
    /**
     * 生成消息ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * 獲取隊列大小
     */
    getQueueSizes() {
        return {
            critical: this.queues[this.PRIORITY.CRITICAL].length,
            high: this.queues[this.PRIORITY.HIGH].length,
            normal: this.queues[this.PRIORITY.NORMAL].length,
            low: this.queues[this.PRIORITY.LOW].length,
            total: this.getTotalSize()
        };
    }
    
    /**
     * 獲取總隊列大小
     */
    getTotalSize() {
        return Object.values(this.queues).reduce((sum, queue) => sum + queue.length, 0);
    }
    
    /**
     * 更新統計
     */
    updateStats() {
        this.stats.queueSizes = this.getQueueSizes();
    }
    
    /**
     * 獲取統計信息
     */
    getStats() {
        return {
            ...this.stats,
            timestamp: new Date().toISOString()
        };
    }
    
    /**
     * 觸發隊列更新事件
     */
    triggerQueueUpdate() {
        document.dispatchEvent(new CustomEvent('message_queue_updated', {
            detail: this.getStats()
        }));
    }
    
    /**
     * 清空隊列
     */
    clear() {
        for (let priority = this.PRIORITY.CRITICAL; priority <= this.PRIORITY.LOW; priority++) {
            this.queues[priority] = [];
        }
        
        this.updateStats();
        this.triggerQueueUpdate();
        
        console.log('🗑️ 所有消息隊列已清空');
    }
    
    /**
     * 清理
     */
    cleanup() {
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
            this.cleanupInterval = null;
        }
    }
}

class SmartWebSocketManager {
    constructor() {
        console.log('🚀 初始化智能WebSocket管理器...');
        
        // 依賴組件
        this.networkMonitor = new NetworkQualityMonitor();
        this.messageQueue = new PriorityMessageQueue();
        
        // WebSocket連接
        this.socket = null;
        this.isConnected = false;
        this.isConnecting = false;
        
        // 連接管理
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 15;  // 增加重試次數
        this.reconnectTimer = null;
        
        // 心跳管理
        this.heartbeatInterval = null;
        this.lastHeartbeatTime = 0;
        this.heartbeatTimeout = null;
        
        // 狀態追蹤
        this.connectionStats = {
            totalConnections: 0,
            successfulConnections: 0,
            failedConnections: 0,
            totalDisconnects: 0,
            averageLatency: 0,
            lastConnectionTime: null
        };
        
        // 配置
        this.config = {
            baseReconnectDelay: 1000,      // 基礎重連延遲
            maxReconnectDelay: 30000,      // 最大重連延遲
            heartbeatBaseInterval: 25000,  // 基礎心跳間隔
            heartbeatMinInterval: 10000,   // 最小心跳間隔
            heartbeatMaxInterval: 60000,   // 最大心跳間隔
            heartbeatTimeout: 10000,       // 心跳超時時間
            batchProcessInterval: 1000,    // 批量處理間隔
            connectionTestUrl: '/api/health/websocket/' // 連接測試URL
        };
        
        // 事件監聽器
        this.eventListeners = new Map();
        
        // 初始化
        this.init();
        
        console.log('✅ 智能WebSocket管理器初始化完成');
    }
    
    init() {
        // 監聽網絡質量變化
        document.addEventListener('network_quality_updated', (event) => {
            this.handleNetworkQualityUpdate(event.detail);
        });
        
        // 監聽消息隊列更新
        document.addEventListener('message_queue_updated', (event) => {
            this.handleMessageQueueUpdate(event.detail);
        });
        
        // 監聽頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // 監聽在線/離線狀態
        window.addEventListener('online', () => this.handleNetworkStatusChange('online'));
        window.addEventListener('offline', () => this.handleNetworkStatusChange('offline'));
        
        // 開始連接
        this.connect();
    }
    
    /**
     * 建立WebSocket連接
     */
    connect() {
        if (this.isConnected || this.isConnecting) {
            console.log('⚠️ WebSocket正在連接或已連接，跳過');
            return;
        }
        
        this.isConnecting = true;
        this.connectionStats.totalConnections++;
        
        // 根據網絡質量決定連接策略
        const networkState = this.networkMonitor.getNetworkState();
        console.log(`🌐 網絡狀態: ${networkState}, 開始連接...`);
        
        // 檢查服務器可用性
        this.checkServerAvailability().then(isAvailable => {
            if (!isAvailable) {
                console.warn('⚠️ 服務器不可用，延遲連接');
                this.scheduleReconnect(5000);
                return;
            }
            
            this.attemptConnection();
        }).catch(error => {
            console.error('❌ 服務器檢查失敗:', error);
            this.attemptConnection(); // 仍然嘗試連接
        });
    }
    
    /**
     * 嘗試連接
     */
    attemptConnection() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/queue/`;
            
            console.log(`🔗 嘗試連接到WebSocket: ${wsUrl}`);
            
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
            this.connectionStats.failedConnections++;
            this.scheduleReconnect();
        }
    }
    
    /**
     * 檢查服務器可用性
     */
    async checkServerAvailability() {
        try {
            const response = await fetch(this.config.connectionTestUrl, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                timeout: 3000
            });
            
            return response.ok;
        } catch (error) {
            console.warn('⚠️ 服務器檢查失敗:', error);
            return false;
        }
    }
    
    /**
     * 處理連接成功
     */
    handleOpen(event) {
        console.log('✅ WebSocket連接成功');
        
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.connectionStats.successfulConnections++;
        this.connectionStats.lastConnectionTime = new Date().toISOString();
        
        // 記錄成功
        this.networkMonitor.recordSuccess();
        
        // 啟動智能心跳
        this.startSmartHeartbeat();
        
        // 處理隊列中的消息
        this.processMessageQueue();
        
        // 觸發連接成功事件
        this.triggerEvent('websocket_connected', {
            timestamp: new Date().toISOString(),
            reconnectAttempts: this.reconnectAttempts,
            networkQuality: this.networkMonitor.getMetrics()
        });
        
        // 清除重連計時器
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
    
    /**
     * 處理連接關閉
     */
    handleClose(event) {
        console.log(`❌ WebSocket連接關閉: 代碼=${event.code}, 原因=${event.reason || '未知'}`);
        
        this.isConnected = false;
        this.isConnecting = false;
        this.socket = null;
        this.connectionStats.totalDisconnects++;
        
        // 停止心跳
        this.stopHeartbeat();
        
        // 觸發斷線事件
        this.triggerEvent('websocket_disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString(),
            networkQuality: this.networkMonitor.getMetrics()
        });
        
        // 非正常關閉才重連
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }
    
    /**
     * 處理錯誤
     */
    handleError(error) {
        console.error('❌ WebSocket錯誤:', error);
        
        // 記錄丟包
        this.networkMonitor.recordPacketLoss();
        
        this.triggerEvent('websocket_error', {
            error: error.toString(),
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * 處理收到的消息
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            
            // 處理pong回應
            if (data.type === 'pong') {
                this.handlePong(data);
                return;
            }
            
            // 記錄延遲（如果消息包含時間戳）
            if (data.server_time && data.client_time) {
                const latency = Date.now() - data.client_time;
                this.networkMonitor.recordLatency(latency);
                this.connectionStats.averageLatency = this.calculateAverageLatency(latency);
            }
            
            // 觸發消息事件
            this.triggerEvent('websocket_message', {
                type: data.type,
                data: data,
                timestamp: new Date().toISOString(),
                latency: data.client_time ? Date.now() - data.client_time : null
            });
            
        } catch (error) {
            console.error('❌ 解析WebSocket消息失敗:', error, event.data);
        }
    }
    
    /**
     * 處理pong回應
     */
    handlePong(data) {
        if (data.client_time) {
            const latency = Date.now() - data.client_time;
            this.networkMonitor.recordLatency(latency);
            this.connectionStats.averageLatency = this.calculateAverageLatency(latency);
            
            // 清除心跳超時
            if (this.heartbeatTimeout) {
                clearTimeout(this.heartbeatTimeout);
                this.heartbeatTimeout = null;
            }
        }
    }
    
    /**
     * 計算平均延遲
     */
    calculateAverageLatency(newLatency) {
        // 簡單的移動平均
        const oldAvg = this.connectionStats.averageLatency || 0;
        return Math.round((oldAvg * 0.7) + (newLatency * 0.3));
    }
    
    /**
     * 啟動智能心跳
     */
    startSmartHeartbeat() {
        // 停止現有心跳
        this.stopHeartbeat();
        
        // 根據網絡質量計算心跳間隔
        const networkScore = this.networkMonitor.getScore();
        let heartbeatInterval;
        
        if (networkScore >= 90) {
            heartbeatInterval = this.config.heartbeatBaseInterval; // 25秒
        } else if (networkScore >= 75) {
            heartbeatInterval = this.config.heartbeatBaseInterval * 0.8; // 20秒
        } else if (networkScore >= 50) {
            heartbeatInterval = this.config.heartbeatBaseInterval * 0.6; // 15秒
        } else {
            heartbeatInterval = this.config.heartbeatMinInterval; // 10秒
        }
        
        // 確保在最小和最大之間
        heartbeatInterval = Math.max(
            this.config.heartbeatMinInterval,
            Math.min(this.config.heartbeatMaxInterval, heartbeatInterval)
        );
        
        console.log(`💓 啟動智能心跳，間隔: ${heartbeatInterval/1000}秒`);
        
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, heartbeatInterval);
        
        // 立即發送第一個心跳
        setTimeout(() => this.sendHeartbeat(), 1000);
    }
    
    /**
     * 發送心跳
     */
    sendHeartbeat() {
        if (!this.isConnected || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        const heartbeatTime = Date.now();
        this.lastHeartbeatTime = heartbeatTime;
        
        const message = {
            type: 'ping',
            client_time: heartbeatTime,
            timestamp: new Date().toISOString(),
            network_quality: this.networkMonitor.getMetrics()
        };
        
        this.sendMessage(message, this.messageQueue.PRIORITY.CRITICAL);
        
        // 設置心跳超時檢測
        this.heartbeatTimeout = setTimeout(() => {
            const timeSinceHeartbeat = Date.now() - heartbeatTime;
            if (timeSinceHeartbeat > this.config.heartbeatTimeout) {
                console.warn(`⚠️ 心跳超時 (${timeSinceHeartbeat}ms)，重新連接...`);
                this.networkMonitor.recordPacketLoss();
                this.disconnect();
                this.scheduleReconnect();
            }
        }, this.config.heartbeatTimeout);
    }
    
    /**
     * 停止心跳
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }
    
    /**
     * 安排重連
     */
    scheduleReconnect(baseDelay = this.config.baseReconnectDelay) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ 達到最大重試次數，停止重連');
            this.triggerEvent('websocket_reconnect_failed', {
                attempts: this.reconnectAttempts,
                timestamp: new Date().toISOString()
            });
            return;
        }
        
        this.reconnectAttempts++;
        
        // 智能重連延遲計算
        const networkState = this.networkMonitor.getNetworkState();
        let delay;
        
        switch (networkState) {
            case 'excellent':
                delay = baseDelay; // 1秒
                break;
            case 'good':
                delay = baseDelay * 2; // 2秒
                break;
            case 'fair':
                delay = baseDelay * 3; // 3秒
                break;
            case 'poor':
                delay = baseDelay * 5; // 5秒
                break;
            default:
                delay = baseDelay * 2;
        }
        
        // 指數退避
        const exponentialDelay = Math.min(
            delay * Math.pow(1.5, this.reconnectAttempts - 1),
            this.config.maxReconnectDelay
        );
        
        // 添加隨機抖動
        const jitter = exponentialDelay * 0.2 * (Math.random() * 2 - 1);
        const finalDelay = Math.max(1000, Math.min(exponentialDelay + jitter, this.config.maxReconnectDelay));
        
        console.log(`🔄 ${Math.round(finalDelay/1000)}秒後嘗試重新連接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, finalDelay);
    }
    
    /**
     * 發送消息
     */
    sendMessage(message, priority = this.messageQueue.PRIORITY.NORMAL) {
        // 如果已連接，直接發送
        if (this.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
                this.socket.send(messageStr);
                this.networkMonitor.recordSuccess();
                return true;
            } catch (error) {
                console.error('❌ 發送WebSocket消息失敗:', error);
                this.networkMonitor.recordPacketLoss();
                // 加入隊列重試
                this.messageQueue.enqueue(message, priority, { error: error.toString() });
                return false;
            }
        } else {
            // 加入隊列
            console.warn('⚠️ WebSocket未連接，消息已加入隊列');
            this.messageQueue.enqueue(message, priority);
            return false;
        }
    }
    
    /**
     * 處理消息隊列
     */
    processMessageQueue() {
        if (!this.isConnected || this.messageQueue.getTotalSize() === 0) {
            return;
        }
        
        console.log(`🔄 處理消息隊列，共 ${this.messageQueue.getTotalSize()} 條消息`);
        
        // 批量處理消息
        const batch = this.messageQueue.dequeueBatch();
        
        batch.forEach(queueItem => {
            const success = this.sendMessage(queueItem.message, queueItem.priority);
            
            if (!success) {
                // 發送失敗，重新加入隊列
                this.messageQueue.requeue(queueItem);
            }
        });
        
        // 如果還有消息，繼續處理
        if (this.messageQueue.getTotalSize() > 0) {
            setTimeout(() => this.processMessageQueue(), this.config.batchProcessInterval);
        }
    }
    
    /**
     * 處理網絡質量更新
     */
    handleNetworkQualityUpdate(metrics) {
        // 根據網絡質量調整心跳間隔
        if (this.isConnected && this.heartbeatInterval) {
            this.startSmartHeartbeat();
        }
        
        // 觸發網絡質量事件
        this.triggerEvent('network_quality_updated', metrics);
    }
    
    /**
     * 處理消息隊列更新
     */
    handleMessageQueueUpdate(stats) {
        this.triggerEvent('message_queue_updated', stats);
    }
    
    /**
     * 處理頁面可見性變化
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // 頁面隱藏，降低活動頻率
            console.log('👁️ 頁面隱藏，降低WebSocket活動');
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.heartbeatInterval = setInterval(() => {
                    this.sendHeartbeat();
                }, 60000); // 60秒
            }
        } else {
            // 頁面顯示，恢復正常活動
            console.log('👁️ 頁面顯示，恢復WebSocket活動');
            if (this.heartbeatInterval) {
                clearInterval(this.heartbeatInterval);
                this.startSmartHeartbeat();
            }
            
            // 檢查連接狀態
            if (!this.isConnected && !this.isConnecting) {
                this.connect();
            }
        }
    }
    
    /**
     * 處理網絡狀態變化
     */
    handleNetworkStatusChange(status) {
        console.log(`🌐 網絡狀態: ${status}`);
        
        if (status === 'online') {
            // 網絡恢復，嘗試重連
            if (!this.isConnected && !this.isConnecting) {
                console.log('🔄 網絡恢復，嘗試重新連接');
                this.connect();
            }
        } else if (status === 'offline') {
            // 網絡斷開
            console.log('🌐 網絡斷開，停止活動');
            this.disconnect();
        }
    }
    
    /**
     * 斷開連接
     */
    disconnect() {
        if (this.socket) {
            console.log('🔌 手動斷開WebSocket連接');
            this.socket.close(1000, 'manual_disconnect');
            this.socket = null;
        }
        
        this.isConnected = false;
        this.isConnecting = false;
        
        this.stopHeartbeat();
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
    
    /**
     * 重新連接
     */
    reconnect() {
        console.log('🔄 手動重新連接WebSocket');
        this.disconnect();
        this.reconnectAttempts = 0;
        setTimeout(() => {
            this.connect();
        }, 500);
    }
    
    /**
     * 註冊事件監聽器
     */
    on(eventName, callback) {
        if (!this.eventListeners.has(eventName)) {
            this.eventListeners.set(eventName, []);
        }
        
        this.eventListeners.get(eventName).push(callback);
        
        // 返回取消函數
        return () => this.off(eventName, callback);
    }
    
    /**
     * 移除事件監聽器
     */
    off(eventName, callback) {
        if (this.eventListeners.has(eventName)) {
            const listeners = this.eventListeners.get(eventName);
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
        if (this.eventListeners.has(eventName)) {
            this.eventListeners.get(eventName).forEach(callback => {
                try {
                    callback({
                        ...detail,
                        timestamp: new Date().toISOString()
                    });
                } catch (error) {
                    console.error(`❌ 事件監聽器執行錯誤 (${eventName}):`, error);
                }
            });
        }
        
        // 同時發送全局事件
        document.dispatchEvent(new CustomEvent(eventName, {
            detail: {
                ...detail,
                timestamp: new Date().toISOString()
            }
        }));
    }
    
    /**
     * 獲取連接狀態
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            isConnecting: this.isConnecting,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts,
            networkQuality: this.networkMonitor.getMetrics(),
            messageQueue: this.messageQueue.getStats(),
            connectionStats: { ...this.connectionStats },
            heartbeatInterval: this.heartbeatInterval ? 'active' : 'inactive',
            lastHeartbeatTime: this.lastHeartbeatTime ? new Date(this.lastHeartbeatTime).toLocaleTimeString() : null
        };
    }
    
    /**
     * 獲取性能報告
     */
    getPerformanceReport() {
        const networkMetrics = this.networkMonitor.getMetrics();
        const queueStats = this.messageQueue.getStats();
        
        return {
            timestamp: new Date().toISOString(),
            summary: {
                connectionStatus: this.isConnected ? 'connected' : 'disconnected',
                networkQuality: networkMetrics.networkState,
                connectionScore: networkMetrics.connectionScore,
                averageLatency: networkMetrics.averageLatency,
                messageQueueSize: queueStats.queueSizes.total
            },
            detailedMetrics: {
                network: networkMetrics,
                queue: queueStats,
                connection: this.connectionStats
            },
            recommendations: this.generateRecommendations(networkMetrics, queueStats)
        };
    }
    
    /**
     * 生成建議
     */
    generateRecommendations(networkMetrics, queueStats) {
        const recommendations = [];
        
        // 網絡質量建議
        if (networkMetrics.networkState === 'poor') {
            recommendations.push({
                type: 'network_quality',
                priority: 'high',
                message: '網絡質量較差，建議檢查網絡連接',
                action: '檢查Wi-Fi或有線連接'
            });
        } else if (networkMetrics.networkState === 'fair') {
            recommendations.push({
                type: 'network_quality',
                priority: 'medium',
                message: '網絡質量一般，可能影響實時更新',
                action: '優化網絡環境'
            });
        }
        
        // 延遲建議
        if (networkMetrics.averageLatency > 200) {
            recommendations.push({
                type: 'latency',
                priority: 'medium',
                message: `網絡延遲較高 (${networkMetrics.averageLatency}ms)`,
                action: '減少網絡負載或切換網絡'
            });
        }
        
        // 消息隊列建議
        if (queueStats.queueSizes.total > 20) {
            recommendations.push({
                type: 'message_queue',
                priority: 'low',
                message: `消息隊列較長 (${queueStats.queueSizes.total}條)`,
                action: '檢查網絡連接或減少發送頻率'
            });
        }
        
        // 連接穩定性建議
        if (this.connectionStats.totalDisconnects > 5) {
            recommendations.push({
                type: 'connection_stability',
                priority: 'high',
                message: `連接不穩定，已斷線 ${this.connectionStats.totalDisconnects}次`,
                action: '檢查服務器狀態和網絡連接'
            });
        }
        
        return recommendations;
    }
    
    /**
     * 發送測試消息
     */
    sendTestMessage(message = '測試消息') {
        const testMessage = {
            type: 'test',
            message: message,
            timestamp: new Date().toISOString(),
            client_time: Date.now()
        };
        
        return this.sendMessage(testMessage, this.messageQueue.PRIORITY.NORMAL);
    }
    
    /**
     * 清空消息隊列
     */
    clearMessageQueue() {
        this.messageQueue.clear();
        console.log('🗑️ 消息隊列已清空');
    }
    
    /**
     * 顯示連接狀態指示器
     */
    showConnectionIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'smart-websocket-indicator';
        indicator.className = 'smart-websocket-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 60px;
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
        `;
        
        // 更新指示器內容
        const updateIndicator = () => {
            const status = this.getConnectionStatus();
            const networkState = status.networkQuality.networkState;
            
            let statusClass = '';
            let statusText = '';
            let statusIcon = '';
            
            if (this.isConnected) {
                switch (networkState) {
                    case 'excellent':
                        statusClass = 'connected-excellent';
                        statusText = '連接優秀';
                        statusIcon = 'fa-wifi';
                        break;
                    case 'good':
                        statusClass = 'connected-good';
                        statusText = '連接良好';
                        statusIcon = 'fa-wifi';
                        break;
                    case 'fair':
                        statusClass = 'connected-fair';
                        statusText = '連接一般';
                        statusIcon = 'fa-wifi';
                        break;
                    case 'poor':
                        statusClass = 'connected-poor';
                        statusText = '連接較差';
                        statusIcon = 'fa-exclamation-triangle';
                        break;
                }
            } else if (this.isConnecting) {
                statusClass = 'connecting';
                statusText = '連接中...';
                statusIcon = 'fa-sync fa-spin';
            } else {
                statusClass = 'disconnected';
                statusText = '連接中斷';
                statusIcon = 'fa-plug';
            }
            
            indicator.className = `smart-websocket-indicator ${statusClass}`;
            indicator.innerHTML = `
                <i class="fas ${statusIcon}"></i>
                <span>${statusText}</span>
                <span class="badge badge-light ml-1">${status.networkQuality.averageLatency}ms</span>
                ${status.messageQueue.queueSizes.total > 0 ? 
                    `<span class="badge badge-warning ml-1">${status.messageQueue.queueSizes.total}</span>` : ''}
            `;
            
            // 懸浮提示
            indicator.title = `WebSocket狀態: ${statusText}
網絡質量: ${networkState}
延遲: ${status.networkQuality.averageLatency}ms
連接分數: ${status.networkQuality.connectionScore}
消息隊列: ${status.messageQueue.queueSizes.total}條
點擊查看詳情`;
        };
        
        // 點擊顯示詳情
        indicator.addEventListener('click', () => {
            this.showConnectionDetails();
        });
        
        // 定期更新
        this.indicatorUpdateInterval = setInterval(updateIndicator, 3000);
        
        // 初始更新
        updateIndicator();
        
        document.body.appendChild(indicator);
        
        return indicator;
    }
    
    /**
     * 顯示連接詳情
     */
    showConnectionDetails() {
        const status = this.getConnectionStatus();
        const report = this.getPerformanceReport();
        
        const details = `
            WebSocket 智能連接詳情
            ═══════════════════════
            
            連接狀態: ${this.isConnected ? '✅ 已連接' : this.isConnecting ? '🔄 連接中' : '❌ 離線'}
            重連次數: ${status.reconnectAttempts}/${status.maxReconnectAttempts}
            
            網絡質量: ${status.networkQuality.networkState}
            連接分數: ${status.networkQuality.connectionScore}/100
            平均延遲: ${status.networkQuality.averageLatency}ms
            平均抖動: ${status.networkQuality.averageJitter}ms
            丟包率: ${(status.networkQuality.packetLoss * 100).toFixed(1)}%
            
            消息隊列: ${status.messageQueue.queueSizes.total}條
              • 關鍵: ${status.messageQueue.queueSizes.critical}
              • 高: ${status.messageQueue.queueSizes.high}
              • 普通: ${status.messageQueue.queueSizes.normal}
              • 低: ${status.messageQueue.queueSizes.low}
            
            連接統計:
              • 總連接: ${status.connectionStats.totalConnections}
              • 成功: ${status.connectionStats.successfulConnections}
              • 失敗: ${status.connectionStats.failedConnections}
              • 斷線: ${status.connectionStats.totalDisconnects}
            
            心跳狀態: ${status.heartbeatInterval === 'active' ? '✅ 活動中' : '❌ 停止'}
            最後心跳: ${status.lastHeartbeatTime || '無'}
            
            ⏱️ 最後更新: ${new Date().toLocaleTimeString()}
        `;
        
        // 使用alert或自定義彈窗顯示
        if (window.toast) {
            window.toast.info(details, 'WebSocket詳情', 10000);
        } else {
            alert(details);
        }
    }
    
    /**
     * 清理
     */
    cleanup() {
        console.log('🔄 清理智能WebSocket管理器...');
        
        // 斷開連接
        this.disconnect();
        
        // 清理組件
        this.networkMonitor.cleanup();
        this.messageQueue.cleanup();
        
        // 清理指示器更新間隔
        if (this.indicatorUpdateInterval) {
            clearInterval(this.indicatorUpdateInterval);
            this.indicatorUpdateInterval = null;
        }
        
        // 清理事件監聽器
        this.eventListeners.clear();
        
        // 移除指示器
        const indicator = document.getElementById('smart-websocket-indicator');
        if (indicator) {
            indicator.remove();
        }
        
        console.log('✅ 智能WebSocket管理器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    // 延遲初始化
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.smartWebSocketManager) {
                console.log('🌍 創建智能WebSocket管理器實例...');
                window.smartWebSocketManager = new SmartWebSocketManager();
                
                // 方便調試
                window.SmartWebSocketManager = SmartWebSocketManager;
                window.NetworkQualityMonitor = NetworkQualityMonitor;
                window.PriorityMessageQueue = PriorityMessageQueue;
                
                console.log('🌍 智能WebSocket管理器已註冊到 window 對象');
                
                // 添加全局輔助方法
                window.WebSocketOptimizer = {
                    reconnect: () => window.smartWebSocketManager?.reconnect(),
                    disconnect: () => window.smartWebSocketManager?.disconnect(),
                    getStatus: () => window.smartWebSocketManager?.getConnectionStatus(),
                    getReport: () => window.smartWebSocketManager?.getPerformanceReport(),
                    sendTest: (msg) => window.smartWebSocketManager?.sendTestMessage(msg),
                    clearQueue: () => window.smartWebSocketManager?.clearMessageQueue(),
                    showIndicator: () => window.smartWebSocketManager?.showConnectionIndicator(),
                    cleanup: () => window.smartWebSocketManager?.cleanup()
                };
                
                // 自動顯示指示器
                setTimeout(() => {
                    if (window.smartWebSocketManager) {
                        window.smartWebSocketManager.showConnectionIndicator();
                    }
                }, 2000);
            }
        }, 1000);
    });
}

// ==================== CSS樣式 ====================

const style = document.createElement('style');
style.textContent = `
.smart-websocket-indicator {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    transition: all 0.3s ease;
}

.smart-websocket-indicator.connected-excellent {
    background: linear-gradient(135deg, #28a745, #20c997) !important;
    color: white !important;
}

.smart-websocket-indicator.connected-good {
    background: linear-gradient(135deg, #17a2b8, #20c997) !important;
    color: white !important;
}

.smart-websocket-indicator.connected-fair {
    background: linear-gradient(135deg, #ffc107, #fd7e14) !important;
    color: #212529 !important;
}

.smart-websocket-indicator.connected-poor {
    background: linear-gradient(135deg, #dc3545, #fd7e14) !important;
    color: white !important;
    animation: pulse 2s infinite;
}

.smart-websocket-indicator.connecting {
    background: linear-gradient(135deg, #6c757d, #adb5bd) !important;
    color: white !important;
    animation: pulse 1.5s infinite;
}

.smart-websocket-indicator.disconnected {
    background: linear-gradient(135deg, #6c757d, #495057) !important;
    color: white !important;
    opacity: 0.8;
}

.smart-websocket-indicator .badge {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

.smart-websocket-indicator:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
}
`;

document.head.appendChild(style);

console.log('🎨 WebSocket優化器CSS樣式已加載');
