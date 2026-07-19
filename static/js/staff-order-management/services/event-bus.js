// static/js/staff-order-management/services/event-bus.js
// ==================== 統一事件匯流排服務 ====================
// 功能：提供統一的應用內事件發布/訂閱機制
// 依賴：無（獨立運行）
//
// 使用方式：
//   // 訂閱事件
//   EventBus.on('fps_payment_confirmed', (data) => { ... });
//   EventBus.on('order_cancelled', (data) => { ... }, { once: true });
//
//   // 發布事件
//   EventBus.emit('fps_payment_confirmed', { order_id: 123, payment_status: 'paid' });
//
//   // 取消訂閱
//   EventBus.off('fps_payment_confirmed', handler);
//
//   // 清理所有
//   EventBus.clear();
//
// 整合方式：
//   在 HTML 中引入此文件後，即可在任何地方使用 EventBus
//   現有代碼中的 document.dispatchEvent(new CustomEvent(...)) 仍可繼續使用
//   EventBus 會自動監聽 document 上的 CustomEvent 並轉發

class EventBus {
    constructor() {
        this.name = 'EventBus';
        this._listeners = new Map();
        this._wildcardListeners = new Set();
        this._bridgeActive = false;
        this._emitDepth = 0;  // 防止 emit 遞迴
        
        console.log('🔄 EventBus 初始化...');
        this._initBridge();
        console.log('✅ EventBus 初始化完成');
    }
    
    /**
     * 初始化與原生 CustomEvent 的橋接
     * 讓 EventBus 能監聽到 document.dispatchEvent(new CustomEvent(...))
     * 
     * 注意：橋接監聽器使用 _emitFromBridge 而非 emit，
     * 避免 emit 內部 dispatchEvent 觸發橋接監聽器造成無限循環
     */
    _initBridge() {
        if (this._bridgeActive) return;
        
        document.addEventListener('fps_payment_confirmed', (e) => {
            this._emitFromBridge('fps_payment_confirmed', e.detail);
        });
        
        document.addEventListener('cash_payment_confirmed', (e) => {
            this._emitFromBridge('cash_payment_confirmed', e.detail);
        });
        
        document.addEventListener('order_cancelled', (e) => {
            this._emitFromBridge('order_cancelled', e.detail);
        });
        
        document.addEventListener('order_status_changed', (e) => {
            this._emitFromBridge('order_status_changed', e.detail);
        });
        
        document.addEventListener('data_refreshed', (e) => {
            this._emitFromBridge('data_refreshed', e.detail);
        });
        
        this._bridgeActive = true;
        console.log('🌉 EventBus 橋接已建立（監聽原生 CustomEvent）');
    }
    
    /**
     * 從橋接器觸發事件（不觸發 CustomEvent，防止無限循環）
     */
    _emitFromBridge(event, data = {}) {
        console.log(`📡 EventBus: 橋接事件 "${event}"`, data);
        
        // 通知特定事件的監聽器
        if (this._listeners.has(event)) {
            this._listeners.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ EventBus: 事件 "${event}" 處理器錯誤:`, error);
                }
            });
        }
        
        // 通知萬用字元監聽器
        this._wildcardListeners.forEach(handler => {
            try {
                handler(event, data);
            } catch (error) {
                console.error(`❌ EventBus: 萬用字元監聽器錯誤:`, error);
            }
        });
        
        // 注意：不觸發 CustomEvent，避免橋接器再次捕獲造成無限循環
    }
    
    /**
     * 發布事件
     */
    emit(event, data = {}) {
        // 防止遞迴：如果 emit 深度超過 10，說明是橋接器觸發的循環
        this._emitDepth++;
        if (this._emitDepth > 10) {
            console.error(`❌ EventBus: 檢測到事件 "${event}" 無限循環，已中斷`);
            this._emitDepth = 0;
            return;
        }
        
        console.log(`📡 EventBus: 發布事件 "${event}"`, data);
        
        // 通知特定事件的監聽器
        if (this._listeners.has(event)) {
            this._listeners.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`❌ EventBus: 事件 "${event}" 處理器錯誤:`, error);
                }
            });
        }
        
        // 通知萬用字元監聽器（監聽所有事件）
        this._wildcardListeners.forEach(handler => {
            try {
                handler(event, data);
            } catch (error) {
                console.error(`❌ EventBus: 萬用字元監聽器錯誤:`, error);
            }
        });
        
        // 同時也觸發原生 CustomEvent（向後兼容）
        try {
            document.dispatchEvent(new CustomEvent(event, { detail: data }));
        } catch (error) {
            // 忽略 CustomEvent 錯誤
        }
        
        this._emitDepth--;
    }
    
    /**
     * 訂閱事件
     * @param {string} event - 事件名稱
     * @param {Function} handler - 處理函數
     * @param {Object} options - 選項 { once: boolean }
     * @returns {Function} 取消訂閱的函數
     */
    on(event, handler, options = {}) {
        if (typeof handler !== 'function') {
            console.error(`❌ EventBus.on: handler 必須是函數`);
            return () => {};
        }
        
        if (!this._listeners.has(event)) {
            this._listeners.set(event, new Set());
        }
        
        const wrappedHandler = options.once ? (...args) => {
            handler(...args);
            this.off(event, wrappedHandler);
        } : handler;
        
        this._listeners.get(event).add(wrappedHandler);
        
        console.log(`📡 EventBus: 訂閱事件 "${event}"`);
        
        // 返回取消訂閱函數
        return () => this.off(event, wrappedHandler);
    }
    
    /**
     * 一次性訂閱
     */
    once(event, handler) {
        return this.on(event, handler, { once: true });
    }
    
    /**
     * 取消訂閱
     */
    off(event, handler) {
        if (!this._listeners.has(event)) return;
        
        if (handler) {
            this._listeners.get(event).delete(handler);
        } else {
            this._listeners.delete(event);
        }
        
        console.log(`📡 EventBus: 取消訂閱事件 "${event}"`);
    }
    
    /**
     * 監聽所有事件（萬用字元）
     */
    onAny(handler) {
        if (typeof handler === 'function') {
            this._wildcardListeners.add(handler);
            return () => this._wildcardListeners.delete(handler);
        }
        return () => {};
    }
    
    /**
     * 獲取所有已訂閱的事件名稱
     */
    getEvents() {
        return Array.from(this._listeners.keys());
    }
    
    /**
     * 獲取特定事件的監聽器數量
     */
    listenerCount(event) {
        return this._listeners.has(event) ? this._listeners.get(event).size : 0;
    }
    
    /**
     * 清理所有訂閱
     */
    clear() {
        this._listeners.clear();
        this._wildcardListeners.clear();
        console.log('🗑️ EventBus: 所有訂閱已清理');
    }
    
    /**
     * 銷毀服務
     */
    destroy() {
        this.clear();
        this._bridgeActive = false;
        console.log('🗑️ EventBus 已銷毀');
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    // 創建全局實例
    window.eventBus = new EventBus();
    window.EventBus = EventBus;
    console.log('🌍 EventBus 已註冊到 window 對象');
}
