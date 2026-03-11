// static/js/staff-order-management/unified-data-manager.js
// ==================== 統一數據管理器 - 核心數據協調中心（增強版） ====================

class UnifiedDataManager {
    constructor() {
        console.log('🔄 初始化統一數據管理器（增強版）...');
        
        // 數據狀態
        this.currentData = null;
        this.lastUpdateTime = null;
        this.isLoading = false;
        this.hasError = false;
        this.errorCount = 0;
        this.maxRetryCount = 3;
        this.retryDelay = 5000; // 5秒
        
        // 監聽器註冊表（修正：添加 completed_orders）
        this.listeners = {
            badge_summary: [],      // 徽章數據監聽器
            waiting_orders: [],     // 等待隊列監聽器
            preparing_orders: [],   // 製作中訂單監聽器
            ready_orders: [],       // 已就緒訂單監聽器
            completed_orders: [],   // ✅ 已提取訂單監聽器（新增）
            all_data: []           // 所有數據監聽器
        };
        
        // 初始化
        this.init();
    }
    
    init() {
        console.log('✅ 統一數據管理器初始化完成');
        
        // 綁定全局事件
        this.bindGlobalEvents();
        
        // 啟動定期刷新
        this.startAutoRefresh();
        
        // 初始加載數據
        setTimeout(() => this.loadUnifiedData(), 1000);
    }
    
    // ==================== 核心方法：加載統一數據（增強版） ====================
    
    async loadUnifiedData(force = false, retryCount = 0) {
        // 防止重複加載
        if (this.isLoading && !force) {
            console.log('⚠️ 數據正在加載中，跳過重複請求');
            return false;
        }
        
        this.isLoading = true;
        const startTime = Date.now();
        
        try {
            console.log(`📡 ${retryCount > 0 ? `[重試 ${retryCount}] ` : ''}開始加載統一隊列數據...`);
            
            // 添加隨機參數防止緩存
            const timestamp = Date.now();
            const response = await fetch(`/eshop/queue/unified-data/?_=${timestamp}`, {
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                // 添加超時設置
                signal: AbortSignal.timeout(10000) // 10秒超時
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }
            
            const result = await response.json();
            
            // ✅ 新增：數據結構驗證
            if (!this.validateDataStructure(result)) {
                throw new Error('API返回數據結構不完整');
            }
            
            if (!result.success) {
                throw new Error(result.error || 'API返回錯誤狀態');
            }
            
            // 重置錯誤計數器
            this.errorCount = 0;
            this.hasError = false;
            
            // 更新當前數據
            this.currentData = result.data;
            this.lastUpdateTime = result.timestamp;
            
            const loadTime = Date.now() - startTime;
            console.log(`✅ 統一數據加載成功 (${loadTime}ms)，數據結構:`, {
                waiting: result.data.waiting_orders?.length || 0,
                preparing: result.data.preparing_orders?.length || 0,
                ready: result.data.ready_orders?.length || 0,
                completed: result.data.completed_orders?.length || 0, // ✅ 新增
                badges: result.data.badge_summary
            });
            
            // 通知所有監聽器（按順序）
            this.notifyAllListeners();
            
            // 觸發全局數據更新事件
            this.dispatchGlobalEvent('updated', {
                data: result.data,
                timestamp: result.timestamp,
                loadTime: loadTime
            });
            
            return true;
            
        } catch (error) {
            console.error('❌ 加載統一數據失敗:', error);
            this.hasError = true;
            this.errorCount++;
            
            // ✅ 新增：避免重複顯示相同錯誤訊息
            const errorMessage = error.message;
            const now = Date.now();
            const lastErrorTime = this.lastErrorTime || 0;
            const errorCooldown = 5000; // 5秒內不重複顯示相同錯誤
            
            // 觸發錯誤事件（但避免重複）
            if (now - lastErrorTime > errorCooldown || retryCount === 0) {
                this.dispatchGlobalEvent('error', {
                    error: errorMessage,
                    timestamp: new Date().toISOString(),
                    retryCount: retryCount,
                    errorCount: this.errorCount,
                    isNetworkError: errorMessage.includes('Network') || errorMessage.includes('timeout')
                });
                this.lastErrorTime = now;
            }
            
            // ✅ 新增：智能重試機制（優化）
            if (retryCount < this.maxRetryCount) {
                const delay = this.calculateRetryDelay(retryCount);
                console.log(`🔄 ${delay/1000}秒後重試 (${retryCount + 1}/${this.maxRetryCount})`);
                
                setTimeout(() => {
                    this.loadUnifiedData(true, retryCount + 1);
                }, delay);
            } else {
                console.error(`❌ 已達到最大重試次數 (${this.maxRetryCount})`);
                this.dispatchGlobalEvent('max_retries_reached', {
                    error: errorMessage,
                    retryCount: retryCount
                });
                
                // 達到最大重試次數後，等待更長時間再重試
                setTimeout(() => {
                    console.log('🔄 長時間等待後重新嘗試連接...');
                    this.errorCount = 0; // 重置錯誤計數
                    this.loadUnifiedData(true);
                }, 30000); // 30秒後再試
            }
            
            return false;
            
        } finally {
            this.isLoading = false;
        }
    }
    
    // ==================== 新增：數據驗證方法 ====================
    
    /**
     * 驗證API返回的數據結構完整性
     */
    validateDataStructure(result) {
        if (!result || typeof result !== 'object') {
            console.error('❌ 數據驗證失敗：結果不是對象');
            return false;
        }
        
        if (!result.success) {
            console.error('❌ 數據驗證失敗：success=false');
            return false;
        }
        
        if (!result.data || typeof result.data !== 'object') {
            console.error('❌ 數據驗證失敗：缺少data字段');
            return false;
        }
        
        // 檢查必要的數據字段
        const requiredFields = [
            'badge_summary',
            'waiting_orders',
            'preparing_orders', 
            'ready_orders',
            'completed_orders' // ✅ 新增
        ];
        
        for (const field of requiredFields) {
            if (result.data[field] === undefined) {
                console.warn(`⚠️ 數據驗證警告：缺少 ${field} 字段`);
                // 不視為致命錯誤，但記錄警告
                result.data[field] = field === 'badge_summary' ? 
                    { waiting: 0, preparing: 0, ready: 0, completed: 0 } : [];
            }
        }
        
        // 驗證徽章數據結構
        const badgeData = result.data.badge_summary;
        if (badgeData) {
            const requiredBadgeFields = ['waiting', 'preparing', 'ready', 'completed'];
            for (const field of requiredBadgeFields) {
                if (typeof badgeData[field] !== 'number') {
                    console.warn(`⚠️ 徽章數據驗證：${field} 不是數字`);
                    badgeData[field] = 0;
                }
            }
        }
        
        return true;
    }
    
    /**
     * 計算重試延遲（指數退避）
     */
    calculateRetryDelay(retryCount) {
        // 指數退避：1s, 2s, 4s, 8s...
        const baseDelay = 1000;
        const maxDelay = 30000; // 30秒
        const delay = Math.min(baseDelay * Math.pow(2, retryCount), maxDelay);
        
        // 添加隨機抖動（±20%）
        const jitter = delay * 0.2 * (Math.random() * 2 - 1);
        return delay + jitter;
    }
    
    // ==================== 監聽器管理（不變） ====================
    
    /**
     * 註冊數據監聽器
     */
    registerListener(dataType, callback, immediate = true) {
        if (!this.listeners[dataType]) {
            console.error(`❌ 未知的數據類型: ${dataType}`);
            // 嘗試創建新的監聽器類型
            this.listeners[dataType] = [];
            console.log(`📝 創建新的監聽器類型: ${dataType}`);
        }
        
        // 避免重複註冊
        const existingIndex = this.listeners[dataType].findIndex(cb => cb === callback);
        if (existingIndex === -1) {
            this.listeners[dataType].push(callback);
            console.log(`✅ 註冊 ${dataType} 監聽器，總數: ${this.listeners[dataType].length}`);
        }
        
        // 立即提供當前數據（如果有）
        if (immediate && this.currentData && this.currentData[dataType] !== undefined) {
            try {
                setTimeout(() => {
                    if (this.currentData) {
                        callback(this.currentData[dataType]);
                    }
                }, 0);
            } catch (error) {
                console.error(`❌ ${dataType} 監聽器立即執行錯誤:`, error);
            }
        }
        
        return () => this.unregisterListener(dataType, callback); // 返回取消函數
    }
    
    /**
     * 移除數據監聽器
     */
    unregisterListener(dataType, callback) {
        if (!this.listeners[dataType]) return;
        
        const index = this.listeners[dataType].indexOf(callback);
        if (index > -1) {
            this.listeners[dataType].splice(index, 1);
            console.log(`🗑️ 移除 ${dataType} 監聽器，剩餘: ${this.listeners[dataType].length}`);
        }
    }
    
    /**
     * 清除所有監聽器
     */
    clearAllListeners() {
        Object.keys(this.listeners).forEach(key => {
            this.listeners[key] = [];
        });
        console.log('🗑️ 清除所有監聽器');
    }
    
    // ==================== 數據通知（修正：添加completed_orders） ====================
    
    /**
     * 通知所有監聽器（按優先級順序）
     */
    notifyAllListeners() {
        if (!this.currentData) {
            console.warn('⚠️ 沒有數據可通知監聽器');
            return;
        }
        
        console.log('📢 開始通知所有監聽器...');
        
        // 通知順序：徽章優先，然後其他數據
        const notifyOrder = [
            'badge_summary',    // 徽章數據（最先更新）
            'waiting_orders',   // 等待隊列
            'preparing_orders', // 製作中訂單
            'ready_orders',     // 已就緒訂單
            'completed_orders'  // ✅ 已提取訂單（新增）
        ];
        
        notifyOrder.forEach(dataType => {
            if (this.currentData[dataType] !== undefined) {
                this.notifyListeners(dataType, this.currentData[dataType]);
            }
        });
        
        // 通知所有數據監聽器
        this.notifyListeners('all_data', this.currentData);
        
        console.log('✅ 所有監聽器通知完成');
    }
    
    /**
     * 通知特定類型的監聽器（增強：錯誤處理）
     */
    notifyListeners(dataType, data) {
        if (!this.listeners[dataType] || this.listeners[dataType].length === 0) {
            console.log(`ℹ️ ${dataType} 沒有註冊的監聽器`);
            return;
        }
        
        console.log(`📢 通知 ${dataType} 監聽器，數量: ${this.listeners[dataType].length}`);
        
        // 執行所有監聽器（新增：批量錯誤處理）
        const errors = [];
        
        this.listeners[dataType].forEach((callback, index) => {
            try {
                callback(data);
            } catch (error) {
                console.error(`❌ ${dataType} 監聽器 #${index} 執行錯誤:`, error);
                errors.push({
                    index,
                    error: error.message,
                    dataType
                });
            }
        });
        
        // 如果有錯誤，觸發錯誤事件
        if (errors.length > 0) {
            this.dispatchGlobalEvent('listener_error', {
                dataType,
                errors,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    // ==================== 事件處理（優化WebSocket監聽） ====================
    
    /**
     * 綁定全局事件（優化：避免重複觸發）
     */
    bindGlobalEvents() {
        // 手動刷新事件
        document.addEventListener('refresh_unified_data', (event) => {
            console.log('🔄 收到手動刷新事件', event.detail);
            this.loadUnifiedData(true);
        });
        
        // ✅ 優化：合併WebSocket事件，避免重複刷新
        let refreshTimeout = null;
        const handleWebSocketEvent = (eventName) => {
            console.log(`🔄 WebSocket事件觸發: ${eventName}`);
            
            // 清除之前的定時器
            if (refreshTimeout) {
                clearTimeout(refreshTimeout);
            }
            
            // 設置新的定時器（防抖）
            refreshTimeout = setTimeout(() => {
                this.loadUnifiedData();
                refreshTimeout = null;
            }, 300); // 300ms防抖
        };
        
        // WebSocket核心事件（合併）
        const coreWsEvents = [
            'queue_updated',           // 隊列更新
            'order_status_changed',    // 訂單狀態變化
            'new_order_created'        // 新訂單
        ];
        
        coreWsEvents.forEach(eventName => {
            document.addEventListener(eventName, () => handleWebSocketEvent(eventName));
        });
        
        // 標籤頁切換時刷新
        let tabChangeTimeout = null;
        document.addEventListener('tab_changed', (event) => {
            console.log(`🔄 標籤頁切換: ${event.detail.tabId}`);
            
            if (tabChangeTimeout) {
                clearTimeout(tabChangeTimeout);
            }
            
            tabChangeTimeout = setTimeout(() => {
                this.loadUnifiedData();
                tabChangeTimeout = null;
            }, 500);
        });
        
        // 頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('🔄 頁面恢復可見，刷新數據');
                setTimeout(() => this.loadUnifiedData(), 1000);
            }
        });
        
        // 網絡狀態恢復（防抖處理）
        let networkRecoveryTimeout = null;
        window.addEventListener('online', () => {
            console.log('🌐 網絡恢復，準備刷新數據...');
            
            // 清除之前的定時器
            if (networkRecoveryTimeout) {
                clearTimeout(networkRecoveryTimeout);
            }
            
            // 等待1秒確保網絡穩定，然後刷新數據
            networkRecoveryTimeout = setTimeout(() => {
                console.log('🔄 網絡穩定，開始刷新數據');
                this.loadUnifiedData(true);
                networkRecoveryTimeout = null;
            }, 1000);
        });
    }
    
    /**
     * 發送全局事件
     */
    dispatchGlobalEvent(eventName, detail = {}) {
        const fullEventName = `unified_data_${eventName}`;
        const event = new CustomEvent(fullEventName, {
            detail: {
                ...detail,
                timestamp: new Date().toISOString(),
                manager: this
            },
            bubbles: true,
            cancelable: true
        });
        
        const dispatched = document.dispatchEvent(event);
        console.log(`📢 發送全局事件: ${fullEventName} (${dispatched ? '成功' : '取消'})`);
    }
    
    // ==================== 輔助方法（新增功能） ====================
    
    /**
     * 啟動智能自動刷新（根據系統負載調整）
     */
    startAutoRefresh() {
        let refreshInterval = 10000; // 默認10秒
        let autoRefreshTimer = null;
        
        const refreshFunction = () => {
            if (this.isLoading) {
                console.log('⚠️ 跳過自動刷新：正在加載中');
                return;
            }
            
            if (this.errorCount > 2) {
                // 錯誤較多時，延長刷新間隔
                refreshInterval = Math.min(60000, refreshInterval * 2); // 最多1分鐘
                console.log(`⚠️ 錯誤較多，延長刷新間隔至 ${refreshInterval/1000}秒`);
            } else {
                // 正常情況下恢復默認間隔
                refreshInterval = 10000;
            }
            
            // 如果頁面不可見，暫停刷新
            if (document.hidden) {
                console.log('⏸️ 頁面不可見，暫停自動刷新');
                return;
            }
            
            this.loadUnifiedData();
        };
        
        // 使用setInterval但動態調整間隔
        autoRefreshTimer = setInterval(() => {
            refreshFunction();
        }, refreshInterval);
        
        console.log(`⏰ 啟動智能自動刷新：初始間隔 ${refreshInterval/1000}秒`);
        
        // 保存定時器引用以便清理
        this.autoRefreshTimer = autoRefreshTimer;
    }
    
    /**
     * 獲取數據統計信息
     */
    getDataStats() {
        if (!this.currentData) return null;
        
        return {
            waiting: this.currentData.waiting_orders?.length || 0,
            preparing: this.currentData.preparing_orders?.length || 0,
            ready: this.currentData.ready_orders?.length || 0,
            completed: this.currentData.completed_orders?.length || 0, // ✅ 新增
            badges: this.currentData.badge_summary || {},
            lastUpdate: this.lastUpdateTime,
            hasError: this.hasError,
            errorCount: this.errorCount
        };
    }
    
    /**
     * 檢查數據新鮮度
     */
    isDataFresh(thresholdMinutes = 5) {
        if (!this.lastUpdateTime) return false;
        
        const lastUpdate = new Date(this.lastUpdateTime);
        const now = new Date();
        const diffMinutes = (now - lastUpdate) / (1000 * 60);
        
        return diffMinutes < thresholdMinutes;
    }
    
    /**
     * 強制刷新數據（公開方法）
     */
    forceRefresh() {
        console.log('🚀 強制刷新數據');
        return this.loadUnifiedData(true);
    }
    
    /**
     * 重置錯誤狀態
     */
    resetErrorState() {
        this.errorCount = 0;
        this.hasError = false;
        console.log('🔄 重置錯誤狀態');
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理統一數據管理器...');
        
        // 清理自動刷新定時器
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
            console.log('🗑️ 清理自動刷新定時器');
        }
        
        this.clearAllListeners();
        this.currentData = null;
        console.log('✅ 統一數據管理器已清理');
    }
}

// ==================== 全局單例和調試支持 ====================

if (typeof window !== 'undefined') {
    // 創建全局實例
    window.unifiedDataManager = new UnifiedDataManager();
    
    // 調試支持
    window.debugUnifiedData = function() {
        const manager = window.unifiedDataManager;
        if (!manager) {
            console.error('❌ UnifiedDataManager 未找到');
            return;
        }
        
        console.group('🔍 UnifiedDataManager 調試信息');
        console.log('📊 數據統計:', manager.getDataStats());
        console.log('⏰ 最後更新:', manager.lastUpdateTime);
        console.log('🔄 正在加載:', manager.isLoading);
        console.log('❌ 錯誤狀態:', manager.hasError, '錯誤次數:', manager.errorCount);
        console.log('👂 監聽器數量:');
        Object.entries(manager.listeners).forEach(([key, listeners]) => {
            console.log(`  - ${key}: ${listeners.length} 個`);
        });
        console.groupEnd();
    };
    
    // 全局快捷方法
    window.refreshUnifiedData = function(force = true) {
        if (window.unifiedDataManager) {
            return window.unifiedDataManager.forceRefresh();
        }
        return false;
    };
    
    console.log('🌍 UnifiedDataManager 增強版已註冊到 window 對象');
}