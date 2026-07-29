// static/js/staff-order-management/renderers-v2/ready-orders-renderer-v2.js
// ==================== 已就緒訂單渲染器 v2 ====================
// 基於 BaseOrderRendererV2 重構
// UI 與原始 ReadyOrdersRenderer 完全一致
// 負責顯示已製作完成、等待顧客取餐的訂單
// 提供「標記為已提取」操作

/**
 * ReadyOrdersRendererV2 - 已就緒訂單渲染器
 * @class
 * @extends BaseOrderRendererV2
 * 
 * 負責顯示已製作完成、等待顧客取餐的訂單，提供：
 * - 標記為已提取
 * - 等待取餐時間即時更新（每 60 秒）
 * 
 * UI 與原始 ReadyOrdersRenderer 完全一致。
 */
class ReadyOrdersRendererV2 extends BaseOrderRendererV2 {
    /**
     * @constructor
     * 初始化已就緒訂單渲染器，設定：
     * - orderType: 'ready'
     * - 容器 ID: 'ready-orders-list'
     * - 空狀態 ID: 'ready-orders-empty'
     * - 啟用排序，禁用倒計時
     * - 刷新間隔 15 秒
     */
    constructor() {
        super('ready', 'ready', 'ready-orders-list', 'ready-orders-empty', {
            enableCountdown: false,
            enableSorting: true,
            refreshInterval: 15000,
            dataKey: 'ready_orders'
        });

        /** @type {Object|null} API 服務實例 */
        this.apiService = window.apiService || null;

        /** @type {number|null} 等待時間即時更新定時器 ID */
        this._waitingTimer = null;
    }

    // ==================== 核心方法：創建訂單元素 ====================

    /**
     * 創建已就緒訂單的 DOM 元素
     * @override
     * @param {Object} order - 訂單數據物件
     * @param {number|string} order.id - 訂單 ID
     * @param {number|string} [order.order_id] - 備用訂單 ID
     * @param {number} [order.coffee_count] - 咖啡數量
     * @param {number} [order.bean_count] - 咖啡豆數量
     * @param {boolean} [order.is_quick_order] - 是否為快速訂單
     * @param {boolean} [order.is_mixed_order] - 是否為混合訂單
     * @param {string} [order.ready_at] - 就緒時間 ISO 字串
     * @param {string} [order.completed_at] - 完成時間 ISO 字串
     * @returns {HTMLElement} 訂單卡片 DOM 元素
     */
    createOrderElement(order) {
        const div = this.createOrderCardDiv(order);
        
        // 設定 data 屬性（與原始 ReadyOrdersRenderer 一致）
        const orderId = this._getOrderId(order);
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        div.setAttribute('data-status', 'ready');
        // 儲存 ready_at 供等待時間即時更新使用
        div.setAttribute('data-ready-at', order.ready_at || order.completed_at || '');
        
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

    // ==================== 構建訂單 HTML（與原始 ReadyOrdersRenderer.renderOrderCard 一致） ====================

    /**
     * 構建已就緒訂單的 HTML 內容
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
        const readyAt = order.ready_at || order.completed_at || '';
        const baristaName = order.barista_name || order.barista || '';
        const isExpedited = order.is_expedited || false;

        // 格式化時間
        const orderTime = this.formatOrderTime(createdAt);

        // 格式化電話
        const formattedPhone = this.formatPhoneNumber(phone);

        // 計算等待取餐時間
        let waitingTimeDisplay = '';
        if (readyAt) {
            try {
                const readyTime = new Date(readyAt);
                const now = new Date();
                const diffMs = now - readyTime;
                const diffMinutes = Math.floor(diffMs / (1000 * 60));

                if (diffMinutes < 1) {
                    waitingTimeDisplay = '剛剛';
                } else if (diffMinutes < 60) {
                    waitingTimeDisplay = `${diffMinutes}分鐘`;
                } else {
                    const hours = Math.floor(diffMinutes / 60);
                    const mins = diffMinutes % 60;
                    waitingTimeDisplay = `${hours}小時${mins}分鐘`;
                }
            } catch (e) {
                waitingTimeDisplay = '';
            }
        }

        // 格式化就緒時間
        let readyTimeDisplay = '';
        if (readyAt) {
            try {
                const date = new Date(readyAt);
                readyTimeDisplay = date.toLocaleTimeString('zh-HK', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                readyTimeDisplay = readyAt;
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

        // 優先處理徽章
        let expediteBadge = '';
        if (isExpedited) {
            expediteBadge = `
                <span class="badge badge-warning ml-1">
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

            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
                <div>
                    <span class="text-success">
                        <i class="fas fa-check-circle mr-1"></i>已就緒
                    </span>
                    ${baristaBadge}
                    ${readyTimeDisplay ? `<span class="ml-2 text-muted small">${readyTimeDisplay}</span>` : ''}
                    ${waitingTimeDisplay ? `<span class="ml-2 badge badge-warning">等待取餐 ${waitingTimeDisplay}</span>` : ''}
                </div>
                <div class="d-flex align-items-center">
                    <button class="btn btn-success btn-sm btn-mark-completed" 
                            data-order-id="${orderId}"
                            title="標記為已提取">
                        <i class="fas fa-hand-paper mr-1"></i>已提取
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
        // 標記為已提取按鈕
        const completedBtn = div.querySelector('.btn-mark-completed');
        if (completedBtn) {
            this._addManagedListener(completedBtn, 'click', (e) => {
                e.stopPropagation();
                this._handleMarkCompleted(order);
            });
        }
    }

    // ==================== 操作處理 ====================

    /**
     * 處理標記為已提取操作
     * @private
     * @async
     * @param {Object} order - 訂單數據物件
     */
    async _handleMarkCompleted(order) {
        const orderNumber = this._getOrderNumber(order);

        await this._executeOrderAction(order, `/eshop/api/orders/{orderId}/mark-completed/`, {
            successMessage: `✅ 訂單 #${orderNumber} 已標記為已提取`,
            failMessage: '❌ 標記提取失敗',
            errorMessage: '❌ 標記提取時發生錯誤'
        });
    }

    // ==================== 排序覆蓋 ====================

    /**
     * 按就緒時間排序已就緒訂單（最早就緒的在最前面）
     * @override
     * @param {Object[]} orders - 訂單數據陣列
     * @returns {Object[]} 排序後的訂單陣列
     */
    sortOrders(orders) {
        return [...orders].sort((a, b) => {
            // 第一優先級：優先處理的訂單排前面
            const isExpA = a.is_expedited || false;
            const isExpB = b.is_expedited || false;
            if (isExpA !== isExpB) {
                return isExpB ? 1 : -1;
            }
            // 第二優先級：按就緒時間排序（最早的在前）
            const readyA = a.ready_at || a.completed_at || a.created_at_iso || a.created_at || '';
            const readyB = b.ready_at || b.completed_at || b.created_at_iso || b.created_at || '';
            return new Date(readyA) - new Date(readyB);
        });
    }

    // ==================== 等待時間即時更新 ====================

    /**
     * 渲染完成後啟動等待時間即時更新
     * @override
     * @param {Object[]} orders - 訂單數據陣列
     */
    afterRender(orders) {
        this._startWaitingTimer();
    }

    /**
     * 清除等待時間更新定時器
     * @override
     */
    cleanup() {
        this._stopWaitingTimer();
        super.cleanup();
    }

    /**
     * 啟動等待時間即時更新定時器（每 60 秒更新一次）
     * 惰性更新：只在有 ready 訂單時才啟動定時器
     * @private
     */
    _startWaitingTimer() {
        this._stopWaitingTimer();

        // 惰性更新：檢查是否有 ready 訂單，沒有則不啟動定時器
        const cards = document.querySelectorAll('#ready-orders-list [data-status="ready"]');
        if (!cards || cards.length === 0) {
            return;
        }

        this._waitingTimer = setInterval(() => {
            this._updateWaitingTimes();
        }, 60000); // 每分鐘更新一次
    }

    /**
     * 停止等待時間更新定時器
     * @private
     */
    _stopWaitingTimer() {
        if (this._waitingTimer) {
            clearInterval(this._waitingTimer);
            this._waitingTimer = null;
        }
    }

    /**
     * 更新所有已就緒訂單卡片的等待取餐時間
     * 遍歷 DOM 中 data-status="ready" 的卡片，重新計算等待時間並更新徽章
     * @private
     */
    _updateWaitingTimes() {
        const cards = document.querySelectorAll('#ready-orders-list [data-status="ready"]');
        cards.forEach(card => {
            const readyAtStr = card.getAttribute('data-ready-at');
            if (!readyAtStr) return;

            try {
                const readyTime = new Date(readyAtStr);
                const now = new Date();
                const diffMs = now - readyTime;
                const diffMinutes = Math.floor(diffMs / (1000 * 60));

                let display = '';
                if (diffMinutes < 1) {
                    display = '剛剛';
                } else if (diffMinutes < 60) {
                    display = `${diffMinutes}分鐘`;
                } else {
                    const hours = Math.floor(diffMinutes / 60);
                    const mins = diffMinutes % 60;
                    display = `${hours}小時${mins}分鐘`;
                }

                const badge = card.querySelector('.badge-warning');
                if (badge) {
                    badge.textContent = `等待取餐 ${display}`;
                }
            } catch (e) {
                // 忽略解析錯誤
            }
        });
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.ReadyOrdersRendererV2 = ReadyOrdersRendererV2;
    console.log('🌍 ReadyOrdersRendererV2 已註冊到 window 對象');
}
