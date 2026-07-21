// static/js/staff-order-management/base-order-renderer-v2.js
// ==================== 統一基礎訂單渲染器 v2 ====================
// 合併自：
//   - BaseOrderRenderer (base-order-renderer.js) — 生命週期管理、數據流
//   - OptimizedBaseRenderer (optimized-base-renderer.js) — DocumentFragment、倒計時、事件管理
//   - BaseRenderer (renderers/base-renderer.js) — 支付方式徽章、格式化工具
//   - CommonUtils (common-utils.js) — 靜態工具函數
//
// 設計原則：
//   1. 子類只需實現 createOrderElement(order) 方法
//   2. 共用方法（renderOrderItems、訂單類型徽章等）由基礎類提供
//   3. 倒計時管理為可選功能（透過 options.enableCountdown 啟用）
//   4. 保留 override 鉤子（beforeRender / afterRender）
//   5. 事件監聽器統一管理，cleanup 時自動移除

class BaseOrderRendererV2 {
    /**
     * @param {string} orderType - 訂單類型 ('payment_pending', 'preparing', 'ready', 'completed')
     * @param {string} tabId - Bootstrap 標籤頁 ID
     * @param {string} listId - 訂單列表容器 ID
     * @param {string} emptyId - 空狀態容器 ID
     * @param {Object} [options] - 配置選項
     * @param {boolean} [options.autoRefresh=true] - 是否啟用自動刷新
     * @param {number} [options.refreshInterval=30000] - 自動刷新間隔（毫秒）
     * @param {boolean} [options.enableCountdown=false] - 是否啟用倒計時
     * @param {boolean} [options.enableSorting=true] - 是否啟用排序
     * @param {string} [options.lastUpdateId] - 最後更新時間元素 ID
     * @param {string} [options.refreshBtnId] - 刷新按鈕 ID
     * @param {string} [options.dataKey] - 統一數據管理器中的數據鍵名（預設為 `${orderType}_orders`）
     */
    constructor(orderType, tabId, listId, emptyId, options = {}) {
        console.log(`🔄 初始化 ${orderType} 訂單渲染器 (v2)...`);

        this.orderType = orderType;
        this.tabId = tabId;
        this.listId = listId;
        this.emptyId = emptyId;

        this.options = {
            autoRefresh: options.autoRefresh !== false,
            refreshInterval: options.refreshInterval || 30000,
            enableCountdown: options.enableCountdown || false,
            enableSorting: options.enableSorting !== false,
            lastUpdateId: options.lastUpdateId || `${orderType}-orders-last-update`,
            refreshBtnId: options.refreshBtnId || `refresh-${orderType}-orders-btn`,
            dataKey: options.dataKey || `${orderType}_orders`,
            ...options
        };

        // 狀態
        this.currentOrders = new Map();      // orderId -> { element, data, updated }
        this.countdownTimers = new Map();     // orderId -> timerId
        this.eventListeners = new Map();      // key -> { target, event, handler }
        this.hasInitialData = false;
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false;
        this.refreshTimer = null;

        // 延遲初始化，確保 DOM 就緒
        setTimeout(() => this.initialize(), 100);
    }

    // ==================== 初始化 ====================

    initialize() {
        console.log(`🔄 ${this.orderType} 渲染器開始初始化 (v2)...`);

        this.registerToUnifiedManager();
        this.bindEvents();
        this.checkAndLoadData();

        if (this.options.autoRefresh) {
            this.startAutoRefresh();
        }

        this.isReady = true;
        console.log(`✅ ${this.orderType} 訂單渲染器初始化完成 (v2)`);
    }

    // ==================== 統一數據管理器註冊 ====================

    registerToUnifiedManager() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.registerToUnifiedManager(), 500);
            return;
        }

        console.log(`✅ ${this.orderType} 訂單渲染器註冊到統一數據管理器 (v2)`);

        const dataKey = this.options.dataKey;

        // 監聽特定訂單類型數據
        this._addManagedListener(window.unifiedDataManager, 'registerListener', null, (listener) => {
            // 使用 registerListener 的返回值來註冊
        });

        // 直接使用 unifiedDataManager 的 registerListener
        window.unifiedDataManager.registerListener(dataKey, (orders) => {
            console.log(`📥 ${this.orderType} 訂單數據接收:`, orders?.length || 0, '個');
            this.hasInitialData = true;

            if (this.isActiveTab()) {
                this.renderOrders(orders);
            } else {
                this.cacheOrders(orders);
            }
        }, true);

        // 監聽所有數據更新
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            const orders = allData[dataKey];
            if (orders) {
                this.hasInitialData = true;
                if (this.isActiveTab()) {
                    this.renderOrders(orders);
                } else {
                    this.cacheOrders(orders);
                }
            }
        }, true);

        // 監聽統一數據更新事件
        this._addManagedListener(document, 'unified_data_updated', () => {
            if (this.isActiveTab() && window.unifiedDataManager?.currentData?.[dataKey]) {
                setTimeout(() => {
                    this.renderOrders(window.unifiedDataManager.currentData[dataKey]);
                }, 100);
            }
        });
    }

    // ==================== 數據檢查與加載 ====================

    checkAndLoadData() {
        console.log(`🔍 檢查 ${this.orderType} 訂單數據...`);

        const dataKey = this.options.dataKey;

        // 情況1：統一數據管理器已有數據
        if (window.unifiedDataManager?.currentData?.[dataKey]) {
            console.log(`📦 從統一數據管理器獲取已有數據:`, window.unifiedDataManager.currentData[dataKey].length, '個');
            this.handleOrdersData(window.unifiedDataManager.currentData[dataKey]);
            return;
        }

        // 情況2：有緩存數據
        if (this.cachedOrders) {
            console.log(`📦 使用緩存數據:`, this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            return;
        }

        // 情況3：強制刷新數據
        console.log(`🔄 請求 ${this.orderType} 訂單數據...`);
        this.requestOrdersData();
    }

    handleOrdersData(orders) {
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單數據為空`);
            this.showEmpty();
            return;
        }

        console.log(`🔄 處理 ${this.orderType} 訂單數據: ${orders.length} 個`);

        if (this.isActiveTab()) {
            this.renderOrders(orders);
        } else {
            this.cacheOrders(orders);
        }
    }

    requestOrdersData() {
        if (!window.unifiedDataManager) {
            setTimeout(() => this.requestOrdersData(), 1000);
            return;
        }

        console.log(`🚀 觸發統一數據管理器加載 ${this.orderType} 數據`);
        window.unifiedDataManager.loadUnifiedData();
    }

    // ==================== 渲染方法 ====================

    /**
     * 渲染訂單列表
     * @param {Array} orders - 訂單數組
     */
    renderOrders(orders) {
        const orderList = document.getElementById(this.listId);
        const emptyElement = document.getElementById(this.emptyId);

        if (!orderList) {
            console.warn(`⚠️ ${this.orderType} 訂單列表容器未找到，100ms後重試`);
            setTimeout(() => this.renderOrders(orders), 100);
            return;
        }

        // 清理現有計時器
        this.cleanupTimers();

        // 清空容器
        orderList.innerHTML = '';
        this.currentOrders.clear();

        // 檢查是否有訂單
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單列表為空`);
            this.showEmpty();
            return;
        }

        console.log(`🎨 渲染 ${this.orderType} 訂單: ${orders.length} 個`);

        // beforeRender 鉤子
        this.beforeRender(orders);

        // 對訂單進行排序
        const sortedOrders = this.sortOrders(orders);

        // 使用 DocumentFragment 提高性能
        const fragment = document.createDocumentFragment();

        // 渲染每個訂單
        sortedOrders.forEach(order => {
            const orderElement = this.createOrderElement(order);
            fragment.appendChild(orderElement);

            // 更新當前訂單映射
            this.currentOrders.set(order.id, {
                element: orderElement,
                data: order,
                updated: new Date().getTime()
            });
        });

        // 一次性添加到 DOM
        orderList.appendChild(fragment);

        // 顯示列表容器，隱藏空狀態
        orderList.style.display = 'block';
        if (emptyElement) {
            emptyElement.style.display = 'none';
        }

        // 初始化倒計時（如果需要）
        if (this.options.enableCountdown) {
            this.initCountdowns();
        }

        // 更新最後更新時間
        this.updateLastUpdateTime();

        // afterRender 鉤子
        this.afterRender(orders);

        console.log(`✅ ${this.orderType} 訂單渲染完成`);
    }

    /**
     * beforeRender 鉤子（子類可覆蓋）
     */
    beforeRender(orders) {
        // 預留鉤子
    }

    /**
     * afterRender 鉤子（子類可覆蓋）
     */
    afterRender(orders) {
        // 預留鉤子
    }

    /**
     * 排序訂單（子類可覆蓋）
     * @param {Array} orders - 訂單數組
     * @returns {Array} 排序後的訂單數組
     */
    sortOrders(orders) {
        if (!this.options.enableSorting) {
            return orders;
        }

        // 默認排序：快速訂單優先，然後按創建時間排序（越早越優先）
        return [...orders].sort((a, b) => {
            // 第一優先級：快速訂單優先
            const isQuickA = a.is_quick_order || false;
            const isQuickB = b.is_quick_order || false;

            if (isQuickA !== isQuickB) {
                return isQuickB ? 1 : -1;
            }

            // 第二優先級：按創建時間排序
            const timeA = a.created_at_iso || a.created_at || '';
            const timeB = b.created_at_iso || b.created_at || '';
            return new Date(timeA) - new Date(timeB);
        });
    }

    /**
     * 創建訂單元素（子類必須實現此方法）
     * @param {Object} order - 訂單對象
     * @returns {HTMLElement} 訂單元素
     */
    createOrderElement(order) {
        throw new Error('子類必須實現 createOrderElement 方法');
    }

    // ==================== 共用渲染方法 ====================

    /**
     * 渲染訂單項目列表
     * @param {Array} items - 訂單項目數組
     * @param {Object} [options] - 配置選項
     * @param {number} [options.imageWidth=80] - 圖片容器寬度
     * @param {number} [options.imageHeight=80] - 圖片容器高度
     * @returns {string} HTML 字符串
     */
    renderOrderItems(items, options = {}) {
        if (!items || items.length === 0) {
            return '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }

        const imgWidth = options.imageWidth || 80;
        const imgHeight = options.imageHeight || 80;

        let itemsHTML = '';

        items.forEach(item => {
            const itemPrice = parseFloat(item.price || 0).toFixed(2);
            const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
            const itemImage = item.image || this.getDefaultImage(item.type);

            itemsHTML += `
                <div class="d-flex align-items-center mb-3">
                    <div class="mr-3">
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: ${imgWidth}px; height: ${imgHeight}px;">
                            <img src="${itemImage}"
                                 alt="${item.name || '商品'}"
                                 class="img-fluid"
                                 style="max-height: ${imgHeight - 5}px;"
                                 loading="lazy">
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${item.name || '商品'}</h6>
                        <p class="mb-1 text-muted">數量: ${item.quantity || 1}</p>
                        <div class="text-muted">
                            ${this._renderItemOptions(item)}
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="h6">$${itemTotal}</span>
                        <div class="text-muted small">$${itemPrice} / 單價</div>
                    </div>
                </div>
            `;
        });

        return itemsHTML;
    }

    /**
     * 渲染商品選項文字（杯型、牛奶、研磨、重量）
     * @private
     */
    _renderItemOptions(item) {
        const options = [
            item.cup_level_cn ? `杯型: ${item.cup_level_cn}` : '',
            item.milk_level_cn ? `牛奶: ${item.milk_level_cn}` : ''
        ].filter(Boolean);

        const options2 = [
            item.grinding_level_cn ? `研磨: ${item.grinding_level_cn}` : '',
            item.weight_cn ? `重量: ${item.weight_cn}` : '',
            item.weight ? `重量: ${item.weight}` : ''
        ].filter(Boolean);

        const separator = (options.length > 0 && options2.length > 0) ? '&nbsp;&nbsp;&nbsp;' : '';

        return options.join('&nbsp;&nbsp;') + separator + options2.join('&nbsp;&nbsp;');
    }

    /**
     * 獲取默認圖片
     * @param {string} itemType - 商品類型 ('coffee', 'bean')
     * @returns {string} 圖片 URL
     */
    getDefaultImage(itemType) {
        switch (itemType) {
            case 'coffee':
                return '/static/images/default-coffee.png';
            case 'bean':
                return '/static/images/default-beans.png';
            default:
                return '/static/images/default-product.png';
        }
    }

    /**
     * 分析訂單類型
     * @param {Object} order - 訂單對象
     * @returns {Object} 訂單類型信息
     */
    analyzeOrderType(order) {
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const hasCoffee = order.has_coffee || coffeeCount > 0;
        const hasBeans = order.has_beans || beanCount > 0;
        const isMixedOrder = order.is_mixed_order || (hasCoffee && hasBeans);
        const isBeansOnly = order.is_beans_only || (hasBeans && !hasCoffee);

        return {
            coffeeCount,
            beanCount,
            hasCoffee,
            hasBeans,
            isMixedOrder,
            isBeansOnly
        };
    }

    /**
     * 生成訂單類型徽章 HTML
     * @param {Object} order - 訂單對象
     * @param {Object} [typeInfo] - 訂單類型信息（可選，不傳則自動分析）
     * @returns {string} 徽章 HTML
     */
    generateOrderTypeBadges(order, typeInfo) {
        const info = typeInfo || this.analyzeOrderType(order);
        const { isMixedOrder } = info;

        if (order.is_quick_order) {
            return `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        } else if (isMixedOrder) {
            return `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        } else {
            return `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }
    }

    /**
     * 生成數量徽章 HTML
     * @param {Object} typeInfo - 訂單類型信息
     * @returns {string} 徽章 HTML
     */
    generateQuantityBadges(typeInfo) {
        const { coffeeCount, beanCount } = typeInfo;

        let badges = '';

        if (coffeeCount > 0) {
            badges += `
                <span class="badge badge-dark ml-1">
                    <i class="fas fa-mug-hot mr-1"></i>${coffeeCount}杯
                </span>
            `;
        }

        if (beanCount > 0) {
            badges += `
                <span class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
                </span>
            `;
        }

        return badges;
    }

    /**
     * 渲染支付方式徽章
     * @param {string} paymentMethod - 支付方式
     * @returns {string} 徽章 HTML
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
     * 渲染商品數量與產品類型顯示
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderItemsDisplayHTML(order) {
        const coffeeCount = order.coffee_count || 0;
        const beanCount = order.bean_count || 0;
        const totalItems = (order.items_count || 0) || (coffeeCount + beanCount);

        let html = `<span class="badge badge-light mr-1">${totalItems}項商品</span>`;

        if (coffeeCount > 0) {
            html += `<span class="badge badge-dark mr-1"><i class="fas fa-mug-hot mr-1"></i>${coffeeCount}杯</span>`;
        }
        if (beanCount > 0) {
            html += `<span class="badge badge-warning mr-1"><i class="fas fa-seedling mr-1"></i>${beanCount}包</span>`;
        }

        return html;
    }

    /**
     * 渲染咖啡師資訊
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderBaristaHTML(order) {
        const barista = order.barista_name || order.barista || '';
        if (!barista) return '';

        return `
            <span class="badge badge-barista ml-1">
                <i class="fas fa-user mr-1"></i>${barista}
            </span>
        `;
    }

    /**
     * 渲染合併徽章（訂單類型 + 支付方式 + 咖啡師）
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderCombinedBadge(order) {
        const typeBadge = this.generateOrderTypeBadges(order);
        const paymentBadge = this.renderPaymentMethodBadge(order.payment_method);
        const baristaBadge = this.renderBaristaHTML(order);

        return `
            <div class="d-flex align-items-center flex-wrap mt-2">
                ${typeBadge}
                ${paymentBadge}
                ${baristaBadge}
            </div>
        `;
    }

    /**
     * 渲染取餐碼
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderPickupCode(order) {
        const pickupCode = order.pickup_code || order.pickupCode || '';
        if (!pickupCode) return '';

        return `
            <span class="badge badge-dark pickup-code-badge">
                <i class="fas fa-qrcode mr-1"></i>取餐碼: ${pickupCode}
            </span>
        `;
    }

    /**
     * 渲染客戶資訊
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderCustomerInfo(order) {
        const customerName = order.customer_name || order.name || '';
        const phone = order.phone || order.customer_phone || '';

        let html = '';
        if (customerName) {
            html += `<span class="customer-name">${customerName}</span>`;
        }
        if (phone) {
            const formattedPhone = this.formatPhoneNumber(phone);
            html += `<span class="customer-phone ml-2"><i class="fas fa-phone mr-1"></i>${formattedPhone}</span>`;
        }

        return html;
    }

    /**
     * 渲染訂單編號
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderOrderNumber(order) {
        const orderNumber = order.order_number || order.id || '';
        return `
            <span class="order-number">
                <i class="fas fa-hashtag mr-1"></i>訂單編號: #${orderNumber}
            </span>
        `;
    }

    /**
     * 渲染訂單時間
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderOrderTime(order) {
        const createdAt = order.created_at_iso || order.created_at || '';
        const formattedTime = this.formatOrderTime(createdAt);
        return `
            <span class="order-time">
                <i class="fas fa-clock mr-1"></i>${formattedTime}
            </span>
        `;
    }

    /**
     * 渲染總價
     * @param {Object} order - 訂單對象
     * @returns {string} HTML
     */
    renderTotalPrice(order) {
        const total = parseFloat(order.total_price || 0).toFixed(2);
        return `
            <span class="order-total-price h5 text-gold">
                <strong>$${total}</strong>
            </span>
        `;
    }

    /**
     * 創建訂單卡片 div
     * @param {Object} order - 訂單對象
     * @returns {HTMLElement} div 元素
     */
    createOrderCardDiv(order) {
        const div = document.createElement('div');
        div.className = 'order-item mb-5 p-5 rounded selectable';
        div.setAttribute('data-order-id', order.id);
        div.setAttribute('data-order-type', this.orderType);
        return div;
    }

    // ==================== 格式化工具 ====================

    /**
     * 格式化訂單時間
     * @param {string} timeString - 時間字符串
     * @returns {string} 格式化後的時間
     */
    formatOrderTime(timeString) {
        if (!timeString) return '--:--';

        if (window.TimeUtils && typeof window.TimeUtils.formatOrderTime === 'function') {
            return window.TimeUtils.formatOrderTime(timeString, false);
        }

        try {
            return new Date(timeString).toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return timeString;
        }
    }

    /**
     * 格式化香港時間
     * @param {string} timeString - 時間字符串
     * @returns {string} 格式化後的時間
     */
    formatHKTime(timeString) {
        if (!timeString) return '--:--';

        if (window.TimeUtils && typeof window.TimeUtils.formatHKTime === 'function') {
            return window.TimeUtils.formatHKTime(timeString);
        }

        try {
            const date = new Date(timeString);
            return date.toLocaleString('zh-HK', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
        } catch (e) {
            return timeString;
        }
    }

    /**
     * 格式化香港時間（僅時間部分）
     * @param {string} timeString - 時間字符串
     * @returns {string} 格式化後的時間
     */
    formatHKTimeOnly(timeString) {
        if (!timeString) return '--:--';

        if (window.TimeUtils && typeof window.TimeUtils.formatHKTimeOnly === 'function') {
            return window.TimeUtils.formatHKTimeOnly(timeString);
        }

        try {
            const date = new Date(timeString);
            return date.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (e) {
            return timeString;
        }
    }

    /**
     * 格式化電話號碼，移除香港地區碼 (+852)
     * @param {string} phone - 電話號碼
     * @returns {string} 格式化後的電話號碼
     */
    formatPhoneNumber(phone) {
        if (!phone) return '';

        if (window.CommonUtils && typeof window.CommonUtils.formatPhoneNumber === 'function') {
            return window.CommonUtils.formatPhoneNumber(phone);
        }

        let cleaned = phone.toString().replace(/\s+/g, '');
        cleaned = cleaned.replace(/^\+852/, '');
        cleaned = cleaned.replace(/^852/, '');
        return cleaned;
    }

    // ==================== 倒計時管理（可選功能） ====================

    initCountdowns() {
        const orderList = document.getElementById(this.listId);
        if (!orderList) return;

        const countdownBadges = orderList.querySelectorAll('.countdown-badge');

        countdownBadges.forEach(badge => {
            const orderId = badge.dataset.orderId;
            const estimatedTimeStr = badge.dataset.estimatedTime;
            const countdownText = badge.querySelector('.countdown-text');

            if (!estimatedTimeStr || !countdownText) return;

            const estimatedTime = new Date(estimatedTimeStr);

            if (isNaN(estimatedTime.getTime())) {
                countdownText.textContent = '時間錯誤';
                return;
            }

            // 檢查是否已經過了預計完成時間
            const now = new Date();
            if (estimatedTime <= now) {
                this.markCountdownCompleted(badge, estimatedTimeStr);
                return;
            }

            this.startCountdown(badge, orderId, estimatedTime);
        });
    }

    startCountdown(badge, orderId, estimatedTime) {
        const countdownText = badge.querySelector('.countdown-text');

        // 清理現有的定時器
        const existingTimer = this.countdownTimers.get(orderId);
        if (existingTimer) {
            clearInterval(existingTimer);
        }

        const updateCountdown = () => {
            const now = new Date();
            const diffMs = estimatedTime - now;

            if (diffMs <= 0) {
                this.markCountdownCompleted(badge, estimatedTime.toISOString());

                const timer = this.countdownTimers.get(orderId);
                if (timer) {
                    clearInterval(timer);
                    this.countdownTimers.delete(orderId);
                }
                return;
            }

            const diffMins = Math.floor(diffMs / (1000 * 60));
            const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);

            if (diffMins > 0) {
                countdownText.textContent = `預計完成: ${diffMins}分${diffSecs.toString().padStart(2, '0')}秒`;
            } else {
                countdownText.textContent = `預計完成: ${diffSecs}秒`;
            }
        };

        // 立即更新一次
        updateCountdown();

        // 每秒更新一次
        const timer = setInterval(updateCountdown, 1000);
        this.countdownTimers.set(orderId, timer);
    }

    markCountdownCompleted(badge, estimatedTimeStr) {
        const countdownText = badge.querySelector('.countdown-text');

        let completedTimeDisplay = '已完成';
        if (window.TimeUtils && typeof window.TimeUtils.formatHKTimeOnly === 'function') {
            completedTimeDisplay = `已完成: ${window.TimeUtils.formatHKTimeOnly(new Date(estimatedTimeStr))}`;
        } else {
            try {
                const estimatedTime = new Date(estimatedTimeStr);
                const formattedTime = estimatedTime.toLocaleTimeString('zh-HK', {
                    hour12: true,
                    hour: '2-digit',
                    minute: '2-digit'
                });
                completedTimeDisplay = `已完成: ${formattedTime}`;
            } catch (e) {
                completedTimeDisplay = '已完成';
            }
        }

        countdownText.textContent = completedTimeDisplay;
        badge.classList.remove('badge-secondary');
        badge.classList.add('badge-success');

        const icon = badge.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check mr-1';
        }
    }

    cleanupTimers() {
        this.countdownTimers.forEach(timer => clearInterval(timer));
        this.countdownTimers.clear();
    }

    // ==================== 自動刷新 ====================

    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (this.isActiveTab()) {
                console.log(`🔄 自動刷新 ${this.orderType} 訂單數據`);
                this.forceRefresh();
            }
        }, this.options.refreshInterval);
    }

    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    // ==================== 事件處理 ====================

    bindEvents() {
        console.log(`🔄 綁定 ${this.orderType} 訂單渲染器事件 (v2)...`);

        // 刷新按鈕
        const refreshBtn = document.getElementById(this.options.refreshBtnId);
        if (refreshBtn) {
            this._addManagedListener(refreshBtn, 'click', () => {
                console.log(`🔄 手動刷新 ${this.orderType} 訂單`);
                this.showToast('🔄 刷新中...', 'info');
                this.forceRefresh();
            });
        }

        // Bootstrap 標籤頁顯示事件
        const $tab = $(`#${this.tabId}`);
        if ($tab && $tab.on) {
            $tab.on('shown.bs.tab', () => {
                console.log(`📌 ${this.orderType} 標籤頁已顯示`);
                this.onTabActivated();
            });
        }

        // 標籤頁點擊事件
        const tabElement = document.getElementById(this.tabId);
        if (tabElement) {
            this._addManagedListener(tabElement, 'click', () => {
                setTimeout(() => {
                    if (this.isActiveTab()) {
                        this.onTabActivated();
                    }
                }, 100);
            });
        }
    }

    /**
     * 標籤頁激活時調用
     */
    onTabActivated() {
        console.log(`🎯 ${this.orderType} 標籤頁激活`);

        // 情況1：有緩存數據
        if (this.cachedOrders) {
            console.log(`📦 渲染緩存數據:`, this.cachedOrders.length, '個');
            this.renderOrders(this.cachedOrders);
            this.cachedOrders = null;
            return;
        }

        // 情況2：統一數據管理器有數據
        const dataKey = this.options.dataKey;
        if (window.unifiedDataManager?.currentData?.[dataKey]) {
            console.log(`📊 從統一數據管理器獲取數據`);
            this.renderOrders(window.unifiedDataManager.currentData[dataKey]);
            return;
        }

        // 情況3：強制刷新
        console.log(`🚀 請求最新數據`);
        this.forceRefresh();
    }

    /**
     * 檢查是否為當前活動標籤頁
     * @returns {boolean}
     */
    isActiveTab() {
        const tabElement = document.getElementById(this.tabId);
        return tabElement && tabElement.classList.contains('active');
    }

    // ==================== UI 輔助方法 ====================

    /**
     * 顯示空狀態
     */
    showEmpty() {
        const orderList = document.getElementById(this.listId);
        const emptyElement = document.getElementById(this.emptyId);

        if (orderList) {
            orderList.innerHTML = '';
            orderList.style.display = 'none';
        }

        if (emptyElement) {
            emptyElement.style.display = 'block';
        }

        console.log(`📭 顯示 ${this.orderType} 空狀態`);
    }

    /**
     * 更新最後更新時間
     */
    updateLastUpdateTime() {
        const timeElement = document.getElementById(this.options.lastUpdateId);
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = now.toLocaleTimeString('zh-HK', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }

    /**
     * 顯示 Toast 通知
     * @param {string} message - 消息內容
     * @param {string} type - 類型 ('info', 'success', 'error', 'warning')
     */
    showToast(message, type = 'info') {
        // 優先使用統一的 toast-manager.js
        if (window.toast) {
            const toastType = type === 'success' ? 'success' :
                             type === 'error' ? 'error' :
                             type === 'warning' ? 'warning' : 'info';

            window.toast[toastType](message);
        } else if (window.orderManager && window.orderManager.showToast) {
            // 備用方案：使用 orderManager 的 showToast
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

    /**
     * 強制刷新數據
     */
    forceRefresh() {
        if (window.unifiedDataManager) {
            window.unifiedDataManager.loadUnifiedData(true);
        }
    }

    /**
     * 緩存訂單數據
     * @param {Array} orders - 訂單數組
     */
    cacheOrders(orders) {
        this.cachedOrders = orders;
        console.log(`📦 緩存 ${this.orderType} 訂單數據: ${orders?.length || 0} 個`);
    }

    // ==================== 事件監聽器管理 ====================

    /**
     * 添加受管理的監聽器（cleanup 時自動移除）
     * @private
     */
    _addManagedListener(target, event, handler) {
        target.addEventListener(event, handler);

        const key = `${event}_${Date.now()}_${Math.random()}`;
        this.eventListeners.set(key, { target, event, handler });

        return () => {
            target.removeEventListener(event, handler);
            this.eventListeners.delete(key);
        };
    }

    /**
     * 移除所有受管理的監聽器
     * @private
     */
    _removeAllManagedListeners() {
        this.eventListeners.forEach(({ target, event, handler }) => {
            target.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
    }

    // ==================== 清理方法 ====================

    /**
     * 清理資源（切換頁面或銷毀時調用）
     */
    cleanup() {
        console.log(`🔄 清理 ${this.orderType} 訂單渲染器 (v2)...`);

        // 停止自動刷新
        this.stopAutoRefresh();

        // 清理倒計時計時器
        this.cleanupTimers();

        // 清理事件監聽器
        this._removeAllManagedListeners();

        // 清理當前訂單映射
        this.currentOrders.clear();

        // 清理緩存
        this.cachedOrders = null;

        // 重置處理狀態
        this.isProcessingAction = false;
        this.hasInitialData = false;
        this.isReady = false;

        console.log(`✅ ${this.orderType} 訂單渲染器已清理 (v2)`);
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.BaseOrderRendererV2 = BaseOrderRendererV2;
    console.log('🌍 BaseOrderRendererV2 已註冊到 window 對象');
}
