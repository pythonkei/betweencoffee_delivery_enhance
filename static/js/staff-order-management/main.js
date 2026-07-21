// static/js/staff-order-management/main.js - 最终统一数据流版本
class OrderManagementSystem {
    constructor() {
        this.initialized = false;
        this.components = {};
        
        this.init();
    }
    
    async init() {
        if (this.initialized) return;
        
        const initStartTime = Date.now();
        console.log('🔄 === 訂單管理系統初始化開始（統一數據流版） ===');
        
        try {
            // 1. 確保時間工具存在
            console.log('📋 [步驟 1/6] 確保時間工具...');
            this.ensureTimeUtils();
            console.log(`✅ [步驟 1/6] 時間工具就緒 (${Date.now() - initStartTime}ms)`);
            
            // 2. 等待統一數據管理器加載（關鍵）
            console.log('📋 [步驟 2/6] 等待統一數據管理器...');
            await this.waitForUnifiedDataManager();
            console.log(`✅ [步驟 2/6] 統一數據管理器就緒 (${Date.now() - initStartTime}ms)`);
            
            // 3. 按正確順序初始化核心組件
            console.log('📋 [步驟 3/6] 初始化核心組件...');
            await this.initCoreComponents();
            console.log(`✅ [步驟 3/6] 核心組件初始化完成 (${Date.now() - initStartTime}ms)`);
            
            // 4. 初始化渲染器
            console.log('📋 [步驟 4/6] 初始化渲染器...');
            this.initRenderers();
            console.log(`✅ [步驟 4/6] 渲染器初始化完成 (${Date.now() - initStartTime}ms)`);
            
            // 4a. 渲染器初始化完成後，主動觸發數據檢查
            console.log('📋 [步驟 4a/6] 觸發渲染器數據檢查...');
            this.triggerRenderersDataCheck();
            console.log(`✅ [步驟 4a/6] 渲染器數據檢查已觸發 (${Date.now() - initStartTime}ms)`);
            
            // 5. 綁定全局事件
            console.log('📋 [步驟 5/6] 綁定全局事件...');
            this.bindGlobalEvents();
            console.log(`✅ [步驟 5/6] 全局事件綁定完成 (${Date.now() - initStartTime}ms)`);
            
            // 6. 啟動系統
            console.log('📋 [步驟 6/6] 啟動系統...');
            await this.startSystem();
            
            this.initialized = true;
            const totalTime = Date.now() - initStartTime;
            console.log(`✅ === 訂單管理系統初始化完成 (總耗時: ${totalTime}ms) ===`);
            
        } catch (error) {
            const failTime = Date.now() - initStartTime;
            console.error(`❌ 訂單管理系統初始化失敗 (${failTime}ms):`, error);
            this.showInitializationError(error);
        }
    }
    
    // ====== 簡化：確保時間工具 ======
    ensureTimeUtils() {
        if (typeof window.TimeUtils === 'undefined') {
            window.TimeUtils = {
                formatHKTime: function(dateString) {
                    if (!dateString) return '';
                    try {
                        const date = new Date(dateString);
                        if (isNaN(date.getTime())) return dateString;
                        return date.toLocaleString('zh-HK', {
                            timeZone: 'Asia/Hong_Kong',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    } catch (error) {
                        console.error('格式化香港時間錯誤:', error);
                        return dateString;
                    }
                },
                
                formatHKTimeOnly: function(dateString) {
                    if (!dateString) return '';
                    try {
                        const date = new Date(dateString);
                        if (isNaN(date.getTime())) return dateString;
                        return date.toLocaleTimeString('zh-HK', {
                            timeZone: 'Asia/Hong_Kong',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    } catch (error) {
                        console.error('格式化香港時間錯誤:', error);
                        return dateString;
                    }
                },
                
                formatRelativeTime: function(dateString) {
                    if (!dateString) return '剛剛';
                    try {
                        const date = new Date(dateString);
                        if (isNaN(date.getTime())) return '剛剛';
                        
                        const now = new Date();
                        const diffMs = now - date;
                        const diffMinutes = Math.floor(diffMs / (1000 * 60));
                        
                        if (diffMinutes < 1) return '剛剛';
                        if (diffMinutes < 60) return `${diffMinutes}分鐘前`;
                        
                        const hours = Math.floor(diffMinutes / 60);
                        if (hours < 24) return `${hours}小時前`;
                        
                        const days = Math.floor(hours / 24);
                        return `${days}天前`;
                    } catch (error) {
                        return '剛剛';
                    }
                }
            };
            console.log('✅ 基礎時間工具已創建');
        }
    }
    
    // ====== 新增：等待統一數據管理器 ======
    waitForUnifiedDataManager() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 10;
            
            const checkInterval = setInterval(() => {
                attempts++;
                
                if (window.unifiedDataManager) {
                    clearInterval(checkInterval);
                    console.log('✅ UnifiedDataManager 已加載');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('❌ UnifiedDataManager 加載超時，請檢查JS加載順序'));
                } else {
                    console.log(`⏳ 等待UnifiedDataManager加載... (${attempts}/${maxAttempts})`);
                }
            }, 500);
        });
    }
    
    async initCoreComponents() {
        // ====== 按正確順序初始化組件 ======
        const initOrder = [
            // 第一步：子標籤頁管理器（無依賴，優先初始化）
            { 
                name: 'subtabManager', 
                Class: window.SubtabManager, 
                required: true,
                onInit: (instance) => {
                    instance.init();
                    console.log('✅ SubtabManager 已初始化，自定義子 tab 切換已啟用');
                }
            },
            
            // 第二步：徽章管理器（依賴統一數據管理器）
            { 
                name: 'badgeManager', 
                Class: window.BadgeManager, 
                required: true,
                onInit: (instance) => {
                    console.log('✅ BadgeManager 已初始化，將從統一數據管理器獲取數據');
                }
            },
            
            // 第三步：隊列管理器（依賴統一數據管理器）
            { 
                name: 'queueManager', 
                Class: window.QueueManager, 
                required: true,
                onInit: (instance) => {
                    console.log('✅ QueueManager 已初始化，將從統一數據管理器獲取數據');
                }
            },
            
            // 第四步：OrderManager（全局管理器）
            { 
                name: 'orderManager', 
                Class: window.OrderManager, 
                required: false,
                onInit: (instance) => {
                    console.log('✅ OrderManager 已初始化');
                }
            },
            
            // 第五步：WebSocket管理器
            { 
                name: 'webSocketManager', 
                Class: window.WebSocketManager, 
                required: true,
                onInit: (instance) => {
                    console.log('✅ WebSocketManager 已初始化');
                }
            }
        ];
        
        for (const component of initOrder) {
            try {
                if (component.Class) {
                    console.log(`🔄 正在初始化 ${component.name}...`);
                    
                    const instance = new component.Class();
                    this.components[component.name] = instance;
                    window[component.name] = instance;
                    
                    // 執行初始化後回調
                    if (component.onInit) {
                        component.onInit(instance);
                    }
                    
                    console.log(`✅ ${component.name} 初始化成功`);
                }
            } catch (error) {
                console.error(`❌ 初始化 ${component.name} 失敗:`, error);
                if (component.required) {
                    throw new Error(`必需組件 ${component.name} 初始化失敗: ${error.message}`);
                }
            }
        }
    }
    
    // 初始化渲染器（按需延迟加载）- 使用 v2 重構版本
    initRenderers() {
        const rendererConfigs = [
            { id: 'payment-pending', name: 'paymentPendingRenderer', Class: window.PaymentPendingRendererV2 },
            { id: 'preparing', name: 'preparingRenderer', Class: window.PreparingOrdersRendererV2 },
            { id: 'ready', name: 'readyRenderer', Class: window.ReadyOrdersRendererV2 },
            { id: 'completed', name: 'completedRenderer', Class: window.CompletedOrdersRendererV2 }
        ];
        
        rendererConfigs.forEach(config => {
            const tab = document.getElementById(config.id);
            if (tab) {
                try {
                    console.log(`🔄 正在初始化 ${config.name} (v2)...`);
                    
                    const instance = new config.Class();
                    this.components[config.name] = instance;
                    window[config.name] = instance;
                    
                    console.log(`✅ ${config.name} (v2) 初始化成功`);
                } catch (error) {
                    console.error(`❌ 初始化 ${config.name} (v2) 失败:`, error);
                    
                    // 降級：嘗試使用舊版渲染器
                    console.log(`⚠️ 嘗試降級使用舊版 ${config.name}...`);
                    try {
                        const fallbackClass = this._getFallbackRenderer(config.name);
                        if (fallbackClass) {
                            const fallbackInstance = new fallbackClass();
                            this.components[config.name] = fallbackInstance;
                            window[config.name] = fallbackInstance;
                            console.log(`✅ ${config.name} (降級) 初始化成功`);
                        }
                    } catch (fallbackError) {
                        console.error(`❌ ${config.name} 降級也失敗:`, fallbackError);
                    }
                }
            }
        });
    }
    
    // 降級方案：獲取舊版渲染器類
    _getFallbackRenderer(name) {
        const fallbackMap = {
            'paymentPendingRenderer': window.PaymentPendingRenderer,
            'preparingRenderer': window.DynamicPreparingOrdersRenderer,
            'readyRenderer': window.DynamicReadyOrdersRenderer,
            'completedRenderer': window.DynamicCompletedOrdersRenderer
        };
        return fallbackMap[name] || null;
    }
    
    // ====== 修正：綁定全局事件 ======
    bindGlobalEvents() {
        // 標籤頁切換事件（使用Bootstrap原生事件）
        $('#orderTabs a[data-toggle="tab"]').on('shown.bs.tab', (e) => {
            const targetId = $(e.target).attr('href'); // 獲取目標標籤頁ID
            console.log(`🔄 切換到標籤頁: ${targetId}`);
            
            // 通知統一數據管理器標籤頁切換
            if (window.unifiedDataManager) {
                window.unifiedDataManager.loadUnifiedData();
            }
        });
        
        // 強制刷新所有數據
        document.addEventListener('force_refresh_all', () => {
            this.refreshAll();
        });
        
        // 页面可见性变化
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('🔄 頁面恢復可見，刷新數據');
                setTimeout(() => {
                    this.refreshCurrentTab();
                }, 1000);
            }
        });
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', (event) => {
            console.log('📢 收到統一數據更新事件');
        });
        
        // 監聽統一數據錯誤事件
        document.addEventListener('unified_data_error', (event) => {
            console.error('❌ 統一數據錯誤:', event.detail.error);
        });
    }
    
    // ====== 新增：加載標籤頁數據（統一數據流版） ======
    loadTabData(tabId) {
        console.log(`🔄 加載標籤頁數據: ${tabId}`);
        
        // 統一數據流架構：所有數據都來自統一數據管理器
        // 只需確保統一數據管理器已加載數據，各渲染器會自動更新
        
        if (window.unifiedDataManager) {
            // 觸發一次數據加載
            window.unifiedDataManager.loadUnifiedData();
        } else {
            console.error('❌ 統一數據管理器未找到');
        }
    }
    
    // ====== 簡化：啟動系統 ======
    async startSystem() {
        console.log('🔄 正在啟動訂單管理系統（統一數據流版）...');
        
        try {
            // 1. 等待組件初始化完成（縮短等待時間）
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // 2. 加載初始數據
            if (window.unifiedDataManager) {
                await window.unifiedDataManager.loadUnifiedData();
                console.log('✅ 初始數據加載完成');
            }
            
            // 3. 顯示系統就緒狀態
            this.showSystemReady();
            
            console.log('✅ 訂單管理系統啟動完成');
            
        } catch (error) {
            console.error('❌ 系統啟動失敗:', error);
            this.showSystemReadyError();
        }
    }
    
    // ====== 新增：刷新當前標籤頁 ======
    refreshCurrentTab() {
        console.log('🔄 刷新當前標籤頁');
        
        // 統一數據流架構：只需刷新統一數據
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData();
        }
    }
    
    // ====== 新增：系統啟動錯誤顯示 ======
    showSystemReadyError() {
        const errorIndicator = document.createElement('div');
        errorIndicator.className = 'alert alert-warning alert-dismissible fade show mt-3';
        errorIndicator.innerHTML = `
            <h5><i class="fas fa-exclamation-triangle mr-2"></i>系統部分功能加載失敗</h5>
            <p class="mb-2">某些功能暫時無法使用，但基本功能正常</p>
            <p class="mb-1 small">請刷新頁面或聯繫技術支持</p>
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-warning mr-2" onclick="window.location.reload()">
                    <i class="fas fa-redo mr-1"></i>刷新頁面
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="checkSystemStatus()">
                    <i class="fas fa-info-circle mr-1"></i>檢查狀態
                </button>
            </div>
        `;
        
        const container = document.querySelector('.container-fluid') || document.body;
        if (container) {
            container.insertBefore(errorIndicator, container.firstChild);
        }
    }
    
    // 刷新所有数据
    async refreshAll() {
        console.log('🔄 强制刷新所有数据...');
        
        try {
            // 统一数据流架构：只需刷新统一数据
            if (window.unifiedDataManager) {
                await window.unifiedDataManager.loadUnifiedData(true); // force refresh
                console.log('✅ 数据已更新');
            }
            
        } catch (error) {
            console.error('❌ 刷新数据失败:', error);
        }
    }
    
    // 顯示系統就緒狀態
    showSystemReady() {
        // 创建系统状态指示器
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'system-status-indicator';
        statusIndicator.className = 'system-status ready';
        statusIndicator.innerHTML = `
            <span class="status-icon">✓</span>
            <span class="status-text">系统就绪 (统一数据流版)</span>
        `;
        
        // 添加到页面
        const container = document.querySelector('.container-fluid') || document.body;
        if (container) {
            container.insertBefore(statusIndicator, container.firstChild);
            
            // 3秒后隐藏
            setTimeout(() => {
                statusIndicator.style.opacity = '0';
                setTimeout(() => {
                    if (statusIndicator.parentNode) {
                        statusIndicator.parentNode.removeChild(statusIndicator);
                    }
                }, 500);
            }, 3000);
        }
    }
    
    // 顯示初始化錯誤
    showInitializationError(error) {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
        errorContainer.innerHTML = `
            <h5><i class="fas fa-exclamation-triangle mr-2"></i>系統初始化失敗</h5>
            <p class="mb-2">${error.message || '未知錯誤'}</p>
            <p class="mb-1 small">請嘗試刷新頁面或聯繫技術支持</p>
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-danger mr-2" onclick="location.reload()">
                    <i class="fas fa-redo mr-1"></i>刷新頁面
                </button>
                <button class="btn btn-sm btn-outline-secondary" onclick="checkSystemStatus()">
                    <i class="fas fa-bug mr-1"></i>調試信息
                </button>
            </div>
        `;
        
        // 添加到页面顶部
        const container = document.querySelector('.container-fluid') || document.body;
        if (container) {
            container.insertBefore(errorContainer, container.firstChild);
        }
    }
    
    // 清理系統
    cleanup() {
        console.log('🔄 正在清理訂單管理系統...');
        
        // 清理所有組件
        Object.values(this.components).forEach(component => {
            if (component && typeof component.cleanup === 'function') {
                try {
                    component.cleanup();
                } catch (error) {
                    console.error('清理組件失敗:', error);
                }
            }
        });
        
        this.initialized = false;
        this.components = {};
        
        console.log('✅ 訂單管理系統已清理');
    }
    
    // ====== 新增：渲染器初始化完成後主動觸發數據檢查 ======
    triggerRenderersDataCheck() {
        console.log('🔄 觸發所有渲染器的數據檢查...');
        
        // 檢查統一數據管理器是否已有數據
        if (window.unifiedDataManager && window.unifiedDataManager.currentData) {
            console.log('✅ 統一數據管理器已有數據，通知所有渲染器');
            
            // 主動通知所有渲染器（確保它們都有數據）
            window.unifiedDataManager.notifyAllListeners();
        } else {
            console.log('⏳ 統一數據管理器尚無數據，等待初始加載完成後自動通知');
            
            // 監聽數據加載完成事件
            const onDataLoaded = () => {
                console.log('✅ 數據加載完成，渲染器將自動更新');
                document.removeEventListener('unified_data_updated', onDataLoaded);
            };
            document.addEventListener('unified_data_updated', onDataLoaded);
            
            // 超時保護：5秒後如果還沒有數據，強制觸發一次加載
            setTimeout(() => {
                if (!window.unifiedDataManager || !window.unifiedDataManager.currentData) {
                    console.log('⚠️ 數據加載超時，強制觸發數據加載');
                    if (window.unifiedDataManager) {
                        window.unifiedDataManager.loadUnifiedData(true);
                    }
                }
            }, 5000);
        }
    }
    
    // ====== 新增：檢查系統狀態 ======
    checkSystemStatus() {
        const status = {
            systemInitialized: this.initialized,
            unifiedDataManager: !!window.unifiedDataManager,
            badgeManager: !!window.badgeManager,
            queueManager: !!window.queueManager,
            webSocketManager: !!window.webSocketManager,
            orderManager: !!window.orderManager,
            preparingRenderer: !!window.preparingRenderer,
            readyRenderer: !!window.readyRenderer,
            completedRenderer: !!window.completedRenderer,
            lastUpdateTime: window.unifiedDataManager ? window.unifiedDataManager.lastUpdateTime : null
        };
        
        console.log('🔍 系統狀態檢查:', status);
        return status;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        try {
            console.log('🔄 開始初始化訂單管理系統（統一數據流版）...');
            window.orderManagementSystem = new OrderManagementSystem();
            window.OMS = window.orderManagementSystem;
        } catch (error) {
            console.error('❌ 初始化訂單管理系統失敗:', error);
            
            // 嘗試降級方案
            try {
                console.log('🔄 嘗試降級初始化...');
                
                // 只初始化關鍵組件
                if (typeof BadgeManager !== 'undefined') {
                    window.badgeManager = new BadgeManager();
                }
                if (typeof QueueManager !== 'undefined') {
                    window.queueManager = new QueueManager();
                }
                
                console.log('✅ 降級初始化完成');
            } catch (fallbackError) {
                console.error('❌ 降級初始化也失敗:', fallbackError);
            }
        }
    }, 100);
});

// 页面卸载前清理
window.addEventListener('beforeunload', function() {
    if (window.orderManagementSystem) {
        window.orderManagementSystem.cleanup();
    }
});

// ====== 全局辅助函数 ======
// 刷新当前标签页
function refreshCurrentTab() {
    if (window.orderManagementSystem) {
        window.orderManagementSystem.refreshCurrentTab();
    } else if (window.unifiedDataManager) {
        window.unifiedDataManager.loadUnifiedData();
    }
}

// 强制刷新所有数据
function forceRefreshAll() {
    if (window.orderManagementSystem) {
        window.orderManagementSystem.refreshAll();
    } else if (window.unifiedDataManager) {
        window.unifiedDataManager.loadUnifiedData(true);
    }
}

// 检查系统状态
function checkSystemStatus() {
    if (window.orderManagementSystem) {
        return window.orderManagementSystem.checkSystemStatus();
    } else {
        console.log('🔍 订单管理系统未初始化');
        return { systemInitialized: false };
    }
}

// 手动触发统一数据刷新
function forceUnifiedDataRefresh() {
    if (window.unifiedDataManager) {
        window.unifiedDataManager.loadUnifiedData(true);
        console.log('🔄 手动触发统一数据刷新');
    }
}

// 暴露全局函数
if (typeof window !== 'undefined') {
    window.refreshCurrentTab = refreshCurrentTab;
    window.forceRefreshAll = forceRefreshAll;
    window.checkSystemStatus = checkSystemStatus;
    window.forceUnifiedDataRefresh = forceUnifiedDataRefresh;
    
    // 调试函数
    window.debugUnifiedData = function() {
        if (window.unifiedDataManager) {
            console.log('🔍 UnifiedDataManager 调试信息:');
            console.log('- 当前数据:', window.unifiedDataManager.currentData);
            console.log('- 最后更新时间:', window.unifiedDataManager.lastUpdateTime);
            console.log('- 是否正在加载:', window.unifiedDataManager.isLoading);
        } else {
            console.error('❌ UnifiedDataManager 未找到');
        }
    };
}

// ====== 初始化完成后的自动检查 ======
setTimeout(() => {
    // 检查徽章ID是否匹配（针对staff_order_management.html的修改）
    const badgeIds = ['queue-badge', 'preparing-orders-badge', 'ready-orders-badge', 'completed-orders-badge'];
    badgeIds.forEach(id => {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`⚠️ 徽章元素 #${id} 未找到，请检查HTML是否匹配`);
        }
    });
    
    // 检查统一数据管理器状态
    if (window.unifiedDataManager) {
        console.log('✅ UnifiedDataManager 状态正常');
    } else {
        console.error('❌ UnifiedDataManager 未初始化，请检查JS加载顺序');
    }
}, 3000);