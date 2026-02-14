// static/js/staff-order-management/preparing-orders-renderer.js - 完整修正版
// ==================== 制作中订单渲染器 - 修复初始加载问题 ====================

class DynamicPreparingOrdersRenderer {
    constructor() {
        console.log('🔄 初始化制作中订单渲染器...');
        
        this.currentOrders = new Map();
        this.countdownTimers = new Map();
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        
        // 延迟初始化，确保DOM和统一数据管理器就绪
        setTimeout(() => this.initialize(), 100);
    }
    
    initialize() {
        console.log('🔄 制作中渲染器开始初始化...');
        
        // 1. 注册到统一数据管理器
        this.registerToUnifiedManager();
        
        // 2. 绑定事件
        this.bindEvents();
        
        // 3. 立即检查并加载数据
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log('✅ 制作中订单渲染器初始化完成');
    }
    
    // ==================== 统一数据管理器注册（增强版） ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            console.error('❌ 未找到统一数据管理器，等待500ms后重试...');
            
            setTimeout(() => {
                if (window.unifiedDataManager) {
                    this.registerToUnifiedManager();
                } else {
                    console.error('❌ 统一数据管理器仍未就绪，将重试...');
                    setTimeout(() => this.registerToUnifiedManager(), 1000);
                }
            }, 500);
            return;
        }
        
        console.log('✅ 制作中订单渲染器注册到统一数据管理器');
        
        // 监听制作中订单数据（强制立即执行）
        window.unifiedDataManager.registerListener('preparing_orders', (orders) => {
            console.log('📥 制作中订单数据接收:', orders?.length || 0, '个');
            this.hasInitialData = true;
            
            if (this.isActiveTab()) {
                console.log('🔄 活动标签页，立即渲染订单');
                this.renderOrders(orders);
            } else {
                console.log('📦 非活动标签页，缓存数据');
                this.cacheOrders(orders);
            }
        }, true); // 强制立即执行
        
        // 监听所有数据更新（备份）
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.preparing_orders) {
                console.log('📥 从all_data接收制作中订单:', allData.preparing_orders.length, '个');
                this.hasInitialData = true;
                
                if (this.isActiveTab()) {
                    this.renderOrders(allData.preparing_orders);
                } else {
                    this.cacheOrders(allData.preparing_orders);
                }
            }
        }, true);
        
        // 监听统一数据更新事件（新增）
        document.addEventListener('unified_data_updated', (event) => {
            console.log('📢 制作中渲染器收到统一数据更新事件');
            
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.preparing_orders) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData.preparing_orders);
                }, 100);
            }
        });
    }
    
    // ==================== 数据检查与加载 ====================
    
    checkAndLoadData() {
        console.log('🔍 检查制作中订单数据...');
        
        // 情况1：统一数据管理器已有数据
        if (window.unifiedDataManager?.currentData?.preparing_orders) {
            console.log('📦 从统一数据管理器获取已有数据:', window.unifiedDataManager.currentData.preparing_orders.length, '个');
            this.handleOrdersData(window.unifiedDataManager.currentData.preparing_orders);
            return;
        }
        
        // 情况2：有缓存数据
        if (this.cachedOrders) {
            console.log('📦 使用缓存数据:', this.cachedOrders.length, '个');
            this.renderOrders(this.cachedOrders);
            return;
        }
        
        // 情况3：强制刷新数据
        console.log('🔄 请求制作中订单数据...');
        this.requestOrdersData();
    }
    
    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log('📭 制作中订单数据为空');
            this.showEmpty();
            return;
        }
        
        console.log(`🔄 处理制作中订单数据: ${orders.length} 个`);
        
        if (this.isActiveTab()) {
            this.renderOrders(orders);
        } else {
            this.cacheOrders(orders);
        }
    }
    
    requestOrdersData() {
        if (!window.unifiedDataManager) {
            console.error('❌ 统一数据管理器未找到，无法请求数据');
            setTimeout(() => this.requestOrdersData(), 1000);
            return;
        }
        
        console.log('🚀 触发统一数据管理器加载');
        window.unifiedDataManager.loadUnifiedData().then(success => {
            if (!success) {
                console.warn('⚠️ 数据加载失败，将重试');
                setTimeout(() => this.requestOrdersData(), 2000);
            }
        });
    }
    
    // ==================== 渲染方法 ====================
    
    renderOrders(orders) {
        const contentContainer = document.getElementById('preparing-orders-content');
        const emptyElement = document.getElementById('preparing-orders-empty');
        
        if (!contentContainer) {
            console.warn('⚠️ 制作中订单内容容器未找到，100ms后重试');
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }
        
        // 清理现有计时器
        this.cleanupTimers();
        
        // 清空容器
        contentContainer.innerHTML = '';
        
        // 检查是否有订单
        if (!orders || orders.length === 0) {
            console.log('📭 制作中订单列表为空');
            this.showEmpty();
            return;
        }
        
        console.log(`🎨 渲染制作中订单: ${orders.length} 个`);
        
        // ====== 關鍵修改：對訂單進行排序 - 快速訂單優先，然後按創建時間排序 ======
        const sortedOrders = [...orders].sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            
            if (isQuickA !== isQuickB) {
                // 如果一個是快速訂單，一個不是，快速訂單優先
                return isQuickB ? 1 : -1; // 注意：排序函數返回負數表示a排在b前面
            }
            
            // 第二優先級：按創建時間排序（越早越優先）
            const timeA = a.created_at_iso || a.created_at || '';
            const timeB = b.created_at_iso || b.created_at || '';
            return new Date(timeA) - new Date(timeB); // 越早的訂單越優先
        });
        
        // 创建订单列表容器
        const orderList = document.createElement('div');
        orderList.className = 'order-list';
        orderList.id = 'preparing-orders-list';
        
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
        
        contentContainer.appendChild(orderList);
        contentContainer.style.display = 'block';
        
        // 隐藏空状态
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 重新初始化倒计时
        this.initCountdowns();
        
        // 更新最后更新时间
        this.updateLastUpdateTime();
        
        console.log('✅ 制作中订单渲染完成（已按快速訂單優先排序）');
    }
    
    createOrderElement(order) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || '';
        const name = order.name || '顾客';
        const phone = order.phone || '';
        const totalPrice = order.total_price || '0.00';
        
        // 关键修复：使用正确的预计完成时间字段
        const estimatedReadyTimeIso = order.estimated_completion_time_iso || '';
        const estimatedReadyTime = order.estimated_completion_time || '--:--';
        
        // 格式化香港时间
        const orderTime = window.TimeUtils ? 
            window.TimeUtils.formatHKTime(order.created_at_iso || order.created_at) : 
            (order.created_at_iso || order.created_at);
        
        // ====== 关键修正：订单类型判断 ======
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
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

        // ====== 队列位置徽章 ======
        let queuePositionBadge = '';
        if (order.queue_position) {
            queuePositionBadge = `
                <span class="badge badge-info ml-1 queue-position-badge">
                    <i class="fas fa-list-ol mr-1"></i>隊列位置: ${order.queue_position}
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

        // ====== 关键修复：倒计时器徽章 ======
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

        // 构建订单HTML
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', orderId);
        orderDiv.setAttribute('data-status', 'preparing');
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-payment', order.payment_method || '');
        orderDiv.setAttribute('data-created', order.created_at_iso || order.created_at);
        orderDiv.setAttribute('data-estimated-ready', estimatedReadyTimeIso);
        
        // 设置订单类型属性
        if (isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }
        
        orderDiv.innerHTML = `
            <!-- 订单类型徽章（左上角） -->
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
                        ${coffeeCountBadge}
                        ${beanCountBadge}
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
                ${this.renderOrderItems(order)}
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
    
    renderOrderItems(order) {
        const items = order.items || order.coffee_items || [];
        
        if (items.length === 0) {
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
                                 style="max-height: 75px;">
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${item.name || '商品'}</h6>
                        <p class="mb-1 text-muted">
                            數量: ${item.quantity || 1} 
                        </p>
                        <div class="text-muted">
                            ${item.cup_level_cn ? `杯型: ${item.cup_level_cn}` : ''}
                            ${item.milk_level_cn ? ` | 牛奶: ${item.milk_level_cn}` : ''}
                            ${item.grinding_level_cn ? ` 研磨: ${item.grinding_level_cn}` : ''}
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
    
    // ==================== 倒计时管理 ====================
    
    initCountdowns() {
        console.log('🔄 初始化製作中訂單倒計時...');
        
        const preparingList = document.getElementById('preparing-orders-list');
        if (!preparingList) return;
        
        const countdownBadges = preparingList.querySelectorAll('.countdown-badge');
        console.log(`在製作中列表中找到 ${countdownBadges.length} 個倒計時徽章`);
        
        if (countdownBadges.length === 0) {
            console.log('沒有找到倒計時徽章，跳過倒計時初始化');
            return;
        }
        
        // 手动启动倒计时
        this.manualStartCountdowns(countdownBadges);
    }
    
    manualStartCountdowns(countdownBadges) {
        console.log('開始手動啟動倒計時，處理', countdownBadges.length, '個徽章');
        
        countdownBadges.forEach(badge => {
            const orderId = badge.dataset.orderId;
            const estimatedTimeStr = badge.dataset.estimatedTime;
            const countdownText = badge.querySelector('.countdown-text');
            
            console.log(`處理訂單 #${orderId}, 預計時間: ${estimatedTimeStr}`);
            
            if (!estimatedTimeStr || estimatedTimeStr === '' || !countdownText) {
                console.warn(`訂單 ${orderId} 無法啟動倒計時`);
                return;
            }
            
            const estimatedTime = new Date(estimatedTimeStr);
            
            if (isNaN(estimatedTime.getTime())) {
                console.error(`訂單 ${orderId} 的預計時間格式錯誤: ${estimatedTimeStr}`);
                countdownText.textContent = '時間錯誤';
                return;
            }
            
            // 檢查是否已經過了預計完成時間
            const now = new Date();
            if (estimatedTime <= now) {
                let completedTimeDisplay = '已完成';
                if (window.TimeUtils) {
                    completedTimeDisplay = this.formatCompletedTime(estimatedTimeStr);
                } else {
                    const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                        hour12: true,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    completedTimeDisplay = `已完成: ${formattedTime}`;
                }
                
                countdownText.textContent = completedTimeDisplay;
                badge.classList.remove('badge-secondary');
                badge.classList.add('badge-success');
                
                const icon = badge.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-check mr-1';
                }
                console.log(`訂單 #${orderId} 已過期，直接顯示完成時間: ${completedTimeDisplay}`);
            } else {
                console.log(`訂單 #${orderId} 尚未完成，啟動倒計時`);
                this.startManualCountdown(badge);
            }
        });
    }
    
    startManualCountdown(badge) {
        const orderId = badge.dataset.orderId;
        const estimatedTimeStr = badge.dataset.estimatedTime;
        const countdownText = badge.querySelector('.countdown-text');
        
        if (!estimatedTimeStr || estimatedTimeStr === '' || !countdownText) {
            console.warn(`訂單 ${orderId} 無法啟動倒計時`);
            return;
        }
        
        const estimatedTime = new Date(estimatedTimeStr);
        
        if (isNaN(estimatedTime.getTime())) {
            console.error(`訂單 ${orderId} 的預計時間格式錯誤: ${estimatedTimeStr}`);
            countdownText.textContent = '時間錯誤';
            return;
        }
        
        // 清理现有的定时器
        const existingTimer = this.countdownTimers.get(orderId);
        if (existingTimer) {
            clearInterval(existingTimer);
        }
        
        // 檢查是否已經過了預計完成時間
        const now = new Date();
        if (estimatedTime <= now) {
            let completedTimeDisplay = '已完成';
            if (window.TimeUtils) {
                completedTimeDisplay = this.formatCompletedTime(estimatedTimeStr);
            } else {
                const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
                completedTimeDisplay = `已完成: ${formattedTime}`;
            }
            
            countdownText.textContent = completedTimeDisplay;
            badge.classList.remove('badge-secondary');
            badge.classList.add('badge-success');
            
            const icon = badge.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-check mr-1';
            }
            console.log(`訂單 #${orderId} 已過預計完成時間，顯示: ${completedTimeDisplay}`);
            return;
        }
        
        // 更新倒计时显示
        const updateCountdown = () => {
            const now = new Date();
            const diffMs = estimatedTime - now;
            
            if (diffMs <= 0) {
                let completedTimeDisplay = '已完成';
                if (window.TimeUtils) {
                    completedTimeDisplay = this.formatCompletedTime(estimatedTimeStr);
                } else {
                    const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                        hour12: true,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    completedTimeDisplay = `已完成: ${formattedTime}`;
                }
                
                countdownText.textContent = completedTimeDisplay;
                badge.classList.remove('badge-secondary');
                badge.classList.add('badge-success');
                
                const icon = badge.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-check mr-1';
                }
                
                console.log(`訂單 #${orderId} 手動倒計時完成，預計完成時間: ${estimatedTimeStr}`);
                
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
        
        // 保存定时器引用
        this.countdownTimers.set(orderId, timer);
        
        console.log(`手動啟動訂單 ${orderId} 的倒計時，預計完成時間: ${estimatedTimeStr}`);
    }
    
    formatCompletedTime(estimatedTimeStr) {
        try {
            const estimatedTime = new Date(estimatedTimeStr);
            if (window.TimeUtils && typeof window.TimeUtils.formatHKTimeOnly === 'function') {
                return `已完成: ${window.TimeUtils.formatHKTimeOnly(estimatedTime)}`;
            } else {
                const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit'
                });
                return `已完成: ${formattedTime}`;
            }
        } catch (error) {
            return '已完成';
        }
    }
    
    cleanupTimers() {
        this.countdownTimers.forEach(timer => clearInterval(timer));
        this.countdownTimers.clear();
    }
    
    // ==================== 事件处理 ====================
    
    bindEvents() {
        console.log('🔄 绑定制作中订单渲染器事件...');
        
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-preparing-orders-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('🔄 手动刷新制作中订单');
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // 标签页切换事件（增强）
        const preparingTab = document.getElementById('preparing-tab');
        if (preparingTab) {
            preparingTab.addEventListener('click', () => {
                console.log('🔄 制作中标签页被点击');
                
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
        
        // Bootstrap标签页显示事件（关键修复）
        $('#preparing-tab').on('shown.bs.tab', () => {
            console.log('📌 制作中标签页已显示');
            this.onTabActivated();
        });
        
        // 订单操作事件（事件委托）
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mark-ready-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.handleMarkAsReady(orderId);
            }
        });
        
        // 监听订单标记就绪事件
        document.addEventListener('order_marked_ready', (event) => {
            const orderId = event.detail.order_id;
            console.log(`📢 收到订单标记就绪事件: #${orderId}`);
            setTimeout(() => {
                this.removeOrderFromList(orderId);
            }, 300);
        });
    }
    
    /**
     * 标签页激活时调用
     */
    onTabActivated() {
        console.log('🎯 制作中标签页激活');
        
        // 情况1：有缓存数据，立即渲染
        if (this.cachedOrders) {
            console.log('📦 渲染缓存数据:', this.cachedOrders.length, '个');
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
            return;
        }
        
        // 情况2：统一数据管理器有数据
        if (window.unifiedDataManager?.currentData?.preparing_orders) {
            console.log('📊 从统一数据管理器获取数据');
            this.renderOrders(window.unifiedDataManager.currentData.preparing_orders);
            return;
        }
        
        // 情况3：强制刷新数据
        console.log('🚀 请求最新数据');
        this.forceRefresh();
    }
    
    /**
     * 处理标记为就绪
     */
    async handleMarkAsReady(orderId) {
        if (!window.queueManager || !window.queueManager.markAsReady) {
            console.error('❌ 队列管理器未找到或markAsReady方法不存在');
            return;
        }
        
        try {
            await window.queueManager.markAsReady(orderId);
        } catch (error) {
            console.error(`标记订单 #${orderId} 为就绪失败:`, error);
            this.showToast(`❌ 操作失败: ${error.message}`, 'error');
        }
    }
    
    /**
     * 从列表中移除订单
     */
    removeOrderFromList(orderId) {
        const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
        if (orderElement) {
            orderElement.style.opacity = '0.5';
            orderElement.style.transition = 'opacity 0.3s';
            
            setTimeout(() => {
                orderElement.remove();
                
                // 更新当前订单映射
                this.currentOrders.delete(orderId);
                
                // 清理计时器
                const timer = this.countdownTimers.get(orderId);
                if (timer) {
                    clearInterval(timer);
                    this.countdownTimers.delete(orderId);
                }
                
                // 检查是否为空
                this.checkIfEmpty();
            }, 300);
        }
    }
    
    // ==================== UI辅助方法 ====================
    
    /**
     * 显示空状态
     */
    showEmpty() {
        const contentContainer = document.getElementById('preparing-orders-content');
        const emptyElement = document.getElementById('preparing-orders-empty');
        
        if (contentContainer) {
            contentContainer.style.display = 'none';
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
        const orderElements = document.querySelectorAll('.order-item[data-status="preparing"]');
        if (orderElements.length === 0) {
            this.showEmpty();
        }
    }
    
    /**
     * 更新最后更新时间
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById('preparing-orders-last-update');
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
        console.log(`📦 缓存制作中订单数据: ${orders?.length || 0} 个`);
    }
    
    /**
     * 检查是否为当前活动标签页
     */
    isActiveTab() {
        const preparingTab = document.getElementById('preparing-tab');
        return preparingTab && preparingTab.classList.contains('active');
    }
    
    showToast(message, type = 'info') {
        if (window.orderManager && window.orderManager.showToast) {
            window.orderManager.showToast(message, type);
        } else {
            // 简单实现
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
            window.unifiedDataManager.loadUnifiedData(true).then(success => {
                if (success) {
                    this.showToast('✅ 数据已刷新', 'success');
                } else {
                    this.showToast('❌ 刷新失败', 'error');
                }
            });
        } else {
            console.error('❌ 统一数据管理器未找到');
            this.showToast('❌ 系统未就绪', 'error');
        }
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理制作中订单渲染器...');
        
        // 清理计时器
        this.cleanupTimers();
        
        // 清理当前订单映射
        this.currentOrders.clear();
        
        // 清理缓存
        this.cachedOrders = null;
        
        console.log('✅ 制作中订单渲染器已清理');
    }
}

// ==================== 全局注册 ====================

if (typeof window !== 'undefined') {
    // 延迟实例化，确保DOM就绪
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.preparingRenderer) {
                console.log('🌍 创建制作中订单渲染器实例...');
                window.preparingRenderer = new DynamicPreparingOrdersRenderer();
                window.DynamicPreparingOrdersRenderer = DynamicPreparingOrdersRenderer;
                console.log('🌍 制作中订单渲染器已注册到 window');
            }
        }, 500);
    });
}