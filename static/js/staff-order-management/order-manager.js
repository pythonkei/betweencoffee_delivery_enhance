// static/js/staff-order-management/order-manager.js
// ==================== 全局訂單管理器 - 統一數據流版本 ====================

class OrderManager {
    constructor() {
        console.log('🔄 初始化全局訂單管理器（統一數據流版）...');
        
        // 全局狀態
        this.isInitialized = false;
        this.systemStatus = {
            unifiedDataManager: false,
            badgeManager: false,
            queueManager: false,
            webSocketManager: false,
            lastUpdateTime: null
        };
        
        // 初始化
        this.init();
    }
    
    // ==================== 初始化方法 ====================
    
    async init() {
        if (this.isInitialized) return;
        
        try {
            console.log('🔄 全局訂單管理器初始化開始...');
            
            // 1. 等待統一數據管理器
            await this.waitForUnifiedManager();
            
            // 2. 監聽系統事件
            this.setupEventListeners();
            
            // 3. 設置全局助手
            this.setupGlobalHelpers();
            
            this.isInitialized = true;
            this.systemStatus.lastUpdateTime = new Date();
            
            console.log('✅ 全局訂單管理器初始化完成');
            
            // 觸發初始化完成事件
            document.dispatchEvent(new CustomEvent('order_manager_initialized', {
                detail: { timestamp: new Date().toISOString() }
            }));
            
        } catch (error) {
            console.error('❌ 全局訂單管理器初始化失敗:', error);
            this.showError('系統初始化失敗', error.message);
        }
    }
    
    /**
     * 等待統一數據管理器
     */
    waitForUnifiedManager() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 15;
            
            const checkInterval = setInterval(() => {
                attempts++;
                
                if (window.unifiedDataManager) {
                    clearInterval(checkInterval);
                    this.systemStatus.unifiedDataManager = true;
                    console.log('✅ UnifiedDataManager 已連接');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    clearInterval(checkInterval);
                    reject(new Error('UnifiedDataManager 加載超時'));
                } else {
                    console.log(`⏳ 等待UnifiedDataManager... (${attempts}/${maxAttempts})`);
                }
            }, 500);
        });
    }
    
    /**
     * 設置事件監聽器
     */
    setupEventListeners() {
        // 統一數據更新事件
        document.addEventListener('unified_data_updated', (event) => {
            this.handleUnifiedDataUpdate(event.detail);
        });
        
        // 統一數據錯誤事件
        document.addEventListener('unified_data_error', (event) => {
            this.handleUnifiedDataError(event.detail.error);
        });
        
        // 徽章更新事件
        document.addEventListener('badges_updated', (event) => {
            console.log('📢 全局管理器收到徽章更新:', event.detail.badges);
            this.systemStatus.lastUpdateTime = new Date();
        });
        
        // WebSocket連接事件
        document.addEventListener('websocket_connected', () => {
            this.systemStatus.webSocketManager = true;
            console.log('✅ WebSocket 已連接');
        });
        
        // WebSocket斷開事件
        document.addEventListener('websocket_disconnected', () => {
            this.systemStatus.webSocketManager = false;
            console.warn('⚠️ WebSocket 已斷開');
        });
        
        // 訂單操作事件
        document.addEventListener('order_started_preparing', (event) => {
            this.handleOrderStartedPreparing(event.detail);
        });
        
        document.addEventListener('order_marked_ready', (event) => {
            this.handleOrderMarkedReady(event.detail);
        });
        
        document.addEventListener('order_collected', (event) => {
            this.handleOrderCollected(event.detail);
        });
        
        // 頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // 窗口獲取焦點
        window.addEventListener('focus', () => {
            this.handleWindowFocus();
        });
    }
    
    /**
     * 設置全局助手
     */
    setupGlobalHelpers() {
        // 全局刷新函數
        window.refreshAllOrders = () => {
            if (window.unifiedDataManager) {
                window.unifiedDataManager.loadUnifiedData(true);
                this.showToast('🔄 正在刷新所有數據...', 'info');
            }
        };
        
        // 系統狀態檢查
        window.checkSystemStatus = () => {
            return this.checkSystemStatus();
        };
        
        // 強制同步
        window.forceSync = async () => {
            return await this.forceSync();
        };
        
        // 顯示訂單詳情
        window.showOrderDetails = (orderId) => {
            this.showOrderDetails(orderId);
        };
        
        console.log('✅ 全局助手已設置');
    }
    
    // ==================== 事件處理方法 ====================
    
    /**
     * 處理統一數據更新
     */
    handleUnifiedDataUpdate(data) {
        console.log('📢 全局管理器收到統一數據更新');
        
        // 更新系統狀態時間戳
        this.systemStatus.lastUpdateTime = new Date();
        
        // 更新其他組件狀態
        this.updateComponentStatus();
        
        // 如果數據中包含統計信息，可以進行額外處理
        if (data.badge_summary) {
            // 徽章數據已由徽章管理器處理，這裡只記錄日誌
            console.log('📊 訂單統計:', data.badge_summary);
        }
    }
    
    /**
     * 處理統一數據錯誤
     */
    handleUnifiedDataError(error) {
        console.error('❌ 全局管理器收到統一數據錯誤:', error);
        
        // 顯示錯誤提示
        this.showError('數據加載失敗', error.message || '未知錯誤');
        
        // 嘗試自動重試（等待5秒）
        setTimeout(() => {
            if (window.unifiedDataManager) {
                console.log('🔄 自動重試數據加載...');
                window.unifiedDataManager.loadUnifiedData();
            }
        }, 5000);
    }
    
    /**
     * 處理訂單開始製作
     */
    handleOrderStartedPreparing(detail) {
        const orderId = detail.order_id;
        const estimatedTime = detail.estimated_ready_time;

        console.log(`🔄 訂單 #${orderId} 開始製作，預計完成: ${estimatedTime}`);

        // 注意：成功訊息已在 queue-manager.js 中顯示，這裡不再重複顯示
        // 只處理其他邏輯，如更新狀態、播放聲音等

        // 更新隊列狀態
        if (window.queueManager) {
            // 隊列管理器會自動處理
        }
    }

    /**
     * 處理訂單標記為就緒
     */
    handleOrderMarkedReady(detail) {
        const orderId = detail.order_id;

        console.log(`🔄 訂單 #${orderId} 已標記為就緒`);

        // 注意：成功訊息已在 queue-manager.js 中顯示，這裡不再重複顯示
        // 只處理其他邏輯，如播放聲音

        // 播放提示音（如果支持）
        this.playNotificationSound('ready');
    }

    /**
     * 處理訂單已提取
     */
    handleOrderCollected(detail) {
        const orderId = detail.order_id;

        console.log(`🔄 訂單 #${orderId} 已標記為已提取`);

        // 注意：成功訊息已在 queue-manager.js 中顯示，這裡不再重複顯示
        // 只處理其他邏輯
    }
    
    /**
     * 處理頁面可見性變化
     */
    handleVisibilityChange() {
        if (!document.hidden) {
            console.log('🔄 頁面恢復可見，刷新數據');
            
            // 延遲刷新，避免網絡擁塞
            setTimeout(() => {
                if (window.unifiedDataManager) {
                    window.unifiedDataManager.loadUnifiedData();
                }
            }, 2000);
        }
    }
    
    /**
     * 處理窗口獲取焦點
     */
    handleWindowFocus() {
        console.log('🔄 窗口獲取焦點，檢查數據新鮮度');
        
        const now = new Date();
        const lastUpdate = this.systemStatus.lastUpdateTime;
        
        // 如果超過1分鐘沒有更新，則刷新數據
        if (lastUpdate && (now - lastUpdate) > 60000) {
            console.log('🔄 數據已過期，自動刷新');
            if (window.unifiedDataManager) {
                window.unifiedDataManager.loadUnifiedData();
            }
        }
    }
    
    /**
     * 更新組件狀態
     */
    updateComponentStatus() {
        this.systemStatus.badgeManager = !!window.badgeManager;
        this.systemStatus.queueManager = !!window.queueManager;
        this.systemStatus.webSocketManager = !!window.webSocketManager;
    }
    
    // ==================== 公共方法 ====================
    
    /**
     * 檢查系統狀態
     */
    checkSystemStatus() {
        const status = {
            initialized: this.isInitialized,
            unifiedDataManager: this.systemStatus.unifiedDataManager,
            badgeManager: this.systemStatus.badgeManager,
            queueManager: this.systemStatus.queueManager,
            webSocketManager: this.systemStatus.webSocketManager,
            lastUpdateTime: this.systemStatus.lastUpdateTime,
            currentTime: new Date(),
            uptime: this.getUptime()
        };
        
        console.log('🔍 系統狀態檢查:', status);
        
        // 顯示狀態面板
        this.showStatusPanel(status);
        
        return status;
    }
    
    /**
     * 強制同步所有數據
     */
    async forceSync() {
        try {
            console.log('🔄 開始強制同步...');
            
            this.showToast('🔄 正在強制同步...', 'info');
            
            // 1. 觸發統一數據刷新
            if (window.unifiedDataManager) {
                await window.unifiedDataManager.loadUnifiedData(true);
            }
            
            // 2. 觸發WebSocket重新連接（如果需要）
            if (window.webSocketManager && window.webSocketManager.reconnect) {
                window.webSocketManager.reconnect();
            }
            
            this.showToast('✅ 強制同步完成', 'success');
            console.log('✅ 強制同步完成');
            
            return { success: true, message: '同步完成' };
            
        } catch (error) {
            console.error('❌ 強制同步失敗:', error);
            this.showToast('❌ 同步失敗: ' + error.message, 'error');
            return { success: false, error: error.message };
        }
    }
    
    /**
     * 顯示訂單詳情
     */
    async showOrderDetails(orderId) {
        try {
            console.log(`🔍 顯示訂單詳情: #${orderId}`);
            
            // 從統一數據管理器獲取數據
            if (window.unifiedDataManager && window.unifiedDataManager.currentData) {
                const allData = window.unifiedDataManager.currentData;
                
                // 在所有訂單中查找
                const allOrders = [
                    ...(allData.waiting_orders || []),
                    ...(allData.preparing_orders || []),
                    ...(allData.ready_orders || []),
                    ...(allData.completed_orders || [])
                ];
                
                const order = allOrders.find(o => o.id == orderId || o.order_id == orderId);
                
                if (order) {
                    this.displayOrderModal(order);
                    return;
                }
            }
            
            // 如果沒找到，從API獲取
            const response = await fetch(`/eshop/queue/order-details/${orderId}/`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.displayOrderModal(data.order);
                } else {
                    throw new Error(data.error || '獲取訂單詳情失敗');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
            
        } catch (error) {
            console.error(`獲取訂單 #${orderId} 詳情失敗:`, error);
            this.showToast(`❌ 獲取訂單詳情失敗: ${error.message}`, 'error');
        }
    }
    
    /**
     * 顯示訂單詳情模態框
     */
    displayOrderModal(order) {
        // 創建模態框
        const modalId = 'order-details-modal';
        let modal = document.getElementById(modalId);
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = modalId;
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('role', 'dialog');
            document.body.appendChild(modal);
        }
        
        // 構建模態框內容
        const itemsHtml = this.formatOrderItemsForModal(order);
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-file-invoice mr-2"></i>
                            訂單詳情 #${order.id}
                        </h5>
                        <button type="button" class="close" data-dismiss="modal">
                            <span>&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>基本信息</h6>
                                <p><strong>取餐碼:</strong> ${order.pickup_code || '無'}</p>
                                <p><strong>顧客姓名:</strong> ${order.name || '未提供'}</p>
                                <p><strong>電話:</strong> ${window.CommonUtils ? window.CommonUtils.formatPhoneNumber(order.phone || '') : (order.phone || '未提供')}</p>
                                <p><strong>總價:</strong> HKD ${order.total_price || '0.00'}</p>
                                <p><strong>支付方式:</strong> ${order.payment_method_display || order.payment_method || '未指定'}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>商品項目</h6>
                                ${itemsHtml}
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">關閉</button>
                    </div>
                </div>
            </div>
        `;
        
        // 顯示模態框
        $(modal).modal('show');
    }
    
    /**
     * 格式化訂單項目用於模態框
     */
    formatOrderItemsForModal(order) {
        const items = order.items || [];
        
        if (items.length === 0) {
            return '<p class="text-muted">無商品項目</p>';
        }
        
        let itemsHtml = '<div class="table-responsive">';
        itemsHtml += '<table class="table table-sm">';
        itemsHtml += '<thead><tr><th>商品</th><th>數量</th><th>單價</th><th>總價</th></tr></thead>';
        itemsHtml += '<tbody>';
        
        items.forEach(item => {
            const itemName = item.name || '未命名商品';
            const quantity = item.quantity || 1;
            const price = item.price || '0.00';
            const total = item.total_price || '0.00';
            
            itemsHtml += `
                <tr>
                    <td>${itemName}</td>
                    <td>${quantity}</td>
                    <td>HKD ${price}</td>
                    <td>HKD ${total}</td>
                </tr>
            `;
        });
        
        itemsHtml += '</tbody></table></div>';
        return itemsHtml;
    }
    
    // ==================== UI輔助方法 ====================
    
    /**
     * 顯示Toast通知 - 使用統一的 toast-manager.js
     */
    showToast(message, type = 'info') {
        // 優先使用統一的 toast-manager.js
        if (window.toast) {
            const toastType = type === 'success' ? 'success' : 
                             type === 'error' ? 'error' : 
                             type === 'warning' ? 'warning' : 'info';
            
            window.toast[toastType](message, this.getToastTitle(type));
        } else {
            // 備用方案：簡單的 alert
            console.log(`[${type.toUpperCase()}] ${message}`);
            
            // 創建簡單的提示
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show fixed-top`;
            alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 1050; max-width: 300px;';
            alertDiv.setAttribute('role', 'alert');
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="close" data-dismiss="alert">
                    <span>&times;</span>
                </button>
            `;
            
            document.body.appendChild(alertDiv);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 3000);
        }
    }
    
    /**
     * 顯示錯誤
     */
    showError(title, message) {
        this.showToast(`${title}: ${message}`, 'error');
    }
    
    /**
     * 顯示狀態面板
     */
    showStatusPanel(status) {
        const panelId = 'system-status-panel';
        let panel = document.getElementById(panelId);
        
        if (!panel) {
            panel = document.createElement('div');
            panel.id = panelId;
            panel.className = 'card';
            panel.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1050; width: 300px;';
            document.body.appendChild(panel);
        }
        
        const uptime = this.formatDuration(status.uptime);
        const lastUpdate = status.lastUpdateTime ? 
            new Date(status.lastUpdateTime).toLocaleTimeString('zh-HK') : '無';
        
        panel.innerHTML = `
            <div class="card-header">
                <h6 class="mb-0">系統狀態</h6>
            </div>
            <div class="card-body">
                <div class="mb-2">
                    <span class="badge ${status.unifiedDataManager ? 'badge-success' : 'badge-danger'} mr-1">統一數據</span>
                    <span class="badge ${status.badgeManager ? 'badge-success' : 'badge-danger'} mr-1">徽章</span>
                    <span class="badge ${status.queueManager ? 'badge-success' : 'badge-danger'} mr-1">隊列</span>
                    <span class="badge ${status.webSocketManager ? 'badge-success' : 'badge-danger'}">WebSocket</span>
                </div>
                <p class="mb-1 small"><strong>運行時間:</strong> ${uptime}</p>
                <p class="mb-1 small"><strong>最後更新:</strong> ${lastUpdate}</p>
                <p class="mb-0 small"><strong>當前時間:</strong> ${new Date().toLocaleTimeString('zh-HK')}</p>
            </div>
            <div class="card-footer text-right">
                <button class="btn btn-sm btn-primary mr-2" onclick="refreshAllOrders()">刷新</button>
                <button class="btn btn-sm btn-secondary" onclick="$('#${panelId}').remove()">關閉</button>
            </div>
        `;
        
        // 5秒後自動關閉
        setTimeout(() => {
            if (panel && panel.parentNode) {
                panel.style.opacity = '0.5';
                setTimeout(() => {
                    if (panel && panel.parentNode) {
                        panel.parentNode.removeChild(panel);
                    }
                }, 1000);
            }
        }, 5000);
    }
    
    // ==================== 輔助方法 ====================
    
    /**
     * 獲取運行時間
     */
    getUptime() {
        if (!this.systemStatus.lastUpdateTime) return 0;
        return Date.now() - this.systemStatus.lastUpdateTime.getTime();
    }
    
    /**
     * 格式化持續時間
     */
    formatDuration(ms) {
        if (ms < 1000) return '剛剛';
        
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds}秒`;
        
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}分鐘`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}小時`;
        
        const days = Math.floor(hours / 24);
        return `${days}天`;
    }
    
    /**
     * 獲取Toast標題
     */
    getToastTitle(type) {
        switch(type) {
            case 'success': return '成功';
            case 'error': return '錯誤';
            case 'warning': return '警告';
            default: return '信息';
        }
    }
    
    /**
     * 播放通知聲音
     */
    playNotificationSound(type) {
        // 簡單的聲音通知實現
        try {
            if (type === 'ready') {
                // 可以添加不同的聲音
                const audio = new Audio('/static/sounds/notification.mp3');
                audio.volume = 0.3;
                audio.play().catch(e => console.log('音頻播放失敗:', e));
            }
        } catch (error) {
            // 忽略音頻錯誤
        }
    }
    
    /**
     * 清理方法
     */
    cleanup() {
        console.log('🔄 清理全局訂單管理器...');
        
        // 移除事件監聽器
        document.removeEventListener('unified_data_updated', this.handleUnifiedDataUpdate);
        document.removeEventListener('unified_data_error', this.handleUnifiedDataError);
        document.removeEventListener('badges_updated', this.handleBadgesUpdated);
        
        // 移除全局助手
        delete window.refreshAllOrders;
        delete window.checkSystemStatus;
        delete window.forceSync;
        delete window.showOrderDetails;
        
        this.isInitialized = false;
        
        console.log('✅ 全局訂單管理器已清理');
    }
}

// ==================== 全局註冊 ====================

if (typeof window !== 'undefined') {
    window.OrderManager = OrderManager;
}