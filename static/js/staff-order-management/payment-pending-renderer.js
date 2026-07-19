/**
 * 待確認付款訂單渲染器
 * 
 * 功能：
 * - 從 UnifiedDataManager 獲取 payment_pending_orders 數據
 * - 渲染 FPS 待確認付款訂單卡片
 * - 提供「確認 FPS 付款」和「取消訂單」按鈕
 * 
 * 依賴：
 * - window.unifiedDataManager
 * - window.queueManager (用於 confirmFpsPayment)
 */

class PaymentPendingRenderer {
    constructor() {
        this.containerId = 'payment-pending-orders-list';
        this.emptyId = 'payment-pending-orders-empty';
        this.lastUpdateId = 'payment-pending-orders-last-update';
        this.refreshBtnId = 'refresh-payment-pending-orders-btn';
        this.name = 'PaymentPendingRenderer';
        
        console.log('🔄 PaymentPendingRenderer 初始化...');
        this.bindEvents();
    }
    
    /**
     * 綁定事件
     */
    bindEvents() {
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', (event) => {
            if (event.detail && event.detail.data) {
                this.render(event.detail.data);
            }
        });
        
        // 監聽刷新按鈕
        const refreshBtn = document.getElementById(this.refreshBtnId);
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
            });
        }
    }
    
    /**
     * 刷新數據
     */
    refresh() {
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData();
        }
    }
    
    /**
     * 渲染待確認付款訂單
     * 
     * @param {Object} data - 統一數據對象
     */
    render(data) {
        const container = document.getElementById(this.containerId);
        const emptyEl = document.getElementById(this.emptyId);
        
        if (!container) {
            console.warn('⚠️ PaymentPendingRenderer: 容器元素不存在');
            return;
        }
        
        const orders = data.payment_pending_orders || [];
        
        // 更新最後更新時間
        const lastUpdateEl = document.getElementById(this.lastUpdateId);
        if (lastUpdateEl) {
            lastUpdateEl.textContent = new Date().toLocaleTimeString('zh-HK');
        }
        
        // 空狀態處理
        if (orders.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'block';
            return;
        }
        
        if (emptyEl) emptyEl.style.display = 'none';
        
        // 渲染訂單卡片
        let html = '';
        orders.forEach(order => {
            html += this.renderOrderCard(order);
        });
        
        container.innerHTML = html;
        
        // 綁定卡片按鈕事件
        this.bindCardEvents(orders);
    }
    
    /**
     * 渲染單個訂單卡片（與等待中卡片設計完全一致）
     * 
     * @param {Object} order - 訂單數據
     * @returns {string} HTML 字符串
     */
    renderOrderCard(order) {
        const orderId = order.id || order.order_id;
        const pickupCode = order.pickup_code || 'N/A';
        const customerName = order.name || order.customer_name || '未知';
        const totalPrice = parseFloat(order.total_price || 0).toFixed(2);
        const createdAt = order.created_at || '';
        const items = order.items || [];
        const itemCount = items.length || order.items_count || 0;
        const phone = order.phone || '';
        
        // 格式化時間
        const orderTime = window.TimeUtils ? 
            window.TimeUtils.formatOrderTime(createdAt, false) : 
            (createdAt ? (() => { try { return new Date(createdAt).toLocaleTimeString('zh-HK', { hour: '2-digit', minute: '2-digit' }); } catch(e) { return createdAt; } })() : '--:--');
        
        // 格式化電話
        const formattedPhone = window.CommonUtils ? 
            window.CommonUtils.formatPhoneNumber(phone) : phone;
        
        // 渲染商品項目（與等待中卡片一致）
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
        
        // ====== 商品數量文字 + 產品類型徽章（order-product-badge 樣式） ======
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
        
        // 決定訂單類型屬性值
        let orderTypeAttr = 'single';
        if (order.is_quick_order) {
            orderTypeAttr = 'quick';
        } else if (isMixedOrder) {
            orderTypeAttr = 'mixed';
        }
        
        return `
            <div class="order-item mb-5 p-5 rounded selectable" data-order-id="${orderId}" data-status="payment_pending" data-order-type="${orderTypeAttr}">
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
                            預計等待: ${order.wait_display || '計算中...'}
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

                <div class="d-flex justify-content-end align-items-center">
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
    
    /**
     * 獲取默認圖片
     * 
     * @param {string} itemType - 商品類型
     * @returns {string} 默認圖片路徑
     */
    getDefaultImage(itemType) {
        switch(itemType) {
            case 'coffee': return '/static/images/default-coffee.png';
            case 'bean': return '/static/images/default-beans.png';
            default: return '/static/images/default-product.png';
        }
    }
    
    /**
     * 綁定卡片按鈕事件
     * 
     * 注意：按鈕事件已由 QueueManager 的 initEventListeners 統一管理（事件委託），
     * 此處不再重複綁定，避免雙重處理。
     * 
     * @param {Array} orders - 訂單數據列表
     */
    bindCardEvents(orders) {
        // 事件已由 QueueManager 統一管理，此處不再重複綁定
        // 保留方法簽名以保持向後兼容
    }

    
}


// 註冊到全局
window.PaymentPendingRenderer = PaymentPendingRenderer;
