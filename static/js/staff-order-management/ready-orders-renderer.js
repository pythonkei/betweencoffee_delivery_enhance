// static/js/staff-order-management/ready-orders-renderer.js - 修正闪烁问题版本
// ==================== 已就緒訂單渲染器 - 修正閃爍問題 ====================

class DynamicReadyOrdersRenderer {
    constructor() {
        console.log('🔄 初始化已就緒訂單渲染器（修正閃爍問題）...');
        
        this.currentOrders = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false; // 新增：防止重複操作
        
        setTimeout(() => this.initialize(), 100);
    }
    
    initialize() {
        console.log('🔄 已就緒渲染器開始初始化...');
        
        // 1. 註冊到統一數據管理器
        this.registerToUnifiedManager();
        
        // 2. 綁定事件
        this.bindEvents();
        
        // 3. 立即檢查並加載數據
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log('✅ 已就緒訂單渲染器初始化完成');
    }
    
    // ==================== 統一數據管理器註冊（保持不變） ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        console.log('✅ 已就緒訂單渲染器註冊到統一數據管理器');
        
        // 監聽已就緒訂單數據
        window.unifiedDataManager.registerListener('ready_orders', (orders) => {
            console.log('📥 已就緒訂單數據接收:', orders?.length || 0, '個');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);
        
        // 監聽所有數據更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.ready_orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(allData.ready_orders);
                } else {
                    this.cacheOrders(allData.ready_orders);
                }
            }
        }, true);
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.ready_orders) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData.ready_orders);
                }, 100);
            }
        });
    }
    
    // ==================== 數據檢查與加載（保持不變） ====================
    
    checkAndLoadData() {
        console.log('🔍 檢查已就緒訂單數據...');
        
        // 情況1：統一數據管理器已有數據
        if (window.unifiedDataManager?.currentData?.ready_orders) {
            this.handleOrdersData(window.unifiedDataManager.currentData.ready_orders);
            return;
        }
        
        // 情況2：有緩存數據
        if (this.cachedOrders) {
            this.renderOrders(this.cachedOrders);
            return;
        }
        
        // 情況3：強制刷新數據
        this.requestOrdersData();
    }
    
    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            this.showEmpty();
            return;
        }
        
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
        
        window.unifiedDataManager.loadUnifiedData();
    }
    
    // ==================== 渲染方法（關鍵修正：統一容器結構） ====================
    
    /**
     * 渲染訂單列表（修正閃爍問題）
     */
    renderOrders(orders) {
        const orderList = document.getElementById('ready-orders-list');
        const emptyElement = document.getElementById('ready-orders-empty');
        
        if (!orderList) {
            console.warn('⚠️ 已就緒訂單列表容器未找到');
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清空容器
        orderList.innerHTML = '';
        this.currentOrders.clear();
        
        // 检查是否有订单
        if (!orders || orders.length === 0) {
            this.showEmpty();
            return;
        }
        
        console.log(`🎨 渲染已就緒訂單: ${orders.length} 個`);
        
        // ====== 關鍵修改：對訂單進行排序 - 快速訂單優先，然後按就緒時間排序 ======
        const sortedOrders = [...orders].sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            
            if (isQuickA !== isQuickB) {
                // 如果一個是快速訂單，一個不是，快速訂單優先
                return isQuickB ? 1 : -1; // 快速訂單排在前面
            }
            
            // 第二優先級：按就緒時間排序（越早就緒越優先）
            const timeA = a.ready_at || a.created_at || '';
            const timeB = b.ready_at || b.created_at || '';
            return new Date(timeA) - new Date(timeB); // 越早就緒的訂單越優先
        });
        
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
        
        // ✅ 關鍵修正：始終顯示列表容器，隱藏空狀態
        if (orderList) {
            orderList.style.display = 'block';
        }
        
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 更新最後更新時間
        this.updateLastUpdateTime();
        
        console.log('✅ 已就緒訂單渲染完成（已按快速訂單優先排序）');
    }
    
    /**
     * 創建訂單元素（徽章修正版）
     */
    createOrderElement(order) {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', order.id);
        orderDiv.setAttribute('data-status', order.status);
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-payment', order.payment_method);
        orderDiv.setAttribute('data-created', order.created_at);
        orderDiv.setAttribute('data-ready-at', order.ready_at || '');
        orderDiv.setAttribute('data-is-beans-only', order.is_beans_only || false);
        
        // ====== 關鍵修正：訂單類型判斷 ======
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);
        
        // 設置訂單類型屬性
        if (isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }
        
        // ====== 訂單類型徽章（左上角） ======
        let orderTypeBadges = '';
        
        // 1. 快速訂單徽章（優先級最高）
        if (order.is_quick_order) {
            orderTypeBadges = `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        }
        // 2. 混合訂單徽章（次優先級）
        else if (isMixedOrder) {
            orderTypeBadges = `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        }
        // 3. 普通訂單徽章（默認）
        else {
            orderTypeBadges = `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }

        // 使用統一時間工具
        const createdTime = window.TimeUtils ? 
            window.TimeUtils.formatHKTime(order.created_at) : 
            order.created_at;
        
        // ====== 修復：純咖啡豆訂單不顯示時間 ======
        let readyTimeBadgeHTML = '';
        
        if (!isBeansOnly && order.ready_at) {
            // 咖啡訂單：顯示已就緒時間
            let formattedTime = '--:--';
            if (window.TimeUtils) {
                formattedTime = window.TimeUtils.formatHKTimeOnly(order.ready_at);
            } else if (order.ready_at) {
                try {
                    const date = new Date(order.ready_at);
                    formattedTime = date.toLocaleTimeString('zh-HK', {
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                } catch (e) {
                    formattedTime = order.ready_at;
                }
            }
            
            readyTimeBadgeHTML = `
                <span class="badge badge-success ml-1">
                    <i class="fas fa-clock mr-1"></i>已就緒: ${formattedTime}
                </span>
            `;
        } else if (isBeansOnly) {
            // 純咖啡豆訂單：顯示現貨可取
            readyTimeBadgeHTML = `
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-box mr-1"></i>現貨可取
                </span>
            `;
        } else {
            // 其他情況：只顯示已就緒狀態
            readyTimeBadgeHTML = `
                <span class="badge badge-success ml-1">
                    <i class="fas fa-check-circle mr-1"></i>已就緒
                </span>
            `;
        }
        
        // ====== 咖啡杯數徽章 ======
        let coffeeCountBadge = '';
        if (coffeeCount > 0) {
            coffeeCountBadge = `
                <span hidden class="badge badge-dark ml-1">
                    <i class="fas fa-mug-hot mr-1"></i>${coffeeCount}杯
                </span>
            `;
        }
        
        // ====== 咖啡豆數量徽章 ======
        let beanCountBadge = '';
        if (beanCount > 0) {
            beanCountBadge = `
                <span hidden class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
                </span>
            `;
        }
        
        // ====== 構建訂單HTML（徽章修正版） ======
        orderDiv.innerHTML = `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-4">
                <div>
                    <h5>訂單編號: #${order.id}</h5>
                    <p class="mb-0">
                        訂單時間: ${createdTime}
                    </p>
                    <div class="mt-2">
                        ${readyTimeBadgeHTML}
                        ${coffeeCountBadge}
                        ${beanCountBadge}
                    </div>
                </div>
                <div class="text-right">
                    <span class="h5 pr-2">$${parseFloat(order.total_price).toFixed(2)}</span>
                </div>
            </div>
            
            <div class="mb-4">
                <p class="mb-2">
                    <strong>取餐码:</strong> <span class="h5 text-primary">${order.pickup_code || ''}</span> | 
                    <strong>客戶:</strong> ${order.name || '顧客'}
                    ${order.phone ? ` | <strong>電話:</strong> ${order.phone}` : ''}
                </p>
                ${isBeansOnly ? `
                <div class="mt-2">
                    <span hidden class="badge badge-info">
                        <i class="fas fa-info-circle mr-1"></i>此為咖啡豆現貨訂單，無需製作時間
                    </span>
                </div>` : ''}
            </div>
            
            <div class="order-items">
                ${this.renderOrderItems(order.items || [])}
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-muted">${order.items_display || (order.items_count || 0) + '項商品'}</span>
                </div>
                <div>
                    <button class="btn btn-info btn-sm mark-collected-btn" data-order-id="${order.id}">
                        <i class="fas fa-check-double mr-1"></i>客戶已提取
                    </button>
                </div>
            </div>
        `;
        
        return orderDiv;
    }
    
    /**
     * 渲染訂單項目
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
    
    // ==================== 事件處理（關鍵修正：防止閃爍） ====================
    
    bindEvents() {
        console.log('🔄 綁定已就緒訂單渲染器事件...');
        
        // 刷新按鈕
        const refreshBtn = document.getElementById('refresh-ready-orders-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('🔄 手動刷新已就緒訂單');
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // 標籤頁切換事件
        const readyTab = document.getElementById('ready-tab');
        if (readyTab) {
            readyTab.addEventListener('click', () => {
                console.log('🔄 已就緒標籤頁被點擊');
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
        
        // Bootstrap標籤頁顯示事件
        $('#ready-tab').on('shown.bs.tab', () => {
            console.log('📌 已就緒標籤頁已顯示');
            this.onTabActivated();
        });
        
        // ✅ 關鍵修正：訂單操作事件（添加防重複處理）
        document.addEventListener('click', (e) => {
            const markCollectedBtn = e.target.closest('.mark-collected-btn');
            if (markCollectedBtn && !this.isProcessingAction) {
                e.preventDefault();
                e.stopPropagation();
                
                const orderId = markCollectedBtn.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) {
                    console.log(`🔄 處理已提取按鈕點擊: 訂單 #${orderId}`);
                    this.handleMarkAsCollected(orderId);
                }
            }
            
            if (e.target.closest('.view-details-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.showOrderDetails(orderId);
            }
        });
        
        // ✅ 關鍵修正：監聽訂單操作事件，但延遲UI更新
        document.addEventListener('order_collected', (event) => {
            const orderId = event.detail.order_id;
            console.log(`📢 收到訂單已提取事件: #${orderId}`);
            
            // ✅ 修正：不像製作中訂單那樣立即移除，等待統一數據更新
            // 只是簡單地標記訂單為處理中，避免閃爍
            const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
            if (orderElement) {
                orderElement.style.opacity = '0.6';
                orderElement.style.transition = 'opacity 0.3s';
                
                // 禁用按鈕防止重複點擊
                const button = orderElement.querySelector('.mark-collected-btn');
                if (button) {
                    button.disabled = true;
                    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>處理中';
                    button.classList.remove('btn-info');
                    button.classList.add('btn-secondary');
                }
            }
        });
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', () => {
            if (this.isActiveTab()) {
                console.log('📢 已就緒渲染器收到統一數據更新');
                this.updateLastUpdateTime();
            }
        });
    }
    
    /**
     * 處理標記為已提取（關鍵修正：防止閃爍）
     */
    async handleMarkAsCollected(orderId) {
        if (!window.queueManager || !window.queueManager.markAsCollected) {
            console.error('❌ 隊列管理器未找到或markAsCollected方法不存在');
            return;
        }
        
        // ✅ 關鍵修正：防止重複操作
        if (this.isProcessingAction) {
            console.log('⚠️ 已有操作正在處理中，跳過');
            return;
        }
        
        this.isProcessingAction = true;
        
        try {
            console.log(`🔄 開始標記訂單 #${orderId} 為已提取`);
            
            // ✅ 關鍵修正：不像製作中訂單那樣立即移除UI元素
            // 只是先標記為處理中，等待服務器響應
            
            await window.queueManager.markAsCollected(orderId);
            
            console.log(`✅ 訂單 #${orderId} 已提交標記為已提取`);
            
            // ✅ 關鍵修正：不立即檢查空狀態，等待統一數據更新
            // 統一數據管理器會觸發數據更新，然後重新渲染
            
        } catch (error) {
            console.error(`❌ 標記訂單 #${orderId} 為已提取失敗:`, error);
            this.showToast(`❌ 操作失敗: ${error.message}`, 'error');
            
            // 恢復按鈕狀態
            const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
            if (orderElement) {
                orderElement.style.opacity = '1';
                const button = orderElement.querySelector('.mark-collected-btn');
                if (button) {
                    button.disabled = false;
                    button.innerHTML = '<i class="fas fa-check-double mr-1"></i>客戶已提取';
                    button.classList.remove('btn-secondary');
                    button.classList.add('btn-info');
                }
            }
        } finally {
            // 短暫延遲後重置處理狀態
            setTimeout(() => {
                this.isProcessingAction = false;
            }, 1000);
        }
    }
    
    /**
     * ✅ 關鍵修正：從列表中移除訂單（統一與製作中訂單的行為）
     */
    removeOrderFromList(orderId) {
        const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
        if (orderElement) {
            // ✅ 修正：不像之前那樣立即移除並檢查空狀態
            // 只是淡出效果，等待統一數據更新
            orderElement.style.opacity = '0.5';
            orderElement.style.transition = 'opacity 0.3s';
            
            setTimeout(() => {
                orderElement.remove();
                
                // 更新當前訂單映射
                this.currentOrders.delete(orderId);
                
                // ✅ 關鍵修正：不立即檢查是否為空
                // 等待統一數據更新後，由renderOrders方法處理空狀態
                console.log(`🗑️ 訂單 #${orderId} 已從UI移除，等待數據更新`);
            }, 300);
        }
    }
    
    /**
     * 標籤頁激活時調用
     */
    onTabActivated() {
        console.log('🎯 已就緒標籤頁激活');
        
        // 情況1：有緩存數據
        if (this.cachedOrders) {
            console.log('📦 渲染緩存數據:', this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
            return;
        }
        
        // 情況2：統一數據管理器有數據
        if (window.unifiedDataManager?.currentData?.ready_orders) {
            console.log('📊 從統一數據管理器獲取數據');
            this.renderOrders(window.unifiedDataManager.currentData.ready_orders);
            return;
        }
        
        // 情況3：強制刷新數據
        console.log('🚀 請求最新數據');
        this.forceRefresh();
    }
    
    /**
     * 強制刷新數據
     */
    forceRefresh() {
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData(true).then(success => {
                if (success) {
                    this.showToast('✅ 數據已刷新', 'success');
                } else {
                    this.showToast('❌ 刷新失敗', 'error');
                }
            });
        } else {
            console.error('❌ 統一數據管理器未找到');
            this.showToast('❌ 系統未就緒', 'error');
        }
    }
    
    // ==================== UI輔助方法（關鍵修正） ====================
    
    /**
     * 顯示空狀態（修正：與製作中訂單保持一致）
     */
    showEmpty() {
        const orderList = document.getElementById('ready-orders-list');
        const emptyElement = document.getElementById('ready-orders-empty');
        
        if (orderList) {
            orderList.innerHTML = '';
            orderList.style.display = 'none'; // ✅ 隱藏列表容器
        }
        
        if (emptyElement) {
            emptyElement.style.display = 'block';
        }
        
        console.log('📭 已就緒訂單列表為空，顯示空狀態');
    }
    
    /**
     * 檢查是否為空（移除立即檢查邏輯）
     */
    checkIfEmpty() {
        // ✅ 關鍵修正：不再立即檢查空狀態
        // 空狀態由renderOrders方法統一處理
        console.log('ℹ️ checkIfEmpty已禁用，空狀態由renderOrders統一處理');
    }
    
    /**
     * 緩存訂單數據
     */
    cacheOrders(orders) {
        this.cachedOrders = orders;
        console.log(`📦 緩存已就緒訂單數據: ${orders?.length || 0} 個`);
    }
    
    /**
     * 加載緩存的訂單數據
     */
    loadCachedOrders() {
        if (this.cachedOrders && this.isActiveTab()) {
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
        }
    }
    
    /**
     * 更新最後更新時間
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById('ready-orders-last-update');
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }
    
    // ==================== 輔助方法 ====================
    
    /**
     * 檢查是否為當前活動標籤頁
     */
    isActiveTab() {
        const readyTab = document.getElementById('ready-tab');
        return readyTab && readyTab.classList.contains('active');
    }
    
    showToast(message, type = 'info') {
        if (window.orderManager && window.orderManager.showToast) {
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
     * 手動觸發數據刷新
     */
    forceRefresh() {
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData(true);
        }
    }
    
    /**
     * 顯示訂單詳情
     */
    showOrderDetails(orderId) {
        if (window.orderManager && window.orderManager.showOrderDetails) {
            window.orderManager.showOrderDetails(orderId);
        } else {
            // 簡單實現
            alert(`訂單 #${orderId} 的詳細信息\n\n此功能待完善...`);
        }
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理已就緒訂單渲染器...');
        
        // 清理當前訂單映射
        this.currentOrders.clear();
        
        // 清理緩存
        this.cachedOrders = null;
        
        // 重置處理狀態
        this.isProcessingAction = false;
        
        console.log('✅ 已就緒訂單渲染器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.readyRenderer) {
                window.readyRenderer = new DynamicReadyOrdersRenderer();
                window.DynamicReadyOrdersRenderer = DynamicReadyOrdersRenderer;
                console.log('🌍 已就緒訂單渲染器（修正閃爍版）已註冊到 window');
            }
        }, 500);
    });
}