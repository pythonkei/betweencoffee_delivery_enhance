// static/js/staff-order-management/renderers-v2/payment-pending-renderer-v2.js
// ==================== 待確認付款渲染器 v2 ====================
// 基於 BaseOrderRendererV2 重構
// UI 與原始 PaymentPendingRenderer 完全一致
// 負責顯示待確認付款的訂單（FPS/現金支付）
// 提供「確認 FPS 付款」/「確認現金付款」和「取消訂單」操作按鈕

class PaymentPendingRendererV2 extends BaseOrderRendererV2 {
    constructor() {
        super('payment_pending', 'payment-pending', 'payment-pending-orders-list', 'payment-pending-empty', {
            enableCountdown: false,
            enableSorting: true,
            refreshInterval: 15000,
            dataKey: 'payment_pending_orders'
        });

        this.apiService = window.apiService || null;
    }

    // ==================== 核心方法：創建訂單元素 ====================

    createOrderElement(order) {
        const div = this.createOrderCardDiv(order);
        
        // 設定 data 屬性（與原始 PaymentPendingRenderer 一致）
        const orderId = order.id || order.order_id;
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        div.setAttribute('data-status', 'payment_pending');
        
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }
        div.setAttribute('data-order-type', orderTypeAttr);
        
        div.innerHTML = this._buildOrderHTML(order);
        this._bindOrderActions(div, order);
        return div;
    }

    // ==================== 構建訂單 HTML（與原始 PaymentPendingRenderer.renderOrderCard 一致） ====================

    _buildOrderHTML(order) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || 'N/A';
        const customerName = order.name || order.customer_name || '未知';
        const totalPrice = parseFloat(order.total_price || 0).toFixed(2);
        const createdAt = order.created_at || '';
        const items = order.items || [];
        const itemCount = items.length || order.items_count || 0;
        const phone = order.phone || '';

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
        const paymentMethod = order.payment_method || '';
        let paymentMethodBadge = '';
        if (paymentMethod) {
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

        // 決定訂單類型屬性值
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }

        // 預計等待
        const waitDisplay = order.wait_display || '計算中...';

        return `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-3">
                <div class="mt-2">
                    ${queuePositionBadge}
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
                        訂單時間: ${orderTime} <span class="ml-3"></span>
                        預計等待: ${waitDisplay}
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

            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-danger"><i class="fas fa-hourglass-half mr-1"></i>待確認付款</span>
                    <span class="ml-2 text-muted small">${orderTime}</span>
                    <span class="ml-2 badge badge-warning">${paymentMethod === 'cash' ? '現金' : 'FPS'} 待確認</span>
                </div>
                <div class="d-flex align-items-center">
                    ${order.payment_method === 'cash' ? `
                        <button class="btn btn-success btn-sm mr-2 btn-confirm-cash-payment" 
                                data-order-id="${orderId}"
                                title="確認現金付款已收到">
                            <i class="fas fa-money-bill-wave mr-1"></i>確認現金付款
                        </button>
                    ` : `
                        <button class="btn btn-success btn-sm mr-2 btn-confirm-fps-payment" 
                                data-order-id="${orderId}"
                                title="確認 FPS 付款已收到">
                            <i class="fas fa-check-circle mr-1"></i>確認 FPS 付款
                        </button>
                    `}
                    <button class="btn btn-outline-danger btn-sm btn-cancel-order" 
                            data-order-id="${orderId}"
                            title="取消此訂單">
                        <i class="fas fa-times mr-1"></i>取消訂單
                    </button>
                </div>
            </div>
        `;
    }

    // ==================== 綁定操作按鈕 ====================

    _bindOrderActions(div, order) {
        const orderId = order.id || order.order_id;

        // 確認 FPS 付款按鈕
        const confirmFpsBtn = div.querySelector('.btn-confirm-fps-payment');
        if (confirmFpsBtn) {
            confirmFpsBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleConfirmPayment(order, 'fps');
            });
        }

        // 確認現金付款按鈕
        const confirmCashBtn = div.querySelector('.btn-confirm-cash-payment');
        if (confirmCashBtn) {
            confirmCashBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleConfirmPayment(order, 'cash');
            });
        }

        // 取消訂單按鈕
        const cancelBtn = div.querySelector('.btn-cancel-order');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._handleCancelOrder(order);
            });
        }
    }

    // ==================== 操作處理 ====================

    async _handleConfirmPayment(order, paymentMethod) {
        if (this.isProcessingAction) return;
        this.isProcessingAction = true;

        try {
            let result;
            if (paymentMethod === 'fps') {
                result = await this._confirmFPSPayment(order);
            } else if (paymentMethod === 'cash') {
                result = await this._confirmCashPayment(order);
            }

            if (result && result.success) {
                this.showToast(`✅ 訂單 #${this._getOrderNumber(order)} 付款已確認`, 'success');
                this.forceRefresh();
            } else {
                this.showToast(`❌ 確認付款失敗: ${result?.error || '未知錯誤'}`, 'error');
            }
        } catch (error) {
            console.error('❌ 確認付款錯誤:', error);
            this.showToast('❌ 確認付款時發生錯誤', 'error');
        } finally {
            this.isProcessingAction = false;
        }
    }

    async _confirmFPSPayment(order) {
        const orderId = this._getOrderId(order);
        const url = `/eshop/api/fps/confirm-payment/${orderId}/`;
        return await this._apiPost(url, { order_id: orderId });
    }

    async _confirmCashPayment(order) {
        const orderId = this._getOrderId(order);
        const url = `/eshop/api/cash/confirm-payment/${orderId}/`;
        return await this._apiPost(url, { order_id: orderId });
    }

    async _handleCancelOrder(order) {
        if (this.isProcessingAction) return;

        if (!confirm(`確定要取消訂單 #${this._getOrderNumber(order)} 嗎？`)) {
            return;
        }

        this.isProcessingAction = true;

        try {
            const orderId = this._getOrderId(order);
            const url = `/eshop/api/orders/${orderId}/cancel/`;
            const result = await this._apiPost(url, { order_id: orderId });

            if (result && result.success) {
                this.showToast(`✅ 訂單 #${this._getOrderNumber(order)} 已取消`, 'success');
                this.forceRefresh();
            } else {
                this.showToast(`❌ 取消訂單失敗: ${result?.error || '未知錯誤'}`, 'error');
            }
        } catch (error) {
            console.error('❌ 取消訂單錯誤:', error);
            this.showToast('❌ 取消訂單時發生錯誤', 'error');
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
            const timeA = a.created_at_iso || a.created_at || '';
            const timeB = b.created_at_iso || b.created_at || '';
            return new Date(timeA) - new Date(timeB);
        });
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.PaymentPendingRendererV2 = PaymentPendingRendererV2;
    console.log('🌍 PaymentPendingRendererV2 已註冊到 window 對象');
}
