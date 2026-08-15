// static/js/staff-order-management/renderers-v2/completed-orders-renderer-v2.js
// ==================== 已完成訂單渲染器 v2 ====================
// 基於 BaseOrderRendererV2 重構
// UI 與原始 CompletedOrdersRenderer 完全一致
// 負責顯示已完成的訂單（顧客已取餐）
// 提供查看詳情功能

/**
 * CompletedOrdersRendererV2 - 已完成訂單渲染器
 * @class
 * @extends BaseOrderRendererV2
 * 
 * 負責顯示已完成的訂單（顧客已取餐），提供：
 * - 查看訂單詳情
 * 
 * UI 與原始 CompletedOrdersRenderer 完全一致。
 */
class CompletedOrdersRendererV2 extends BaseOrderRendererV2 {
    /**
     * @constructor
     * 初始化已完成訂單渲染器，設定：
     * - orderType: 'completed'
     * - 容器 ID: 'completed-orders-list'
     * - 空狀態 ID: 'completed-orders-empty'
     * - 啟用排序，禁用倒計時
     * - 刷新間隔 30 秒（較長，因為已完成訂單變化較少）
     */
    constructor() {
        super('completed', 'completed', 'completed-orders-list', 'completed-orders-empty', {
            enableCountdown: false,
            enableSorting: true,
            refreshInterval: 30000,
            dataKey: 'completed_orders'
        });

        /** @type {Object|null} API 服務實例 */
        this.apiService = window.apiService || null;
    }

    // ==================== 核心方法：創建訂單元素 ====================

    /**
     * 創建已完成訂單的 DOM 元素
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
        
        // 設定 data 屬性（與原始 CompletedOrdersRenderer 一致）
        const orderId = this._getOrderId(order);
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        div.setAttribute('data-status', 'completed');
        
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

    // ==================== 構建訂單 HTML（與原始 CompletedOrdersRenderer.renderOrderCard 一致） ====================

    /**
     * 構建已完成訂單的 HTML 內容
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
        const completedAt = order.completed_at || order.ready_at || '';
        const baristaName = order.barista_name || order.barista || '';
        const isExpedited = order.is_expedited || false;

        // 格式化時間
        const orderTime = this.formatOrderTime(createdAt);

        // 格式化電話
        const formattedPhone = this.formatPhoneNumber(phone);

        // 格式化完成時間
        let completedTimeDisplay = '';
        if (completedAt) {
            try {
                const date = new Date(completedAt);
                completedTimeDisplay = date.toLocaleTimeString('zh-HK', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                completedTimeDisplay = completedAt;
            }
        }

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
                            <div class="bc-order-item-img-container">
                                <img src="${itemImage}" 
                                    alt="${item.name || '商品'}" 
                                    class="img-fluid bc-order-item-img">
                            </div>
                        </div>
                        <div class="flex-grow-1">
                            <p class="h5 mb-1">${item.name || '商品'}</p>
                            <p class="card-text-md mb-0">
                                數量: ${item.quantity || 1} 
                            </p>
                            <div class="card-text-md">
                                <div class="bc-options-row">${item.cup_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">water_full</span> 杯量: <span class="ov">${item.cup_level_cn}</span></span>` : ''}${(item.strength_level_cn || item.strength_level) ? `<span class="option-item"><span class="icon material-symbols-outlined">bolt</span> 濃度: <span class="ov">${item.strength_level_cn || item.strength_level}</span></span>` : ''}${item.milk_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">humidity_mid</span> 奶量: <span class="ov">${item.milk_level_cn}</span></span>` : ''}${item.grinding_level_cn ? `<span class="option-item">研磨: <span class="ov">${item.grinding_level_cn}</span></span>` : ''}${item.weight_cn ? `<span class="option-item">重量: <span class="ov">${item.weight_cn}</span></span>` : ''}${Object.entries(item.extra_options_cn||{}).map(([k,v])=>`<span class="option-item"><span class="icon material-symbols-outlined">${(item.extra_options_icons||{})[k]||'add_circle'}</span> ${(item.extra_options_labels||{})[k]||k}: <span class="ov">${v}</span></span>`).join('')}</div>
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

        // 優先處理徽章
        let expediteBadge = '';
        if (isExpedited) {
            expediteBadge = `
                <span class="badge badge-expedited ml-1">
                    <i class="fas fa-bolt mr-1"></i>優先處理
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

        // 決定訂單類型屬性值
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }

        return `
            <!-- 訂單類型徽章（左上角） -->
            <div class="order-type-badges-container">
                ${orderTypeBadges}${paymentMethodBadge}
            </div>
            
            <div class="d-flex justify-content-between mb-3 mt-3">
                <div class="mt-2">
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

            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-muted">
                        <i class="fas fa-check-double mr-1"></i>已完成
                    </span>
                    ${baristaBadge}
                    ${completedTimeDisplay ? `<span class="ml-2 text-muted small">${completedTimeDisplay}</span>` : ''}
                </div>
                <div class="d-flex align-items-center">
                    <button class="btn btn-outline-warning btn-sm btn-view-details" 
                            data-order-id="${orderId}"
                            title="查看訂單詳情">
                        <i class="fas fa-info-circle mr-1"></i>詳情
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
        // 查看詳情按鈕
        const detailsBtn = div.querySelector('.btn-view-details');
        if (detailsBtn) {
            this._addManagedListener(detailsBtn, 'click', (e) => {
                e.stopPropagation();
                this._handleViewDetails(order);
            });
        }
    }

    // ==================== 操作處理 ====================

    /**
     * 處理查看訂單詳情操作
     * 觸發自定義事件 'order:view-details'，由主控制器處理詳情顯示
     * @private
     * @param {Object} order - 訂單數據物件
     */
    _handleViewDetails(order) {
        // 觸發事件，讓主控制器處理詳情顯示
        const event = new CustomEvent('order:view-details', {
            detail: { order: order }
        });
        document.dispatchEvent(event);
    }

    // ==================== 排序覆蓋 ====================

    /**
     * 按完成時間排序已完成訂單（最新的在前面）
     * @override
     * @param {Object[]} orders - 訂單數據陣列
     * @returns {Object[]} 排序後的訂單陣列
     */
    sortOrders(orders) {
        return [...orders].sort((a, b) => {
            const completedA = a.completed_at || a.ready_at || a.created_at_iso || a.created_at || '';
            const completedB = b.completed_at || b.ready_at || b.created_at_iso || b.created_at || '';
            return new Date(completedB) - new Date(completedA);
        });
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.CompletedOrdersRendererV2 = CompletedOrdersRendererV2;
    console.log('🌍 CompletedOrdersRendererV2 已註冊到 window 對象');
}
