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
        
        // 咖啡杯數徽章
        let coffeeCountBadge = '';
        if (coffeeCount > 0) {
            coffeeCountBadge = `
                <span hidden class="badge badge-dark ml-1">
                    <i class="fas fa-mug-hot mr-1"></i>${coffeeCount}杯
                </span>
            `;
        }
        
        // 咖啡豆數量徽章
        let beanCountBadge = '';
        if (beanCount > 0) {
            beanCountBadge = `
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
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
            <div class="order-item mb-5 p-5 rounded selectable" data-order-id="${orderId}" data-status="payment_pending" data-order-type="${orderTypeAttr}">
                <!-- 訂單類型徽章（左上角） -->
                <div class="order-type-badges-container">
                    ${orderTypeBadges}
                </div>
                
                <div class="d-flex justify-content-between mb-3 mt-3">
                    <div class="mt-2">
                        ${queuePositionBadge}
                        ${coffeeCountBadge}
                        ${beanCountBadge}
                    </div>
                </div>

                <div class="order-items">
                    ${itemsHTML}
                    <div>
                        <span class="card-text-md">${itemCount > 0 ? itemCount + '項商品' : '0項商品'}</span>
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
                    <button class="btn btn-success btn-sm mr-2 btn-confirm-fps-payment" 
                            data-order-id="${orderId}"
                            title="確認 FPS 付款已收到">
                        <i class="fas fa-check-circle mr-1"></i>確認 FPS 付款
                    </button>
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
     * @param {Array} orders - 訂單數據列表
     */
    bindCardEvents(orders) {
        // 確認 FPS 付款按鈕
        document.querySelectorAll('.btn-confirm-fps-payment').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const orderId = btn.dataset.orderId;
                this.confirmFpsPayment(orderId);
            });
        });
        
        // 取消訂單按鈕
        document.querySelectorAll('.btn-cancel-order').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const orderId = btn.dataset.orderId;
                this.cancelOrder(orderId);
            });
        });
    }
    
    /**
     * 確認 FPS 付款
     * 
     * @param {number} orderId - 訂單 ID
     */
    async confirmFpsPayment(orderId) {
        // 禁用按鈕防止重複點擊
        const buttons = document.querySelectorAll(`.btn-confirm-fps-payment[data-order-id="${orderId}"]`);
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>處理中...';
        });
        
        try {
            // 使用 queueManager 的 confirmFpsPayment 方法（queueManager 內部已處理 toast 顯示）
            if (window.queueManager && typeof window.queueManager.confirmFpsPayment === 'function') {
                const result = await window.queueManager.confirmFpsPayment(orderId);
                
                // queueManager 內部已顯示 toast，此處不再重複顯示
                // 只根據結果決定是否刷新
                if (result && result.success) {
                    // 刷新數據
                    setTimeout(() => {
                        this.refresh();
                    }, 1000);
                } else {
                    // 恢復按鈕
                    buttons.forEach(btn => {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fas fa-check mr-1"></i>確認 FPS 付款';
                    });
                }
            } else {
                // 直接調用 API（備用方案）
                const response = await fetch(`/eshop/api/fps/confirm-payment/${orderId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken(),
                    },
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showToast('success', `訂單 #${orderId} FPS 付款已確認成功`);
                    setTimeout(() => {
                        this.refresh();
                    }, 1000);
                } else {
                    this.showToast('error', `訂單 #${orderId} 確認失敗: ${result.message || '未知錯誤'}`);
                    buttons.forEach(btn => {
                        btn.disabled = false;
                        btn.innerHTML = '<i class="fas fa-check mr-1"></i>確認 FPS 付款';
                    });
                }
            }
        } catch (error) {
            console.error('❌ 確認 FPS 付款失敗:', error);
            this.showToast('error', `系統錯誤: ${error.message}`);
            
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-check mr-1"></i>確認 FPS 付款';
            });
        }
    }
    
    /**
     * 取消訂單
     * 
     * @param {number} orderId - 訂單 ID
     */
    async cancelOrder(orderId) {
        const buttons = document.querySelectorAll(`.btn-cancel-order[data-order-id="${orderId}"]`);
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>處理中...';
        });
        
        try {
            const response = await fetch(`/eshop/api/cancel-order/${orderId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('info', `訂單 #${orderId} 已取消`);
                setTimeout(() => {
                    this.refresh();
                }, 1000);
            } else {
                this.showToast('error', `取消訂單 #${orderId} 失敗: ${result.message || '未知錯誤'}`);
                buttons.forEach(btn => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-times mr-1"></i>取消訂單';
                });
            }
        } catch (error) {
            console.error('❌ 取消訂單失敗:', error);
            this.showToast('error', `系統錯誤: ${error.message}`);
            buttons.forEach(btn => {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-times mr-1"></i>取消訂單';
            });
        }
    }
    
    /**
     * 獲取 CSRF Token
     * 
     * @returns {string} CSRF Token
     */
    getCsrfToken() {
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
    
    /**
     * 顯示 Toast 通知
     * 
     * @param {string} type - 類型 (success/error/info)
     * @param {string} message - 訊息內容
     */
    showToast(type, message) {
        // 嘗試使用全局 toast 方法
        if (window.showToast) {
            window.showToast(type, message);
            return;
        }
        
        // 自定義 Toast 實現
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;';
            document.body.appendChild(container);
        }
        
        const bgClass = type === 'success' ? 'bg-success' : 
                        type === 'error' ? 'bg-danger' : 'bg-info';
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast ${bgClass} text-white`;
        toastEl.style.minWidth = '250px';
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.setAttribute('data-delay', '3000');
        
        toastEl.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <strong class="mr-auto">
                    ${type === 'success' ? '✅ 成功' : type === 'error' ? '❌ 錯誤' : 'ℹ️ 提示'}
                </strong>
                <button type="button" class="ml-2 mb-1 close text-white" data-dismiss="toast">
                    <span>&times;</span>
                </button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        document.getElementById('toast-container').appendChild(toastEl);
        
        if (typeof $ !== 'undefined' && $.fn && $.fn.toast) {
            $(toastEl).toast('show');
            setTimeout(() => {
                $(toastEl).toast('dispose');
            }, 3500);
        } else {
            toastEl.style.display = 'block';
            setTimeout(() => {
                toastEl.remove();
            }, 3500);
        }
    }
}

// 註冊到全局
window.PaymentPendingRenderer = PaymentPendingRenderer;
