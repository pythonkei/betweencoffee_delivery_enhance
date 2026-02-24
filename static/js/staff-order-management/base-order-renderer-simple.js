// static/js/staff-order-management/base-order-renderer-simple.js
// ==================== 簡化版訂單渲染器基礎類 ====================
// 專注於核心功能，避免複雜繼承結構

class BaseOrderRendererSimple {
    /**
     * 簡化版基礎訂單渲染器
     * @param {string} orderType - 訂單類型 ('completed', 'ready', 'preparing')
     * @param {string} containerId - 容器ID
     */
    constructor(orderType, containerId) {
        console.log(`🔄 初始化 ${orderType} 簡化版訂單渲染器...`);
        
        this.orderType = orderType;
        this.containerId = containerId;
        this.orders = [];
        this.isInitialized = false;
        
        this.init();
    }
    
    // ==================== 初始化方法 ====================
    
    init() {
        console.log(`🔄 ${this.orderType} 簡化渲染器開始初始化...`);
        
        // 檢查容器是否存在
        if (!this.getContainer()) {
            console.warn(`⚠️ ${this.orderType} 容器未找到，延遲初始化`);
            setTimeout(() => this.init(), 500);
            return;
        }
        
        this.bindEvents();
        this.loadData();
        
        this.isInitialized = true;
        console.log(`✅ ${this.orderType} 簡化訂單渲染器初始化完成`);
    }
    
    // ==================== 數據加載方法 ====================
    
    loadData() {
        console.log(`🔍 加載 ${this.orderType} 訂單數據...`);
        
        // 使用統一數據管理器或直接API調用
        if (window.unifiedDataManager) {
            this.loadFromUnifiedManager();
        } else {
            this.loadFromAPI();
        }
    }
    
    loadFromUnifiedManager() {
        const dataKey = `${this.orderType}_orders`;
        
        // 監聽數據更新
        window.unifiedDataManager.registerListener(dataKey, (orders) => {
            console.log(`📥 ${this.orderType} 數據接收:`, orders?.length || 0, '個');
            this.updateOrders(orders);
        }, true);
        
        // 檢查現有數據
        if (window.unifiedDataManager.currentData?.[dataKey]) {
            this.updateOrders(window.unifiedDataManager.currentData[dataKey]);
        }
    }
    
    loadFromAPI() {
        // 簡單的API調用
        fetch(`/eshop/queue/unified-data/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data[`${this.orderType}_orders`]) {
                    this.updateOrders(data.data[`${this.orderType}_orders`]);
                }
            })
            .catch(error => {
                console.error(`❌ 加載 ${this.orderType} 數據失敗:`, error);
            });
    }
    
    // ==================== 核心渲染方法 ====================
    
    updateOrders(orders) {
        if (!orders || orders.length === 0) {
            this.showEmptyState();
            return;
        }
        
        console.log(`🔄 更新 ${this.orderType} 訂單: ${orders.length} 個`);
        this.orders = orders;
        this.render();
    }
    
    render() {
        const container = this.getContainer();
        if (!container) return;
        
        // 清空容器
        container.innerHTML = '';
        
        // 排序訂單（最新的在前面）
        const sortedOrders = [...this.orders].sort((a, b) => {
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        });
        
        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderCard(order);
            container.appendChild(orderElement);
        });
        
        console.log(`✅ ${this.orderType} 訂單渲染完成`);
    }
    
    createOrderCard(order) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.id = `order-${order.id}`;
        
        // 訂單頭部
        const header = this.createOrderHeader(order);
        
        // 訂單內容
        const content = this.createOrderContent(order);
        
        // 訂單操作
        const actions = this.createOrderActions(order);
        
        card.appendChild(header);
        card.appendChild(content);
        if (actions) {
            card.appendChild(actions);
        }
        
        return card;
    }
    
    createOrderHeader(order) {
        const header = document.createElement('div');
        header.className = 'card-header d-flex justify-content-between align-items-center';
        
        // 訂單ID和時間
        const orderInfo = document.createElement('div');
        orderInfo.innerHTML = `
            <h6 class="mb-0">
                <strong>訂單 #${order.id}</strong>
                <small class="text-muted ml-2">${this.formatTime(order.created_at)}</small>
            </h6>
            <div class="small text-muted">
                取餐碼: <span class="badge badge-secondary">${order.pickup_code || 'N/A'}</span>
            </div>
        `;
        
        // 訂單狀態徽章
        const statusBadge = document.createElement('div');
        statusBadge.innerHTML = this.getStatusBadge(order);
        
        header.appendChild(orderInfo);
        header.appendChild(statusBadge);
        
        return header;
    }
    
    createOrderContent(order) {
        const content = document.createElement('div');
        content.className = 'card-body';
        
        // 客戶信息
        const customerInfo = `
            <div class="mb-3">
                <h6 class="mb-1">客戶信息</h6>
                <p class="mb-1">
                    <i class="fas fa-user mr-1"></i> ${order.customer_name || '未提供'}
                    <span class="ml-3">
                        <i class="fas fa-phone mr-1"></i> ${order.customer_phone || '未提供'}
                    </span>
                </p>
            </div>
        `;
        
        // 商品列表
        const itemsList = this.createItemsList(order.items || []);
        
        // 訂單摘要
        const orderSummary = this.createOrderSummary(order);
        
        content.innerHTML = customerInfo;
        content.appendChild(itemsList);
        content.appendChild(orderSummary);
        
        return content;
    }
    
    createItemsList(items) {
        const container = document.createElement('div');
        container.className = 'mb-3';
        
        if (!items || items.length === 0) {
            container.innerHTML = '<p class="text-muted mb-0">暫無商品信息</p>';
            return container;
        }
        
        const title = document.createElement('h6');
        title.className = 'mb-2';
        title.textContent = '商品列表';
        container.appendChild(title);
        
        items.forEach(item => {
            const itemElement = document.createElement('div');
            itemElement.className = 'd-flex align-items-center mb-2 p-2 border rounded';
            
            itemElement.innerHTML = `
                <div class="mr-3" style="width: 60px; height: 60px;">
                    <img src="${item.image || '/static/images/default-product.png'}"
                         alt="${item.name || '商品'}"
                         class="img-fluid rounded"
                         style="max-height: 55px;">
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex justify-content-between">
                        <strong>${item.name || '商品'}</strong>
                        <span class="text-primary">$${parseFloat(item.total_price || 0).toFixed(2)}</span>
                    </div>
                    <div class="small text-muted">
                        數量: ${item.quantity || 1} × $${parseFloat(item.price || 0).toFixed(2)}
                        ${item.cup_level_cn ? ` | ${item.cup_level_cn}` : ''}
                        ${item.milk_level_cn ? ` | ${item.milk_level_cn}` : ''}
                    </div>
                </div>
            `;
            
            container.appendChild(itemElement);
        });
        
        return container;
    }
    
    createOrderSummary(order) {
        const summary = document.createElement('div');
        summary.className = 'border-top pt-3';
        
        const total = parseFloat(order.total_amount || 0).toFixed(2);
        const paymentMethod = this.getPaymentMethodText(order.payment_method);
        
        summary.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <strong>總金額:</strong>
                    <div class="small text-muted">支付方式: ${paymentMethod}</div>
                </div>
                <div class="text-right">
                    <h5 class="text-primary mb-0">$${total}</h5>
                    ${order.is_quick_order ? '<div class="small text-warning"><i class="fas fa-bolt"></i> 快速訂單</div>' : ''}
                </div>
            </div>
        `;
        
        return summary;
    }
    
    createOrderActions(order) {
        // 子類可以覆蓋此方法添加特定操作
        return null;
    }
    
    // ==================== 輔助方法 ====================
    
    getContainer() {
        return document.getElementById(this.containerId);
    }
    
    showEmptyState() {
        const container = this.getContainer();
        if (!container) return;
        
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-clipboard-list fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">暫無${this.getOrderTypeText()}訂單</h5>
                <p class="text-muted small">當有新的${this.getOrderTypeText()}訂單時，這裡會顯示相關信息</p>
            </div>
        `;
    }
    
    getOrderTypeText() {
        const types = {
            'completed': '已完成',
            'ready': '已就緒',
            'preparing': '製作中',
            'waiting': '等待中'
        };
        return types[this.orderType] || this.orderType;
    }
    
    getStatusBadge(order) {
        const status = order.status || this.orderType;
        const badges = {
            'completed': 'badge-success',
            'ready': 'badge-warning',
            'preparing': 'badge-info',
            'waiting': 'badge-secondary'
        };
        
        const badgeClass = badges[status] || 'badge-secondary';
        const statusText = this.getOrderTypeText();
        
        return `<span class="badge ${badgeClass}">${statusText}</span>`;
    }
    
    getPaymentMethodText(method) {
        const methods = {
            'alipay': '支付寶',
            'paypal': 'PayPal',
            'fps': 'FPS轉數快',
            'cash': '現金'
        };
        return methods[method] || method || '未知';
    }
    
    formatTime(timeString) {
        if (!timeString) return '未知時間';
        
        try {
            const date = new Date(timeString);
            return date.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return timeString;
        }
    }
    
    // ==================== 事件處理 ====================
    
    bindEvents() {
        console.log(`🔄 綁定 ${this.orderType} 事件...`);
        
        // 刷新按鈕
        const refreshBtn = document.getElementById(`refresh-${this.orderType}`);
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                console.log(`🔄 手動刷新 ${this.orderType} 訂單`);
                this.showNotification('🔄 刷新中...', 'info');
                this.loadData();
            });
        }
        
        // 監聽數據更新事件
        document.addEventListener('unified_data_updated', () => {
            if (window.unifiedDataManager?.currentData?.[`${this.orderType}_orders`]) {
                setTimeout(() => {
                    this.updateOrders(window.unifiedDataManager.currentData[`${this.orderType}_orders`]);
                }, 100);
            }
        });
    }
    
    showNotification(message, type = 'info') {
        // 簡單的通知實現
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
        notification.setAttribute('role', 'alert');
        notification.innerHTML = `
            ${message}
            <button type="button" class="close" data-dismiss="alert">
                <span>&times;</span>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    // ==================== 公共方法 ====================
    
    refresh() {
        console.log(`🔄 強制刷新 ${this.orderType} 數據`);
        this.loadData();
    }
    
    destroy() {
        console.log(`🔄 銷毀 ${this.orderType} 渲染器`);
        this.orders = [];
        this.isInitialized = false;
        
        const container = this.getContainer();
        if (container) {
            container.innerHTML = '';
        }
    }
}

// 導出類
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BaseOrderRendererSimple;
}