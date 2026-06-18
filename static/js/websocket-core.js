/**
 * websocket-core.js - WebSocket 統一核心管理器
 * 
 * 整合所有 WebSocket 功能為單一核心，避免多個管理器衝突。
 * 所有其他 WebSocket 管理器（員工端、顧客端、優化器）都依賴此核心。
 * 
 * 功能：
 * - 單一 WebSocket 連線管理（避免多個連線衝突）
 * - 智能重連（指數退避 + 抖動）
 * - 統一心跳檢測（30 秒間隔，與服務端同步）
 * - 離線訊息佇列
 * - 連接健康度監控
 * - 事件系統（供其他管理器訂閱）
 * - 頁面可見性處理（節省資源）
 * 
 * 版本: 2.1.0
 * 最後更新: 2026-06-18
 */

class WebSocketCore {
    /**
     * @param {Object} options
     * @param {string} options.url - WebSocket URL（預設自動生成）
     * @param {number} options.heartbeatInterval - 心跳間隔（毫秒，預設 30000）
     * @param {number} options.heartbeatTimeout - 心跳超時（毫秒，預設 10000）
     * @param {number} options.maxRetries - 最大重試次數（預設 10）
     * @param {number} options.baseDelay - 基礎重連延遲（毫秒，預設 1000）
     * @param {number} options.maxDelay - 最大重連延遲（毫秒，預設 30000）
     * @param {boolean} options.enableJitter - 是否啟用抖動（預設 true）
     * @param {number} options.jitterFactor - 抖動因子（預設 0.2）
     * @param {boolean} options.autoConnect - 是否自動連接（預設 true）
     * @param {boolean} options.showIndicator - 是否顯示連接指示器（預設 false）
     */
    constructor(options = {}) {
        // 防止重複初始化
        if (WebSocketCore._instance) {
            console.warn('⚠️ WebSocketCore 已存在實例，返回現有實例');
            return WebSocketCore._instance;
        }

        // 配置
        this.options = {
            url: options.url || this._getDefaultUrl(),
            heartbeatInterval: options.heartbeatInterval || 30000,
            heartbeatTimeout: options.heartbeatTimeout || 10000,
            maxRetries: options.maxRetries || 10,
            baseDelay: options.baseDelay || 1000,
            maxDelay: options.maxDelay || 30000,
            enableJitter: options.enableJitter !== false,
            jitterFactor: options.jitterFactor || 0.2,
            autoConnect: options.autoConnect !== false,
            showIndicator: options.showIndicator || false,
            ...options
        };

        // WebSocket 實例
        this.socket = null;

        // 連接狀態
        this.state = {
            isConnected: false,
            isConnecting: false,
            reconnectAttempts: 0,
            lastError: null,
            connectionStartTime: null,
            lastMessageTime: null,
            messageCount: 0,
            bytesSent: 0,
            bytesReceived: 0
        };

        // 心跳
        this.heartbeat = {
            timer: null,
            timeoutTimer: null,
            lastPingTime: null,
            lastPongTime: Date.now(),
            latency: 0
        };

        // 重連
        this.reconnectTimer = null;

        // 離線訊息佇列
        this.messageQueue = [];
        this.maxQueueSize = 100;
        this.isProcessingQueue = false;

        // 連接品質
        this.quality = {
            score: 100,
            latencySamples: [],
            disconnects: 0,
            reconnectSuccess: 0,
            reconnectFailed: 0
        };

        // 事件監聽器: { eventType: [callback, ...] }
        this.listeners = {};

        // 頁面可見性
        this._pageHidden = false;

        // 連接指示器
        this.indicator = null;

        // 設定為單例
        WebSocketCore._instance = this;

        console.log(`🔧 WebSocketCore 初始化: ${this.options.url}`);

        // 自動連接
        if (this.options.autoConnect) {
            this.connect();
        }

        // 設置頁面可見性監聽
        this._setupVisibilityHandler();

        // 設置網絡狀態監聽
        this._setupNetworkHandler();
    }

    // ==================== 靜態方法 ====================

    /**
     * 獲取單例實例
     * @returns {WebSocketCore}
     */
    static getInstance() {
        return WebSocketCore._instance || null;
    }

    // ==================== 連接管理 ====================

    /**
     * 建立 WebSocket 連接
     */
    connect() {
        if (this.state.isConnected) {
            console.log('ℹ️ 已連接，跳過');
            return;
        }
        if (this.state.isConnecting) {
            console.log('ℹ️ 連接中，跳過');
            return;
        }

        this.state.isConnecting = true;

        try {
            console.log(`🔗 連接 WebSocket: ${this.options.url}`);
            this.socket = new WebSocket(this.options.url);

            this.socket.onopen = (event) => this._handleOpen(event);
            this.socket.onmessage = (event) => this._handleMessage(event);
            this.socket.onclose = (event) => this._handleClose(event);
            this.socket.onerror = (error) => this._handleError(error);

        } catch (error) {
            console.error('❌ 建立 WebSocket 連接失敗:', error);
            this.state.isConnecting = false;
            this.state.lastError = error;
            this._scheduleReconnect();
        }
    }

    /**
     * 斷開 WebSocket 連接
     * @param {number} code - 關閉代碼
     * @param {string} reason - 關閉原因
     */
    disconnect(code = 1000, reason = '手動斷開') {
        this._stopHeartbeat();
        this._clearReconnectTimer();

        if (this.socket) {
            try {
                this.socket.close(code, reason);
            } catch (e) {
                // 忽略關閉錯誤
            }
            this.socket = null;
        }

        this.state.isConnected = false;
        this.state.isConnecting = false;
        this._updateIndicator();
    }

    /**
     * 重新連接
     */
    reconnect() {
        console.log('🔄 手動重新連接');
        this.disconnect();
        this.state.reconnectAttempts = 0;
        setTimeout(() => this.connect(), 500);
    }

    // ==================== 訊息發送 ====================

    /**
     * 發送訊息
     * @param {Object|string} data - 要發送的數據
     * @param {number} [priority] - 優先級（0=最高，3=最低）
     * @returns {boolean} 是否成功發送
     */
    send(data, priority = 2) {
        if (this.state.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
            try {
                const message = typeof data === 'string' ? data : JSON.stringify(data);
                this.socket.send(message);
                this.state.messageCount++;
                this.state.bytesSent += message.length;
                return true;
            } catch (error) {
                console.error('❌ 發送失敗:', error);
                this._enqueue(data, priority);
                return false;
            }
        } else {
            this._enqueue(data, priority);
            return false;
        }
    }

    /**
     * 發送 JSON 訊息（自動序列化）
     * @param {Object} data
     * @param {number} [priority]
     * @returns {boolean}
     */
    sendJSON(data, priority = 2) {
        return this.send(data, priority);
    }

    // ==================== 事件系統 ====================

    /**
     * 註冊事件監聽器
     * @param {string} event - 事件名稱
     * @param {Function} callback - 回調函數
     * @returns {Function} 取消註冊函數
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
        return () => this.off(event, callback);
    }

    /**
     * 移除事件監聽器
     * @param {string} event
     * @param {Function} callback
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * 觸發事件
     * @param {string} event
     * @param {*} data
     */
    _emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => {
                try { cb(data); } catch (e) {
                    console.error(`❌ 事件監聽器錯誤 (${event}):`, e);
                }
            });
        }
        // 同時發送 DOM 事件
        document.dispatchEvent(new CustomEvent(`ws:${event}`, { detail: data }));
    }

    // ==================== 連接狀態查詢 ====================

    /**
     * 獲取完整連接狀態
     * @returns {Object}
     */
    getStatus() {
        const readyStateMap = { 0: 'CONNECTING', 1: 'OPEN', 2: 'CLOSING', 3: 'CLOSED' };
        return {
            isConnected: this.state.isConnected,
            isConnecting: this.state.isConnecting,
            readyState: this.socket ? readyStateMap[this.socket.readyState] : 'CLOSED',
            reconnectAttempts: this.state.reconnectAttempts,
            maxRetries: this.options.maxRetries,
            messageCount: this.state.messageCount,
            queueSize: this.messageQueue.length,
            latency: this.heartbeat.latency,
            qualityScore: this.quality.score,
            disconnects: this.quality.disconnects,
            uptime: this.state.connectionStartTime
                ? Date.now() - this.state.connectionStartTime
                : 0
        };
    }

    /**
     * 獲取健康度評分（0-100）
     * @returns {number}
     */
    getHealthScore() {
        return this.quality.score;
    }

    // ==================== 私有方法 ====================

    /**
     * 獲取預設 WebSocket URL
     */
    _getDefaultUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/queue/`;
    }

    /**
     * 處理連接成功
     */
    _handleOpen(event) {
        console.log('✅ WebSocket 連接成功');
        this.state.isConnected = true;
        this.state.isConnecting = false;
        this.state.connectionStartTime = Date.now();
        this.state.reconnectAttempts = 0;
        this.heartbeat.lastPongTime = Date.now();

        // 更新品質
        this.quality.reconnectSuccess++;
        this.quality.disconnects = 0;
        this._updateQualityScore();

        // 啟動心跳
        this._startHeartbeat();

        // 處理離線佇列
        this._processQueue();

        // 更新指示器
        this._updateIndicator();

        // 觸發事件
        this._emit('connected', { timestamp: new Date().toISOString() });
    }

    /**
     * 處理訊息接收
     */
    _handleMessage(event) {
        this.state.lastMessageTime = Date.now();
        this.state.messageCount++;
        this.state.bytesReceived += (event.data && event.data.length) || 0;

        try {
            const data = JSON.parse(event.data);

            // 處理 pong（心跳回應）
            if (data.type === 'pong') {
                this._handlePong(data);
                return;
            }

            // 觸發通用 message 事件
            this._emit('message', data);

            // 觸發特定類型事件
            if (data.type) {
                this._emit(`message:${data.type}`, data);
            }

        } catch (e) {
            // 非 JSON 訊息，直接觸發 raw 事件
            this._emit('raw_message', event.data);
        }
    }

    /**
     * 處理連接關閉
     */
    _handleClose(event) {
        console.log(`🔌 WebSocket 關閉: code=${event.code}, reason=${event.reason || '未知'}`);
        this.state.isConnected = false;
        this.state.isConnecting = false;
        this.socket = null;

        // 更新品質
        this.quality.disconnects++;
        this._updateQualityScore();

        // 停止心跳
        this._stopHeartbeat();

        // 更新指示器
        this._updateIndicator();

        // 觸發事件
        this._emit('disconnected', {
            code: event.code,
            reason: event.reason,
            timestamp: new Date().toISOString()
        });

        // 非正常關閉才重連
        if (event.code !== 1000) {
            this._scheduleReconnect();
        }
    }

    /**
     * 處理錯誤
     */
    _handleError(error) {
        console.error('❌ WebSocket 錯誤:', error);
        this.state.lastError = error;
        this._emit('error', { error: error.toString() });
    }

    /**
     * 處理 pong 回應
     */
    _handlePong(data) {
        if (this.heartbeat.lastPingTime) {
            this.heartbeat.latency = Date.now() - this.heartbeat.lastPingTime;
            this.heartbeat.lastPongTime = Date.now();

            // 記錄延遲樣本
            this.quality.latencySamples.push(this.heartbeat.latency);
            if (this.quality.latencySamples.length > 10) {
                this.quality.latencySamples.shift();
            }
            this._updateQualityScore();
        }

        // 清除心跳超時
        if (this.heartbeat.timeoutTimer) {
            clearTimeout(this.heartbeat.timeoutTimer);
            this.heartbeat.timeoutTimer = null;
        }
    }

    // ==================== 心跳機制 ====================

    /**
     * 啟動心跳
     */
    _startHeartbeat() {
        this._stopHeartbeat();
        this.heartbeat.timer = setInterval(() => this._sendPing(), this.options.heartbeatInterval);
        // 1 秒後發送第一次心跳
        setTimeout(() => this._sendPing(), 1000);
    }

    /**
     * 停止心跳
     */
    _stopHeartbeat() {
        if (this.heartbeat.timer) {
            clearInterval(this.heartbeat.timer);
            this.heartbeat.timer = null;
        }
        if (this.heartbeat.timeoutTimer) {
            clearTimeout(this.heartbeat.timeoutTimer);
            this.heartbeat.timeoutTimer = null;
        }
    }

    /**
     * 發送 ping
     */
    _sendPing() {
        if (!this.state.isConnected || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
            return;
        }

        this.heartbeat.lastPingTime = Date.now();
        this.sendJSON({
            type: 'ping',
            client_time: this.heartbeat.lastPingTime,
            timestamp: new Date().toISOString()
        }, 0); // 最高優先級

        // 設置超時檢測
        this.heartbeat.timeoutTimer = setTimeout(() => {
            const elapsed = Date.now() - this.heartbeat.lastPingTime;
            if (elapsed >= this.options.heartbeatTimeout) {
                console.warn(`⚠️ 心跳超時 (${elapsed}ms)`);
                this.quality.score = Math.max(0, this.quality.score - 20);
                this._emit('heartbeat_timeout', { elapsed });
                // 主動重連
                this.disconnect(1001, '心跳超時');
                this._scheduleReconnect();
            }
        }, this.options.heartbeatTimeout);
    }

    // ==================== 重連機制 ====================

    /**
     * 安排重連
     */
    _scheduleReconnect() {
        if (this.state.reconnectAttempts >= this.options.maxRetries) {
            console.error(`❌ 達到最大重試次數 (${this.options.maxRetries})，停止重連`);
            this.quality.reconnectFailed++;
            this._updateQualityScore();
            this._emit('reconnect_failed', {
                attempts: this.state.reconnectAttempts
            });
            return;
        }

        this.state.reconnectAttempts++;

        // 指數退避
        let delay = this.options.baseDelay * Math.pow(1.5, this.state.reconnectAttempts - 1);
        delay = Math.min(delay, this.options.maxDelay);

        // 抖動
        if (this.options.enableJitter) {
            const jitter = delay * this.options.jitterFactor * (Math.random() * 2 - 1);
            delay = Math.max(1000, delay + jitter);
        }

        console.log(`🔄 ${Math.round(delay/1000)}秒後重連 (${this.state.reconnectAttempts}/${this.options.maxRetries})`);

        this._emit('reconnecting', {
            attempt: this.state.reconnectAttempts,
            maxRetries: this.options.maxRetries,
            delay: Math.round(delay)
        });

        this._updateIndicator();

        this.reconnectTimer = setTimeout(() => this.connect(), delay);
    }

    /**
     * 清除重連定時器
     */
    _clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    // ==================== 離線佇列 ====================

    /**
     * 加入佇列
     */
    _enqueue(data, priority) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            this.messageQueue.shift(); // 丟棄最舊
        }
        this.messageQueue.push({
            data,
            priority,
            timestamp: Date.now(),
            attempts: 0
        });
        this._emit('queue_updated', { size: this.messageQueue.length });
    }

    /**
     * 處理佇列
     */
    async _processQueue() {
        if (this.isProcessingQueue || this.messageQueue.length === 0 || !this.state.isConnected) {
            return;
        }

        this.isProcessingQueue = true;
        console.log(`🔄 處理離線佇列: ${this.messageQueue.length} 條`);

        const failed = [];

        while (this.messageQueue.length > 0) {
            const item = this.messageQueue.shift();

            // 過期丟棄（5 分鐘）
            if (Date.now() - item.timestamp > 300000) {
                continue;
            }

            // 重試次數過多
            item.attempts++;
            if (item.attempts > 3) {
                continue;
            }

            try {
                if (!this.send(item.data, item.priority)) {
                    failed.push(item);
                }
            } catch (e) {
                failed.push(item);
            }
        }

        // 失敗的重新入隊
        failed.forEach(item => this.messageQueue.unshift(item));

        this.isProcessingQueue = false;
        console.log(`✅ 佇列處理完成，剩餘: ${this.messageQueue.length} 條`);
        this._emit('queue_processed', { remaining: this.messageQueue.length });
    }

    // ==================== 品質評分 ====================

    /**
     * 更新品質評分
     */
    _updateQualityScore() {
        let score = 100;

        // 延遲扣分
        const avgLatency = this._getAvgLatency();
        if (avgLatency > 1000) score -= 30;
        else if (avgLatency > 500) score -= 15;
        else if (avgLatency > 200) score -= 5;

        // 斷線扣分
        score -= Math.min(30, this.quality.disconnects * 10);

        // 重連失敗扣分
        score -= Math.min(20, this.quality.reconnectFailed * 5);

        this.quality.score = Math.max(0, Math.min(100, score));
    }

    /**
     * 獲取平均延遲
     */
    _getAvgLatency() {
        if (this.quality.latencySamples.length === 0) return 0;
        const sum = this.quality.latencySamples.reduce((a, b) => a + b, 0);
        return sum / this.quality.latencySamples.length;
    }

    // ==================== 頁面可見性 ====================

    /**
     * 設置頁面可見性處理
     */
    _setupVisibilityHandler() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this._pageHidden = true;
                // 頁面隱藏時延長心跳間隔
                this._stopHeartbeat();
                this.heartbeat.timer = setInterval(() => this._sendPing(), 60000);
            } else {
                this._pageHidden = false;
                // 恢復正常心跳
                this._stopHeartbeat();
                this._startHeartbeat();
                // 如果斷線了，嘗試重連
                if (!this.state.isConnected && !this.state.isConnecting) {
                    console.log('👁️ 頁面恢復，重新連接');
                    this.state.reconnectAttempts = 0;
                    this.connect();
                }
                // 發送同步請求獲取最新狀態
                this._emit('page_visible', { timestamp: new Date().toISOString() });
            }
        });
    }

    /**
     * 設置網絡狀態處理
     */
    _setupNetworkHandler() {
        window.addEventListener('online', () => {
            console.log('🌐 網絡恢復');
            if (!this.state.isConnected && !this.state.isConnecting) {
                this.state.reconnectAttempts = 0;
                this.connect();
            }
        });

        window.addEventListener('offline', () => {
            console.log('🌐 網絡中斷');
            this._emit('network_offline', { timestamp: new Date().toISOString() });
        });
    }

    // ==================== 連接指示器 ====================

    /**
     * 顯示連接狀態指示器
     */
    showIndicator() {
        if (this.indicator) return;

        this.indicator = document.createElement('div');
        this.indicator.id = 'ws-core-indicator';
        this.indicator.style.cssText = `
            position: fixed; bottom: 10px; right: 10px;
            padding: 6px 12px; border-radius: 20px;
            font-size: 12px; z-index: 9999;
            background: rgba(0,0,0,0.8); color: white;
            display: flex; align-items: center; gap: 6px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            cursor: pointer; transition: all 0.3s ease;
        `;
        this.indicator.addEventListener('click', () => this._showDetails());
        document.body.appendChild(this.indicator);
        this._updateIndicator();
    }

    /**
     * 更新指示器
     */
    _updateIndicator() {
        if (!this.indicator) return;

        let html, title;

        if (this.state.isConnected) {
            const score = this.quality.score;
            let color = '#28a745';
            let text = '已連線';
            if (score < 50) { color = '#dc3545'; text = '連線不佳'; }
            else if (score < 80) { color = '#ffc107'; text = '連線一般'; }

            html = `<span style="color:${color}">●</span> ${text} <span style="opacity:0.7">${Math.round(this.heartbeat.latency)}ms</span>`;
            title = `WebSocket 已連線 | 品質: ${score}分 | 延遲: ${Math.round(this.heartbeat.latency)}ms | 佇列: ${this.messageQueue.length}條`;
        } else if (this.state.isConnecting) {
            html = `<span style="color:#ffc107">⟳</span> 連線中...`;
            title = '正在建立 WebSocket 連線...';
        } else {
            html = `<span style="color:#dc3545">●</span> 離線`;
            title = `WebSocket 離線 | 重試: ${this.state.reconnectAttempts}/${this.options.maxRetries}`;
            if (this.state.reconnectAttempts > 0) {
                html += ` <span style="opacity:0.7">(${this.state.reconnectAttempts})</span>`;
            }
        }

        this.indicator.innerHTML = html;
        this.indicator.title = title;
    }

    /**
     * 顯示詳細資訊
     */
    _showDetails() {
        const status = this.getStatus();
        const lines = [
            'WebSocket 核心狀態',
            '═══════════════════',
            `狀態: ${status.isConnected ? '✅ 已連線' : status.isConnecting ? '🔄 連線中' : '❌ 離線'}`,
            `品質: ${status.qualityScore}分`,
            `延遲: ${Math.round(status.latency)}ms`,
            `重連: ${status.reconnectAttempts}/${status.maxRetries}`,
            `訊息: ${status.messageCount}條`,
            `佇列: ${status.queueSize}條`,
            `運行: ${Math.round(status.uptime / 1000)}秒`,
            '',
            `⏱ ${new Date().toLocaleTimeString()}`
        ];
        alert(lines.join('\n'));
    }

    // ==================== 清理 ====================

    /**
     * 清理資源
     */
    cleanup() {
        this.disconnect();
        this.messageQueue = [];
        this.listeners = {};
        if (this.indicator) {
            this.indicator.remove();
            this.indicator = null;
        }
        WebSocketCore._instance = null;
        console.log('🧹 WebSocketCore 已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.WebSocketCore = WebSocketCore;

    // 立即初始化（同步腳本加載順序）
    // 使用 setTimeout(0) 確保在當前執行緒完成後初始化，
    // 但早於其他依賴 WebSocketCore 的腳本
    setTimeout(() => {
        if (!WebSocketCore.getInstance()) {
            const core = new WebSocketCore({
                autoConnect: true,
                showIndicator: false // 預設不顯示，由各頁面決定
            });
            window.wsCore = core;
            console.log('🌍 WebSocketCore 已註冊到 window.wsCore');
        }
    }, 0);
}

console.log('✅ websocket-core.js 加載完成');
