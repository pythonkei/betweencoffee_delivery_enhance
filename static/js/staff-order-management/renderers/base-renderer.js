// static/js/staff-order-management/renderers/base-renderer.js
// ==================== 基礎渲染器 ====================
// 功能：提供所有渲染器的共用基礎類，減少重複代碼
// 依賴：無（獨立運行）
//
// 使用方式：
//   class MyRenderer extends BaseRenderer {
//       constructor() {
//           super('my-renderer', {
//               containerId: 'my-orders-list',
//               emptyId: 'my-orders-empty',
//               lastUpdateId: 'my-orders-last-update',
//               refreshBtnId: 'refresh-my-orders-btn',
//           });
//       }
//       
//       renderOrders(orders) {
//           // 實現具體渲染邏輯
//       }
//   }

class BaseRenderer {
    /**
     * @param {string} name - 渲染器名稱
     * @param {Object} config - 配置
     * @param {string} config.containerId - 容器元素 ID
     * @param {string} config.emptyId - 空狀態元素 ID
     * @param {string} [config.lastUpdateId] - 最後更新時間元素 ID
     * @param {string} [config.refreshBtnId] - 刷新按鈕 ID
     * @param {string} [config.dataKey] - 統一數據管理器中的數據鍵名
     */
    constructor(name, config = {}) {
        this.name = name || 'BaseRenderer';
        this.config = config;
        this.containerId = config.containerId;
        this.emptyId = config.emptyId;
        this.lastUpdateId = config.lastUpdateId || null;
        this.refreshBtnId = config.refreshBtnId || null;
        this.dataKey = config.dataKey || null;
        this.isReady = false;
        this.cachedOrders = null;
        this.hasInitialData = false;
        
        console.log(`🔄 ${this.name} 初始化...`);
    }
    
    /**
     * 初始化渲染器
     */
    initialize() {
        this.bindEvents();
        this.registerToUnifiedManager();
        this.isReady = true;
        console.log(`✅ ${this.name} 初始化完成`);
    }
    
    /**
     * 綁定事件
     */
    bindEvents() {
        // 監聽統一數據更新事件
        document.addEventListener('unified_data_updated', (event) => {
            const data = event.detail?.data || event.detail;
            if (data) {
                this.handleDataUpdate(data);
            }
        });
        
        // 監聽刷新按鈕
        if (this.refreshBtnId) {
            const refreshBtn = document.getElementById(this.refreshBtnId);
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => this.refresh());
            }
        }
    }
    
    /**
     * 註冊到統一數據管理器
     */
    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }
        
        if (this.dataKey) {
            window.unifiedDataManager.registerListener(this.dataKey, (orders) => {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(orders);
                } else {
                    this.cacheOrders(orders);
                }
            }, true);
        }
        
        // 監聽所有數據更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            const orders = this.dataKey ? allData[this.dataKey] : allData;
            if (orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(orders);
                } else {
                    this.cacheOrders(orders);
                }
            }
        }, true);
    }
    
    /**
     * 處理數據更新
     */
    handleDataUpdate(data) {
        const orders = this.dataKey ? data[this.dataKey] : data;
        if (!orders) return;
        
        if (this.isActiveTab()) {
            this.renderOrders(orders);
        } else {
            this.cacheOrders(orders);
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
     * 檢查當前標籤頁是否激活
     */
    isActiveTab() {
        const tab = document.querySelector(`[data-toggle="tab"][href="#${this.containerId?.replace('-list', '')?.replace('-content', '')}"]`);
        if (tab) {
            return tab.getAttribute('aria-selected') === 'true';
        }
        // 如果找不到對應標籤，預設為激活
        return true;
    }
    
    /**
     * 緩存訂單數據
     */
    cacheOrders(orders) {
        this.cachedOrders = orders;
    }
    
    /**
     * 渲染訂單（入口方法）
     */
    render(orders) {
        this.renderOrders(orders || this.cachedOrders || []);
    }
    
    /**
     * 子類需實現的渲染方法
     */
    renderOrders(orders) {
        throw new Error(`${this.name} 必須實現 renderOrders 方法`);
    }
    
    /**
     * 更新最後更新時間
     */
    updateLastUpdateTime() {
        if (this.lastUpdateId) {
            const el = document.getElementById(this.lastUpdateId);
            if (el) {
                el.textContent = new Date().toLocaleTimeString('zh-HK');
            }
        }
    }
    
    /**
     * 處理空狀態
     */
    handleEmptyState(orders) {
        const container = document.getElementById(this.containerId);
        const emptyEl = document.getElementById(this.emptyId);
        
        if (!container) return;
        
        if (!orders || orders.length === 0) {
            container.innerHTML = '';
            if (emptyEl) emptyEl.style.display = 'block';
            return true;
        }
        
        if (emptyEl) emptyEl.style.display = 'none';
        return false;
    }
    
    /**
     * 獲取容器元素
     */
    getContainer() {
        return document.getElementById(this.containerId);
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
    
    /**
     * 格式化訂單時間
     */
    formatOrderTime(createdAt) {
        if (window.TimeUtils) {
            return window.TimeUtils.formatOrderTime(createdAt, false);
        }
        if (createdAt) {
            try {
                return new Date(createdAt).toLocaleTimeString('zh-HK', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                });
            } catch(e) {
                return createdAt;
            }
        }
        return '--:--';
    }
    
    /**
     * 格式化電話號碼
     */
    formatPhone(phone) {
        if (window.CommonUtils) {
            return window.CommonUtils.formatPhoneNumber(phone);
        }
        return phone || '';
    }
    
    /**
     * 渲染商品項目 HTML
     */
    renderItemsHTML(items) {
        if (!items || items.length === 0) {
            return '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }
        
        return items.map(item => {
            const itemPrice = parseFloat(item.price || 0).toFixed(2);
            const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
            const itemImage = item.image || this.getDefaultImage(item.type);
            
            return `
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
        }).join('');
    }
    
    /**
     * 渲染訂單類型徽章
     */
    renderOrderTypeBadges(order) {
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        
        if (order.is_quick_order) {
            return `
                <span class="badge order-type-badge" data-order-type="quick">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        } else if (isMixedOrder) {
            return `
                <span class="badge order-type-badge" data-order-type="mixed">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        }
        return `
            <span class="badge order-type-badge" data-order-type="single">
                <i class="fas fa-shopping-bag mr-1"></i>普通訂單
            </span>
        `;
    }
    
    /**
     * 渲染支付方式徽章
     */
    renderPaymentMethodBadge(paymentMethod) {
        if (!paymentMethod) return '';
        
        const methods = {
            alipay: { icon: '<i class="fab fa-alipay mr-1"></i>', text: '支付寶' },
            fps: { icon: '<i class="fas fa-money-bill-wave mr-1"></i>', text: 'FPS' },
            cash: { icon: '<i class="fas fa-money-bill-alt mr-1"></i>', text: '現金' },
            paypal: { icon: '<i class="fab fa-paypal mr-1"></i>', text: 'PayPal' },
        };
        
        const method = methods[paymentMethod] || { 
            icon: '<i class="fas fa-money-check-alt mr-1"></i>', 
            text: paymentMethod 
        };
        
        return `
            <span class="badge badge-success ml-1">
                ${method.icon}${method.text}
            </span>
        `;
    }
    
    /**
     * 清理資源
     */
    cleanup() {
        this.cachedOrders = null;
        this.hasInitialData = false;
        this.isReady = false;
        console.log(`🗑️ ${this.name} 已清理`);
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.BaseRenderer = BaseRenderer;
    console.log('🌍 BaseRenderer 已註冊到 window 對象');
}
