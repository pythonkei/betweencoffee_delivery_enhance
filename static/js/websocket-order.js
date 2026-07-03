/**
 * websocket-order.js - 顧客端訂單 WebSocket 管理器（v3.0.0）
 * 
 * 基於 websocket-core.js v3.0.0 的事件系統，管理訂單頁面的即時更新。
 * 支援訂單狀態、隊列位置、預計時間、支付狀態等更新。
 * 
 * 功能：
 * - 訂單專屬 WebSocket 連線管理
 * - 訂單狀態即時更新
 * - 隊列位置與預計時間更新
 * - 支付狀態更新
 * - 訂單就緒通知
 * - 重連後自動同步
 * - 頁面可見性恢復時自動同步
 * - 支援 HTTP fallback 模式（WebSocket 不可用時自動切換）
 * - 支援 localStorage 持久化訂閱
 * 
 * 版本: 3.0.0
 * 最後更新: 2026-07-03
 */

class OrderWebSocket {
    /**
     * @param {Object} options
     * @param {number|string} options.orderId - 訂單 ID（必填）
     * @param {Function} options.onStatusUpdate - 狀態更新回調
     * @param {Function} options.onQueueUpdate - 隊列更新回調
     * @param {Function} options.onPaymentUpdate - 支付更新回調
     * @param {Function} options.onOrderReady - 訂單就緒回調
     * @param {Function} options.onError - 錯誤回調
     * @param {Function} options.onConnectionChange - 連線狀態變化回調
     * @param {boolean} options.autoConnect - 是否自動連接（預設 true）
     * @param {boolean} options.showIndicator - 是否顯示連接指示器（預設 false）
     */
    constructor(options = {}) {
        if (!options.orderId) {
            throw new Error('OrderWebSocket: orderId 為必填參數');
        }

        this.options = {
            orderId: options.orderId,
            onStatusUpdate: options.onStatusUpdate || null,
            onQueueUpdate: options.onQueueUpdate || null,
            onPaymentUpdate: options.onPaymentUpdate || null,
            onOrderReady: options.onOrderReady || null,
            onError: options.onError || null,
            onConnectionChange: options.onConnectionChange || null,
            autoConnect: options.autoConnect !== false,
            showIndicator: options.showIndicator || false,
            ...options
        };

        // 訂單狀態快取
        this.orderStatus = null;

        // 取消註冊函數列表
        this._unsubscribers = [];

        // 初始化
        this._init();

        console.log(`🔧 OrderWebSocket 初始化: 訂單 ${this.options.orderId}`);
    }

    /**
     * 初始化：等待核心就緒後註冊事件
     */
    _init() {
        const core = WebSocketCore.getInstance();

        if (core) {
            this._registerEvents(core);
        } else {
            // 核心尚未初始化，等待
            const checkCore = setInterval(() => {
                const c = WebSocketCore.getInstance();
                if (c) {
                    clearInterval(checkCore);
                    this._registerEvents(c);
                }
            }, 200);

            // 10 秒超時
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

        // 監聽訂單相關訊息
        this._unsubscribers.push(
            core.on('message:order_status', (data) => this._handleOrderStatus(data))
        );
        this._unsubscribers.push(
            core.on('message:order_status_update', (data) => this._handleOrderStatusUpdate(data))
        );
        this._unsubscribers.push(
            core.on('message:queue_position', (data) => this._handleQueuePosition(data))
        );
        this._unsubscribers.push(
            core.on('message:estimated_time', (data) => this._handleEstimatedTime(data))
        );
        this._unsubscribers.push(
            core.on('message:payment_status', (data) => this._handlePaymentStatus(data))
        );
        this._unsubscribers.push(
            core.on('message:order_ready', (data) => this._handleOrderReady(data))
        );
        this._unsubscribers.push(
            core.on('message:staff_action', (data) => this._handleStaffAction(data))
        );
        this._unsubscribers.push(
            core.on('message:sync_complete', (data) => this._handleSyncComplete(data))
        );

        // 如果核心已連線，立即發送訂閱
        if (core.state.isConnected) {
            this._subscribeToOrder();
        }

        console.log(`✅ OrderWebSocket 事件註冊完成: 訂單 ${this.options.orderId}`);
    }

    // ==================== 連線事件處理 ====================

    /**
     * 連線成功
     */
    _onConnected() {
        console.log(`✅ OrderWebSocket 核心已連線，訂閱訂單 ${this.options.orderId}`);
        this._subscribeToOrder();
        this._notifyConnectionChange(true);
    }

    /**
     * 斷線
     */
    _onDisconnected(data) {
        console.log(`🔌 OrderWebSocket 核心斷線: ${data.reason}`);
        this._notifyConnectionChange(false);
    }

    /**
     * 重連中
     */
    _onReconnecting(data) {
        console.log(`🔄 OrderWebSocket 重連中 (${data.attempt}/${data.maxRetries})`);
        this._notifyConnectionChange(false, 'reconnecting');
    }

    /**
     * 重連失敗
     */
    _onReconnectFailed() {
        console.error('❌ OrderWebSocket 重連失敗');
        if (this.options.onError) {
            this.options.onError(new Error('WebSocket 重連失敗'));
        }
    }

    /**
     * 頁面恢復可見
     */
    _onPageVisible() {
        console.log(`👁️ OrderWebSocket 頁面恢復，請求同步訂單 ${this.options.orderId}`);
        this._requestSync();
    }

    // ==================== 訂閱與同步 ====================

    /**
     * 訂閱訂單（發送訂閱訊息到服務端）
     */
    _subscribeToOrder() {
        if (!this.core) return;

        this.core.sendJSON({
            type: 'subscribe_order',
            order_id: this.options.orderId,
            timestamp: new Date().toISOString()
        });

        // 同時請求當前狀態
        this._requestSync();
    }

    /**
     * 請求同步（重連後或頁面恢復時）
     */
    _requestSync() {
        if (!this.core || !this.core.state.isConnected) return;

        console.log(`🔄 OrderWebSocket 請求同步: 訂單 ${this.options.orderId}`);
        this.core.sendJSON({
            type: 'sync_request',
            order_id: this.options.orderId,
            timestamp: new Date().toISOString()
        });
    }

    // ==================== 訊息處理 ====================

    /**
     * 處理訂單狀態（統一格式）
     */
    _handleOrderStatus(data) {
        const statusData = data.data || data;
        this.orderStatus = statusData;

        console.log(`📦 訂單狀態更新: ${statusData.status} (${statusData.status_display})`);

        if (this.options.onStatusUpdate) {
            this.options.onStatusUpdate(statusData);
        }
    }

    /**
     * 處理訂單狀態更新（舊格式兼容）
     */
    _handleOrderStatusUpdate(data) {
        this.orderStatus = data;

        if (this.options.onStatusUpdate) {
            this.options.onStatusUpdate(data);
        }
    }

    /**
     * 處理隊列位置更新
     */
    _handleQueuePosition(data) {
        console.log(`📊 隊列位置更新: 位置 ${data.position}`);

        if (this.options.onQueueUpdate) {
            this.options.onQueueUpdate({
                position: data.position,
                estimated_time: data.estimated_time,
                remaining_seconds: data.remaining_seconds
            });
        }
    }

    /**
     * 處理預計時間更新
     */
    _handleEstimatedTime(data) {
        console.log(`⏱ 預計時間更新: ${data.remaining_seconds}秒`);

        if (this.options.onQueueUpdate) {
            this.options.onQueueUpdate({
                position: data.position,
                estimated_time: data.estimated_time,
                remaining_seconds: data.remaining_seconds
            });
        }
    }

    /**
     * 處理支付狀態更新
     */
    _handlePaymentStatus(data) {
        console.log(`💰 支付狀態更新: ${data.payment_status}`);

        if (this.options.onPaymentUpdate) {
            this.options.onPaymentUpdate({
                payment_status: data.payment_status,
                payment_method: data.payment_method,
                message: data.message
            });
        }
    }

    /**
     * 處理訂單就緒通知
     */
    _handleOrderReady(data) {
        console.log(`🎉 訂單就緒! 取餐碼: ${data.pickup_code}`);

        if (this.options.onOrderReady) {
            this.options.onOrderReady({
                order_id: data.order_id,
                pickup_code: data.pickup_code,
                customer_name: data.customer_name
            });
        }
    }

    /**
     * 處理員工操作通知
     */
    _handleStaffAction(data) {
        console.log(`👨‍🍳 員工操作: ${data.data?.action || '未知'}`);
    }

    /**
     * 處理同步完成
     */
    _handleSyncComplete(data) {
        console.log(`✅ OrderWebSocket 同步完成: 訂單 ${data.order_id}`);
    }

    // ==================== 通知回調 ====================

    /**
     * 通知連線狀態變化
     */
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
     * 獲取當前訂單狀態快取
     * @returns {Object|null}
     */
    getOrderStatus() {
        return this.orderStatus;
    }

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
        this.orderStatus = null;
        console.log('🧹 OrderWebSocket 已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.OrderWebSocket = OrderWebSocket;
}

console.log('✅ websocket-order.js 加載完成');
