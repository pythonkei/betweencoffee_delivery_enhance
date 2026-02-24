// static/js/staff-order-management/optimized-base-renderer.js
// ==================== 優化版基礎訂單渲染器 ====================
// 提取所有渲染器的共用邏輯，提供更好的性能和可維護性

class OptimizedBaseRenderer {
    /**
     * 優化版基礎訂單渲染器構造函數
     * @param {string} orderType - 訂單類型 ('preparing', 'ready', 'completed')
     * @param {string} tabId - 標籤頁ID
     * @param {string} listId - 列表容器ID
     * @param {string} emptyId - 空狀態容器ID
     * @param {Object} options - 配置選項
     */
    constructor(orderType, tabId, listId, emptyId, options = {}) {
        console.log(`🔄 初始化 ${orderType} 訂單渲染器（優化版）...`);
        
        this.orderType = orderType;
        this.tabId = tabId;
        this.listId = listId;
        this.emptyId = emptyId;
        this.options = {
            autoRefresh: options.autoRefresh !== false,
            refreshInterval: options.refreshInterval || 30000,
            enableCountdown: options.enableCountdown || false,
            enableSorting: options.enableSorting !== false,
            ...options
        };
        
        this.currentOrders = new Map();
        this.countdownTimers = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false;
        this.refreshTimer = null;
        this.eventListeners = new Map();
        
        // 延遲初始化，確保DOM就緒
        setTimeout(() => this.initialize(), 100);
    }
    
    // ==================== 初始化方法 ====================
    
    initialize() {
        console.log(`🔄 ${this.orderType} 渲染器開始初始化...`);
        
        this.registerToUnifiedManager();
        this.bindEvents();
        this.checkAndLoadData();
        
        if (this.options.autoRefresh) {
            this.startAutoRefresh();
        }
        
        this.isReady = true;
        console.log(`✅ ${this.orderType} 訂單渲染器初始化完成`);
    }
    
    // ==================== 統一數據管理器註冊 ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        console.log(`✅ ${this.orderType} 訂單渲染器註冊到統一數據管理器`);
        
        const dataKey = `${this.orderType}_orders`;
        
        // 監聽特定訂單類型數據
        this.registerListener('unified_data_manager', dataKey, (orders) => {
            console.log(`📥 ${this.orderType} 訂單數據接收:`, orders?.length || 0, '個');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);
        
        // 監聽所有數據更新
        this.registerListener('unified_data_manager', 'all_data', (allData) => {
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
        this.registerListener('document', 'unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.[dataKey]) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData[dataKey]);
                }, 100);
            }
        });
    }
    
    // ==================== 數據檢查與加載 ====================
    
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
    
    // ==================== 渲染方法 ====================
    
    renderOrders(orders) {
        const orderList = document.getElementById(this.listId);
        const emptyElement = document.getElementById(this.emptyId);
        
        if (!orderList) {
            console.warn(`⚠️ ${this.orderType} 訂單列表容器未找到，100ms後重試`);
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清理現有計時器
        this.cleanupTimers();
        
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
        
        // 對訂單進行排序
        const sortedOrders = this.sortOrders(orders);
        
        // 使用 DocumentFragment 提高性能
        const fragment = document.createDocumentFragment();
        
        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            fragment.appendChild(orderElement);
            
            // 更新當前訂單映射
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });
        
        // 一次性添加到DOM
        orderList.appendChild(fragment);
        
        // 顯示列表容器，隱藏空狀態
        orderList.style.display = 'block';
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 初始化倒計時（如果需要）
        if (this.options.enableCountdown) {
            this.initCountdowns();
        }
        
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
        if (!this.options.enableSorting) {
            return orders;
        }
        
        // 默認排序：快速訂單優先，然後按創建時間排序
        return [...orders].sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            
            if (isQuickA !== isQuickB) {
                return isQuickB ? 1 : -1; // 快速訂單排在前面
            }
            
            // 第二優先級：按創建時間排序（越早越優先）
            const timeA = a.created_at_iso || a.created_at || '';
            const timeB = b.created_at_iso || b.created_at || '';
            return new Date(timeA) - new Date(timeB);
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
            return '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }

        let itemsHTML = '';

        items.forEach(item => {
            const itemPrice = parseFloat(item.price || 0).toFixed(2);
            const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
            const itemImage = item.image || this.getDefaultImage(item.type);

            itemsHTML += `
                <div class="d-flex align-items-center mb-3">
                    <div class="mr-3">
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                            <img src="${itemImage}" 
                                 alt="${item.name || '商品'}" 
                                 class="img-fluid" 
                                 style="max-height: 75px;"
                                 loading="lazy">
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
    
    getDefaultImage(itemType) {
        if (itemType === 'coffee') {
            return '/static/images/default-coffee.png';
        } else if (itemType === 'bean') {
            return '/static/images/default-beans.png';
        }
        return '/static/images/default-product.png';
    }
    
    // ==================== 倒計時管理 ====================
    
    initCountdowns() {
        const orderList = document.getElementById(this.listId);
        if (!orderList) return;
        
        const countdownBadges = orderList.querySelectorAll('.countdown-badge');
        
        countdownBadges.forEach(badge => {
            const orderId = badge.dataset.orderId;
            const estimatedTimeStr = badge.dataset.estimatedTime;
            const countdownText = badge.querySelector('.countdown-text');
            
            if (!estimatedTimeStr || !countdownText) return;
            
            const estimatedTime = new Date(estimatedTimeStr);
            
            if (isNaN(estimatedTime.getTime())) {
                countdownText.textContent = '時間錯誤';
                return;
            }
            
            // 檢查是否已經過了預計完成時間
            const now = new Date();
            if (estimatedTime <= now) {
                this.markCountdownCompleted(badge, estimatedTimeStr);
                return;
            }
            
            this.startCountdown(badge, orderId, estimatedTime);
        });
    }
    
    startCountdown(badge, orderId, estimatedTime) {
        const countdownText = badge.querySelector('.countdown-text');
        
        // 清理現有的定時器
        const existingTimer = this.countdownTimers.get(orderId);
        if (existingTimer) {
            clearInterval(existingTimer);
        }
        
        const updateCountdown = () => {
            const now = new Date();
            const diffMs = estimatedTime - now;
            
            if (diffMs <= 0) {
                this.markCountdownCompleted(badge, estimatedTime.toISOString());
                
                const timer = this.countdownTimers.get(orderId);
                if (timer) {
                    clearInterval(timer);
                    this.countdownTimers.delete(orderId);
                }
                return;
            }
            
            const diffMins = Math.floor(diffMs / (1000 * 60));
            const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);
            
            if (diffMins > 0) {
                countdownText.textContent = `預計完成: ${diffMins}分${diffSecs.toString().padStart(2, '0')}秒`;
            } else {
                countdownText.textContent = `預計完成: ${diffSecs}秒`;
            }
        };
        
        // 立即更新一次
        updateCountdown();
        
        // 每秒更新一次
        const timer = setInterval(updateCountdown, 1000);
        this.countdownTimers.set(orderId, timer);
    }
    
    markCountdownCompleted(badge, estimatedTimeStr) {
        const countdownText = badge.querySelector('.countdown-text');
        
        let completedTimeDisplay = '已完成';
        if (window.TimeUtils && typeof window.TimeUtils.formatHKTimeOnly === 'function') {
            completedTimeDisplay = `已完成: ${window.TimeUtils.formatHKTimeOnly(new Date(estimatedTimeStr))}`;
        } else {
            try {
                const estimatedTime = new Date(estimatedTimeStr);
                const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit'
                });
                completedTimeDisplay = `已完成: ${formattedTime}`;
            } catch (e) {
                completedTimeDisplay = '已完成';
            }
        }
        
        countdownText.textContent = completedTimeDisplay;
        badge.classList.remove('badge-secondary');
        badge.classList.add('badge-success');
        
        const icon = badge.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check mr-1';
        }
    }
    
    cleanupTimers() {
        this.countdownTimers.forEach(timer => clearInterval(timer));
        this.countdownTimers.clear();
    }
    
    // ==================== 事件處理 ====================
    
    bindEvents() {
        console.log(`🔄 綁定 ${this.orderType} 訂單渲染器事件...`);
        
        // 刷新按鈕
        const refreshBtn = document.getElementById(`refresh-${this.orderType}-orders-btn`);
        if (refreshBtn) {
            this.registerListener(refreshBtn, 'click', () => {
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
            this.registerListener(tabElement, 'click', () => {
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
    }
    
    /**
     * 註冊事件監聽器（統一管理）
     */
    registerListener(element, event, handler) {
        const target = typeof element === 'string' ? document : element;
        target.addEventListener(event, handler);
        
        const key = `${event}_${Date.now()}_${Math.random()}`;
        this.eventListeners.set(key, { target, event, handler });
        
        return () => {
            target.removeEventListener(event, handler);
            this.eventListeners.delete(key);
        };
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
       