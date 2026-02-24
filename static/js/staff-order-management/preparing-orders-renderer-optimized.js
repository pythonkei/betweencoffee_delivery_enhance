// static/js/staff-order-management/preparing-orders-renderer-optimized.js
// ==================== 優化版製作中訂單渲染器 ====================
// 使用共用工具模塊，減少代碼重複，提高性能

class OptimizedPreparingOrdersRenderer {
    constructor() {
        console.log('🔄 初始化製作中訂單渲染器（優化版）...');
        
        this.currentOrders = new Map();
        this.countdownTimers = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false;
        
        // 延遲初始化，確保DOM就緒
        setTimeout(() => this.initialize(), 100);
    }
    
    initialize() {
        console.log('🔄 製作中渲染器開始初始化...');
        
        this.registerToUnifiedManager();
        this.bindEvents();
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log('✅ 製作中訂單渲染器初始化完成');
    }
    
    // ==================== 統一數據管理器註冊 ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        console.log('✅ 製作中訂單渲染器註冊到統一數據管理器');
        
        // 監聽製作中訂單數據
        window.unifiedDataManager.registerListener('preparing_orders', (orders) => {
            console.log('📥 製作中訂單數據接收:', orders?.length || 0, '個');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);
        
        // 監聽所有數據更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.preparing_orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(allData.preparing_orders);
                } else {
                    this.cacheOrders(allData.preparing_orders);
                }
            }
        }, true);
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.preparing_orders) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData.preparing_orders);
                }, 100);
            }
        });
    }
    
    // ==================== 數據檢查與加載 ====================
    
    checkAndLoadData() {
        console.log('🔍 檢查製作中訂單數據...');
        
        // 情況1：統一數據管理器已有數據
        if (window.unifiedDataManager?.currentData?.preparing_orders) {
            console.log('📦 從統一數據管理器獲取已有數據:', window.unifiedDataManager.currentData.preparing_orders.length, '個');
            this.handleOrdersData(window.unifiedDataManager.currentData.preparing_orders);
            return;
        }
        
        // 情況2：有緩存數據
        if (this.cachedOrders) {
            console.log('📦 使用緩存數據:', this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            return;
        }
        
        // 情況3：強制刷新數據
        console.log('🔄 請求製作中訂單數據...');
        this.requestOrdersData();
    }
    
    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log('📭 製作中訂單數據為空');
            this.showEmpty();
            return;
        }
        
        console.log(`🔄 處理製作中訂單數據: ${orders.length} 個`);
        
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
        
        console.log('🚀 觸發統一數據管理器加載');
        window.unifiedDataManager.loadUnifiedData();
    }
    
    // ==================== 渲染方法（使用共用工具） ====================
    
    renderOrders(orders) {
        const contentContainer = document.getElementById('preparing-orders-content');
        const emptyElement = document.getElementById('preparing-orders-empty');
        
        if (!contentContainer) {
            console.warn('⚠️ 製作中訂單內容容器未找到，100ms後重試');
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清理現有計時器
        this.cleanupTimers();
        
        // 清空容器
        contentContainer.innerHTML = '';
        
        // 檢查是否有訂單
        if (!orders || orders.length === 0) {
            console.log('📭 製作中訂單列表為空');
            this.showEmpty();
            return;
        }
        
        console.log(`🎨 渲染製作中訂單: ${orders.length} 個`);
        
        // 對訂單進行排序 - 快速訂單優先，然後按創建時間排序
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
        contentContainer.appendChild(fragment);
        contentContainer.style.display = 'block';
        
        // 隱藏空狀態
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 重新初始化倒計時
        this.initCountdowns();
        
        // 更新最後更新時間
        this.updateLastUpdateTime();
        
        console.log('✅ 製作中訂單渲染完成（已按快速訂單優先排序）');
    }
    
    /**
     * 排序訂單
     */
    sortOrders(orders) {
        return [...orders].sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            
            if (isQuickA !== isQuickB) {
                return isQuickB ? 1 : -1;
            }
            
            // 第二優先級：按創建時間排序（越早越優先）
            const timeA = a.created_at_iso || a.created_at || '';
            const timeB = b.created_at_iso || b.created_at || '';
            return new Date(timeA) - new Date(timeB);
        });
    }
    
    /**
     * 創建訂單元素（使用共用工具）
     */
    createOrderElement(order) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || '';
        const name = order.name || '顾客';
        const phone = order.phone || '';
        const totalPrice = order.total_price || '0.00';
        
        // 使用共用工具分析訂單類型
        const typeInfo = window.CommonUtils ? 
            window.CommonUtils.analyzeOrderType(order) : 
            this.analyzeOrderType(order);
        
        // 使用共用工具生成訂單類型徽章
        const orderTypeBadges = window.CommonUtils ?
            window.CommonUtils.generateOrderTypeBadges(order, typeInfo) :
            this.generateOrderTypeBadges(order, typeInfo);
        
        // 使用共用工具生成數量徽章
        const quantityBadges = window.CommonUtils ?
            window.CommonUtils.generateQuantityBadges(typeInfo) :
            this.generateQuantityBadges(typeInfo);
        
        // 關鍵修復：使用正確的預計完成時間字段
        const estimatedReadyTimeIso = order.estimated_completion_time_iso || '';
        
        // 使用共用工具格式化時間
        const orderTime = window.CommonUtils ?
            window.CommonUtils.formatHKTime(order.created_at_iso || order.created_at) :
            (order.created_at_iso || order.created_at);
        
        // 隊列位置徽章
        let queuePositionBadge = '';
        if (order.queue_position) {
            queuePositionBadge = `
                <span class="badge badge-info ml-1 queue-position-badge">
                    <i class="fas fa-list-ol mr-1"></i>隊列位置: ${order.queue_position}
                </span>
            `;
        }
        
        // 倒計時器徽章
        let countdownBadge = '';
        if (estimatedReadyTimeIso) {
            countdownBadge = `
                <span class="badge badge-secondary ml-1 countdown-badge" 
                    data-order-id="${orderId}" 
                    data-estimated-time="${estimatedReadyTimeIso}">
                    <i class="fas fa-hourglass-half mr-1"></i>
                    <span class="countdown-text">預計完成: 計算中...</span>
                </span>
            `;
        }
        
        // 構建訂單HTML
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', orderId);
        orderDiv.setAttribute('data-status', 'preparing');
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-payment', order.payment_method || '');
        orderDiv.setAttribute('data-created', order.created_at_iso || order.created_at);
        orderDiv.setAttribute('data-estimated-ready', estimatedReadyTimeIso);
        
        // 設置訂單類型屬性
        if (typeInfo.isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }
        
        // 使用共用工具渲染訂單項目
        const orderItemsHTML = window.CommonUtils ?
            window.CommonUtils.renderOrderItems(order.items || order.coffee_items || []) :
            this.renderOrderItems(order.items || order.coffee_items || []);
        
        orderDiv.innerHTML = `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-4">
                <div>
                    <h5>訂單編號: #${orderId}</h5>
                    <p class="mb-0">
                        訂單時間: ${orderTime}
                    </p>
                    <div class="mt-2">
                        <span hidden class="badge badge-warning">
                            <i class="fas fa-clock mr-1"></i>製作中
                        </span>
                        ${queuePositionBadge}
                        ${countdownBadge}
                        ${quantityBadges}
                    </div>
                </div>
                <div class="text-right">
                    <span class="h5 pr-2">$${parseFloat(totalPrice).toFixed(2)}</span>
                </div>
            </div>
            
            <div class="mb-4">
                <p class="mb-2">
                    <strong>取餐碼:</strong> <span class="h5 text-primary">${pickupCode}</span> | 
                    <strong>客戶:</strong> ${name} | 
                    <strong>電話:</strong> ${phone}
                </p>
            </div>
            
            <div class="order-items">
                ${orderItemsHTML}
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-muted">${order.items_display || (order.items_count || 0) + '項商品'}</span>
                </div>
                <div>
                    <button class="btn btn-success btn-sm mark-ready-btn" data-order-id="${orderId}">
                        <i class="fas fa-check mr-1"></i>已就緒
                    </button>
                </div>
            </div>
        `;
        
        return orderDiv;
    }
    
    // ==================== 倒計時管理 ====================
    
    initCountdowns() {
        const contentContainer = document.getElementById('preparing-orders-content');
        if (!contentContainer) return;
        
        const countdownBadges = contentContainer.querySelectorAll('.countdown-badge');
        
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
        if (window.CommonUtils) {
            completedTimeDisplay = `已完成: ${window.CommonUtils.formatHKTimeOnly(estimatedTimeStr)}`;
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
        console.log('🔄 綁定製作中訂單渲染器事件...');
        
        // 刷新按鈕
        const refreshBtn = document.getElementById('refresh-preparing-orders-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('🔄 手動刷新製作中訂單');
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // Bootstrap標籤頁顯示事件
        $('#preparing-tab').on('shown.bs.tab', () => {
            console.log('📌 製作中標籤頁已顯示');
            this.onTabActivated();
        });
        
        // 標籤頁點擊事件
        const preparingTab = document.getElementById('preparing-tab');
        if (preparingTab) {
            preparingTab.addEventListener('click', () => {
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
        
        // 訂單操作事件（事件委托）
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mark-ready-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.handleMarkAsReady(orderId);
            }
        });
        
        // 監聽訂單標記就緒事件
        document.addEventListener('order_marked_ready', (event) => {
            const orderId = event.detail.order_id;
            console.log(`📢 收到訂單標記就緒事件