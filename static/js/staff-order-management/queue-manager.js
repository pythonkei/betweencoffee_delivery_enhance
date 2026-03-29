// static/js/staff-order-management/queue-manager.js
// ==================== 隊列管理器 - 統一數據流版本（外觀復古版） ====================

class QueueManager {
    constructor() {
        console.log('🔄 初始化隊列管理器（統一數據流版）...');
        
        // 只保留必要的屬性
        this.isLoading = false;
        this.remainingTimers = new Map();
        
        // 新增：防止重複顯示訊息的標誌
        this.recentlyShownToasts = new Map();
        this.toastCooldown = 3000; // 3秒內不顯示相同訊息
        
        // 註冊到統一數據管理器
        this.registerToUnifiedManager();
        
        // 初始化事件監聽器
        this.initEventListeners();
        
        console.log('✅ 隊列管理器初始化完成');
    }
    
    // ==================== 統一數據管理器註冊 ====================
    
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            console.error('❌ 未找到統一數據管理器');
            return;
        }
        
        console.log('✅ 隊列管理器註冊到統一數據管理器');
        
        // 監聽等待隊列數據
        window.unifiedDataManager.registerListener('waiting_orders', (waitingOrders) => {
            this.updateWaitingQueueImmediately(waitingOrders);
        });
        
        // 監聽製作中隊列數據
        window.unifiedDataManager.registerListener('preparing_orders', (preparingOrders) => {
            this.updatePreparingQueueImmediately(preparingOrders);
        });
        
        // 監聽已就緒隊列數據
        window.unifiedDataManager.registerListener('ready_orders', (readyOrders) => {
            this.updateReadyQueueImmediately(readyOrders);
        });
        
        // 監聽所有數據更新（備用）
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            if (allData.waiting_orders) {
                this.updateWaitingQueueImmediately(allData.waiting_orders);
            }
            if (allData.preparing_orders) {
                this.updatePreparingQueueImmediately(allData.preparing_orders);
            }
            if (allData.ready_orders) {
                this.updateReadyQueueImmediately(allData.ready_orders);
            }
        });
    }
    
    // ==================== UI更新方法 ====================
    
    /**
     * 更新等待隊列（舊版外觀）
     */
    updateWaitingQueueImmediately(orders) {
        const waitingList = document.getElementById('waiting-orders-list');
        const emptyElement = document.getElementById('waiting-queue-empty');
        
        if (!waitingList) {
            console.warn('⚠️ 等待隊列容器未找到');
            return;
        }
        
        // 清空容器
        waitingList.innerHTML = '';
        
        if (orders && orders.length > 0) {
            // 渲染每個訂單卡片（使用舊版外觀）
            orders.forEach(order => {
                if (order && order.id) {
                    const orderCard = this.createWaitingOrderCard(order);
                    waitingList.appendChild(orderCard);
                }
            });
            
            // 顯示內容，隱藏空狀態
            if (waitingList.parentElement) {
                waitingList.parentElement.style.display = 'block';
            }
            if (emptyElement) {
                emptyElement.style.display = 'none';
            }
            
            console.log(`✅ 更新等待隊列: ${orders.length} 個訂單`);
        } else {
            // 顯示空狀態
            if (waitingList.parentElement) {
                waitingList.parentElement.style.display = 'none';
            }
            if (emptyElement) {
                emptyElement.style.display = 'block';
            }
            
            console.log('✅ 等待隊列為空');
        }
    }
    
    /**
     * 更新製作中隊列（舊版外觀）
     */
    updatePreparingQueueImmediately(orders) {
        const tbody = document.getElementById('preparing-queue-body');
        const content = document.getElementById('preparing-queue-content');
        const emptyElement = document.getElementById('preparing-queue-empty');
        
        if (!tbody) {
            console.warn('⚠️ 製作中隊列表格未找到');
            return;
        }
        
        tbody.innerHTML = '';
        
        // 清理現有計時器
        this.remainingTimers.forEach(timer => clearInterval(timer));
        this.remainingTimers.clear();
        
        if (orders && orders.length > 0) {
            orders.forEach(order => {
                const orderId = order.id || order.order_id;
                const remainingSeconds = order.remaining_seconds || 0;
                
                // 渲染咖啡項目（舊版樣式）
                let coffeeItemsHtml = '';
                const items = order.coffee_items || [];
                
                if (items.length > 0) {
                    items.forEach((item, index) => {
                        const itemName = item.name || `咖啡項目 ${index + 1}`;
                        const itemQuantity = item.quantity || 1;
                        
                        coffeeItemsHtml += `
                            <div class="coffee-item d-flex justify-content-between align-items-center mb-1">
                                <div class="d-flex align-items-center">
                                    <span class="coffee-name text-truncate" style="max-width: 100px;">${itemName}</span>
                                    <div class="ml-2">
                                        <span class="badge badge-warning ml-1">${itemQuantity}杯</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                } else {
                    coffeeItemsHtml = '<span class="text-muted small">無咖啡項目</span>';
                }
                
                // 舊版表格行樣式
                const row = document.createElement('tr');
                row.setAttribute('data-order-id', orderId);
                row.setAttribute('data-remaining-seconds', remainingSeconds);
                row.innerHTML = `
                    <td>#${orderId}</td>
                    <td><span class="badge badge-primary">${order.pickup_code || ''}</span></td>
                    <td style="min-width: 180px; max-width: 180px;">
                        <div class="coffee-items-container" style="max-height: 100px; overflow-y: auto;">
                            ${coffeeItemsHtml}
                        </div>
                    </td>
                    <td class="time-display">${order.estimated_completion_time || '--:--'}</td>
                    <td class="remaining-time" data-order-id="${orderId}" data-remaining-seconds="${remainingSeconds}">
                        ${this.formatRemainingTime(remainingSeconds)}
                    </td>
                    <td>
                        <div class="barista-info mb-1">
                            <span class="badge badge-info">
                                <i class="fas fa-user"></i> ${order.barista || '未分配'}
                            </span>
                        </div>
                        <button class="btn btn-sm btn-success mark-ready-btn">
                            <i class="fas fa-check"></i> 已就緒
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
                
                // 啟動倒計時
                if (remainingSeconds > 0) {
                    this.startRemainingTimer(orderId, remainingSeconds);
                }
            });
            
            // 顯示內容，隱藏空狀態
            if (content) content.style.display = 'block';
            if (emptyElement) emptyElement.style.display = 'none';
            
            console.log(`✅ 更新製作中隊列: ${orders.length} 個訂單`);
        } else {
            // 顯示空狀態
            if (content) content.style.display = 'none';
            if (emptyElement) emptyElement.style.display = 'block';
            
            console.log('✅ 製作中隊列為空');
        }
    }
    
    /**
     * 更新已就緒隊列（舊版外觀）
     */
    updateReadyQueueImmediately(orders) {
        const tbody = document.getElementById('ready-queue-body');
        const content = document.getElementById('ready-queue-content');
        const emptyElement = document.getElementById('ready-queue-empty');
        
        if (!tbody) {
            console.warn('⚠️ 已就緒隊列表格未找到');
            return;
        }
        
        tbody.innerHTML = '';
        
        if (orders && orders.length > 0) {
            orders.forEach(order => {
                const completedTime = order.completed_time || '--:--';
                
                // 渲染咖啡項目（舊版樣式）
                let coffeeItemsHtml = '';
                const items = order.coffee_items || [];
                
                if (items.length > 0) {
                    items.forEach((item, index) => {
                        const itemName = item.name || `咖啡項目 ${index + 1}`;
                        const itemQuantity = item.quantity || 1;
                        
                        coffeeItemsHtml += `
                            <div class="coffee-item d-flex justify-content-between align-items-center mb-1">
                                <span class="coffee-name text-truncate" style="max-width: 120px;">${itemName}</span>
                                <span class="badge badge-primary ml-2">${itemQuantity}杯</span>
                            </div>
                        `;
                    });
                } else {
                    coffeeItemsHtml = '<span class="text-muted small">無咖啡項目</span>';
                }
                
                // 舊版表格行樣式
                const row = document.createElement('tr');
                row.setAttribute('data-order-id', order.id || order.order_id);
                row.innerHTML = `
                    <td>#${order.id || order.order_id}</td>
                    <td><span class="badge badge-primary">${order.pickup_code || ''}</span></td>
                    <td style="min-width: 140px; max-width: 180px;">
                        <div class="coffee-items-container" style="max-height: 100px; overflow-y: auto;">
                            ${coffeeItemsHtml}
                        </div>
                    </td>
                    <td>
                        <span class="time-display">
                            <i class="fas fa-check-circle text-success mr-1"></i>
                            ${completedTime}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-info mark-collected-btn">
                            <i class="fas fa-check-double"></i> 已提取
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
            
            // 顯示內容，隱藏空狀態
            if (content) content.style.display = 'block';
            if (emptyElement) emptyElement.style.display = 'none';
            
            console.log(`✅ 更新已就緒隊列: ${orders.length} 個訂單`);
        } else {
            // 顯示空狀態
            if (content) content.style.display = 'none';
            if (emptyElement) emptyElement.style.display = 'block';
            
            console.log('✅ 已就緒隊列為空');
        }
    }
    
    // ==================== 創建訂單卡片方法（舊版外觀） ====================
    
    /**
     * 創建等待訂單卡片（舊版外觀）
     */
    createWaitingOrderCard(order) {
        const orderDiv = document.createElement('div');
        orderDiv.className = 'order-item mb-5 p-5 rounded selectable';
        orderDiv.setAttribute('data-order-id', order.id);
        orderDiv.setAttribute('data-status', 'waiting');
        orderDiv.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        orderDiv.setAttribute('data-payment', order.payment_method);
        orderDiv.setAttribute('data-created', order.created_at);
        
        // ====== 關鍵修正：訂單類型判斷 ======
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        // 設置訂單類型屬性
        if (isMixedOrder) {
            orderDiv.setAttribute('data-order-type', 'mixed');
        } else {
            orderDiv.setAttribute('data-order-type', 'single');
        }

        // 格式化價格
        const totalPrice = parseFloat(order.total_price || 0).toFixed(2);
        
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

        // ====== 隊列位置徽章 ======
        let queuePositionBadge = '';
        if (order.position) {
            queuePositionBadge = `
                <span class="badge badge-info ml-1">
                    <i class="fas fa-list-ol mr-1"></i>隊列位置: ${order.position}
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
        
        // ====== 關鍵修復：使用統一的 window.TimeUtils.formatOrderTime 格式化香港時間 ======
        const orderTime = window.TimeUtils ? 
            window.TimeUtils.formatOrderTime(order.created_at, false) : // 只顯示時間
            (order.created_at_display || '--:--');
        
        // ====== 咖啡豆數量徽章 ======
        let beanCountBadge = '';
        if (beanCount > 0) {
            beanCountBadge = `
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
                </span>
            `;
        }
        
        // ====== 支付方式徽章 ======
        let paymentMethodBadge = '';
        if (order.payment_method) {
            const paymentMethod = order.payment_method;
            let paymentIcon = '';
            let paymentText = '';
            
            switch(paymentMethod) {
                case 'alipay':
                    paymentIcon = '<i class="fab fa-alipay mr-1"></i>';
                    paymentText = '支付寶';
                    break;
                case 'fps':
                    paymentIcon = '<i class="fas fa-money-bill-wave mr-1"></i>';
                    paymentText = 'FPS';
                    break;
                case 'cash':
                    paymentIcon = '<i class="fas fa-money-bill-alt mr-1"></i>';
                    paymentText = '現金';
                    break;
                case 'paypal':
                    paymentIcon = '<i class="fab fa-paypal mr-1"></i>';
                    paymentText = 'PayPal';
                    break;
                default:
                    paymentIcon = '<i class="fas fa-money-check-alt mr-1"></i>';
                    paymentText = order.payment_method_display || '其他';
            }
            
            paymentMethodBadge = `
                <span class="badge badge-success ml-1">
                    ${paymentIcon}${paymentText}
                </span>
            `;
        }

        // 構建訂單HTML（徽章修正版）
        orderDiv.innerHTML = `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-4">
                <div>
                    <h5>訂單編號: #${order.id}</h5>
                    <p class="mb-0">
                        訂單時間: ${orderTime} | 
                        預計等待: ${order.wait_display || '計算中...'}
                    </p>
                    <div class="mt-2">
                        <span hidden class="badge badge-warning">
                            <i class="fas fa-clock mr-1"></i>等待中
                        </span>
                        ${queuePositionBadge}
                        ${coffeeCountBadge}
                        ${beanCountBadge}
                        <!-- ${paymentMethodBadge} -->
                    </div>
                </div>
                <div class="text-right">
                    <span class="h5 pr-2">$${totalPrice}</span>
                </div>
            </div>
            
            <div class="mb-4">
                <p class="mb-2">
                    <strong>取餐碼:</strong> <span class="h5 text-primary">${order.pickup_code || ''}</span> | 
                    <strong>客戶:</strong> ${order.name || '顧客'} | 
                    <strong>電話:</strong> ${window.CommonUtils ? window.CommonUtils.formatPhoneNumber(order.phone || '') : (order.phone || '')}
                </p>
                ${isMixedOrder ? `
                <div hidden class="mt-2">
                    <span class="badge badge-secondary">
                        <i class="fas fa-info-circle mr-1"></i>此訂單包含咖啡飲品和咖啡豆商品
                    </span>
                </div>` : ''}
            </div>
            
            <div class="order-items">
                ${this.renderWaitingOrderItems(order)}
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-muted">${order.items_display || (order.items_count || 0) + '項商品'}</span>
                </div>
                <div>
                    <button class="btn btn-primary btn-sm start-preparation-btn" data-order-id="${order.id}">
                        <i class="fas fa-play mr-1"></i>開始製作
                    </button>
                </div>
            </div>
        `;
        
        return orderDiv;
    }
    
    /**
     * 渲染等待訂單項目（與製作中訂單一致）
     */
    renderWaitingOrderItems(order) {
        let itemsHTML = '';
        
        // 優先使用完整的訂單項目數據
        const items = order.items || order.coffee_items || [];
        
        if (items.length > 0) {
            items.forEach(item => {
                const itemPrice = parseFloat(item.price || 0).toFixed(2);
                const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
                const itemImage = item.image || this.getDefaultImage(item.type);
                
                // 區分商品類型
                const isCoffee = item.type === 'coffee';
                const isBean = item.type === 'bean';
                
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
        } else {
            itemsHTML = '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }
        
        return itemsHTML;
    }
    
    /**
     * 獲取默認圖片
     */
    getDefaultImage(itemType) {
        switch(itemType) {
            case 'coffee': return '/static/images/default-coffee.png';
            case 'bean': return '/static/images/default-beans.png';
            default: return '/static/images/default-product.png';
        }
    }
    
    // ==================== 操作API方法（保持不變） ====================
    
    async startPreparation(orderId) {
        try {
            if (this.isLoading) {
                console.log('⏳ 已有操作正在進行，跳過重複請求');
                return;
            }
            this.isLoading = true;
            
            // ====== 階段1優化：樂觀更新 ======
            // 1. 記錄開始時間用於性能監控
            const startTime = Date.now();
            
            // 2. 立即更新UI（樂觀更新）
            this.showImmediateFeedback(orderId, 'preparing');
            
            // 3. 記錄UI更新性能
            if (window.recordUiUpdate) {
                window.recordUiUpdate('queue-manager', 'showImmediateFeedback', 
                    startTime, Date.now(), 1);
            }
            
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                // 如果無法獲取token，回滾UI更新
                this.rollbackImmediateFeedback(orderId);
                throw new Error('無法獲取安全令牌，請刷新頁面重試');
            }
            
            console.log(`🚀 開始製作訂單 #${orderId}，CSRF token: ${csrfToken.substring(0, 20)}...`);
            
            const response = await fetch(`/eshop/queue/start/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
        
            // 計算HTTP請求耗時
            const httpDuration = Date.now() - startTime;
            console.log(`📡 開始製作 API 響應: HTTP ${response.status} ${response.statusText}, 耗時: ${httpDuration}ms`);
            
            // 記錄HTTP請求性能
            if (window.recordHttpRequest) {
                window.recordHttpRequest(
                    `/eshop/queue/start/${orderId}/`,
                    'POST',
                    startTime,
                    Date.now(),
                    response.status,
                    response.ok
                );
            }
            
            if (response.ok) {
                const data = await response.json();
                console.log('📊 API 響應數據:', data);
                
                if (data.success) {
                    // 4. 請求成功，顯示成功提示
                    this.showToast('✅ 已開始製作訂單 #' + orderId, 'success');
                    
                    // 5. 觸發事件，讓統一數據管理器刷新數據
                    document.dispatchEvent(new CustomEvent('order_started_preparing', {
                        detail: { 
                            order_id: orderId,
                            estimated_ready_time: data.estimated_ready_time
                        }
                    }));
                    
                    // 6. 觸發統一數據刷新
                    if (window.unifiedDataManager) {
                        setTimeout(() => window.unifiedDataManager.loadUnifiedData(), 500);
                    }
                    
                    // 7. 記錄成功操作
                    this.recordOperationSuccess('start_preparation', orderId, httpDuration);
                    
                    // 8. 記錄操作性能
                    if (window.recordOperation) {
                        window.recordOperation(
                            'start_preparation',
                            orderId,
                            startTime,
                            Date.now(),
                            true,
                            null
                        );
                    }
                } else {
                    // 9. 如果API返回失敗，回滾UI更新
                    this.rollbackImmediateFeedback(orderId);
                    throw new Error(data.message || data.error || '操作失敗');
                }
            } else if (response.status === 403) {
                // 處理 403 Forbidden 錯誤
                const errorText = await response.text();
                console.error('❌ HTTP 403 Forbidden 錯誤詳情:', errorText);
                
                // 回滾UI更新
                this.rollbackImmediateFeedback(orderId);
                
                try {
                    const errorData = JSON.parse(errorText);
                    throw new Error(`權限不足: ${errorData.error || errorData.message || '請確認您有足夠權限執行此操作'}`);
                } catch {
                    throw new Error(`權限不足或安全令牌無效 (HTTP 403)`);
                }
            } else {
                const errorText = await response.text();
                console.error(`❌ HTTP ${response.status} 錯誤詳情:`, errorText);
                
                // 回滾UI更新
                this.rollbackImmediateFeedback(orderId);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('開始製作失敗:', error);
            
            // 記錄操作失敗性能
            if (window.recordOperation) {
                window.recordOperation(
                    'start_preparation',
                    orderId,
                    startTime,
                    Date.now(),
                    false,
                    error.message
                );
            }
            
            // 根據錯誤類型顯示不同的提示
            let errorMessage = error.message;
            if (errorMessage.includes('權限不足') || errorMessage.includes('403')) {
                this.showToast('❌ 權限不足：請確認您已登錄並有足夠權限', 'error');
            } else if (errorMessage.includes('安全令牌')) {
                this.showToast('❌ 安全令牌錯誤：請刷新頁面重試', 'error');
            } else if (errorMessage.includes('網絡')) {
                this.showToast('❌ 網絡錯誤：請檢查網絡連接', 'error');
            } else {
                this.showToast('❌ 操作失敗: ' + errorMessage, 'error');
            }
            
            // 記錄操作失敗
            this.recordOperationFailure('start_preparation', orderId, errorMessage);
        } finally {
            this.isLoading = false;
        }
    }
    
    async markAsReady(orderId) {
        try {
            if (this.isLoading) {
                console.log('⏳ 已有操作正在進行，跳過重複請求');
                return;
            }
            this.isLoading = true;
            
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('無法獲取安全令牌，請刷新頁面重試');
            }
            
            console.log(`🚀 標記訂單 #${orderId} 為就緒，CSRF token: ${csrfToken.substring(0, 20)}...`);
            
            const response = await fetch(`/eshop/queue/ready/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
            
            console.log(`📡 標記就緒 API 響應: HTTP ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📊 API 響應數據:', data);
                
                if (data.success) {
                    this.showToast(`✅ 訂單 #${orderId} 已標記為就緒`, 'success');
                    
                    // 觸發事件
                    document.dispatchEvent(new CustomEvent('order_marked_ready', {
                        detail: { order_id: orderId }
                    }));
                    
                    // 觸發統一數據刷新
                    if (window.unifiedDataManager) {
                        setTimeout(() => window.unifiedDataManager.loadUnifiedData(), 500);
                    }
                } else {
                    throw new Error(data.message || data.error || '操作失敗');
                }
            } else if (response.status === 403) {
                // 處理 403 Forbidden 錯誤
                const errorText = await response.text();
                console.error('❌ HTTP 403 Forbidden 錯誤詳情:', errorText);
                
                try {
                    const errorData = JSON.parse(errorText);
                    throw new Error(`權限不足: ${errorData.error || errorData.message || '請確認您有足夠權限執行此操作'}`);
                } catch {
                    throw new Error(`權限不足或安全令牌無效 (HTTP 403)`);
                }
            } else {
                const errorText = await response.text();
                console.error(`❌ HTTP ${response.status} 錯誤詳情:`, errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`標記訂單 #${orderId} 為就緒失敗:`, error);
            
            // 根據錯誤類型顯示不同的提示
            let errorMessage = error.message;
            if (errorMessage.includes('權限不足') || errorMessage.includes('403')) {
                this.showToast('❌ 權限不足：請確認您已登錄並有足夠權限', 'error');
            } else if (errorMessage.includes('安全令牌')) {
                this.showToast('❌ 安全令牌錯誤：請刷新頁面重試', 'error');
            } else if (errorMessage.includes('網絡')) {
                this.showToast('❌ 網絡錯誤：請檢查網絡連接', 'error');
            } else {
                this.showToast(`❌ 操作失敗: ${errorMessage}`, 'error');
            }
        } finally {
            this.isLoading = false;
        }
    }
    
    async markAsCollected(orderId) {
        try {
            if (this.isLoading) {
                console.log('⏳ 已有操作正在進行，跳過重複請求');
                return;
            }
            this.isLoading = true;
            
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('無法獲取安全令牌，請刷新頁面重試');
            }
            
            console.log(`🚀 標記訂單 #${orderId} 為已提取，CSRF token: ${csrfToken.substring(0, 20)}...`);
            
            const response = await fetch(`/eshop/queue/collected/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
            
            console.log(`📡 標記提取 API 響應: HTTP ${response.status} ${response.statusText}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('📊 API 響應數據:', data);
                
                if (data.success) {
                    this.showToast(`✅ 訂單 #${orderId} 已標記為已提取`, 'success');
                    
                    // 觸發事件
                    document.dispatchEvent(new CustomEvent('order_collected', {
                        detail: { order_id: orderId }
                    }));
                    
                    // 觸發統一數據刷新
                    if (window.unifiedDataManager) {
                        setTimeout(() => window.unifiedDataManager.loadUnifiedData(), 500);
                    }
                } else {
                    throw new Error(data.message || data.error || '操作失敗');
                }
            } else if (response.status === 403) {
                // 處理 403 Forbidden 錯誤
                const errorText = await response.text();
                console.error('❌ HTTP 403 Forbidden 錯誤詳情:', errorText);
                
                try {
                    const errorData = JSON.parse(errorText);
                    throw new Error(`權限不足: ${errorData.error || errorData.message || '請確認您有足夠權限執行此操作'}`);
                } catch {
                    throw new Error(`權限不足或安全令牌無效 (HTTP 403)`);
                }
            } else {
                const errorText = await response.text();
                console.error(`❌ HTTP ${response.status} 錯誤詳情:`, errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`標記訂單 #${orderId} 為已提取失敗:`, error);
            
            // 根據錯誤類型顯示不同的提示
            let errorMessage = error.message;
            if (errorMessage.includes('權限不足') || errorMessage.includes('403')) {
                this.showToast('❌ 權限不足：請確認您已登錄並有足夠權限', 'error');
            } else if (errorMessage.includes('安全令牌')) {
                this.showToast('❌ 安全令牌錯誤：請刷新頁面重試', 'error');
            } else if (errorMessage.includes('網絡')) {
                this.showToast('❌ 網絡錯誤：請檢查網絡連接', 'error');
            } else {
                this.showToast(`❌ 操作失敗: ${errorMessage}`, 'error');
            }
        } finally {
            this.isLoading = false;
        }
    }
    
    // ==================== 事件監聽器 ====================
    
    initEventListeners() {
        // 使用事件委託處理操作按鈕
        document.addEventListener('click', (e) => {
            if (e.target.closest('.start-preparation-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.startPreparation(orderId);
            }
            
            if (e.target.closest('.mark-ready-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.markAsReady(orderId);
            }
            
            if (e.target.closest('.mark-collected-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.markAsCollected(orderId);
            }
            
            if (e.target.closest('.view-details-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const orderId = e.target.closest('[data-order-id]')?.dataset.orderId;
                if (orderId) this.showOrderDetails(orderId);
            }
        });
        
        // 監聽標籤頁切換事件
        const queueTab = document.getElementById('queue-tab');
        if (queueTab) {
            queueTab.addEventListener('click', () => {
                // 確保統一數據管理器刷新數據
                if (window.unifiedDataManager) {
                    setTimeout(() => window.unifiedDataManager.loadUnifiedData(), 300);
                }
            });
        }
    }
    
    // ==================== 輔助方法（保持不變） ====================
    
    formatRemainingTime(seconds) {
        if (seconds <= 0) return '已完成';
        
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    startRemainingTimer(orderId, initialSeconds) {
        const timerElement = document.querySelector(`.remaining-time[data-order-id="${orderId}"]`);
        if (!timerElement) return;
        
        let remainingSeconds = initialSeconds;
        
        const timer = setInterval(() => {
            remainingSeconds--;
            
            if (remainingSeconds <= 0) {
                timerElement.textContent = '已完成';
                clearInterval(timer);
                this.remainingTimers.delete(orderId);
            } else {
                timerElement.textContent = this.formatRemainingTime(remainingSeconds);
            }
        }, 1000);
        
        this.remainingTimers.set(orderId, timer);
    }
    
    showToast(message, type = 'info') {
        // 防止重複顯示相同訊息
        const now = Date.now();
        const messageKey = `${message}_${type}`;
        
        if (this.recentlyShownToasts.has(messageKey)) {
            const lastShownTime = this.recentlyShownToasts.get(messageKey);
            if (now - lastShownTime < this.toastCooldown) {
                console.log(`⏭️ 跳過重複訊息: ${message} (${type})`);
                return; // 在冷卻時間內，不顯示相同訊息
            }
        }
        
        // 記錄顯示時間
        this.recentlyShownToasts.set(messageKey, now);
        
        // 定期清理過期的記錄
        setTimeout(() => {
            this.recentlyShownToasts.delete(messageKey);
        }, this.toastCooldown);
        
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
    
    getCsrfToken() {
        console.log('🔄 嘗試獲取 CSRF token...');
        
        // 方法1：從 cookie 獲取（原始方法）
        let token = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // 嘗試多種可能的 cookie 名稱
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    token = decodeURIComponent(cookie.substring(10));
                    console.log('✅ 從 cookie (csrftoken) 獲取 token');
                    break;
                } else if (cookie.substring(0, 11) === 'csrf_token=') {
                    token = decodeURIComponent(cookie.substring(11));
                    console.log('✅ 從 cookie (csrf_token) 獲取 token');
                    break;
                } else if (cookie.substring(0, 8) === 'csrf=') {
                    token = decodeURIComponent(cookie.substring(8));
                    console.log('✅ 從 cookie (csrf) 獲取 token');
                    break;
                }
            }
        }
        
        // 方法2：從 meta 標籤獲取（備用方案）
        if (!token) {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                token = metaToken.getAttribute('content');
                console.log('✅ 從 meta 標籤獲取 token');
            }
        }
        
        // 方法3：從表單輸入獲取（備用方案）
        if (!token) {
            const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (inputToken) {
                token = inputToken.value;
                console.log('✅ 從表單輸入獲取 token');
            }
        }
        
        // 方法4：從 Django 模板變量獲取（如果可用）
        if (!token && typeof django !== 'undefined' && django.csrf) {
            token = django.csrf.getToken();
            console.log('✅ 從 Django 模板變量獲取 token');
        }
        
        if (token) {
            console.log('✅ CSRF token 獲取成功');
            return token;
        } else {
            console.error('❌ 無法獲取 CSRF token');
            this.showToast('❌ 系統錯誤：無法獲取安全令牌，請刷新頁面重試', 'error');
            return null;
        }
    }
    
    showOrderDetails(orderId) {
        // 簡單實現，可以彈出模態框顯示詳細信息
        alert(`訂單 #${orderId} 的詳細信息\n\n此功能待完善...`);
    }
    
    // ==================== 樂觀更新輔助方法 ====================
    
    /**
     * 顯示立即反饋（樂觀更新）
     */
    showImmediateFeedback(orderId, action) {
        console.log(`⚡ 樂觀更新: 訂單 #${orderId} ${action}`);
        
        // 1. 禁用按鈕，防止重複點擊
        const button = document.querySelector(`.start-preparation-btn[data-order-id="${orderId}"]`);
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>處理中...';
            button.classList.remove('btn-primary');
            button.classList.add('btn-secondary');
        }
        
        // 2. 顯示處理中提示
        this.showToast(`正在處理訂單 #${orderId}...`, 'info');
        
        // 3. 記錄樂觀更新狀態
        if (!this.optimisticUpdates) {
            this.optimisticUpdates = new Map();
        }
        this.optimisticUpdates.set(orderId, {
            action: action,
            timestamp: Date.now(),
            originalButtonState: button ? {
                html: button.innerHTML,
                disabled: button.disabled,
                classes: button.className
            } : null
        });
    }
    
    /**
     * 回滾樂觀更新
     */
    rollbackImmediateFeedback(orderId) {
        console.log(`↩️ 回滾樂觀更新: 訂單 #${orderId}`);
        
        if (!this.optimisticUpdates || !this.optimisticUpdates.has(orderId)) {
            return;
        }
        
        const updateInfo = this.optimisticUpdates.get(orderId);
        
        // 1. 恢復按鈕狀態
        const button = document.querySelector(`.start-preparation-btn[data-order-id="${orderId}"]`);
        if (button && updateInfo.originalButtonState) {
            button.disabled = updateInfo.originalButtonState.disabled;
            button.innerHTML = updateInfo.originalButtonState.html;
            button.className = updateInfo.originalButtonState.classes;
        }
        
        // 2. 從記錄中移除
        this.optimisticUpdates.delete(orderId);
        
        // 3. 顯示回滾提示
        this.showToast(`訂單 #${orderId} 操作已取消`, 'warning');
    }
    
    /**
     * 記錄操作成功
     */
    recordOperationSuccess(operation, orderId, duration) {
        console.log(`✅ 操作成功: ${operation} 訂單 #${orderId}, 耗時: ${duration}ms`);
        
        // 清理樂觀更新記錄
        if (this.optimisticUpdates && this.optimisticUpdates.has(orderId)) {
            this.optimisticUpdates.delete(orderId);
        }
        
        // 記錄性能數據
        if (!this.performanceMetrics) {
            this.performanceMetrics = [];
        }
        
        this.performanceMetrics.push({
            operation: operation,
            orderId: orderId,
            duration: duration,
            success: true,
            timestamp: new Date().toISOString()
        });
        
        // 保持性能數據大小
        if (this.performanceMetrics.length > 100) {
            this.performanceMetrics = this.performanceMetrics.slice(-50);
        }
    }
    
    /**
     * 記錄操作失敗
     */
    recordOperationFailure(operation, orderId, error) {
        console.error(`❌ 操作失敗: ${operation} 訂單 #${orderId}, 錯誤: ${error}`);
        
        // 記錄性能數據
        if (!this.performanceMetrics) {
            this.performanceMetrics = [];
        }
        
        this.performanceMetrics.push({
            operation: operation,
            orderId: orderId,
            error: error,
            success: false,
            timestamp: new Date().toISOString()
        });
        
        // 保持性能數據大小
        if (this.performanceMetrics.length > 100) {
            this.performanceMetrics = this.performanceMetrics.slice(-50);
        }
    }
    
    /**
     * 獲取性能指標
     */
    getPerformanceMetrics() {
        if (!this.performanceMetrics) {
            return {
                totalOperations: 0,
                successRate: 0,
                averageDuration: 0,
                recentOperations: []
            };
        }
        
        const successfulOps = this.performanceMetrics.filter(m => m.success);
        const failedOps = this.performanceMetrics.filter(m => !m.success);
        const totalDuration = successfulOps.reduce((sum, m) => sum + (m.duration || 0), 0);
        
        return {
            totalOperations: this.performanceMetrics.length,
            successfulOperations: successfulOps.length,
            failedOperations: failedOps.length,
            successRate: this.performanceMetrics.length > 0 ? 
                (successfulOps.length / this.performanceMetrics.length * 100).toFixed(1) : 0,
            averageDuration: successfulOps.length > 0 ? 
                Math.round(totalDuration / successfulOps.length) : 0,
            recentOperations: this.performanceMetrics.slice(-10)
        };
    }
    
    // ==================== 清理方法 ====================
    
    cleanup() {
        console.log('🔄 清理隊列管理器...');
        
        // 清理所有計時器
        this.remainingTimers.forEach(timer => clearInterval(timer));
        this.remainingTimers.clear();
        
        // 清理樂觀更新記錄
        if (this.optimisticUpdates) {
            this.optimisticUpdates.clear();
        }
        
        console.log('✅ 隊列管理器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.QueueManager = QueueManager;
}