/**
 * websocket-staff.js - 員工端隊列 WebSocket 管理器
 * 
 * 基於 websocket-core.js 的事件系統，管理員工隊列頁面的即時更新。
 * 支援新訂單通知、隊列更新、訂單就緒通知、支付更新等。
 * 
 * 功能：
 * - 隊列即時更新
 * - 新訂單通知（含音效提示）
 * - 訂單就緒通知
 * - 支付狀態更新
 * - 系統訊息廣播
 * - 重連後自動同步
 * - 頁面可見性恢復時自動同步
 * 
 * 版本: 2.0.0
 * 最後更新: 2026-06-17
 */

class StaffWebSocket {
    /**
     * @param {Object} options
     * @param {Function} options.onQueueUpdate - 隊列更新回調
     * @param {Function} options.onNewOrder - 新訂單回調
     * @param {Function} options.onOrderReady - 訂單就緒回調
     * @param {Function} options.onPaymentUpdate - 支付更新回調
     * @param {Function} options.onSystemMessage - 系統訊息回調
     * @param {Function} options.onError - 錯誤回調
     * @param {Function} options.onConnectionChange - 連線狀態變化回調
     * @param {boolean} options.autoConnect - 是否自動連接（預設 true）
     * @param {boolean} options.enableSound - 是否啟用新訂單音效（預設 true）
     * @param {boolean} options.showIndicator - 是否顯示連接指示器（預設 false）
     */
    constructor(options = {}) {
        this.options = {
            onQueueUpdate: options.onQueueUpdate || null,
            onNewOrder: options.onNewOrder || null,
            onOrderReady: options.onOrderReady || null,
            onPaymentUpdate: options.onPaymentUpdate || null,
            onSystemMessage: options.onSystemMessage || null,
            onError: options.onError || null,
            onConnectionChange: options.onConnectionChange || null,
            autoConnect: options.autoConnect !== false,
            enableSound: options.enableSound !== false,
            showIndicator: options.showIndicator || false,
            ...options
        };

        // 取消註冊函數列表
        this._unsubscribers = [];

        // 初始化
        this._init();

        console.log('🔧 StaffWebSocket 初始化');
    }

    /**
     * 初始化：等待核心就緒後註冊事件
     */
    _init() {
        const core = WebSocketCore.getInstance();

        if (core) {
            this._registerEvents(core);
        } else {
            const checkCore = setInterval(() => {
                const c = WebSocketCore.getInstance();
                if (c) {
                    clearInterval(checkCore);
                    this._registerEvents(c);
                }
            }, 200);

            setTimeout(() => clearInterval(checkCore), 10000);
        }
    }

    /**
     * 註冊事件監聽
     */
    _registerEvents(core) {
        this.core = core;

        // 監聽連線事件
        this._unsubscribers.push(
            core.on('connected', () => this._onConnected())
        );
        this._unsubscribers.push(
            core.on('disconnected', (data) => this._onDisconnected(data))
        );
        this._unsubscribers.push(
            core.on('reconnecting', (data) => this._onReconnecting(data))
        );
        this._unsubscribers.push(
            core.on('reconnect_failed', () => this._onReconnectFailed())
        );
        this._unsubscribers.push(
            core.on('page_visible', () => this._onPageVisible())
        );

        // 監聽隊列相關訊息
        this._unsubscribers.push(
            core.on('message:queue_update', (data) => this._handleQueueUpdate(data))
        );
        this._unsubscribers.push(
            core.on('message:new_order', (data) => this._handleNewOrder(data))
        );
        this._unsubscribers.push(
            core.on('message:order_ready', (data) => this._handleOrderReady(data))
        );
        this._unsubscribers.push(
            core.on('message:payment_update', (data) => this._handlePaymentUpdate(data))
        );
        this._unsubscribers.push(
            core.on('message:system', (data) => this._handleSystemMessage(data))
        );
        this._unsubscribers.push(
            core.on('message:staff_action', (data) => this._handleStaffAction(data))
        );

        // 如果核心已連線，立即請求同步
        if (core.state.isConnected) {
            this._requestSync();
        }

        console.log('✅ StaffWebSocket 事件註冊完成');
    }

    // ==================== 連線事件處理 ====================

    _onConnected() {
        console.log('✅ StaffWebSocket 核心已連線');
        this._requestSync();
        this._notifyConnectionChange(true);
    }

    _onDisconnected(data) {
        console.log(`🔌 StaffWebSocket 核心斷線: ${data.reason}`);
        this._notifyConnectionChange(false);
    }

    _onReconnecting(data) {
        console.log(`🔄 StaffWebSocket 重連中 (${data.attempt}/${data.maxRetries})`);
        this._notifyConnectionChange(false, 'reconnecting');
    }

    _onReconnectFailed() {
        console.error('❌ StaffWebSocket 重連失敗');
        if (this.options.onError) {
            this.options.onError(new Error('WebSocket 重連失敗'));
        }
    }

    _onPageVisible() {
        console.log('👁️ StaffWebSocket 頁面恢復，請求同步');
        this._requestSync();
    }

    // ==================== 同步 ====================

    _requestSync() {
        if (!this.core || !this.core.state.isConnected) return;

        console.log('🔄 StaffWebSocket 請求同步');
        this.core.sendJSON({
            type: 'sync_request',
            timestamp: new Date().toISOString()
        });
    }

    // ==================== 訊息處理 ====================

    /**
     * 處理隊列更新
     */
    _handleQueueUpdate(data) {
        console.log(`📊 隊列更新: ${data.action || 'update'}`);

        if (this.options.onQueueUpdate) {
            this.options.onQueueUpdate(data);
        }
    }

    /**
     * 處理新訂單通知
     */
    _handleNewOrder(data) {
        console.log(`🆕 新訂單: #${data.order_id} - ${data.customer_name}`);

        // 播放音效
        if (this.options.enableSound) {
            this._playNotificationSound();
        }

        if (this.options.onNewOrder) {
            this.options.onNewOrder(data);
        }
    }

    /**
     * 處理訂單就緒通知
     */
    _handleOrderReady(data) {
        console.log(`🎉 訂單就緒: #${data.order_id}`);

        if (this.options.onOrderReady) {
            this.options.onOrderReady(data);
        }
    }

    /**
     * 處理支付更新
     */
    _handlePaymentUpdate(data) {
        console.log(`💰 支付更新: #${data.order_id} - ${data.payment_status}`);

        if (this.options.onPaymentUpdate) {
            this.options.onPaymentUpdate(data);
        }
    }

    /**
     * 處理系統訊息
     */
    _handleSystemMessage(data) {
        console.log(`📢 系統訊息: ${data.message}`);

        if (this.options.onSystemMessage) {
            this.options.onSystemMessage(data);
        }
    }

    /**
     * 處理員工操作通知
     */
    _handleStaffAction(data) {
        console.log(`👨‍🍳 員工操作: ${data.data?.action || '未知'}`);
    }

    // ==================== 音效 ====================

    /**
     * 播放新訂單通知音效
     * 使用 Web Audio API 生成簡單提示音，無需外部音檔
     */
    _playNotificationSound() {
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            // 設定音調：兩聲短促提示音
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, audioCtx.currentTime); // A5
            oscillator.frequency.setValueAtTime(660, audioCtx.currentTime + 0.15); // E5

            gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);

            oscillator.start(audioCtx.currentTime);
            oscillator.stop(audioCtx.currentTime + 0.3);

            // 清理
            oscillator.onended = () => audioCtx.close();
        } catch (e) {
            // 音效播放失敗不影響主要功能
            console.debug('🔇 音效播放失敗:', e.message);
        }
    }

    // ==================== 通知回調 ====================

    _notifyConnectionChange(isConnected, status) {
        if (this.options.onConnectionChange) {
            this.options.onConnectionChange({
                isConnected,
                status: status || (isConnected ? 'connected' : 'disconnected')
            });
        }
    }

    // ==================== 公共方法 ====================

    /**
     * 手動請求同步
     */
    requestSync() {
        this._requestSync();
    }

    /**
     * 清理資源
     */
    cleanup() {
        this._unsubscribers.forEach(unsub => {
            try { unsub(); } catch (e) { /* ignore */ }
        });
        this._unsubscribers = [];
        this.core = null;
        console.log('🧹 StaffWebSocket 已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.StaffWebSocket = StaffWebSocket;
}

console.log('✅ websocket-staff.js 加載完成');
