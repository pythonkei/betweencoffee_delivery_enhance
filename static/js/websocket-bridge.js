/**
 * websocket-bridge.js - WebSocket 新舊架構兼容橋接層
 * 
 * 讓現有的 UnifiedOrderUpdaterEnhanced 和其他舊版 WebSocket 管理器
 * 可以無縫使用新的 WebSocketCore 核心管理器。
 * 
 * 橋接策略：
 * 1. 如果 WebSocketCore 已初始化，使用核心的單一連線
 * 2. 如果核心未初始化，回退到舊版獨立 WebSocket 連線
 * 3. 提供統一的 API 介面，讓遷移過程平滑無痛
 * 
 * 版本: 1.0.0
 * 最後更新: 2026-06-17
 */

class WebSocketBridge {
    /**
     * @param {Object} options
     * @param {string} options.url - WebSocket URL
     * @param {string} options.type - 連線類型 ('order' | 'queue' | 'test')
     * @param {number|string} [options.orderId] - 訂單 ID（type='order' 時必填）
     * @param {Object} options.callbacks - 回調函數
     */
    constructor(options = {}) {
        this.options = {
            url: options.url || this._getDefaultUrl(options.type),
            type: options.type || 'queue',
            orderId: options.orderId || null,
            callbacks: {
                onOpen: options.onOpen || null,
                onClose: options.onClose || null,
                onMessage: options.onMessage || null,
                onError: options.onError || null,
                onReconnect: options.onReconnect || null,
                ...(options.callbacks || {})
            }
        };

        // 核心實例引用
        this.core = WebSocketCore.getInstance();
        this._useCore = !!this.core;

        // 舊版 WebSocket（當核心不可用時）
        this._ws = null;
        this._reconnectTimer = null;
        this._reconnectAttempts = 0;
        this._heartbeatTimer = null;
        this._isConnected = false;

        // 取消註冊函數
        this._unsubscribers = [];

        if (this._useCore) {
            this._setupWithCore();
        } else {
            this._setupLegacy();
        }

        console.log(`🔗 WebSocketBridge 初始化: type=${this.options.type}, mode=${this._useCore ? 'core' : 'legacy'}`);
    }

    /**
     * 獲取預設 URL
     */
    _getDefaultUrl(type) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;

        if (type === 'order' && this.options.orderId) {
            return `${protocol}//${host}/ws/order/${this.options.orderId}/`;
        }
        return `${protocol}//${host}/ws/queue/`;
    }

    /**
     * 使用核心管理器設置
     */
    _setupWithCore() {
        // 監聽核心事件並轉發到舊版回調
        if (this.options.callbacks.onOpen) {
            this._unsubscribers.push(
                this.core.on('connected', () => this.options.callbacks.onOpen())
            );
        }
        if (this.options.callbacks.onClose) {
            this._unsubscribers.push(
                this.core.on('disconnected', (data) => this.options.callbacks.onClose(data))
            );
        }
        if (this.options.callbacks.onReconnect) {
            this._unsubscribers.push(
                this.core.on('reconnecting', (data) => {
                    if (this.options.callbacks.onReconnect) {
                        this.options.callbacks.onReconnect(data.attempt, data.maxRetries);
                    }
                })
            );
        }

        // 監聽所有訊息並轉發
        if (this.options.callbacks.onMessage) {
            this._unsubscribers.push(
                this.core.on('message', (data) => this.options.callbacks.onMessage({
                    data: JSON.stringify(data)
                }))
            );
        }

        // 如果核心已連線，觸發 onOpen
        if (this.core.state.isConnected && this.options.callbacks.onOpen) {
            setTimeout(() => this.options.callbacks.onOpen(), 100);
        }

        this._isConnected = this.core.state.isConnected;
    }

    /**
     * 使用舊版獨立 WebSocket
     */
    _setupLegacy() {
        console.log('⚠️ WebSocketBridge: 核心不可用，使用舊版獨立連線');
        this.connect();
    }

    /**
     * 建立連線（舊版模式）
     */
    connect() {
        if (this._useCore) {
            if (!this.core.state.isConnected) {
                this.core.connect();
            }
            return;
        }

        if (this._ws && this._ws.readyState === WebSocket.OPEN) return;

        try {
            this._ws = new WebSocket(this.options.url);
            this._ws.onopen = (e) => {
                this._isConnected = true;
                this._reconnectAttempts = 0;
                this._startHeartbeat();
                if (this.options.callbacks.onOpen) this.options.callbacks.onOpen(e);
            };
            this._ws.onclose = (e) => {
                this._isConnected = false;
                this._stopHeartbeat();
                if (this.options.callbacks.onClose) this.options.callbacks.onClose(e);
                if (e.code !== 1000) this._scheduleReconnect();
            };
            this._ws.onmessage = (e) => {
                if (this.options.callbacks.onMessage) this.options.callbacks.onMessage(e);
            };
            this._ws.onerror = (e) => {
                if (this.options.callbacks.onError) this.options.callbacks.onError(e);
            };
        } catch (err) {
            console.error('❌ WebSocketBridge 連線失敗:', err);
            this._scheduleReconnect();
        }
    }

    /**
     * 發送訊息
     */
    send(data) {
        if (this._useCore) {
            return this.core.send(data);
        }

        if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            try {
                this._ws.send(typeof data === 'string' ? data : JSON.stringify(data));
                return true;
            } catch (e) {
                console.error('❌ WebSocketBridge 發送失敗:', e);
                return false;
            }
        }
        return false;
    }

    /**
     * 斷開連線
     */
    disconnect() {
        if (this._useCore) {
            // 核心模式下不真正斷開，只取消訂閱
            this._unsubscribers.forEach(fn => { try { fn(); } catch(e) {} });
            this._unsubscribers = [];
            return;
        }

        this._stopHeartbeat();
        this._clearReconnectTimer();
        if (this._ws) {
            try { this._ws.close(1000); } catch(e) {}
            this._ws = null;
        }
        this._isConnected = false;
    }

    /**
     * 檢查是否已連線
     */
    isConnected() {
        if (this._useCore) {
            return this.core && this.core.state.isConnected;
        }
        return this._isConnected;
    }

    /**
     * 舊版心跳
     */
    _startHeartbeat() {
        this._stopHeartbeat();
        this._heartbeatTimer = setInterval(() => {
            if (this._ws && this._ws.readyState === WebSocket.OPEN) {
                this._ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    _stopHeartbeat() {
        if (this._heartbeatTimer) {
            clearInterval(this._heartbeatTimer);
            this._heartbeatTimer = null;
        }
    }

    /**
     * 舊版重連
     */
    _scheduleReconnect() {
        if (this._reconnectAttempts >= 10) return;
        this._reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(1.5, this._reconnectAttempts - 1), 30000);
        if (this.options.callbacks.onReconnect) {
            this.options.callbacks.onReconnect(this._reconnectAttempts, 10);
        }
        this._reconnectTimer = setTimeout(() => this.connect(), delay);
    }

    _clearReconnectTimer() {
        if (this._reconnectTimer) {
            clearTimeout(this._reconnectTimer);
            this._reconnectTimer = null;
        }
    }

    /**
     * 清理資源
     */
    cleanup() {
        this.disconnect();
        console.log('🧹 WebSocketBridge 已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.WebSocketBridge = WebSocketBridge;
}

console.log('✅ websocket-bridge.js 加載完成');
