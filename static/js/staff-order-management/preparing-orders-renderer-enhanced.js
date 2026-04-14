// static/js/staff-order-management/preparing-orders-renderer-enhanced.js
// ==================== 增強版製作中訂單渲染器 - 支持分層標籤頁系統 ====================
// 版本: 2.0.0
// 功能: 將製作中訂單分為「倒計時進行中」和「倒計時已完成」兩個子標籤頁

class EnhancedPreparingOrdersRenderer {
    constructor() {
        console.log('🔄 初始化增強版製作中訂單渲染器...');
        
        // 數據管理
        this.allPreparingOrders = new Map(); // 所有製作中訂單
        this.countdownActiveOrders = new Map(); // 倒計時進行中訂單
        this.countdownCompletedOrders = new Map(); // 倒計時已完成訂單
        
        // 計時器管理
        this.countdownTimers = new Map();
        this.statusCheckInterval = null;
        
        // 狀態標誌
        this.isReady = false;
        this.hasInitialData = false;
        this.isActiveTab = false;
        
        // 延遲初始化
        setTimeout(() => this.initialize(), 100);
    }
    
    // ==================== 初始化方法 ====================
    
    initialize() {
        console.log('🔄 增強版渲染器開始初始化...');
        
        // 1. 註冊到統一數據管理器
        this.registerToUnifiedManager();
        
        // 2. 綁定事件
        this.bindEvents();
        
        // 3. 啟動狀態檢查間隔
        this.startStatusCheckInterval();
        
        // 4. 檢查並加載數據
        this.checkAndLoadData();
        
        this.isReady = true;
        console.log('✅ 增強版製作中訂單渲染器初始化完成');
    }
    
    // ==================== 統一數據管理器註冊 ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            console.error('❌ 未找到統一數據管理器，等待500ms後重試...');
            
            setTimeout(() => {
                if (window.unifiedDataManager) {
                    this.registerToUnifiedManager();
                } else {
                    console.error('❌ 統一數據管理器仍未就緒，將重試...');
                    setTimeout(() => this.registerToUnifiedManager(), 1000);
                }
            }, 500);
            return;
        }
        
        console.log('✅ 增強版渲染器註冊到統一數據管理器');
        
        // 監聽製作中訂單數據
        window.unifiedDataManager.registerListener('preparing_orders', (orders) => {
            console.log('📥 接收製作中訂單數據:', orders?.length || 0, '個');
            this.hasInitialData = true;
            
            // 處理訂單數據
            this.processOrdersData(orders);
            
            // 如果當前是活動標籤頁，立即渲染
            if (this.isTabActive()) {
                console.log('🔄 活動標籤頁，立即渲染訂單');
                this.renderAllOrders();
            }
        }, true);
        
        // 監聽所有數據更新（備份）
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.preparing_orders) {
                console.log('📥 從all_data接收製作中訂單:', allData.preparing_orders.length, '個');
                this.hasInitialData = true;
                
                this.processOrdersData(allData.preparing_orders);
                
                if (this.isTabActive()) {
                    this.renderAllOrders();
                }
            }
        }, true);
        
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', (event) => {
            console.log('📢 增強版渲染器收到統一數據更新事件');
            
            if (this.isTabActive() && window.unifiedDataManager?.currentData?.preparing_orders) {
                setTimeout(() => {
                    this.processOrdersData(window.unifiedDataManager.currentData.preparing_orders);
                    this.renderAllOrders();
                }, 100);
            }
        });
    }
    
    // ==================== 數據處理方法 ====================
    
    processOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log('📭 製作中訂單數據為空');
            this.clearAllOrders();
            this.updateBadges();
            this.showEmptyStates();
            return;
        }
        
        console.log(`🔄 處理製作中訂單數據: ${orders.length} 個`);
        
        // 清空現有數據
        this.clearAllOrders();
        
        // 處理每個訂單
        orders.forEach(order => {
            this.processSingleOrder(order);
        });
        
        // 更新徽章
        this.updateBadges();
        
        console.log(`✅ 訂單處理完成: 總數=${this.allPreparingOrders.size}, 進行中=${this.countdownActiveOrders.size}, 已完成=${this.countdownCompletedOrders.size}`);
    }
    
    processSingleOrder(order) {
        const orderId = order.id || order.order_id;
        
        if (!orderId) {
            console.warn('⚠️ 訂單缺少ID，跳過處理');
            return;
        }
        
        // 添加到所有訂單映射
        this.allPreparingOrders.set(orderId, order);
        
        // 檢查訂單狀態
        const orderStatus = this.checkOrderStatus(order);
        
        // 根據狀態分類
        if (orderStatus === 'countdown_active') {
            this.countdownActiveOrders.set(orderId, order);
        } else if (orderStatus === 'countdown_completed') {
            this.countdownCompletedOrders.set(orderId, order);
        } else {
            console.warn(`⚠️ 訂單 #${orderId} 狀態未知: ${orderStatus}`);
        }
    }
    
    checkOrderStatus(order) {
        const orderId = order.id || order.order_id;
        const estimatedTimeIso = order.estimated_completion_time_iso || order.estimated_ready_time_iso || '';
        
        // 如果沒有預計完成時間，默認為倒計時進行中
        if (!estimatedTimeIso || estimatedTimeIso === '') {
            console.log(`訂單 #${orderId} 沒有預計完成時間，默認為倒計時進行中`);
            return 'countdown_active';
        }
        
        try {
            const estimatedTime = new Date(estimatedTimeIso);
            const now = new Date();
            
            if (isNaN(estimatedTime.getTime())) {
                console.error(`訂單 #${orderId} 的預計時間格式錯誤: ${estimatedTimeIso}`);
                return 'countdown_active';
            }
            
            // 檢查是否已經過了預計完成時間
            if (estimatedTime <= now) {
                // 檢查是否已經超過5分鐘（避免長時間未處理的訂單）
                const diffMinutes = Math.floor((now - estimatedTime) / (1000 * 60));
                if (diffMinutes > 5) {
                    console.warn(`訂單 #${orderId} 倒計時已完成超過5分鐘（${diffMinutes}分鐘），可能需要手動處理`);
                }
                return 'countdown_completed';
            } else {
                return 'countdown_active';
            }
        } catch (error) {
            console.error(`檢查訂單 #${orderId} 狀態時出錯:`, error);
            return 'countdown_active';
        }
    }
    
    clearAllOrders() {
        this.allPreparingOrders.clear();
        this.countdownActiveOrders.clear();
        this.countdownCompletedOrders.clear();
        
        // 清理計時器
        this.cleanupTimers();
    }
    
    // ==================== 渲染方法 ====================
    
    renderAllOrders() {
        console.log('🎨 開始渲染所有訂單...');
        
        // 渲染倒計時進行中訂單
        this.renderCountdownActiveOrders();
        
        // 渲染倒計時已完成訂單
        this.renderCountdownCompletedOrders();
        
        // 更新最後更新時間
        this.updateLastUpdateTime();
        
        console.log('✅ 所有訂單渲染完成');
    }
    
    renderCountdownActiveOrders() {
        const contentContainer = document.getElementById('countdown-active-content');
        const emptyElement = document.getElementById('countdown-active-empty');
        
        if (!contentContainer) {
            console.warn('⚠️ 倒計時進行中內容容器未找到');
            return;
        }
        
        // 清空容器
        contentContainer.innerHTML = '';
        
        // 檢查是否有訂單
        if (this.countdownActiveOrders.size === 0) {
            console.log('📭 倒計時進行中訂單列表為空');
            if (contentContainer) contentContainer.style.display = 'none';
            if (emptyElement) emptyElement.style.display = 'block';
            return;
        }
        
        console.log(`🎨 渲染倒計時進行中訂單: ${this.countdownActiveOrders.size} 個`);
        
        // 創建訂單列表容器
        const orderList = document.createElement('div');
        orderList.className = 'order-list';
        orderList.id = 'countdown-active-list';
        
        // 對訂單進行排序：快速訂單優先，然後按預計完成時間排序
        const sortedOrders = Array.from(this.countdownActiveOrders.values()).sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            
            if (isQuickA !== isQuickB) {
                return isQuickB ? 1 : -1;
            }
            
            // 第二優先級：按預計完成時間排序（越早越優先）
            const timeA = a.estimated_completion_time_iso || a.estimated_ready_time_iso || '';
            const timeB = b.estimated_completion_time_iso || b.estimated_ready_time_iso || '';
            
            if (timeA && timeB) {
                return new Date(timeA) - new Date(timeB);
            }
            
            // 第三優先級：按創建時間排序
            return new Date(a.created_at_iso || a.created_at) - new Date(b.created_at_iso || b.created_at);
        });
        
        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order, 'countdown_active');
            orderList.appendChild(orderElement);
        });
        
        contentContainer.appendChild(orderList);
        contentContainer.style.display = 'block';
        
        // 隱藏空狀態
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 初始化倒計時
        this.initCountdowns('countdown_active');
    }
    
    renderCountdownCompletedOrders() {
        const contentContainer = document.getElementById('countdown-completed-content');
        const emptyElement = document.getElementById('countdown-completed-empty');
        
        if (!contentContainer) {
            console.warn('⚠️ 倒計時已完成內容容器未找到');
            return;
        }
        
        // 清空容器
        contentContainer.innerHTML = '';
        
        // 檢查是否有訂單
        if (this.countdownCompletedOrders.size === 0) {
            console.log('📭 倒計時已完成訂單列表為空');
            if (contentContainer) contentContainer.style.display = 'none';
            if (emptyElement) emptyElement.style.display = 'block';
            return;
        }
        
        console.log(`🎨 渲染倒計時已完成訂單: ${this.countdownCompletedOrders.size} 個`);
        
        // 創建訂單列表容器
        const orderList = document.createElement('div');
        orderList.className = 'order-list';
        orderList.id = 'countdown-completed-list';
        
        // 對訂單進行排序：按倒計時完成時間排序（越早完成越優先）
        const sortedOrders = Array.from(this.countdownCompletedOrders.values()).sort((a, b) => {
            const timeA = a.estimated_completion_time_iso || a.estimated_ready_time_iso || '';
            const timeB = b.estimated_completion_time_iso || b.estimated_ready_time_iso || '';
            
            if (timeA && timeB) {
                return new Date(timeA) - new Date(timeB);
            }
            
            return new Date(a.created_at_iso || a.created_at) - new Date(b.created_at_iso || b.created_at);
        });
        
        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order, 'countdown_completed');
            orderList.appendChild(orderElement);
        });
        
        contentContainer.appendChild(orderList);
        contentContainer.style.display = 'block';
        
        // 隱藏空狀態
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }
        
        // 初始化已完成訂單的顯示
        this.initCompletedOrdersDisplay();
    }
    
    createOrderElement(order, statusType) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || '';
        const name = order.name || '顧客';
        const phone = window.CommonUtils ? window.CommonUtils.formatPhoneNumber(order.phone || '') : (order.phone || '');
        const totalPrice = order.total_price || '0.00';
        
        // 預計完成時間
        const estimatedReadyTimeIso = order.estimated_completion_time_iso || order.estimated_ready_time_iso || '';
        const estimatedReadyTime = order.estimated_completion_time || order.estimated_ready_time || '--:--';
        
        // 格式化香港時間 - 使用統一的 formatOrderTime 方法
        const orderTime = window.TimeUtils ? 
            window.TimeUtils.formatOrderTime(order.created_at_iso || order.created_at, false) : // 只顯示時間
            (order.created_at_iso || order.created_at);
        
        // 訂單類型判斷
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);
        
        // ====== 訂單類型徽章 ======
        let orderTypeBadges = '';
        
        if (order.is_quick_order) {
            orderTypeBadges = `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        } else if (isMixedOrder) {
            orderTypeBadges = `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        } else {
            orderTypeBadges = `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }
        
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
        
        // ====== 倒計時顯示 ======
        let countdownDisplay = '';
        if (statusType === 'countdown_active' && estimatedReadyTimeIso) {
            countdownDisplay = `
                <span class="badge badge-secondary ml-1 countdown-badge" 
                    data-order-id="${orderId}" 
                    data-estimated-time="${estimatedReadyTimeIso}">
                    <i class="fas fa-hourglass-half mr-1"></i>
                    <span class="countdown-text">預計完成: 計算中...</span>
                </span>
            `;
        } else if (statusType === 'countdown_completed' && estimatedReadyTimeIso) {
            let completedTimeDisplay = '已完成';
            if (window.TimeUtils) {
                try {
                    const estimatedTime = new Date(estimatedReadyTimeIso);
                    completedTimeDisplay = `已完成: ${window.TimeUtils.formatHKTimeOnly(estimatedTime)}`;
                } catch (error) {
                    completedTimeDisplay = '已完成';
                }
            }
            countdownDisplay = `
                <span class="badge badge-completed ml-1">
                    <i class="fas fa-check mr-1"></i>${completedTimeDisplay}
                </span>
            `;
        }
        
        // ====== 合併徽章顯示 ======
        let combinedBadge = '';
        if (countdownDisplay && baristaHTML) {
            combinedBadge = `
                <div class="d-flex align-items-center mt-2">
                    ${countdownDisplay}
                    ${baristaHTML}
                </div>
            `;
        } else if (countdownDisplay) {
            combinedBadge = `
                <div class="d-flex align-items-center mt-2">
                    ${countdownDisplay}
                </div>
            `;
        } else if (baristaHTML) {
            combinedBadge = `
                <div class="d-flex align-items-center mt-2">
                    ${baristaHTML}
                </div>
            `;
        }
        
        // 構建訂單HTML（修正版：統一布局結構）
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', orderId);
        orderDiv.setAttribute('data-status', 'preparing');
        orderDiv.setAttribute('data-sub-status', statusType);
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-created', order.created_at_iso || order.created_at);
        orderDiv.setAttribute('data-estimated-ready', estimatedReadyTimeIso);
        
        // 設置訂單類型屬性（與其他渲染器保持一致）
        if (isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }

        // ====== 構建訂單HTML ======
        orderDiv.innerHTML = `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>

            <div class="d-flex justify-content-between mb-3 mt-3">
                <div class="mt-2">
                    ${combinedBadge}
                    ${isMixedOrder ? `
                    <div hidden class="mt-2">
                        <span class="badge badge-secondary">
                            <i class="fas fa-info-circle mr-1"></i>此訂單包含咖啡飲品和咖啡豆商品
                        </span>
                    </div>` : ''}
                </div>
            </div>

            <!-- 商品項目 -->
            <div class="order-items">
                <div>
                    ${this.renderOrderItems(order)}
                </div>
                <div>
                    <span class="card-text-md">${order.items_display || (order.items_count || 0) + '項商品'}</span>
                </div>
            </div>


            <div class="d-flex justify-content-between align-items-top mt-5 mb-2 pt-4 border-top">
                <div>
                    <h5>訂單編號: #${order.id}</h5>
                    <p class="mb-0">
                        訂單時間: ${orderTime}
                    </p>
                </div>
                <div class="text-right">
                    <span class="h5 pr-2">$${totalPrice}</span>
                    <span hidden class="h5 pr-2">$${parseFloat(totalPrice).toFixed(2)}</span>
                </div>
            </div>

            <div class="d-flex justify-content-between align-items-center">
                <div class="mb-2 card-text-md">
                    <div class="mb-2">
                        <span class="card-text-md badge badge-dark"><i class="fas fa-user mr-2"></i>取餐碼:${order.pickup_code || ''}</span>
                    </div>
                    <p class="card-text-md mb-2">
                        客戶: ${order.name || '顧客'} <span class="ml-3"></span>
                        電話: ${order.phone ? `${window.CommonUtils ? window.CommonUtils.formatPhoneNumber(order.phone) : order.phone}` : ''}
                    </p>
                    <div hidden>
                    <strong>取餐碼:</strong> <span class="h5 pickup-code">${pickupCode}</span>
                    <strong>客戶:</strong> ${name}${phone ? ` | <strong>電話:</strong> ${phone}` : ''}
                    </div>
                </div>
            </div>
            
            <!-- 操作按鈕 -->
            <div class="d-flex justify-content-end align-items-center">
                <button class="btn btn-success btn-sm mark-ready-btn" data-order-id="${orderId}">
                    <i class="fas fa-check mr-1"></i>已就緒
                </button>
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
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 105px; height: 110px;">
                            <img src="${itemImage || '/static/images/default-product.png'}" 
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
    
    // ==================== 倒計時管理 ====================
    
    initCountdowns(statusType) {
        console.log(`🔄 初始化${statusType === 'countdown_active' ? '倒計時進行中' : '倒計時已完成'}訂單倒計時...`);
        
        const listId = statusType === 'countdown_active' ? 'countdown-active-list' : 'countdown-completed-list';
        const orderList = document.getElementById(listId);
        
        if (!orderList) return;
        
        const countdownBadges = orderList.querySelectorAll('.countdown-badge');
        console.log(`在${listId}中找到 ${countdownBadges.length} 個倒計時徽章`);
        
        if (countdownBadges.length === 0) {
            console.log('沒有找到倒計時徽章，跳過倒計時初始化');
            return;
        }
        
        // 手動啟動倒計時
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
                badge.classList.add('badge-completed');

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
        
        // 清理現有的定時器
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
            badge.classList.add('badge-completed');
            
            const icon = badge.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-check mr-1';
            }
            console.log(`訂單 #${orderId} 已過預計完成時間，顯示: ${completedTimeDisplay}`);
            return;
        }
        
        // 更新倒計時顯示
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
                badge.classList.add('badge-completed');
                
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
        
        // 保存定時器引用
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
    
    initCompletedOrdersDisplay() {
        // 對於倒計時已完成的訂單，不需要倒計時，只需要顯示完成時間
        console.log('🔄 初始化倒計時已完成訂單顯示');
    }
    
    cleanupTimers() {
        this.countdownTimers.forEach(timer => clearInterval(timer));
        this.countdownTimers.clear();
    }
    
    // ==================== 狀態檢查間隔 ====================
    
    startStatusCheckInterval() {
        // 每30秒檢查一次訂單狀態
        this.statusCheckInterval = setInterval(() => {
            this.checkAndUpdateOrderStatuses();
        }, 30000); // 30秒
        
        console.log('🔄 啟動狀態檢查間隔（每30秒）');
    }
    
    checkAndUpdateOrderStatuses() {
        if (!this.isTabActive() || this.allPreparingOrders.size === 0) {
            return;
        }
        
        console.log('🔄 定期檢查訂單狀態...');
        
        let statusChanged = false;
        
        // 檢查所有訂單狀態
        this.allPreparingOrders.forEach((order, orderId) => {
            const oldStatus = this.checkOrderStatus(order);
            const newStatus = this.checkOrderStatus(order); // 重新檢查
            
            if (oldStatus !== newStatus) {
                console.log(`訂單 #${orderId} 狀態變化: ${oldStatus} → ${newStatus}`);
                statusChanged = true;
                
                // 更新訂單分類
                if (newStatus === 'countdown_completed') {
                    this.countdownActiveOrders.delete(orderId);
                    this.countdownCompletedOrders.set(orderId, order);
                } else if (newStatus === 'countdown_active') {
                    this.countdownCompletedOrders.delete(orderId);
                    this.countdownActiveOrders.set(orderId, order);
                }
            }
        });
        
        // 如果狀態有變化，重新渲染
        if (statusChanged) {
            console.log('🔄 訂單狀態有變化，重新渲染');
            this.updateBadges();
            this.renderAllOrders();
        }
    }
    
    // ==================== 事件處理 ====================
    
    bindEvents() {
        console.log('🔄 綁定增強版渲染器事件...');
        
        // 刷新按鈕
        const refreshBtn = document.getElementById('refresh-preparing-orders-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log('🔄 手動刷新製作中訂單');
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }
        
        // 標籤頁切換事件
        const preparingTab = document.getElementById('preparing-tab');
        if (preparingTab) {
            preparingTab.addEventListener('click', () => {
                console.log('🔄 製作中標籤頁被點擊');
                
                setTimeout(() => {
                    if (this.isTabActive()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
        
        // Bootstrap標籤頁顯示事件
        $('#preparing-tab').on('shown.bs.tab', () => {
            console.log('📌 製作中標籤頁已顯示');
            this.onTabActivated();
        });
        
        // 子標籤頁切換事件
        $('#countdown-active-tab').on('shown.bs.tab', () => {
            console.log('📌 倒計時進行中子標籤頁已顯示');
        });
        
        $('#countdown-completed-tab').on('shown.bs.tab', () => {
            console.log('📌 倒計時已完成子標籤頁已顯示');
        });
        
        // 訂單操作事件（事件委託）
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
            console.log(`📢 收到訂單標記就緒事件: #${orderId}`);
            setTimeout(() => {
                this.removeOrderFromAllLists(orderId);
            }, 300);
        });
    }
    
    /**
     * 標籤頁激活時調用
     */
    onTabActivated() {
        console.log('🎯 製作中標籤頁激活');
        this.isActiveTab = true;
        
        // 如果有數據，立即渲染
        if (this.allPreparingOrders.size > 0) {
            console.log(`🔄 渲染現有數據: ${this.allPreparingOrders.size} 個訂單`);
            this.renderAllOrders();
            return;
        }
        
        // 強制刷新數據
        console.log('🚀 請求最新數據');
        this.forceRefresh();
    }
    
    /**
     * 處理標記為就緒
     */
    async handleMarkAsReady(orderId) {
        if (!window.queueManager || !window.queueManager.markAsReady) {
            console.error('❌ 隊列管理器未找到或markAsReady方法不存在');
            return;
        }
        
        try {
            await window.queueManager.markAsReady(orderId);
        } catch (error) {
            console.error(`標記訂單 #${orderId} 為就緒失敗:`, error);
        }
    }
    
    /**
     * 從所有列表中移除訂單
     */
    removeOrderFromAllLists(orderId) {
        // 從數據映射中移除
        this.allPreparingOrders.delete(orderId);
        this.countdownActiveOrders.delete(orderId);
        this.countdownCompletedOrders.delete(orderId);
        
        // 從DOM中移除
        const orderElement = document.querySelector(`[data-order-id="${orderId}"]`);
        if (orderElement) {
            orderElement.style.opacity = '0.5';
            orderElement.style.transition = 'opacity 0.3s';
            
            setTimeout(() => {
                orderElement.remove();
                
                // 清理計時器
                const timer = this.countdownTimers.get(orderId);
                if (timer) {
                    clearInterval(timer);
                    this.countdownTimers.delete(orderId);
                }
                
                // 檢查是否為空
                this.checkIfEmpty();
                this.updateBadges();
            }, 300);
        }
    }
    
    // ==================== UI輔助方法 ====================
    
    /**
     * 顯示空狀態
     */
    showEmptyStates() {
        // 倒計時進行中空狀態
        const activeEmpty = document.getElementById('countdown-active-empty');
        const activeContent = document.getElementById('countdown-active-content');
        if (activeEmpty && activeContent) {
            activeContent.style.display = 'none';
            activeEmpty.style.display = 'block';
        }
        
        // 倒計時已完成空狀態
        const completedEmpty = document.getElementById('countdown-completed-empty');
        const completedContent = document.getElementById('countdown-completed-content');
        if (completedEmpty && completedContent) {
            completedContent.style.display = 'none';
            completedEmpty.style.display = 'block';
        }
    }
    
    /**
     * 檢查是否為空
     */
    checkIfEmpty() {
        // 檢查倒計時進行中
        const activeList = document.getElementById('countdown-active-list');
        const activeEmpty = document.getElementById('countdown-active-empty');
        const activeContent = document.getElementById('countdown-active-content');
        
        if (activeList && activeList.children.length === 0) {
            if (activeContent) activeContent.style.display = 'none';
            if (activeEmpty) activeEmpty.style.display = 'block';
        }
        
        // 檢查倒計時已完成
        const completedList = document.getElementById('countdown-completed-list');
        const completedEmpty = document.getElementById('countdown-completed-empty');
        const completedContent = document.getElementById('countdown-completed-content');
        
        if (completedList && completedList.children.length === 0) {
            if (completedContent) completedContent.style.display = 'none';
            if (completedEmpty) completedEmpty.style.display = 'block';
        }
    }
    
    /**
     * 更新徽章
     */
    updateBadges() {
        // 更新主徽章
        const preparingBadge = document.getElementById('preparing-orders-badge');
        if (preparingBadge) {
            preparingBadge.textContent = this.allPreparingOrders.size;
            preparingBadge.className = 'badge ml-2';
            if (this.allPreparingOrders.size > 0) {
                preparingBadge.classList.add('badge-warning');
            }
        }
        
        // 更新子標籤頁徽章
        const activeBadge = document.getElementById('countdown-active-badge');
        if (activeBadge) {
            activeBadge.textContent = this.countdownActiveOrders.size;
            activeBadge.className = 'badge badge-red-active ml-2';
        }

        const completedBadge = document.getElementById('countdown-completed-badge');
        if (completedBadge) {
            completedBadge.textContent = this.countdownCompletedOrders.size;
            completedBadge.className = 'badge badge-red-completed ml-2';
        }
    }
    
    /**
     * 更新最後更新時間
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
     * 檢查並加載數據
     */
    checkAndLoadData() {
        console.log('🔍 檢查製作中訂單數據...');
        
        // 情況1：統一數據管理器已有數據
        if (window.unifiedDataManager?.currentData?.preparing_orders) {
            console.log('📦 從統一數據管理器獲取已有數據:', window.unifiedDataManager.currentData.preparing_orders.length, '個');
            this.processOrdersData(window.unifiedDataManager.currentData.preparing_orders);
            return;
        }
        
        // 情況2：強制刷新數據
        console.log('🔄 請求製作中訂單數據...');
        this.requestOrdersData();
    }
    
    requestOrdersData() {
        if (!window.unifiedDataManager) {
            console.error('❌ 統一數據管理器未找到，無法請求數據');
            setTimeout(() => this.requestOrdersData(), 1000);
            return;
        }
        
        console.log('🚀 觸發統一數據管理器加載');
        window.unifiedDataManager.loadUnifiedData().then(success => {
            if (!success) {
                console.warn('⚠️ 數據加載失敗，將重試');
                setTimeout(() => this.requestOrdersData(), 2000);
            }
        });
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
    
    /**
     * 檢查是否為當前活動標籤頁
     */
    isTabActive() {
        const preparingTab = document.getElementById('preparing-tab');
        return preparingTab && preparingTab.classList.contains('active');
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
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理增強版製作中訂單渲染器...');
        
        // 清理計時器
        this.cleanupTimers();
        
        // 清理狀態檢查間隔
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
        
        // 清理數據映射
        this.clearAllOrders();
        
        console.log('✅ 增強版製作中訂單渲染器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    // 延遲實例化，確保DOM就緒
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (!window.enhancedPreparingRenderer) {
                console.log('🌍 創建增強版製作中訂單渲染器實例...');
                window.enhancedPreparingRenderer = new EnhancedPreparingOrdersRenderer();
                window.EnhancedPreparingOrdersRenderer = EnhancedPreparingOrdersRenderer;
                console.log('🌍 增強版製作中訂單渲染器已註冊到 window');
            }
        }, 500);
    });
}
