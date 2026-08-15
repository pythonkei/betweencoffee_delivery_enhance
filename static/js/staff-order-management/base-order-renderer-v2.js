// static/js/staff-order-management/base-order-renderer-v2.js
// ==================== 統一基礎訂單渲染器 v2 ====================
// 合併自（已移除孤兒檔案 base-order-renderer.js / optimized-base-renderer.js）：
//   - BaseRenderer (renderers/base-renderer.js) — 支付方式徽章、格式化工具
//   - CommonUtils (common-utils.js) — 靜態工具函數
//   - 原 BaseOrderRenderer — 生命週期管理、數據流
//   - 原 OptimizedBaseRenderer — DocumentFragment、倒計時、事件管理
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
        this.eventListeners = new Map();      // key -> { target, event, handler }
        this.hasInitialData = false;
        this.hasRenderedOnce = false;  // 追蹤是否已渲染過一次（初始加載用）
        this.isReady = false;
        this.cachedOrders = null;
        this.isProcessingAction = false;
        this.refreshTimer = null;

        // 模板快取（Phase 3C 效能優化）
        /** @type {Map<string, string>} 模板快取 Map */
        this._templateCache = new Map();
        /** @type {number} 模板快取最大數量（防止記憶體洩漏） */
        this._templateCacheMaxSize = 50;

        // 延遲初始化，確保 DOM 就緒
        setTimeout(() => this.initialize(), 100);
    }

    // ==================== 訂單 ID 標準化方法 ====================

    /**
     * 獲取訂單 ID（標準化 order.id / order.order_id）
     * 統一處理後端可能回傳不同欄位名稱的情況
     * @param {Object} order - 訂單數據物件
     * @returns {number|string} 訂單 ID
     */
    _getOrderId(order) {
        return order.id || order.order_id;
    }

    /**
     * 獲取訂單編號（優先使用 order_number，其次為 id）
     * @param {Object} order - 訂單數據物件
     * @returns {number|string} 訂單編號
     */
    _getOrderNumber(order) {
        return order.order_number || order.id || order.order_id;
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

        // Phase 4 A1: 統一 all_data 渲染
        // 只監聽 all_data，不再獨立監聽 dataKey，消除冗餘渲染
        // 使用 requestAnimationFrame 防抖，避免多次通知重複渲染
        this._pendingAllDataRender = false;
        
        window.unifiedDataManager.registerListener('all_data', (allData) => {
            const orders = allData[dataKey];
            if (orders) {
                this.hasInitialData = true;
                // 直接渲染，確保非活躍標籤頁也即時更新
                this.renderOrders(orders);
                this.hasRenderedOnce = true;
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

        // Phase 4 B1: 增量 DOM 更新
        // 檢查是否有訂單
        if (!orders || orders.length === 0) {
            console.log(`📭 ${this.orderType} 訂單列表為空`);
            this.showEmpty();
            this.currentOrders.clear();
            return;
        }

        // 對訂單進行排序
        const ordersWithSortKey = orders.map(o => ({
            id: this._getOrderId(o),
            data: o,
            sortKey: this._getSortKey(o)
        }));
        const sortedOrders = this.sortOrders(orders);

        // 構建新的 ID 集合
        const newOrderIds = new Set(ordersWithSortKey.map(o => o.id));

        // 移除不再存在的訂單
        let hasRemoved = false;
        this.currentOrders.forEach((entry, id) => {
            if (!newOrderIds.has(id)) {
                entry.element.remove();
                this.currentOrders.delete(id);
                hasRemoved = true;
            }
        });

        // 找出需要新增的訂單（比對現有 ID）
        const newOrders = sortedOrders.filter(o => !this.currentOrders.has(this._getOrderId(o)));

        // 如果沒有任何變化，跳過
        if (!hasRemoved && newOrders.length === 0 && this.currentOrders.size === sortedOrders.length) {
            console.log(`⏭️ ${this.orderType} 訂單無變化，跳過重建`);
            return;
        }

        console.log(`🎨 ${this.orderType} 增量更新: 現有=${this.currentOrders.size}, 新增=${newOrders.length}, 總數=${sortedOrders.length}`);

        // 清理現有計時器
        this.cleanupTimers();

        // 新增訂單
        if (newOrders.length > 0) {
            const fragment = document.createDocumentFragment();
            newOrders.forEach(order => {
                const orderElement = this.createOrderElement(order);
                fragment.appendChild(orderElement);
                this.currentOrders.set(this._getOrderId(order), {
                    element: orderElement,
                    data: order,
                    updated: new Date().getTime()
                });
            });

            // 根據排序找到正確的插入位置
            sortedOrders.forEach(order => {
                const id = this._getOrderId(order);
                if (!this.currentOrders.has(id)) return;
                const existingEl = this.currentOrders.get(id).element;
                if (existingEl.parentNode !== orderList) {
                    // 找到應該插入的位置
                    let insertBefore = null;
                    for (const sortedOrder of sortedOrders) {
                        const sid = this._getOrderId(sortedOrder);
                        if (sid === id) break;
                        const existing = this.currentOrders.get(sid);
                        if (existing && existing.element.parentNode === orderList) {
                            insertBefore = existing.element.nextSibling;
                        }
                    }
                    orderList.insertBefore(existingEl, insertBefore || null);
                }
            });
        }

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

        console.log(`✅ ${this.orderType} 增量更新完成`);
    }

    /**
     * 獲取排序鍵（默認使用創建時間）
     * @protected
     */
    _getSortKey(order) {
        return order.created_at_iso || order.created_at || '';
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

    // ==================== 模板快取（Phase 3C 效能優化） ====================

    /**
     * 獲取快取的模板 HTML
     * 避免重複拼接相同的模板字符串，減少 GC 壓力
     * @param {string} key - 模板鍵名（例如 'order-card', 'badge-group'）
     * @param {Function} builderFn - 模板建構函數，首次調用時執行並快取結果
     * @returns {string} 模板 HTML
     */
    getCachedTemplate(key, builderFn) {
        if (this._templateCache.has(key)) {
            return this._templateCache.get(key);
        }

        // 檢查快取是否已滿，若已滿則刪除最早的一筆
        if (this._templateCache.size >= this._templateCacheMaxSize) {
            const firstKey = this._templateCache.keys().next().value;
            this._templateCache.delete(firstKey);
        }

        const html = builderFn();
        this._templateCache.set(key, html);
        return html;
    }

    /**
     * 清除模板快取
     * 在需要強制重新生成模板時調用（例如語言切換、主題切換）
     */
    clearTemplateCache() {
        this._templateCache.clear();
    }

    // ==================== 共用渲染方法 ====================

    /**
     * 渲染訂單項目列表
     * @param {Array} items - 訂單項目數組
     * @param {Object} [options] - 配置選項
     * @param {number} [options.imageWidth=105] - 圖片容器寬度
     * @param {number} [options.imageHeight=110] - 圖片容器高度
     * @returns {string} HTML 字符串
     */
    renderOrderItems(items, options = {}) {
        if (!items || items.length === 0) {
            return '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }

        const imgWidth = options.imageWidth || 105;
        const imgHeight = options.imageHeight || 110;


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
            item.cup_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">water_full</span> 杯量: <span class="ov">${item.cup_level_cn}</span></span>` : '',
            (item.strength_level_cn || item.strength_level) ? `<span class="option-item"><span class="icon material-symbols-outlined">bolt</span> 濃度: <span class="ov">${item.strength_level_cn || item.strength_level}</span></span>` : '',
            item.milk_level_cn ? `<span class="option-item"><span class="icon material-symbols-outlined">humidity_mid</span> 奶量: <span class="ov">${item.milk_level_cn}</span></span>` : '',
            item.grinding_level_cn ? `<span class="option-item">研磨: <span class="ov">${item.grinding_level_cn}</span></span>` : '',
            item.weight_cn ? `<span class="option-item">重量: <span class="ov">${item.weight_cn}</span></span>` : '',
            item.weight ? `<span class="option-item">重量: <span class="ov">${item.weight}</span></span>` : '',
            ...Object.entries(item.extra_options_cn || {}).map(([k, v]) => `<span class="option-item"><span class="icon material-symbols-outlined">${(item.extra_options_icons || {})[k] || 'add_circle'}</span> ${(item.extra_options_labels || {})[k] || k}: <span class="ov">${v}</span></span>`)
        ].filter(Boolean);

        return `<div class="bc-options-row">${options.join('')}</div>`;
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
        const orderNumber = this._getOrderNumber(order);
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
        div.setAttribute('data-order-id', this._getOrderId(order));
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

    // ==================== 全域倒數計時（優化版） ====================
    // 使用單一全域 setInterval 取代每個訂單獨立的 setInterval
    // 避免大量 timer 同時運作造成的效能問題

    /**
     * 啟動全域倒數計時循環
     * 所有渲染器共享一個 timer，透過 DOM 查詢更新所有活躍的倒數計時
     */
    static startGlobalCountdown() {
        if (BaseOrderRendererV2._globalTimerRunning) return;
        BaseOrderRendererV2._globalTimerRunning = true;

        BaseOrderRendererV2._globalTimer = setInterval(() => {
            // 查詢所有活躍的倒數計時 badge
            const activeBadges = document.querySelectorAll('.countdown-badge.active');
            const now = new Date();

            activeBadges.forEach(badge => {
                const estimatedTimeStr = badge.dataset.estimatedTime;
                const countdownText = badge.querySelector('.countdown-text');
                if (!estimatedTimeStr || !countdownText) return;

                const estimatedTime = new Date(estimatedTimeStr);
                const diffMs = estimatedTime - now;

                if (diffMs <= 0) {
                    // 倒數完成，標記為已完成
                    countdownText.textContent = '已完成';
                    badge.classList.remove('active', 'badge-secondary');
                    badge.classList.add('badge-success');

                    const icon = badge.querySelector('i');
                    if (icon) {
                        icon.className = 'fas fa-check mr-1';
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
            });
        }, 1000);

        console.log('🌍 全域倒數計時已啟動（單一 setInterval）');
    }

    /**
     * 停止全域倒數計時循環
     */
    static stopGlobalCountdown() {
        if (BaseOrderRendererV2._globalTimer) {
            clearInterval(BaseOrderRendererV2._globalTimer);
            BaseOrderRendererV2._globalTimer = null;
            BaseOrderRendererV2._globalTimerRunning = false;
            console.log('🌍 全域倒數計時已停止');
        }
    }

    /**
     * 啟動單個訂單的倒數計時
     * 不再建立獨立的 setInterval，而是將 badge 標記為 active
     * 由全域 timer 統一更新
     */
    startCountdown(badge, orderId, estimatedTime) {
        // 確保全域 timer 已啟動
        BaseOrderRendererV2.startGlobalCountdown();

        // 在 badge 上儲存預計完成時間
        badge.dataset.estimatedTime = estimatedTime.toISOString();
        badge.classList.add('active');

        // 立即更新一次
        const countdownText = badge.querySelector('.countdown-text');
        if (!countdownText) return;

        const now = new Date();
        const diffMs = estimatedTime - now;

        if (diffMs <= 0) {
            this.markCountdownCompleted(badge, estimatedTime.toISOString());
            return;
        }

        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffSecs = Math.floor((diffMs % (1000 * 60)) / 1000);

        if (diffMins > 0) {
            countdownText.textContent = `預計完成: ${diffMins}分${diffSecs.toString().padStart(2, '0')}秒`;
        } else {
            countdownText.textContent = `預計完成: ${diffSecs}秒`;
        }
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
        badge.classList.remove('active', 'badge-secondary');
        badge.classList.add('badge-success');

        const icon = badge.querySelector('i');
        if (icon) {
            icon.className = 'fas fa-check mr-1';
        }

        // ===== 將訂單卡片從「進行中」容器移動到「已完成」容器 =====
        // 從 badge 向上找到訂單卡片容器
        const orderItem = badge.closest('.order-item');
        if (!orderItem) {
            console.warn('⚠️ markCountdownCompleted: 找不到訂單卡片容器');
            return;
        }

        // 獲取訂單 ID
        const orderId = orderItem.getAttribute('data-order-id');
        if (!orderId) {
            console.warn('⚠️ markCountdownCompleted: 訂單卡片缺少 data-order-id');
            return;
        }

        // 找到「已完成」容器
        const completedList = document.getElementById('countdown-completed-content');
        const activeList = document.getElementById('countdown-active-content');
        const completedEmpty = document.getElementById('countdown-completed-empty');
        const activeEmpty = document.getElementById('countdown-active-empty');

        if (!completedList || !activeList) {
            console.warn('⚠️ markCountdownCompleted: 找不到子標籤頁容器');
            return;
        }

        // 檢查訂單是否已經在「已完成」容器中（避免重複移動）
        if (orderItem.parentNode === completedList) {
            return;
        }

        // 將訂單卡片移動到「已完成」容器
        completedList.appendChild(orderItem);

        // 更新進行中容器的顯示/隱藏
        if (activeList.children.length === 0) {
            activeList.style.display = 'none';
            if (activeEmpty) activeEmpty.style.display = 'block';
        }

        // 更新已完成容器的顯示/隱藏
        completedList.style.display = 'block';
        if (completedEmpty) completedEmpty.style.display = 'none';

        console.log(`📦 訂單 ${orderId} 倒計時結束，已移動到「已完成」子標籤頁`);
    }

    cleanupTimers() {
        // 全域 timer 由靜態方法管理，不在實例層級清理
        // renderOrders 中的 cleanupTimers 不應停止全域 timer
        // 因為全域 timer 是所有 renderer 共享的，不應由單次重建停止
        // 全域 timer 只在 cleanup() 方法中停止
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

    // ==================== API 請求（共享方法） ====================

    /**
     * 發送 POST 請求到 API
     * 優先使用 apiService，如果不可用則使用 fetch
     * @param {string} url - API URL
     * @param {Object} data - 請求數據
     * @returns {Promise<Object>} 響應數據
     */
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

    // ==================== 通用業務操作處理 ====================

    /**
     * 執行訂單操作（通用方法，減少各渲染器重複程式碼）
     * 
     * 統一處理所有訂單操作的通用模式：
     * 1. isProcessingAction 檢查（防止重複提交）
     * 2. 設定 isProcessingAction = true
     * 3. try/catch/finally 包裹 API 調用
     * 4. 成功/失敗 Toast 通知
     * 5. forceRefresh() 刷新數據
     * 6. finally 中重置 isProcessingAction = false
     * 
     * @protected
     * @async
     * @param {Object} order - 訂單數據物件
     * @param {string} url - API URL（可使用 {orderId} 佔位符）
     * @param {Object} [options] - 配置選項
     * @param {string} [options.successMessage] - 成功時顯示的 Toast 訊息
     * @param {string} [options.failMessage] - 失敗時顯示的 Toast 訊息前綴
     * @param {string} [options.errorMessage] - 異常時顯示的 Toast 訊息
     * @param {Object} [options.extraData] - 額外的請求數據
     * @param {boolean} [options.requireConfirm=false] - 是否需要確認對話框
     * @param {string} [options.confirmMessage] - 確認對話框訊息
     * @returns {Promise<boolean>} 操作是否成功
     */
    async _executeOrderAction(order, url, options = {}) {
        if (this.isProcessingAction) return false;
        this.isProcessingAction = true;

        const {
            successMessage = '✅ 操作成功',
            failMessage = '❌ 操作失敗',
            errorMessage = '❌ 操作時發生錯誤',
            extraData = {},
            requireConfirm = false,
            confirmMessage = '確定要執行此操作嗎？'
        } = options;

        // 需要確認對話框
        if (requireConfirm) {
            if (!confirm(confirmMessage)) {
                this.isProcessingAction = false;
                return false;
            }
        }

        // Step 3: 改用 OrderActionService 處理 API 調用 + 數據刷新 + 通知
        if (window.orderActionService) {
            const orderId = this._getOrderId(order);
            const finalUrl = url.replace('{orderId}', orderId);
            
            const result = await window.orderActionService.executeOrderAction(
                orderId, finalUrl, {
                    successMessage,
                    failMessage,
                    errorMessage,
                    extraData
                }
            );
            
            this.isProcessingAction = false;
            return result;
        }
        
        // 降級方案：保留原有邏輯
        try {
            const orderId = this._getOrderId(order);
            const finalUrl = url.replace('{orderId}', orderId);
            const result = await this._apiPost(finalUrl, { order_id: orderId, ...extraData });

            if (result && result.success) {
                if (window.unifiedDataManager) {
                    await window.unifiedDataManager.loadUnifiedData(true);
                }
                if (window.unifiedDataManager?.currentData) {
                    window.unifiedDataManager.notifyAllListeners();
                }
                this.showToast(successMessage, 'success');
                return true;
            } else {
                this.showToast(`${failMessage}: ${result?.error || '未知錯誤'}`, 'error');
                return false;
            }
        } catch (error) {
            console.error(`❌ ${errorMessage}:`, error);
            this.showToast(errorMessage, 'error');
            return false;
        } finally {
            this.isProcessingAction = false;
        }
    }

    /**
     * 獲取 CSRF Token
     * @returns {string} CSRF Token
     */
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
