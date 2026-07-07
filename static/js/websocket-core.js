/**
 * websocket-core.js - WebSocket 統一核心管理器（增強版 v3.0.0）
 * 
 * 整合所有 WebSocket 功能為單一核心，避免多個管理器衝突。
 * 所有其他 WebSocket 管理器（員工端、顧客端、優化器）都依賴此核心。
 * 
 * 增強功能：
 * - 無限重連 + 動態指數退避（最長5分鐘間隔）
 * - localStorage 持久化（離線佇列、訂閱狀態）
 * - HTTP 長輪詢 fallback 機制（WebSocket 不可用時自動切換）
 * - 服務端 reload 信號處理
 * - 統一 UI 連接狀態指示器
 * - Service Worker 背景監控（可選）
 * 
 * 版本: 3.0.0
 * 最後更新: 2026-07-03
 */
(function() {
    'use strict';

    class WebSocketCore {
        /**
         * @param {Object} options
         * @param {string} options.url - WebSocket URL（預設自動生成）
         * @param {number} options.heartbeatInterval - 心跳間隔（毫秒，預設 30000）
         * @param {number} options.heartbeatTimeout - 心跳超時（毫秒，預設 10000）
         * @param {number} options.baseDelay - 基礎重連延遲（毫秒，預設 1000）
         * @param {number} options.maxDelay - 最大重連延遲（毫秒，預設 300000 = 5分鐘）
         * @param {boolean} options.enableJitter - 是否啟用抖動（預設 true）
         * @param {number} options.jitterFactor - 抖動因子（預設 0.2）
         * @param {boolean} options.autoConnect - 是否自動連接（預設 true）
         * @param {boolean} options.showIndicator - 是否顯示連接指示器（預設 true）
         * @param {boolean} options.enableFallback - 是否啟用 HTTP fallback（預設 true）
         * @param {string} options.fallbackUrl - HTTP fallback URL（預設自動生成）
         * @param {number} options.fallbackInterval - fallback 輪詢間隔（毫秒，預設 5000）
         * @param {boolean} options.enablePersistence - 是否啟用 localStorage 持久化（預設 true）
         * @param {string} options.storageKey - localStorage 鍵前綴（預設 'ws_core_'）
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
                baseDelay: options.baseDelay || 1000,
                maxDelay: options.maxDelay || 300000, // 5分鐘
                enableJitter: options.enableJitter !== false,
                jitterFactor: options.jitterFactor || 0.2,
                autoConnect: options.autoConnect !== false,
                showIndicator: options.showIndicator !== false,
                enableFallback: options.enableFallback !== false,
                fallbackUrl: options.fallbackUrl || this._getDefaultFallbackUrl(),
                fallbackInterval: options.fallbackInterval || 5000,
                enablePersistence: options.enablePersistence !== false,
                storageKey: options.storageKey || 'ws_core_',
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
                bytesReceived: 0,
                consecutiveFailures: 0, // 連續失敗次數（用於觸發 fallback）
                isFallbackMode: false,  // 是否處於 fallback 模式
                isDestroyed: false      // 是否已銷毀
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

            // 離線訊息佇列（記憶體 + localStorage）
            this.messageQueue = [];
            this.maxQueueSize = 100;
            this.isProcessingQueue = false;

            // Fallback 輪詢
            this.fallback = {
                timer: null,
                lastPollTime: null,
                pollData: null,
                active: false
            };

            // 連接品質
            this.quality = {
                score: 100,
                latencySamples: [],
                disconnects: 0,
                reconnectSuccess: 0,
                reconnectFailed: 0,
                fallbackActivations: 0
            };

            // 事件監聽器: { eventType: [callback, ...] }
            this.listeners = {};

            // 頁面可見性
            this._pageHidden = false;

            // 連接指示器
            this.indicator = null;
            this.indicatorDetails = null;

            // 訂閱狀態（用於重連後自動恢復）
            this.subscriptions = {
                orders: new Set(),   // 訂閱的訂單 ID
                queues: new Set()    // 訂閱的隊列
            };

            // 設定為單例
            WebSocketCore._instance = this;

            console.log(`🔧 WebSocketCore v3.0.0 初始化: ${this.options.url}`);

            // 從 localStorage 恢復狀態
            if (this.options.enablePersistence) {
                this._loadPersistedState();
            }

            // 自動連接
            if (this.options.autoConnect) {
                this.connect();
            }

            // 設置頁面可見性監聽
            this._setupVisibilityHandler();

            // 設置網絡狀態監聽
            this._setupNetworkHandler();

            // 顯示連接指示器
            if (this.options.showIndicator) {
                this.showIndicator();
            }
        }

        // ==================== 靜態方法 ====================

        /**
         * 獲取單例實例
         * @returns {WebSocketCore|null}
         */
        static getInstance() {
            return WebSocketCore._instance || null;
        }

        /**
         * 重置單例（僅用於測試）
         */
        static resetInstance() {
            if (WebSocketCore._instance) {
                WebSocketCore._instance.cleanup();
            }
            WebSocketCore._instance = null;
        }

        // ==================== 連接管理 ====================

        /**
         * 建立 WebSocket 連接
         */
        connect() {
            if (this.state.isDestroyed) return;
            if (this.state.isConnected) {
                console.log('ℹ️ 已連接，跳過');
                return;
            }
            if (this.state.isConnecting) {
                console.log('ℹ️ 連接中，跳過');
                return;
            }

            this.state.isConnecting = true;
            this._updateIndicator();

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
                this.state.consecutiveFailures++;
                this._checkFallbackTrigger();
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
            this.state.reconnectAttempts = 0;
            this.state.consecutiveFailures = 0;
            this._stopFallback();
            this.disconnect();
            setTimeout(() => this.connect(), 500);
        }

        /**
         * 完全銷毀實例
         */
        destroy() {
            this.state.isDestroyed = true;
            this._stopFallback();
            this.cleanup();
        }

        // ==================== 訊息發送 ====================

        /**
         * 發送訊息
         * @param {Object|string} data - 要發送的數據
         * @param {number} [priority] - 優先級（0=最高，3=最低）
         * @returns {boolean} 是否成功發送
         */
        send(data, priority = 2) {
            if (this.state.isDestroyed) return false;

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

        // ==================== 訂閱管理 ====================

        /**
         * 訂閱訂單更新
         * @param {number|string} orderId
         */
        subscribeOrder(orderId) {
            this.subscriptions.orders.add(String(orderId));
            this._persistSubscriptions();

            if (this.state.isConnected) {
                this.sendJSON({
                    type: 'subscribe_order',
                    order_id: orderId,
                    timestamp: new Date().toISOString()
                });
            }
        }

        /**
         * 取消訂閱訂單
         * @param {number|string} orderId
         */
        unsubscribeOrder(orderId) {
            this.subscriptions.orders.delete(String(orderId));
            this._persistSubscriptions();
        }

        /**
         * 訂閱隊列更新
         */
        subscribeQueue() {
            this.subscriptions.queues.add('main');
            this._persistSubscriptions();
        }

        /**
         * 取消訂閱隊列
         */
        unsubscribeQueue() {
            this.subscriptions.queues.delete('main');
            this._persistSubscriptions();
        }

        /**
         * 獲取所有訂閱的訂單 ID
         * @returns {string[]}
         */
        getSubscribedOrders() {
            return Array.from(this.subscriptions.orders);
        }

        /**
         * 是否訂閱了隊列
         * @returns {boolean}
         */
        isSubscribedToQueue() {
            return this.subscriptions.queues.has('main');
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
                isFallbackMode: this.state.isFallbackMode,
                readyState: this.socket ? readyStateMap[this.socket.readyState] : 'CLOSED',
                reconnectAttempts: this.state.reconnectAttempts,
                messageCount: this.state.messageCount,
                queueSize: this.messageQueue.length,
                latency: this.heartbeat.latency,
                qualityScore: this.quality.score,
                disconnects: this.quality.disconnects,
                fallbackActivations: this.quality.fallbackActivations,
                uptime: this.state.connectionStartTime
                    ? Date.now() - this.state.connectionStartTime
                    : 0,
                subscribedOrders: this.getSubscribedOrders(),
                subscribedToQueue: this.isSubscribedToQueue()
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
         * 獲取預設 Fallback URL
         */
        _getDefaultFallbackUrl() {
            return `${window.location.protocol}//${window.location.host}/api/ws-fallback/`;
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
            this.state.consecutiveFailures = 0;
            this.heartbeat.lastPongTime = Date.now();

            // 如果之前是 fallback 模式，切換回來
            if (this.state.isFallbackMode) {
                this.state.isFallbackMode = false;
                this._stopFallback();
                console.log('🔄 WebSocket 已恢復，退出 fallback 模式');
            }

            // 更新品質
            this.quality.reconnectSuccess++;
            this.quality.disconnects = 0;
            this._updateQualityScore();

            // 啟動心跳
            this._startHeartbeat();

            // 恢復訂閱
            this._restoreSubscriptions();

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

                // 處理服務端 reload 信號
                if (data.type === 'server_reload' || data.type === 'force_reconnect') {
                    console.log('🔄 收到服務端重連信號');
                    this._emit('server_reload', data);
                    // 延遲重連
                    setTimeout(() => {
                        this.reconnect();
                    }, data.delay || 1000);
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
            this.state.consecutiveFailures++;
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

            // 檢查是否觸發 fallback
            this._checkFallbackTrigger();

            // 非正常關閉才重連（code 1000 = 正常關閉）
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
            this.state.consecutiveFailures++;
            this._checkFallbackTrigger();
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
                    this.state.consecutiveFailures++;
                    this._checkFallbackTrigger();
                    this._emit('heartbeat_timeout', { elapsed });
                    // 主動重連
                    this.disconnect(1001, '心跳超時');
                    this._scheduleReconnect();
                }
            }, this.options.heartbeatTimeout);
        }

        // ==================== 重連機制（增強版：無限重連 + 動態退避）====================

        /**
         * 安排重連（增強版：無限重連 + 動態退避）
         */
        _scheduleReconnect() {
            if (this.state.isDestroyed) return;

            this.state.reconnectAttempts++;

            // 動態指數退避
            let delay = this.options.baseDelay * Math.pow(2, Math.min(this.state.reconnectAttempts - 1, 10));
            delay = Math.min(delay, this.options.maxDelay);

            // 抖動
            if (this.options.enableJitter) {
                const jitter = delay * this.options.jitterFactor * (Math.random() * 2 - 1);
                delay = Math.max(1000, delay + jitter);
            }

            console.log(`🔄 ${Math.round(delay/1000)}秒後重連 (第 ${this.state.reconnectAttempts} 次)`);

            this._emit('reconnecting', {
                attempt: this.state.reconnectAttempts,
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

        // ==================== Fallback 機制（HTTP 長輪詢）====================

        /**
         * 檢查是否觸發 fallback 模式
         * 連續 3 次失敗後自動啟用
         */
        _checkFallbackTrigger() {
            if (!this.options.enableFallback) return;
            if (this.state.isFallbackMode) return;
            if (this.state.consecutiveFailures >= 3) {
                console.log('⚠️ 連續失敗 3 次，啟用 HTTP fallback 模式');
                this._startFallback();
            }
        }

        /**
         * 啟動 HTTP fallback 輪詢
         */
        _startFallback() {
            if (this.fallback.active) return;

            this.state.isFallbackMode = true;
            this.fallback.active = true;
            this.quality.fallbackActivations++;

            console.log(`🌐 啟動 HTTP fallback 輪詢: ${this.options.fallbackUrl}`);
            this._emit('fallback_start', { url: this.options.fallbackUrl });

            // 立即執行一次輪詢
            this._doFallbackPoll();

            // 定時輪詢
            this.fallback.timer = setInterval(() => {
                this._doFallbackPoll();
            }, this.options.fallbackInterval);

            this._updateIndicator();
        }

        /**
         * 執行一次 fallback 輪詢
         */
        async _doFallbackPoll() {
            if (!this.fallback.active || this.state.isDestroyed) return;

            try {
                // 構建查詢參數：訂閱的訂單 ID
                const params = new URLSearchParams();
                const orderIds = this.getSubscribedOrders();
                if (orderIds.length > 0) {
                    params.set('order_ids', orderIds.join(','));
                }
                if (this.isSubscribedToQueue()) {
                    params.set('queue', '1');
                }
                if (this.fallback.lastPollTime) {
                    params.set('since', this.fallback.lastPollTime);
                }

                const url = `${this.options.fallbackUrl}?${params.toString()}`;
                const response = await fetch(url, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(30000) // 30 秒超時
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                this.fallback.lastPollTime = new Date().toISOString();

                // 處理返回的更新
                if (data.updates && Array.isArray(data.updates)) {
                    data.updates.forEach(update => {
                        this._emit('message', update);
                        if (update.type) {
                            this._emit(`message:${update.type}`, update);
                        }
                    });
                }

                // 如果有訂單狀態，觸發訂單更新事件
                if (data.orders) {
                    Object.entries(data.orders).forEach(([orderId, orderData]) => {
                        this._emit('message:order_status', {
                            type: 'order_status',
                            data: orderData,
                            order_id: orderId
                        });
                    });
                }

                // 如果有隊列更新
                if (data.queue) {
                    this._emit('message:queue_update', {
                        type: 'queue_update',
                        ...data.queue
                    });
                }

                this._emit('fallback_poll', { timestamp: this.fallback.lastPollTime });

            } catch (error) {
                if (error.name === 'AbortError') {
                    console.debug('⏱️ Fallback 輪詢超時（正常）');
                } else {
                    console.warn('⚠️ Fallback 輪詢失敗:', error.message);
                }
            }
        }

        /**
         * 停止 fallback 輪詢
         */
        _stopFallback() {
            if (this.fallback.timer) {
                clearInterval(this.fallback.timer);
                this.fallback.timer = null;
            }
            this.fallback.active = false;
            this.state.isFallbackMode = false;
            this._updateIndicator();
        }

        // ==================== 離線佇列（增強版：localStorage 持久化）====================

        /**
         * 加入佇列
         */
        _enqueue(data, priority) {
            if (this.messageQueue.length >= this.maxQueueSize) {
                this.messageQueue.shift(); // 丟棄最舊
            }
            const item = {
                data,
                priority,
                timestamp: Date.now(),
                attempts: 0
            };
            this.messageQueue.push(item);

            // 持久化到 localStorage
            if (this.options.enablePersistence) {
                this._persistQueue();
            }

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

            // 持久化更新後的佇列
            if (this.options.enablePersistence) {
                this._persistQueue();
            }

            this.isProcessingQueue = false;
            console.log(`✅ 佇列處理完成，剩餘: ${this.messageQueue.length} 條`);
            this._emit('queue_processed', { remaining: this.messageQueue.length });
        }

        // ==================== localStorage 持久化 ====================

        /**
         * 持久化訂閱狀態
         */
        _persistSubscriptions() {
            try {
                const key = this.options.storageKey + 'subscriptions';
                const data = {
                    orders: Array.from(this.subscriptions.orders),
                    queues: Array.from(this.subscriptions.queues)
                };
                localStorage.setItem(key, JSON.stringify(data));
            } catch (e) {
                console.warn('⚠️ 持久化訂閱狀態失敗:', e.message);
            }
        }

        /**
         * 持久化離線佇列
         */
        _persistQueue() {
            try {
                const key = this.options.storageKey + 'queue';
                // 只持久化最近 20 條，避免 localStorage 滿
                const recentItems = this.messageQueue.slice(-20).map(item => ({
                    data: item.data,
                    priority: item.priority,
                    timestamp: item.timestamp,
                    attempts: item.attempts
                }));
                localStorage.setItem(key, JSON.stringify(recentItems));
            } catch (e) {
                console.warn('⚠️ 持久化離線佇列失敗:', e.message);
            }
        }

        /**
         * 從 localStorage 恢復狀態
         */
        _loadPersistedState() {
            try {
                // 恢復訂閱狀態
                const subKey = this.options.storageKey + 'subscriptions';
                const subData = localStorage.getItem(subKey);
                if (subData) {
                    const parsed = JSON.parse(subData);
                    if (parsed.orders) {
                        parsed.orders.forEach(id => this.subscriptions.orders.add(String(id)));
                    }
                    if (parsed.queues) {
                        parsed.queues.forEach(q => this.subscriptions.queues.add(q));
                    }
                    console.log(`📦 已恢復訂閱狀態: ${parsed.orders?.length || 0} 個訂單, ${parsed.queues?.length || 0} 個隊列`);
                }

                // 恢復離線佇列
                const queueKey = this.options.storageKey + 'queue';
                const queueData = localStorage.getItem(queueKey);
                if (queueData) {
                    const parsed = JSON.parse(queueData);
                    if (Array.isArray(parsed)) {
                        this.messageQueue = parsed;
                        console.log(`📦 已恢復離線佇列: ${parsed.length} 條`);
                    }
                }
            } catch (e) {
                console.warn('⚠️ 恢復持久化狀態失敗:', e.message);
            }
        }

        /**
         * 清除所有持久化數據
         */
        clearPersistedData() {
            try {
                localStorage.removeItem(this.options.storageKey + 'subscriptions');
                localStorage.removeItem(this.options.storageKey + 'queue');
                console.log('🧹 已清除所有持久化數據');
            } catch (e) {
                console.warn('⚠️ 清除持久化數據失敗:', e.message);
            }
        }

        /**
         * 重連後恢復訂閱
         */
        _restoreSubscriptions() {
            // 恢復訂單訂閱
            this.subscriptions.orders.forEach(orderId => {
                this.sendJSON({
                    type: 'subscribe_order',
                    order_id: orderId,
                    timestamp: new Date().toISOString()
                });
                console.log(`📋 恢復訂單訂閱: ${orderId}`);
            });

            // 恢復隊列訂閱
            if (this.subscriptions.queues.has('main')) {
                this.sendJSON({
                    type: 'subscribe_queue',
                    timestamp: new Date().toISOString()
                });
                console.log('📋 恢復隊列訂閱');
            }

            // 請求同步
            if (this.subscriptions.orders.size > 0 || this.subscriptions.queues.size > 0) {
                this.sendJSON({
                    type: 'sync_request',
                    timestamp: new Date().toISOString()
                });
            }
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

            // Fallback 模式扣分
            if (this.state.isFallbackMode) {
                score -= 20;
            }

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
                        this.state.consecutiveFailures = 0;
                        this._stopFallback();
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
                    this.state.consecutiveFailures = 0;
                    this._stopFallback();
                    this.connect();
                }
            });

            window.addEventListener('offline', () => {
                console.log('🌐 網絡中斷');
                this._emit('network_offline', { timestamp: new Date().toISOString() });
            });
        }

        // ==================== 連接指示器（增強版）====================

        /**
         * 顯示連接狀態指示器
         */
        showIndicator() {
            if (this.indicator) return;

            // 創建指示器容器
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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            `;
            this.indicator.addEventListener('click', () => this._showDetails());
            document.body.appendChild(this.indicator);
            this._updateIndicator();
        }

        /**
         * 隱藏連接狀態指示器
         */
        hideIndicator() {
            if (this.indicator) {
                this.indicator.remove();
                this.indicator = null;
            }
        }

        /**
         * 更新指示器
         */
        _updateIndicator() {
            if (!this.indicator) return;

            let html, title;

            if (this.state.isFallbackMode) {
                // Fallback 模式（黃色）
                html = `<span style="color:#ff9800">●</span> 輪詢模式 <span style="opacity:0.7">${Math.round(this.heartbeat.latency)}ms</span>`;
                title = `HTTP Fallback 輪詢模式 | 品質: ${this.quality.score}分 | 激活: ${this.quality.fallbackActivations}次`;
            } else if (this.state.isConnected) {
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
                title = `WebSocket 離線 | 重試: ${this.state.reconnectAttempts}次`;
                if (this.state.reconnectAttempts > 0) {
                    html += ` <span style="opacity:0.7">(${this.state.reconnectAttempts})</span>`;
                }
            }

            this.indicator.innerHTML = html;
            this.indicator.title = title;
        }

        /**
         * 顯示詳細資訊（彈窗）
         */
        _showDetails() {
            const status = this.getStatus();
            const lines = [
                'WebSocket 核心狀態 v3.0.0',
                '═══════════════════════',
                `狀態: ${status.isConnected ? '✅ 已連線' : status.isFallbackMode ? '🌐 輪詢模式' : status.isConnecting ? '🔄 連線中' : '❌ 離線'}`,
                `品質: ${status.qualityScore}分`,
                `延遲: ${Math.round(status.latency)}ms`,
                `重連: ${status.reconnectAttempts}次`,
                `Fallback: ${status.fallbackActivations}次`,
                `訊息: ${status.messageCount}條`,
                `佇列: ${status.queueSize}條`,
                `訂閱訂單: ${status.subscribedOrders.length}個`,
                `訂閱隊列: ${status.subscribedToQueue ? '是' : '否'}`,
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
            this._stopFallback();
            this.disconnect();
            this.messageQueue = [];
            this.listeners = {};
            this.hideIndicator();
            WebSocketCore._instance = null;
            console.log('🧹 WebSocketCore v3.0.0 已清理');
        }
    }

    // ==================== 全局註冊 ====================

    if (typeof window !== 'undefined') {
        window.WebSocketCore = WebSocketCore;

        // 立即初始化
        setTimeout(() => {
            if (!WebSocketCore.getInstance()) {
                const core = new WebSocketCore({
                    autoConnect: true,
                    showIndicator: false,
                    enableFallback: true,
                    enablePersistence: true
                });
                window.wsCore = core;
                console.log('🌍 WebSocketCore v3.0.0 已註冊到 window.wsCore');
            }
        }, 0);
    }

    console.log('✅ websocket-core.js v3.0.0 加載完成');
})();
