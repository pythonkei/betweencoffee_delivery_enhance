// static/js/staff-order-management/base-order-renderer-fixed.js
// ==================== 訂單渲染器基礎類（完整修復版） ====================
// 提取自 completed-orders-renderer.js, ready-orders-renderer.js, preparing-orders-renderer.js 的重複代碼

class BaseOrderRendererFixed {
    /**
     * 基礎訂單渲染器構造函數
     * @param {string} orderType - 訂單類型 ('completed', 'ready', 'preparing')
     * @param {string} tabId - 標籤頁ID
     * @param {string} listId - 列表容器ID
     * @param {string} emptyId - 空狀態容器ID
     */
    constructor(orderType, tabId, listId, emptyId) {
        console.log(`🔄 初始化 ${orderType} 訂單渲染器基礎類...`);
        
        this.orderType = orderType;
        this.tabId = tabId;
        this.listId = listId;
        this.emptyId = emptyId;
        
        this.currentOrders = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false;
        
        setTimeout(() => this.initialize(), 100);
    }
    
    // ==================== 初始化方法 ====================
    
    initialize() {
        console.log(`🔄 ${this.orderType} 渲染器開始初始化...`);
        
        this.registerToUnifiedManager();
        this.bindEvents();
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log(`✅ ${this.orderType} 訂單渲染器初始化完成`);
    }
    
    // ==================== 統一數據管理器註冊（共用） ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        console.log(`✅ ${this.orderType} 訂單渲染器註冊到統一數據管理器`);
        
        // 監聽特定訂單類型數據
        const dataKey = `${this.orderType}_orders`;
        window.unifiedDataManager.registerListener(dataKey, (orders) => {
            console.log(`📥 ${this.orderType} 訂單數據接收:`, orders?.length || 0, '個');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);
        
        // 監聽所有數據更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            const orders = allData[dataKey];
            if (orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(orders);
                } else {
                    this.cacheOrders(orders);
                }
            }
        }, true);
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.[dataKey]) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData[dataKey]);
                }, 100);
            }
        });
    }
    
    // ==================== 數據檢查與加載（共用） ====================
    
    checkAndLoadData() {
        console.log(`🔍 檢查 ${this.orderType} 訂單數據...`);
        
        const dataKey = `${this.orderType}_orders`;
        
        // 情況1：統一數據管理器已有數據
        if (window.unifiedDataManager?.currentData?.[dataKey]) {
            console.log(`📦 從統一數據管理器獲取已有數據:`, window.unifiedDataManager.currentData[dataKey].length, '個');
            this.handleOrdersData(window.unifiedDataManager.currentData[dataKey]);
            return;
        }
        
        // 情況2：有緩存數據
        if (this.cachedOrders) {
            console.log(`📦 使用緩存數據:`, this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            return;
        }
        
        // 情況3：強制刷新數據
        console.log(`🔄 請求 ${this.orderType} 訂單數據...`);
        this.requestOrdersData();
    }
    
    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單數據為空`);
            this.showEmpty();
            return;
        }
        
        console.log(`🔄 處理 ${this.orderType} 訂單數據: ${orders.length} 個`);
        
        if (this.isActiveTab()) {
            this.renderOrders(orders);
        } else {
            this.cacheOrders(orders);
        }
    }
    
    requestOrdersData() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.requestOrdersData(), 1000);
            return;
        }
        
        console.log(`🚀 觸發統一數據管理器加載 ${this.orderType} 數據`);
        window.unifiedDataManager.loadUnifiedData();
    }
    
    // ==================== 渲染方法（共用基礎） ====================
    
    renderOrders(orders) {
        const orderList = document.getElementById(this.listId);
        const emptyElement = document.getElementById(this.emptyId);
        
        if (!orderList) {
            console.warn(`⚠️ ${this.orderType} 訂單列表容器未找到，100ms後重試`);
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清空容器
        orderList.innerHTML = '';
        this.currentOrders.clear();
        
        // 檢查是否有訂單
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單列表為空`);
            this.showEmpty();
            return;
        }
        
        console.log(`🎨 渲染 ${this.orderType} 訂單: ${orders.length} 個`);
        
        // 對訂單進行排序（子類可以覆蓋此方法）
        const sortedOrders = this.sortOrders(orders);
        
        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            orderList.appendChild(orderElement);
            
            // 更新當前訂單映射
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });
        
        // 隱藏空狀態
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 顯示列表容器
        orderList.style.display = 'block';
        
        // 更新最後更新時間
        this.updateLastUpdateTime();
        
        console.log(`✅ ${this.orderType} 訂單渲染完成`);
    }
    
    /**
     * 排序訂單（子類可以覆蓋此方法）
     * @param {Array} orders - 訂單數組
     * @returns {Array} 排序後的訂單數組
     */
    sortOrders(orders) {
        // 默認按創建時間降序排序（最新的在前面）
        return [...orders].sort((a, b) => {
            const timeA = a.created_at || '';
            const timeB = b.created_at || '';
            return new Date(timeB) - new Date(timeA);
        });
    }
    
    /**
     * 創建訂單元素（子類必須實現此方法）
     * @param {Object} order - 訂單對象
     * @returns {HTMLElement} 訂單元素
     */
    createOrderElement(order) {
        throw new Error('子類必須實現 createOrderElement 方法');
    }
    
    /**
     * 渲染訂單項目（共用）
     * @param {Array} items - 訂單項目數組
     * @returns {string} HTML字符串
     */
    renderOrderItems(items) {
        if (!items || items.length === 0) {
            return '<p class="text-muted">暫無商品信息</p>';
        }

        let itemsHTML = '';

        items.forEach(item => {
            const itemPrice = parseFloat(item.price || 0).toFixed(2);
            const itemTotal = parseFloat(item.total_price || 0).toFixed(2);

            itemsHTML += `
                <div class="d-flex align-items-center mb-3">
                    <div class="mr-3">
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                            <img src="${item.image || '/static/images/default-product.png'}"
                                 alt="${item.name || '商品'}"
                                 class="img-fluid"
                                 style="max-height: 75px;">
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${item.name || '商品'}</h6>
                        <p class="mb-1 text-muted">數量: ${item.quantity || 1}</p>
                        <div class="text-muted">
                            ${item.cup_level_cn ? `杯型: ${item.cup_level_cn}` : ''}
                            ${item.milk_level_cn ? ` | 牛奶: ${item.milk_level_cn}` : ''}
                            ${item.grinding_level_cn ? ` | 研磨: ${item.grinding_level_cn}` : ''}
                            ${item.weight ? ` | 重量: ${item.weight}` : ''}
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="h6">$${itemTotal}</span>
                        <div class="text-muted small">$${itemPrice} / 單價</div>
                    </div>
                </div>
            `;
        });

        return itemsHTML;
    }
    
    // ==================== 事件處理（共用基礎） ====================
    
    bindEvents() {
        console.log(`🔄 綁定 ${this.orderType} 訂單渲染器事件...`);
        
        // 刷新按鈕
        const refreshBtn = document.getElementById(`refresh-${this.orderType}-orders-btn`);
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log(`🔄 手動刷新 ${this.orderType} 訂單`);
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // Bootstrap標籤頁顯示事件
        $(`#${this.tabId}`).on('shown.bs.tab', () => {
            console.log(`📌 ${this.orderType} 標籤頁已顯示`);
            this.onTabActivated();
        });
        
        // 標籤頁點擊事件
        const tabElement = document.getElementById(this.tabId);
        if (tabElement) {
            tabElement.addEventListener('click', () => {
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
    }
    
    /**
     * 標籤頁激活時調用
     */
    onTabActivated() {
        console.log(`🎯 ${this.orderType} 標籤頁激活`);
        
        // 情況1：有緩存數據
        if (this.cachedOrders) {
            console.log(`📦 渲染緩存數據:`, this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
            return;
        }
        
        // 情況2：統一數據管理器有數據
        const dataKey = `${this.orderType}_orders`;
        if (window.unifiedDataManager?.currentData?.[dataKey]) {
            console.log(`📊 從統一數據管理器獲取數據`);
            this.renderOrders(window.unifiedDataManager.currentData[dataKey]);
            return;
        }
        
        // 情況3：強制刷新
        console.log(`🚀 請求最新數據`);
        this.forceRefresh();
    }
    
    // ==================== UI輔助方法（共用） ====================
    
    /**
     * 顯示空狀態
     */
    showEmpty() {
        const orderList = document.getElementById(this.listId);
        const emptyElement = document.getElementById(this.emptyId);
        
        if (orderList) {
            orderList.innerHTML = '';
            orderList.style.display = 'none';
        }
        
        if (emptyElement) {
            emptyElement.style.display = 'block';
        }
        
        console.log(`📭 顯示 ${this.orderType} 空狀態`);
    }
    
    /**
     * 更新最後更新時間
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById(`${this.orderType}-orders-last-update`);
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }
    
    /**
     * 緩存訂單數據
     */
    cacheOrders(orders) {
        this.cachedOrders = orders;
        console.log(`📦 緩存 ${this.orderType} 訂單數據: ${orders?.length || 0} 個`);
    }
    
    /**
     * 檢查是否為當前活動標籤頁
     */
    isActiveTab() {
        const tabElement = document.getElementById(this.tabId);
        return tabElement && tabElement.classList.contains('active');
    }
    
    /**
     * 顯示Toast通知
     */
    showToast(message, type = 'info') {
        // 優先使用統一的 toast-manager.js
        if (window.toast) {
            const toastType = type === 'success' ? 'success' : 
                             type === 'error' ? 'error' : 
                             type === 'warning' ? 'warning' : 'info';
            
            window.toast[toastType](message);
        } else if (window.orderManager && window.orderManager.showToast) {
            // 備用方案：使用 orderManager 的 showToast
            window.orderManager.showToast(message, type);
        } else {
            // 簡單實現
            const toastClass = type === 'success' ? 'alert-success' : 
                              type === 'error' ? 'alert-danger' : 'alert-info';
            
            const toast = document.createElement('div');
            toast.className = `alert ${toastClass} alert-dismissible fade show fixed-top`;
            toast.style.cssText = 'top: 80px; right: 20px; z-index: 1050; max-width: 300px;';
            toast.setAttribute('role', 'alert');
            toast.innerHTML = `
                ${message}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            `;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.remove();
            }, 3000);
        }
    }
    
    /**
     * 強制刷新數據
     */
    forceRefresh() {
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData(true);
        }
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log(`🔄 清理 ${this.orderType} 訂單渲染器...`);
        
        // 清理當前訂單映射
        this.currentOrders.clear();
        
        // 清理緩存
        this.cachedOrders = null;
        
        // 重置處理狀態
        this.isProcessingAction = false;
        
        console.log(`✅ ${this.orderType} 訂單渲染器已清理`);
    }
    
    // ==================== 訂單類型判斷輔助方法（共用） ====================
    
    /**
     * 分析訂單類型
     * @param {Object} order - 訂單對象
     * @returns {Object} 訂單類型信息
     */
    analyzeOrderType(order) {
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);
        
        return {
            coffeeCount,
            beanCount,
            hasCoffee,
            hasBeans,
            isMixedOrder,
            isBeansOnly
        };
    }
    
    /**
     * 生成訂單類型徽章HTML
     * @param {Object} order - 訂單對象
     * @param {Object} typeInfo - 訂單類型信息
     * @returns {string} 徽章HTML
     */
    generateOrderTypeBadges(order, typeInfo) {
        const { isMixedOrder, isBeansOnly } = typeInfo;
        
        // 1. 快速訂單徽章（優先級最高）
        if (order.is_quick_order) {
            return `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        }
        // 2. 混合訂單徽章（次優先級）
        else if (isMixedOrder) {
            return `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        }
        // 3. 普通訂單徽章（默認）
        else {
            return `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }
    }
    
    /**
     * 生成數量徽章HTML
     * @param {Object} order - 訂單對象
