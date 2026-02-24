// static/js/staff-order-management/common-utils.js
// ==================== 共用工具模塊 ====================
// 提取所有渲染器的共用工具函數，減少代碼重複

class CommonUtils {
    /**
     * 顯示Toast通知
     * @param {string} message - 消息內容
     * @param {string} type - 類型 ('info', 'success', 'error', 'warning')
     */
    static showToast(message, type = 'info') {
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
     * 分析訂單類型
     * @param {Object} order - 訂單對象
     * @returns {Object} 訂單類型信息
     */
    static analyzeOrderType(order) {
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
     * 生成訂單類型徽章HTML
     * @param {Object} order - 訂單對象
     * @param {Object} typeInfo - 訂單類型信息
     * @returns {string} 徽章HTML
     */
    static generateOrderTypeBadges(order, typeInfo) {
        const { isMixedOrder, isBeansOnly } = typeInfo;
        
        // 1. 快速訂單徽章（優先級最高）
        if (order.is_quick_order) {
            return `
                <span class="badge badge-quickorder order-type-badge">
                    <i class="fas fa-bolt mr-1"></i>快速訂單
                </span>
            `;
        }
        // 2. 混合訂單徽章（次優先級）
        else if (isMixedOrder) {
            return `
                <span class="badge badge-primary order-type-badge">
                    <i class="fas fa-random mr-1"></i>混合訂單
                </span>
            `;
        }
        // 3. 普通訂單徽章（默認）
        else {
            return `
                <span class="badge badge-info order-type-badge">
                    <i class="fas fa-shopping-bag mr-1"></i>普通訂單
                </span>
            `;
        }
    }
    
    /**
     * 生成數量徽章HTML
     * @param {Object} typeInfo - 訂單類型信息
     * @returns {string} 徽章HTML
     */
    static generateQuantityBadges(typeInfo) {
        const { coffeeCount, beanCount } = typeInfo;
        
        let badges = '';
        
        if (coffeeCount > 0) {
            badges += `
                <span hidden class="badge badge-dark ml-1">
                    <i class="fas fa-mug-hot mr-1"></i>${coffeeCount}杯
                </span>
            `;
        }
        
        if (beanCount > 0) {
            badges += `
                <span hidden class="badge badge-warning ml-1">
                    <i class="fas fa-seedling mr-1"></i>${beanCount}包咖啡豆
                </span>
            `;
        }
        
        return badges;
    }
    
    /**
     * 渲染訂單項目
     * @param {Array} items - 訂單項目數組
     * @returns {string} HTML字符串
     */
    static renderOrderItems(items) {
        if (!items || items.length === 0) {
            return '<p class="text-muted text-center py-3">暫無商品詳細信息</p>';
        }

        let itemsHTML = '';

        items.forEach(item => {
            const itemPrice = parseFloat(item.price || 0).toFixed(2);
            const itemTotal = parseFloat(item.total_price || 0).toFixed(2);
            const itemImage = item.image || CommonUtils.getDefaultImage(item.type);

            itemsHTML += `
                <div class="d-flex align-items-center mb-3">
                    <div class="mr-3">
                        <div class="p-2 rounded d-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                            <img src="${itemImage}" 
                                 alt="${item.name || '商品'}" 
                                 class="img-fluid" 
                                 style="max-height: 75px;"
                                 loading="lazy">
                        </div>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${item.name || '商品'}</h6>
                        <p class="mb-1 text-muted">數量: ${item.quantity || 1}</p>
                        <div class="text-muted">
                            ${item.cup_level_cn ? `杯型: ${item.cup_level_cn}` : ''}
                            ${item.milk_level_cn ? ` | 牛奶: ${item.milk_level_cn}` : ''}
                            ${item.grinding_level_cn ? ` | 研磨: ${item.grinding_level_cn}` : ''}
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

        return itemsHTML;
    }
    
    /**
     * 獲取默認圖片
     * @param {string} itemType - 商品類型
     * @returns {string} 圖片URL
     */
    static getDefaultImage(itemType) {
        if (itemType === 'coffee') {
            return '/static/images/default-coffee.png';
        } else if (itemType === 'bean') {
            return '/static/images/default-beans.png';
        }
        return '/static/images/default-product.png';
    }
    
    /**
     * 格式化香港時間
     * @param {string} timeString - 時間字符串
     * @returns {string} 格式化後的時間
     */
    static formatHKTime(timeString) {
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
    static formatHKTimeOnly(timeString) {
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
     * 檢查是否為當前活動標籤頁
     * @param {string} tabId - 標籤頁ID
     * @returns {boolean} 是否為活動標籤頁
     */
    static isActiveTab(tabId) {
        const tabElement = document.getElementById(tabId);
        return tabElement && tabElement.classList.contains('active');
    }
    
    /**
     * 更新最後更新時間
     * @param {string} elementId - 時間元素ID
     */
    static updateLastUpdateTime(elementId) {
        const timeElement = document.getElementById(elementId);
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
     * 防抖函數
     * @param {Function} func - 要執行的函數
     * @param {number} wait - 等待時間（毫秒）
     * @returns {Function} 防抖後的函數
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * 節流函數
     * @param {Function} func - 要執行的函數
     * @param {number} limit - 限制時間（毫秒）
     * @returns {Function} 節流後的函數
     */
    static throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    /**
     * 安全設置innerHTML（防止XSS）
     * @param {HTMLElement} element - 目標元素
     * @param {string} html - HTML內容
     */
    static safeSetInnerHTML(element, html) {
        if (!element) return;
        
        // 簡單的XSS防護：只允許安全的HTML標籤
        const safeHTML = html
            .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
            .replace(/javascript:/gi, '')
            .replace(/on\w+\s*=/gi, '');
        
        element.innerHTML = safeHTML;
    }
    
    /**
     * 創建DOM元素
     * @param {string} tag - 標籤名
     * @param {Object} attributes - 屬性對象
     * @param {Array} children - 子元素數組
     * @returns {HTMLElement} 創建的元素
     */
    static createElement(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);
        
        // 設置屬性
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else if (key === 'innerHTML') {
                CommonUtils.safeSetInnerHTML(element, value);
            } else if (key.startsWith('on')) {
                element.addEventListener(key.substring(2).toLowerCase(), value);
            } else {
                element.setAttribute(key, value);
            }
        });
        
        // 添加子元素
        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });
        
        return element;
    }
}

// 全局註冊
if (typeof window !== 'undefined') {
    window.CommonUtils = CommonUtils;
    console.log('✅ 共用工具模塊已加載');
}

