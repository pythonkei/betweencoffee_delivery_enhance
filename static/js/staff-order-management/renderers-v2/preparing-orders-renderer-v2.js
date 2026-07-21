// static/js/staff-order-management/renderers-v2/preparing-orders-renderer-v2.js
// ==================== 製作中訂單渲染器 v2 ====================
// 基於 BaseOrderRendererV2 重構
// UI 與原始 PreparingOrdersRendererEnhanced 完全一致
// 負責顯示正在製作的訂單
// 提供倒計時顯示、完成製作、加速處理操作

class PreparingOrdersRendererV2 extends BaseOrderRendererV2 {
    constructor() {
        // 使用 countdown-active-content 作為主要容器（對應 HTML 中的進行中子標籤頁）
        super('preparing', 'preparing', 'countdown-active-content', 'countdown-active-empty', {
            enableCountdown: true,
            enableSorting: true,
            refreshInterval: 15000,
            dataKey: 'preparing_orders',
            // 第二個子標籤頁（已完成）的容器 ID
            completedListId: 'countdown-completed-content',
            completedEmptyId: 'countdown-completed-empty'
        });

        this.apiService = window.apiService || null;

        // 第二個子標籤頁的容器和空狀態元素
        this.completedListId = 'countdown-completed-content';
        this.completedEmptyId = 'countdown-completed-empty';
    }

    // ==================== 覆蓋 renderOrders：分發到兩個子標籤頁 ====================

    /**
     * 覆蓋父類的 renderOrders 方法，將訂單分發到兩個子標籤頁：
     *   - countdown-active-content（進行中）：倒計時尚未結束
     *   - countdown-completed-content（已完成）：倒計時已結束
     */
    renderOrders(orders) {
        const activeList = document.getElementById(this.listId);
        const completedList = document.getElementById(this.completedListId);
        const activeEmpty = document.getElementById(this.emptyId);
        const completedEmpty = document.getElementById(this.completedEmptyId);

        if (!activeList || !completedList) {
            console.warn(`⚠️ ${this.orderType} 子標籤頁容器未找到，100ms後重試`);
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }

        // 清理現有計時器
        this.cleanupTimers();

        // 清空兩個容器
        activeList.innerHTML = '';
        completedList.innerHTML = '';
        this.currentOrders.clear();

        // 檢查是否有訂單
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單列表為空`);
            this._showBothEmpty();
            return;
        }

        console.log(`🎨 渲染 ${this.orderType} 訂單: ${orders.length} 個`);

        // beforeRender 鉤子
        this.beforeRender(orders);

        // 對訂單進行排序
        const sortedOrders = this.sortOrders(orders);

        // 將訂單分為「進行中」和「已完成」兩組
        const now = new Date();
        const activeOrders = [];
        const completedOrders = [];

        sortedOrders.forEach(order => {
            const estimatedTime = order.estimated_completion_time_iso || order.estimated_ready_time_iso || '';
            let isCountdownCompleted = false;

            if (estimatedTime) {
                try {
                    const estimatedDate = new Date(estimatedTime);
                    isCountdownCompleted = estimatedDate <= now;
                } catch (e) {
                    // 時間解析失敗，預設為進行中
                }
            }

            if (isCountdownCompleted) {
                completedOrders.push(order);
            } else {
                activeOrders.push(order);
            }
        });

        console.log(`📊 進行中: ${activeOrders.length} 個, 已完成: ${completedOrders.length} 個`);

        // 使用 DocumentFragment 提高性能
        const activeFragment = document.createDocumentFragment();
        const completedFragment = document.createDocumentFragment();

        // 渲染進行中的訂單
        activeOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            activeFragment.appendChild(orderElement);
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });

        // 渲染已完成的訂單
        completedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            completedFragment.appendChild(orderElement);
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });

        // 一次性添加到 DOM
        activeList.appendChild(activeFragment);
        completedList.appendChild(completedFragment);

        // 控制進行中容器的顯示/隱藏
        if (activeOrders.length > 0) {
            activeList.style.display = 'block';
            if (activeEmpty) activeEmpty.style.display = 'none';
        } else {
            activeList.style.display = 'none';
            if (activeEmpty) activeEmpty.style.display = 'block';
        }

        // 控制已完成容器的顯示/隱藏
        if (completedOrders.length > 0) {
            completedList.style.display = 'block';
            if (completedEmpty) completedEmpty.style.display = 'none';
        } else {
            completedList.style.display = 'none';
            if (completedEmpty) completedEmpty.style.display = 'block';
        }

        // 初始化倒計時（僅對進行中的訂單）
        if (this.options.enableCountdown) {
            this.initCountdowns();
        }

        // 更新子標籤頁徽章
        this._updateSubtabBadges();

        // 更新最後更新時間
        this.updateLastUpdateTime();

        // afterRender 鉤子
        this.afterRender(orders);

        console.log(`✅ ${this.orderType} 訂單渲染完成`);
    }

    /**
     * 覆蓋父類的 showEmpty 方法，同時顯示兩個子標籤頁的空狀態
     */
    showEmpty() {
        this._showBothEmpty();
    }

    /**
     * 同時顯示兩個子標籤頁的空狀態
     * @private
     */
    _showBothEmpty() {
        const activeList = document.getElementById(this.listId);
        const completedList = document.getElementById(this.completedListId);
        const activeEmpty = document.getElementById(this.emptyId);
        const completedEmpty = document.getElementById(this.completedEmptyId);

        if (activeList) {
            activeList.innerHTML = '';
            activeList.style.display = 'none';
        }
        if (completedList) {
            completedList.innerHTML = '';
            completedList.style.display = 'none';
        }
        if (activeEmpty) {
            activeEmpty.style.display = 'block';
        }
        if (completedEmpty) {
            completedEmpty.style.display = 'block';
        }

        console.log(`📭 顯示 ${this.orderType} 兩個子標籤頁空狀態`);
    }

    // ==================== 核心方法：創建訂單元素 ====================

    createOrderElement(order) {
        const div = this.createOrderCardDiv(order);
        
        // 設定 data 屬性（與原始 PreparingOrdersRendererEnhanced 一致）
        const orderId = order.id || order.order_id;
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        div.setAttribute('data-status', 'preparing');
        
        // sub-status: 根據訂單類型決定
        let subStatus = 'normal';
        if (order.is_quick_order) {
            subStatus = 'quick';
        } else if (isMixedOrder) {
            subStatus = 'mixed';
        }
        div.setAttribute('data-sub-status', subStatus);
        
        // data-type: quick / normal
        div.setAttribute('data-type', order.is_quick_order ? 'quick' : 'normal');
        
        // data-order-type: quick / mixed / single
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }
        div.setAttribute('data-order-type', orderTypeAttr);
        
        // data-created: 創建時間
        const createdAt = order.created_at_iso || order.created_at || '';
        if (createdAt) {
            div.setAttribute('data-created', createdAt);
        }
        
        // data-estimated-ready: 預計完成時間
        const estimatedReady = order.estimated_completion_time_iso || order.estimated_ready_time_iso || '';
        if (estimatedReady) {
            div.setAttribute('data-estimated-ready', estimatedReady);
        }
        
        div.innerHTML = this._buildOrderHTML(order);
        this._bindOrderActions(div, order);
        return div;
    }

    // ==================== 構建訂單 HTML（與原始 PreparingOrdersRendererEnhanced.renderOrderCard 一致） ====================

    _buildOrderHTML(order) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || 'N/A';
        const customerName = order.name || order.customer_name || '未知';
        const totalPrice = parseFloat(order.total_price || 0).toFixed(2);
        const createdAt = order.created_at || '';
        const items = order.items || [];
        const itemCount = items.length || order.items_count || 0;
        const phone = order.phone || '';
        const baristaName = order.barista_name || order.barista || '';
        const estimatedTime = order.estimated_completion_time_iso || order.estimated_ready_time_iso || '';
        const isExpedited = order.is_expedited || false;

        // 格式化時間
        const orderTime = this.formatOrderTime(createdAt);

        // 格式化電話
        const formattedPhone = this.formatPhoneNumber(phone);

        // 渲染商品項目
        let itemsHTML = '';
        if (items.length > 0) {
            items.forEach(item => {
                const itemPrice = parseFloat(item.price || 0).toFixed(2);
                const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
                const itemImage = item.image || this.getDefaultImage(item.type);

                itemsHTML += `
                    <div class="d-flex align-items-center mb-3">
                        <div class="mr-3">
                            <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 105px; height: 110px;">
                                <img src="${itemImage}" 
                                    alt="${item.name || '商品'}" 
                                    class="img-fluid" 
                                    style="max-height: 96px;">
                            </div>
                        </div>
                        <div class="flex-grow-1">
                            <p class="h5 mb-1">${item.name || '商品'}</p>
                            <p class="card-text-md mb-0">
                                數量: ${item.quantity || 1} 
                            </p>
                            <div class="card-text-md">
                                ${[item.cup_level_cn ? `杯型: ${item.cup_level_cn}` : '', item.milk_level_cn ? `牛奶: ${item.milk_level_cn}` : ''].filter(Boolean).join('&nbsp;&nbsp;')}${(item.cup_level_cn || item.milk_level_cn) && (item.grinding_level_cn || item.weight_cn) ? '&nbsp;&nbsp;&nbsp;' : ''}${[item.grinding_level_cn ? `研磨: ${item.grinding_level_cn}` : '', item.weight_cn ? `重量: ${item.weight_cn}` : ''].filter(Boolean).join('&nbsp;&nbsp;')}
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

        // 訂單類型徽章
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);

        let orderTypeBadges = '';
        if (order.is_quick_order) {
            orderTypeBadges = `
                <span class="badge order-type-badge" data-order-type="quick">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        } else if (isMixedOrder) {
            orderTypeBadges = `
                <span class="badge order-type-badge" data-order-type="mixed">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        } else {
            orderTypeBadges = `
                <span class="badge order-type-badge" data-order-type="single">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }

        // 加速徽章
        let expediteBadge = '';
        if (isExpedited) {
            expediteBadge = `
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-bolt mr-1"></i>加速中
                </span>
            `;
        }

        // 隊列位置徽章
        let queuePositionBadge = '';
        if (order.position) {
            queuePositionBadge = `
                <span class="badge badge-info ml-1">
                    <i class="fas fa-list-ol mr-1"></i>隊列位置: ${order.position}
                </span>
            `;
        }

        // 商品數量文字 + 產品類型徽章
        let itemsDisplayHTML = (itemCount > 0 ? itemCount + '項商品' : '0項商品');
        if (coffeeCount > 0) {
            itemsDisplayHTML += ` - <span class="order-product-badge">${coffeeCount}杯咖啡</span>`;
        }
        if (beanCount > 0) {
            if (coffeeCount > 0) {
                itemsDisplayHTML += ` <span class="order-product-badge">${beanCount}包咖啡豆</span>`;
            } else {
                itemsDisplayHTML += ` - <span class="order-product-badge">${beanCount}包咖啡豆</span>`;
            }
        }

        // 支付方式徽章
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

        // 咖啡師徽章
        let baristaBadge = '';
        if (baristaName) {
            baristaBadge = `
                <span class="badge badge-barista ml-1">
                    <i class="fas fa-user mr-1"></i>${baristaName}
                </span>
            `;
        }

        // 決定訂單類型屬性值
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }

        // 判斷訂單是否已完成（倒計時已結束）
        const now = new Date();
        let isCountdownCompleted = false;
        if (estimatedTime) {
            try {
                const estimatedDate = new Date(estimatedTime);
                isCountdownCompleted = estimatedDate <= now;
            } catch (e) {
                // 時間解析失敗，預設為進行中
            }
        }

        // 倒計時 HTML（僅進行中訂單顯示）
        let countdownHTML = '';
        if (estimatedTime && !isCountdownCompleted) {
            countdownHTML = `
                <div class="countdown-badge badge badge-secondary mb-2"
                     data-order-id="${orderId}"
                     data-estimated-time="${estimatedTime}">
                    <i class="fas fa-hourglass-half mr-1"></i>
                    <span class="countdown-text">計算中...</span>
                </div>
            `;
        }

        // 已完成時間顯示（僅已完成訂單顯示）
        let completedTimeDisplay = '';
        if (isCountdownCompleted && estimatedTime) {
            let completedText = '已完成';
            if (window.TimeUtils) {
                try {
                    const estimatedDate = new Date(estimatedTime);
                    completedText = `已完成: ${window.TimeUtils.formatHKTimeOnly(estimatedDate)}`;
                } catch (e) {
                    completedText = '已完成';
                }
            }
            completedTimeDisplay = `
                <span class="badge badge-completed ml-1">
                    <i class="fas fa-check mr-1"></i>${completedText}
                </span>
            `;
        }

        // 底部狀態資訊區塊
        let footerStatusHTML = '';
        if (isCountdownCompleted) {
            // 已完成訂單：顯示「已完成」狀態，無操作按鈕
            footerStatusHTML = `
                <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                    <div>
                        ${completedTimeDisplay}
                        <div class="mt-1">
                            <span class="text-success">
                                <i class="fas fa-check-circle mr-1"></i>訂單已完成
                            </span>
                            ${baristaBadge}
                        </div>
                    </div>
                </div>
            `;
        } else {
            // 進行中訂單：顯示倒計時 + 製作中狀態 + 操作按鈕
            footerStatusHTML = `
                <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                    <div>
                        ${countdownHTML}
                        <div class="mt-1">
                            <span class="text-info">
                                <i class="fas fa-mug-hot mr-1"></i>製作中
                            </span>
                            ${baristaBadge}
                        </div>
                    </div>
                    <div class="d-flex align-items-center">
                        <button class="btn btn-success btn-sm mr-2 btn-mark-ready" 
                                data-order-id="${orderId}"
                                title="標記為已就緒">
                            <i class="fas fa-check mr-1"></i>完成製作
                        </button>
                        <button class="btn btn-outline-warning btn-sm btn-expedite" 
                                data-order-id="${orderId}"
                                title="加速處理此訂單">
                            <i class="fas fa-bolt mr-1"></i>加速
                        </button>
                    </div>
                </div>
            `;
        }

        return `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-3">
                <div class="mt-2">
                    ${queuePositionBadge}
                    ${expediteBadge}
                </div>
            </div>

            <div class="order-items">
                ${itemsHTML}
                <div class="mt-4">
                    <span class="card-text-md">${itemsDisplayHTML}</span>
                </div>
            </div>
            
            <div class="d-flex justify-content-between align-items-center mt-5 mb-2 pt-4 border-top">
                <div>
                    <h5>訂單編號: #${orderId}</h5>
                    <p class="mb-0">
                        訂單時間: ${orderTime}
                    </p>
                </div>
                <div class="text-right">
                    <span class="h5 pr-2">$${totalPrice}</span>
                </div>
            </div>

            <div class="d-flex justify-content-between align-items-center">
                <div class="mb-2 card-text-md">
                    <div class="mb-2">
                        <span class="card-text-md badge badge-dark"><i class="fas fa-user mr-2"></i>取餐碼:${pickupCode}</span>
                    </div>
                    <p class="card-text-md mb-2">
                        客戶: ${customerName} <span class="ml-3"></span>
                        電話: ${formattedPhone}
                    </p>
                </div>
            </div>

            ${footerStatusHTML}
        `;
    }

    // ==================== 綁定操作按鈕 ====================

    _bindOrderActions(div, order) {
        const orderId = order.id || order.order_id;

        // 完成製作按鈕
        const readyBtn = div.querySelector('.btn-mark-ready');
        if (readyBtn) {
            readyBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleMarkReady(order);
            });
        }

        // 加速處理按鈕
        const expediteBtn = div.querySelector('.btn-expedite');
        if (expediteBtn) {
            expediteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleExpedite(order);
            });
        }
    }

    // ==================== 操作處理 ====================

    async _handleMarkReady(order) {
        if (this.isProcessingAction) return;
        this.isProcessingAction = true;

        try {
            const url = `/eshop/api/orders/${order.id}/mark-ready/`;
            const result = await this._apiPost(url, { order_id: order.id });

            if (result && result.success) {
                this.showToast(`✅ 訂單 #${order.order_number || order.id} 已標記為就緒`, 'success');
                this.forceRefresh();
            } else {
                this.showToast(`❌ 標記就緒失敗: ${result?.error || '未知錯誤'}`, 'error');
            }
        } catch (error) {
            console.error('❌ 標記就緒錯誤:', error);
            this.showToast('❌ 標記就緒時發生錯誤', 'error');
        } finally {
            this.isProcessingAction = false;
        }
    }

    async _handleExpedite(order) {
        if (this.isProcessingAction) return;
        this.isProcessingAction = true;

        try {
            const url = `/eshop/api/orders/${order.id}/expedite/`;
            const result = await this._apiPost(url, { order_id: order.id });

            if (result && result.success) {
                this.showToast(`✅ 訂單 #${order.order_number || order.id} 已加速`, 'success');
                this.forceRefresh();
            } else {
                this.showToast(`❌ 加速失敗: ${result?.error || '未知錯誤'}`, 'error');
            }
        } catch (error) {
            console.error('❌ 加速錯誤:', error);
            this.showToast('❌ 加速時發生錯誤', 'error');
        } finally {
            this.isProcessingAction = false;
        }
    }

    // ==================== API 請求 ====================

    async _apiPost(url, data) {
        if (this.apiService && typeof this.apiService.post === 'function') {
            return await this.apiService.post(url, data);
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this._getCSRFToken()
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('❌ API 請求失敗:', error);
            throw error;
        }
    }

    _getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return '';
    }

    // ==================== 排序覆蓋 ====================

    sortOrders(orders) {
        return [...orders].sort((a, b) => {
            // 第一優先級：快速訂單
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;
            if (isQuickA !== isQuickB) {
                return isQuickB ? 1 : -1;
            }

            // 第二優先級：加速訂單
            const isExpA = a.is_expedited || false;
            const isExpB = b.is_expedited || false;
            if (isExpA !== isExpB) {
                return isExpB ? 1 : -1;
            }

            // 第三優先級：按預計完成時間排序
            const timeA = a.estimated_completion_time_iso || a.estimated_ready_time_iso || '';
            const timeB = b.estimated_completion_time_iso || b.estimated_ready_time_iso || '';
            if (timeA && timeB) {
                return new Date(timeA) - new Date(timeB);
            }

            // 第四優先級：按創建時間排序
            const createdA = a.created_at_iso || a.created_at || '';
            const createdB = b.created_at_iso || b.created_at || '';
            return new Date(createdA) - new Date(createdB);
        });
    }

    // ==================== 覆蓋 markCountdownCompleted：倒計時結束時直接移動 DOM ====================

    /**
     * 覆蓋父類的 markCountdownCompleted 方法。
     * 當倒計時結束時，除了更新徽章樣式外，還直接將訂單卡片
     * 從「進行中」容器移動到「已完成」容器，實現即時移動。
     */
    markCountdownCompleted(badge, estimatedTimeStr) {
        // 先調用父類方法更新徽章樣式
        super.markCountdownCompleted(badge, estimatedTimeStr);

        // 找到訂單卡片元素
        const orderCard = badge.closest('[data-status="preparing"]');
        if (!orderCard) return;

        const activeList = document.getElementById(this.listId);
        const completedList = document.getElementById(this.completedListId);
        const activeEmpty = document.getElementById(this.emptyId);
        const completedEmpty = document.getElementById(this.completedEmptyId);

        if (!activeList || !completedList) return;

        // 更新卡片底部 HTML：將「製作中」狀態改為「已完成」狀態
        // 移除倒計時徽章和操作按鈕，顯示已完成狀態
        const footerSection = orderCard.querySelector('.d-flex.justify-content-between.align-items-center.mt-3.pt-3.border-top');
        if (footerSection) {
            // 建立已完成狀態的底部 HTML
            let completedText = '已完成';
            if (window.TimeUtils && estimatedTimeStr) {
                try {
                    const estimatedDate = new Date(estimatedTimeStr);
                    completedText = `已完成: ${window.TimeUtils.formatHKTimeOnly(estimatedDate)}`;
                } catch (e) {
                    completedText = '已完成';
                }
            }

            // 取得咖啡師名稱（如果有的話）
            const baristaBadge = orderCard.querySelector('.badge-barista');
            const baristaHTML = baristaBadge ? baristaBadge.outerHTML : '';

            footerSection.innerHTML = `
                <div>
                    <span class="badge badge-completed ml-1">
                        <i class="fas fa-check mr-1"></i>${completedText}
                    </span>
                    <div class="mt-1">
                        <span class="text-success">
                            <i class="fas fa-check-circle mr-1"></i>訂單已完成
                        </span>
                        ${baristaHTML}
                    </div>
                </div>
            `;
        }

        // 從進行中容器移動到已完成容器
        activeList.removeChild(orderCard);
        completedList.appendChild(orderCard);

        // 更新進行中容器的顯示狀態
        if (activeList.children.length === 0) {
            activeList.style.display = 'none';
            if (activeEmpty) activeEmpty.style.display = 'block';
        }

        // 更新已完成容器的顯示狀態
        if (completedList.style.display === 'none' || completedList.children.length === 1) {
            completedList.style.display = 'block';
            if (completedEmpty) completedEmpty.style.display = 'none';
        }

        // 更新子標籤頁徽章
        this._updateSubtabBadges();

        console.log(`⏰ 倒計時結束，訂單已即時移動到「已完成」子標籤頁，底部狀態已更新`);
    }

    // ==================== 更新子標籤頁徽章 ====================

    /**
     * 更新 countdown-active-badge 和 countdown-completed-badge 子徽章數字。
     * 這兩個子徽章不在 BadgeManager 的管理範圍內，由 PreparingOrdersRendererV2 自行維護。
     */
    _updateSubtabBadges() {
        const activeList = document.getElementById(this.listId);
        const completedList = document.getElementById(this.completedListId);
        const activeBadge = document.getElementById('countdown-active-badge');
        const completedBadge = document.getElementById('countdown-completed-badge');

        if (activeBadge && activeList) {
            const count = activeList.children.length || 0;
            activeBadge.textContent = count;
            activeBadge.style.display = 'inline-block';
            activeBadge.style.visibility = 'visible';
        }
        if (completedBadge && completedList) {
            const count = completedList.children.length || 0;
            completedBadge.textContent = count;
            completedBadge.style.display = 'inline-block';
            completedBadge.style.visibility = 'visible';
        }
    }

    // ==================== afterRender 鉤子 ====================

    afterRender(orders) {
        // 初始化倒計時（由 BaseOrderRendererV2 的 renderOrders 調用）
    }
}
