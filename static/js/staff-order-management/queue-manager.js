// static/js/staff-order-management/queue-manager.js
// ==================== 隊列管理器 - 統一數據流版本（外觀復古版） ====================

class QueueManager {
    constructor() {
        console.log('🔄 初始化隊列管理器（統一數據流版）...');
        
        // 只保留必要的屬性
        this.isLoading = false;
        this.remainingTimers = new Map();
        
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
        
        // ====== 關鍵修復：使用 window.TimeUtils 格式化香港時間 ======
        const orderTime = window.TimeUtils ? 
            window.TimeUtils.formatHKTimeOnly(order.created_at) : 
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
                    <strong>電話:</strong> ${order.phone || ''}
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
            if (this.isLoading) return;
            this.isLoading = true;
            
            const csrfToken = this.getCsrfToken();
            const response = await fetch(`/eshop/queue/start/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
        
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.showToast('✅ 已開始製作訂單 #' + orderId, 'success');
                    
                    // 觸發事件，讓統一數據管理器刷新數據
                    document.dispatchEvent(new CustomEvent('order_started_preparing', {
                        detail: { 
                            order_id: orderId,
                            estimated_ready_time: data.estimated_ready_time
                        }
                    }));
                    
                    // 觸發統一數據刷新
                    if (window.unifiedDataManager) {
                        setTimeout(() => window.unifiedDataManager.loadUnifiedData(), 500);
                    }
                } else {
                    throw new Error(data.message || '操作失敗');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('開始製作失敗:', error);
            this.showToast('❌ 操作失敗: ' + error.message, 'error');
        } finally {
            this.isLoading = false;
        }
    }
    
    async markAsReady(orderId) {
        try {
            if (this.isLoading) return;
            this.isLoading = true;
            
            const csrfToken = this.getCsrfToken();
            const response = await fetch(`/eshop/queue/ready/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
            
            if (response.ok) {
                const data = await response.json();
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
                    throw new Error(data.message || '操作失敗');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`標記訂單 #${orderId} 為就緒失敗:`, error);
            this.showToast(`❌ 操作失敗: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
        }
    }
    
    async markAsCollected(orderId) {
        try {
            if (this.isLoading) return;
            this.isLoading = true;
            
            const csrfToken = this.getCsrfToken();
            const response = await fetch(`/eshop/queue/collected/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({}),
            });
            
            if (response.ok) {
                const data = await response.json();
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
                    throw new Error(data.message || '操作失敗');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error(`標記訂單 #${orderId} 為已提取失敗:`, error);
            this.showToast(`❌ 操作失敗: ${error.message}`, 'error');
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
        // 使用已有的toast系統或簡單實現
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
    
    getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    showOrderDetails(orderId) {
        // 簡單實現，可以彈出模態框顯示詳細信息
        alert(`訂單 #${orderId} 的詳細信息\n\n此功能待完善...`);
    }
    
    // ==================== 清理方法 ====================
    
    cleanup() {
        console.log('🔄 清理隊列管理器...');
        
        // 清理所有計時器
        this.remainingTimers.forEach(timer => clearInterval(timer));
        this.remainingTimers.clear();
        
        console.log('✅ 隊列管理器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.QueueManager = QueueManager;
}