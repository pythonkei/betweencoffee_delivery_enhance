// static/js/staff-order-management/renderers-v2/payment-pending-renderer-v2.js
// ==================== 待確認付款渲染器 v2 ====================
// 基於 BaseOrderRendererV2 重構
// UI 與原始 PaymentPendingRenderer 完全一致
// 負責顯示待確認付款的訂單（FPS/現金支付）
// 提供「確認 FPS 付款」/「確認現金付款」和「取消訂單」操作按鈕

/**
 * PaymentPendingRendererV2 - 待確認付款訂單渲染器
 * @class
 * @extends BaseOrderRendererV2
 * 
 * 負責顯示待確認付款的訂單（FPS/現金支付），提供：
 * - 確認 FPS 付款
 * - 確認現金付款
 * - 取消訂單
 * 
 * UI 與原始 PaymentPendingRenderer 完全一致。
 */
class PaymentPendingRendererV2 extends BaseOrderRendererV2 {
    /**
     * @constructor
     * 初始化待確認付款渲染器，設定：
     * - orderType: 'payment_pending'
     * - 容器 ID: 'payment-pending-orders-list'
     * - 空狀態 ID: 'payment-pending-empty'
     * - 啟用排序，禁用倒計時
     * - 刷新間隔 15 秒
     */
    constructor() {
        super('payment_pending', 'payment-pending', 'payment-pending-orders-list', 'payment-pending-empty', {
            enableCountdown: false,
            enableSorting: true,
            refreshInterval: 15000,
            dataKey: 'payment_pending_orders'
        });

        /** @type {Object|null} API 服務實例 */
        this.apiService = window.apiService || null;
    }

    // ==================== 核心方法：創建訂單元素 ====================

    /**
     * 創建待確認付款訂單的 DOM 元素
     * @override
     * @param {Object} order - 訂單數據物件
     * @param {number|string} order.id - 訂單 ID
     * @param {number|string} [order.order_id] - 備用訂單 ID
     * @param {number} [order.coffee_count] - 咖啡數量
     * @param {number} [order.bean_count] - 咖啡豆數量
     * @param {boolean} [order.is_quick_order] - 是否為快速訂單
     * @param {boolean} [order.is_mixed_order] - 是否為混合訂單
     * @returns {HTMLElement} 訂單卡片 DOM 元素
     */
    createOrderElement(order) {
        const div = this.createOrderCardDiv(order);
        
        // 設定 data 屬性（與原始 PaymentPendingRenderer 一致）
        const orderId = this._getOrderId(order);
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

    /**
     * 構建待確認付款訂單的 HTML 內容
     * @private
     * @param {Object} order - 訂單數據物件
     * @returns {string} 訂單卡片的 HTML 字串
     */
    _buildOrderHTML(order) {
        const orderId = this._getOrderId(order);
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
                                <div class="bc-options-row">${item.cup_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">water_full</span> 杯量: <span class="ov">${item.cup_level_cn}</span></span>` : ''}${(item.strength_level_cn || item.strength_level) ? `<span class="option-item"><span class="icon material-symbols-outlined">bolt</span> 濃度: <span class="ov">${item.strength_level_cn || item.strength_level}</span></span>` : ''}${item.milk_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">humidity_mid</span> 奶量: <span class="ov">${item.milk_level_cn}</span></span>` : ''}${item.grinding_level_cn ? `<span class="option-item">研磨: <span class="ov">${item.grinding_level_cn}</span></span>` : ''}${item.weight_cn ? `<span class="option-item">重量: <span class="ov">${item.weight_cn}</span></span>` : ''}</div>
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
                ${orderTypeBadges}${paymentMethodBadge}
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

    /**
     * 綁定訂單卡片的操作按鈕事件
     * @private
     * @param {HTMLElement} div - 訂單卡片 DOM 元素
     * @param {Object} order - 訂單數據物件
     */
    _bindOrderActions(div, order) {
        // 確認 FPS 付款按鈕
        const confirmFpsBtn = div.querySelector('.btn-confirm-fps-payment');
        if (confirmFpsBtn) {
            this._addManagedListener(confirmFpsBtn, 'click', (e) => {
                e.stopPropagation();
                this._handleConfirmPayment(order, 'fps');
            });
        }

        // 確認現金付款按鈕
        const confirmCashBtn = div.querySelector('.btn-confirm-cash-payment');
        if (confirmCashBtn) {
            this._addManagedListener(confirmCashBtn, 'click', (e) => {
                e.stopPropagation();
                this._handleConfirmPayment(order, 'cash');
            });
        }

        // 取消訂單按鈕
        const cancelBtn = div.querySelector('.btn-cancel-order');
        if (cancelBtn) {
            this._addManagedListener(cancelBtn, 'click', (e) => {
                e.stopPropagation();
                this._handleCancelOrder(order);
            });
        }
    }

    // ==================== 操作處理 ====================

    /**
     * 處理確認付款操作
     * @private
     * @async
     * @param {Object} order - 訂單數據物件
     * @param {string} paymentMethod - 支付方式 ('fps' | 'cash')
     */
    async _handleConfirmPayment(order, paymentMethod) {
        const orderNumber = this._getOrderNumber(order);
        const orderId = this._getOrderId(order);

        if (paymentMethod === 'fps') {
            await this._executeOrderAction(order, `/eshop/api/fps/confirm-payment/${orderId}/`, {
                successMessage: `✅ 訂單 #${orderNumber} 付款已確認`,
                failMessage: '❌ 確認付款失敗',
                errorMessage: '❌ 確認付款時發生錯誤'
            });
        } else if (paymentMethod === 'cash') {
            await this._executeOrderAction(order, `/eshop/api/cash/confirm-payment/${orderId}/`, {
                successMessage: `✅ 訂單 #${orderNumber} 付款已確認`,
                failMessage: '❌ 確認付款失敗',
                errorMessage: '❌ 確認付款時發生錯誤'
            });
        }
    }

    /**
     * 處理取消訂單操作
     * @private
     * @async
     * @param {Object} order - 訂單數據物件
     */
    async _handleCancelOrder(order) {
        const orderNumber = this._getOrderNumber(order);

        await this._executeOrderAction(order, `/eshop/api/orders/{orderId}/cancel/`, {
            successMessage: `✅ 訂單 #${orderNumber} 已取消`,
            failMessage: '❌ 取消訂單失敗',
            errorMessage: '❌ 取消訂單時發生錯誤',
            requireConfirm: true,
            confirmMessage: `確定要取消訂單 #${orderNumber} 嗎？`
        });
    }

    // ==================== 排序覆蓋 ====================

    /**
     * 按創建時間排序待確認付款訂單（最早的在最前面）
     * @override
     * @param {Object[]} orders - 訂單數據陣列
     * @returns {Object[]} 排序後的訂單陣列
     */
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
