// static/js/staff-order-management/completed-orders-renderer.js - 完整修正版
// ==================== 已提取订单渲染器 - 修复初始加载问题 ====================

class DynamicCompletedOrdersRenderer {
    constructor() {
        console.log('🔄 初始化已提取订单渲染器...');
        
        this.currentOrders = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        
        setTimeout(() => this.initialize(), 100);
    }
    
    initialize() {
        console.log('🔄 已提取渲染器开始初始化...');
        
        this.registerToUnifiedManager();
        this.bindEvents();
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log('✅ 已提取订单渲染器初始化完成');
    }
    
    // ==================== 统一数据管理器注册（增强版） ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        console.log('✅ 已提取订单渲染器注册到统一数据管理器');
        
        // 监听已提取订单数据（立即执行）
        window.unifiedDataManager.registerListener('completed_orders', (orders) => {
            console.log('📥 已提取订单数据接收:', orders?.length || 0, '个');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);
        
        // 监听所有数据更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.completed_orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(allData.completed_orders);
                } else {
                    this.cacheOrders(allData.completed_orders);
                }
            }
        }, true);
        
        // 监听统一数据更新事件
        document.addEventListener('unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.completed_orders) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData.completed_orders);
                }, 100);
            }
        });
    }
    
    // ==================== 数据检查与加载 ====================
    
    checkAndLoadData() {
        console.log('🔍 检查已提取订单数据...');
        
        // 情况1：统一数据管理器已有数据
        if (window.unifiedDataManager?.currentData?.completed_orders) {
            console.log('📦 从统一数据管理器获取已有数据:', window.unifiedDataManager.currentData.completed_orders.length, '个');
            this.handleOrdersData(window.unifiedDataManager.currentData.completed_orders);
            return;
        }
        
        // 情况2：有缓存数据
        if (this.cachedOrders) {
            console.log('📦 使用缓存数据:', this.cachedOrders.length, '个');
            this.renderOrders(this.cachedOrders);
            return;
        }
        
        // 情况3：强制刷新数据
        console.log('🔄 请求已提取订单数据...');
        this.requestOrdersData();
    }
    
    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log('📭 已提取订单数据为空');
            this.showEmpty();
            return;
        }
        
        console.log(`🔄 处理已提取订单数据: ${orders.length} 个`);
        
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
        
        console.log('🚀 触发统一数据管理器加载');
        window.unifiedDataManager.loadUnifiedData();
    }
    
    // ==================== 渲染方法 ====================
    
    renderOrders(orders) {
        const orderList = document.getElementById('completed-orders-list');
        const emptyElement = document.getElementById('completed-orders-empty');
        
        if (!orderList) {
            console.warn('⚠️ 已提取订单列表容器未找到，100ms后重试');
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清空容器
        orderList.innerHTML = '';
        this.currentOrders.clear();
        
        // 检查是否有订单
        if (!orders || orders.length === 0) {
            console.log('📭 已提取订单列表为空');
            this.showEmpty();
            return;
        }
        
        console.log(`🎨 渲染已提取订单: ${orders.length} 个`);
        
        // 对订单进行排序（最新的在前面）
        const sortedOrders = [...orders].sort((a, b) => {
            const timeA = a.picked_up_at || a.created_at || '';
            const timeB = b.picked_up_at || b.created_at || '';
            return new Date(timeB) - new Date(timeA);
        });
        
        // 渲染每个订单
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            orderList.appendChild(orderElement);
            
            // 更新当前订单映射
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });
        
        // 隐藏空状态
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 更新最后更新时间
        this.updateLastUpdateTime();
        
        console.log('✅ 已提取订单渲染完成');
    }
    
    createOrderElement(order) {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', order.id);
        orderDiv.setAttribute('data-status', order.status);
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-payment', order.payment_method);
        orderDiv.setAttribute('data-created', order.created_at);
        orderDiv.setAttribute('data-picked-at', order.picked_up_at || '');
        
        // ====== 关键修正：订单类型判断 ======
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);
        
        // 设置订单类型属性
        if (isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }
        
        // ====== 订单类型徽章（左上角） ======
        let orderTypeBadges = '';
        
        // 1. 快速订单徽章（优先级最高）
        if (order.is_quick_order) {
            orderTypeBadges = `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        }
        // 2. 混合订单徽章（次优先级）
        else if (isMixedOrder) {
            orderTypeBadges = `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        }
        // 3. 普通订单徽章（默认）
        else {
            orderTypeBadges = `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }

        // ====== 关键修复：使用统一的 window.TimeUtils.formatOrderTime 格式化香港时间 ======
        const createdTime = window.TimeUtils ? 
            window.TimeUtils.formatOrderTime(order.created_at, false) : // 只显示时间
            (order.created_at || '');
        
        const pickedTime = window.TimeUtils ? 
            window.TimeUtils.formatOrderTime(order.picked_up_at, false) : // 只显示时间
            (order.picked_up_at || '');
        
        // ====== 关键修改：根据订单类型显示适当的等待时间 ======
        const waitDisplay = isBeansOnly ? '現貨可取' : (order.wait_duration || '計算中...');
        const waitIcon = isBeansOnly ? 'fa-box' : 'fa-clock';
        const waitBadgeClass = isBeansOnly ? 'badge-warning' : 'badge-light';
        
        // ====== 咖啡師信息 ======
        // 純咖啡豆訂單不顯示咖啡師
        let baristaName = '';
        let baristaClass = '';
        let baristaHTML = '';
        
        if (!isBeansOnly) {
            // 非純咖啡豆訂單：顯示咖啡師
            baristaName = order.barista || '未分配';
            baristaClass = order.barista ? 'badge-barista' : 'badge-no-barista';
            baristaHTML = `
                <span class="badge ${baristaClass} ml-2">
                    <i class="fas fa-user mr-1"></i>${baristaName}
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
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
                </span>
            `;
        }
        
        // ====== 合併徽章顯示 ======
        let combinedBadge = '';
        const extractedBadge = `
            <span class="badge badge-info">
                <i class="fas fa-check-double mr-1"></i>已提取 ${pickedTime}
            </span>
        `;
        
        if (baristaHTML) {
            combinedBadge = `
                <div class="d-flex align-items-center mt-2">
                    ${extractedBadge}
                    ${baristaHTML}
                </div>
            `;
        } else {
            combinedBadge = `
                <div class="d-flex align-items-center mt-2">
                    ${extractedBadge}
                </div>
            `;
        }
        
    // ====== 構建訂單HTML ======
    orderDiv.innerHTML = `
        <!-- 訂單類型徽章（左上角） -->
        <div class="order-type-badges-container">
            ${orderTypeBadges}
        </div>
        
        <div class="d-flex justify-content-between mb-3 mt-3">
            <div class="mt-2">
                ${coffeeCountBadge}
                ${beanCountBadge}
                ${combinedBadge}
            </div>
        </div>

        <div class="order-items">
            <div>
                ${this.renderOrderItems(order.items || [])}
            </div>
            <div>
                <span class="card-text-md">${order.items_display || (order.items_count || 0) + '項商品'}</span>
            </div>
        </div>


        <div class="d-flex justify-content-between align-items-top mt-5 mb-2 pt-4 border-top">
            <div>
                <h5>訂單編號: #${order.id}</h5>
                <p class="mb-0">
                    訂單時間: ${createdTime}
                </p>
                <div hidden class="mt-2">
                    ${coffeeCountBadge}
                    ${beanCountBadge}
                    ${isBeansOnly ? `
                    <div class="mt-2">
                        <span class="badge badge-warning">
                            <i class="fas fa-box mr-1"></i>咖啡豆現貨訂單
                        </span>
                    </div>` : ''}
                </div>
            </div>
            <div class="text-right">
                <span class="h5 pr-2">$${parseFloat(order.total_price).toFixed(2)}</span>
            </div>
        </div>
        
        <div class="d-flex justify-content-between align-items-top">
            <div class="mb-2 card-text-md">
                <div class="mb-2">
                    <span class="card-text-md badge badge-dark"><i class="fas fa-user mr-2"></i>取餐碼:${order.pickup_code || ''}</span>
                </div>
                <p class="card-text-md mb-2">
                    客戶: ${order.name || '顧客'} <span class="ml-3"></span>
                    電話: ${order.phone ? `${window.CommonUtils ? window.CommonUtils.formatPhoneNumber(order.phone) : order.phone}` : ''}
                </p>
            </div>
        </div>
        
        <div class="d-flex justify-content-end align-items-center">
            <p class="badge-v2 badge-info">
                <i class="fas fa-check-circle mr-1"></i>訂單已完成
            </p>
        </div>
    `;
        
        return orderDiv;
    }
    
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
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 105px; height: 110px;">
                            <img src="${item.image || '/static/images/default-product.png'}"
                                 alt="${item.name || '商品'}"
                                 class="img-fluid"
                                 style="max-height: 96px;">
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <p class="h5 mb-0">${item.name || '商品'}</p>
                        <p class="card-text-md mb-0">
                            數量: ${item.quantity || 1} 
                        </p>
                        <div class="card-text-md">
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
    
    // ==================== 事件处理 ====================
    
    bindEvents() {
        console.log('🔄 绑定已提取订单渲染器事件...');
        
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-completed-orders-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('🔄 手动刷新已提取订单');
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // Bootstrap标签页显示事件（关键修复）
        $('#completed-tab').on('shown.bs.tab', () => {
            console.log('📌 已提取标签页已显示');
            this.onTabActivated();
        });
        
        // 标签页点击事件
        const completedTab = document.getElementById('completed-tab');
        if (completedTab) {
            completedTab.addEventListener('click', () => {
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
    }
    
    /**
     * 标签页激活时调用
     */
    onTabActivated() {
        console.log('🎯 已提取标签页激活');
        
        // 情况1：有缓存数据
        if (this.cachedOrders) {
            console.log('📦 渲染缓存数据:', this.cachedOrders.length, '个');
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
            return;
        }
        
        // 情况2：统一数据管理器有数据
        if (window.unifiedDataManager?.currentData?.completed_orders) {
            console.log('📊 从统一数据管理器获取数据');
            this.renderOrders(window.unifiedDataManager.currentData.completed_orders);
            return;
        }
        
        // 情况3：强制刷新
        console.log('🚀 请求最新数据');
        this.forceRefresh();
    }
    
    // ==================== UI辅助方法 ====================
    
    /**
     * 显示空状态
     */
    showEmpty() {
        const orderList = document.getElementById('completed-orders-list');
        const emptyElement = document.getElementById('completed-orders-empty');
        
        if (orderList) {
            orderList.innerHTML = '';
        }
        
        if (emptyElement) {
            emptyElement.style.display = 'block';
        }
        
        console.log('📭 显示空状态');
    }
    
    /**
     * 检查是否为空
     */
    checkIfEmpty() {
        const orderElements = document.querySelectorAll('.order-item[data-status="completed"]');
        if (orderElements.length === 0) {
            this.showEmpty();
        }
    }
    
    /**
     * 更新最后更新时间
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById('completed-orders-last-update');
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
     * 缓存订单数据
     */
    cacheOrders(orders) {
        this.cachedOrders = orders;
        console.log(`📦 缓存已提取订单数据: ${orders?.length || 0} 个`);
    }
    
    /**
     * 检查是否为当前活动标签页
     */
    isActiveTab() {
        const completedTab = document.getElementById('completed-tab');
        return completedTab && completedTab.classList.contains('active');
    }
    
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
     * 强制刷新数据
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
        console.log('🔄 清理已提取订单渲染器...');
        
        // 清理当前订单映射
        this.currentOrders.clear();
        
        // 清理缓存
        this.cachedOrders = null;
        
        console.log('✅ 已提取订单渲染器已清理');
    }
}

// ==================== 全局注册 ====================

if (typeof window !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.completedRenderer) {
                console.log('🌍 创建已提取订单渲染器实例...');
                window.completedRenderer = new DynamicCompletedOrdersRenderer();
                window.DynamicCompletedOrdersRenderer = DynamicCompletedOrdersRenderer;
                console.log('🌍 已提取订单渲染器已注册到 window');
            }
        }, 500);
    });
}