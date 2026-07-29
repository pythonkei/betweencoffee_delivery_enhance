// static/js/staff-order-management/services/order-action-service.js
// ==================== 統一的訂單操作服務 ====================
// 
// 功能：整合 QueueManager 和 v2 Renderers 的業務操作
// - 開始製作
// - 標記為就緒
// - 標記為已提取
// - FPS 付款確認
// - 現金付款確認
// - 取消訂單
//
// 所有操作統一流程：
// 1. 檢查 isProcessing（防止重複提交）
// 2. 執行 API 調用
// 3. 等待數據刷新
// 4. 強制通知所有渲染器
// 5. 顯示 Toast 通知
//
// 依賴：
// - ApiService (services/api-service.js)
// - ToastService (services/toast-service.js)
// - UnifiedDataManager (unified-data-manager.js)

class OrderActionService {
    constructor() {
        console.log('🔄 初始化訂單操作服務...');
        
        // 防止重複提交
        this.isProcessing = false;
        
        console.log('✅ 訂單操作服務初始化完成');
    }
    
    // ==================== 共用輔助方法 ====================
    
    /**
     * 獲取 CSRF Token
     */
    getCsrfToken() {
        // 優先使用 ApiService
        if (window.apiService && typeof window.apiService.getCsrfToken === 'function') {
            return window.apiService.getCsrfToken();
        }
        
        // 從 cookie 獲取
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    return decodeURIComponent(cookie.substring(10));
                }
            }
        }
        
        // 從 meta 標籤獲取
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        return null;
    }
    
    /**
     * 顯示 Toast 通知
     */
    showToast(message, type = 'info') {
        if (window.toast) {
            const toastType = type === 'success' ? 'success' :
                             type === 'error' ? 'error' :
                             type === 'warning' ? 'warning' : 'info';
            window.toast[toastType](message);
        } else if (window.orderManager && window.orderManager.showToast) {
            window.orderManager.showToast(message, type);
        }
    }
    
    /**
     * 刷新數據並通知所有渲染器
     */
    async refreshAndNotify() {
        if (window.unifiedDataManager) {
            await window.unifiedDataManager.loadUnifiedData(true);
            if (window.unifiedDataManager.currentData) {
                window.unifiedDataManager.notifyAllListeners();
            }
        }
    }
    
    /**
     * 發送 POST 請求
     */
    async post(url, data = {}) {
        const csrfToken = this.getCsrfToken();
        if (!csrfToken) {
            throw new Error('無法獲取安全令牌，請刷新頁面重試');
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(data),
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || result.message || `HTTP ${response.status}`);
        }
        
        if (!result.success) {
            throw new Error(result.error || result.message || '操作失敗');
        }
        
        return result;
    }
    
    // ==================== 業務操作 ====================
    
    /**
     * 開始製作（從等待中轉到進行中）
     */
    async startPreparation(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/queue/start/${orderId}/`, {});
            
            // 觸發事件
            document.dispatchEvent(new CustomEvent('order_started_preparing', {
                detail: { 
                    order_id: orderId,
                    estimated_ready_time: result.estimated_ready_time
                }
            }));
            
            // 等待刷新
            await this.refreshAndNotify();
            
            this.showToast(`✅ 已開始製作訂單 #${orderId}`, 'success');
            return true;
        } catch (error) {
            this.showToast(`❌ 開始製作失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 標記為就緒（從進行中轉到已就緒）
     */
    async markAsReady(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/queue/ready/${orderId}/`, {});
            
            document.dispatchEvent(new CustomEvent('order_marked_ready', {
                detail: { order_id: orderId }
            }));
            
            await this.refreshAndNotify();
            
            this.showToast(`✅ 訂單 #${orderId} 已標記為就緒`, 'success');
            return true;
        } catch (error) {
            this.showToast(`❌ 標記就緒失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 標記為已提取（從已就緒轉到已完成）
     */
    async markAsCollected(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/queue/collected/${orderId}/`, {});
            
            document.dispatchEvent(new CustomEvent('order_collected', {
                detail: { order_id: orderId }
            }));
            
            await this.refreshAndNotify();
            
            this.showToast(`✅ 訂單 #${orderId} 已標記為已提取`, 'success');
            return true;
        } catch (error) {
            this.showToast(`❌ 標記提取失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 通過 API 執行訂單操作（供 v2 Renderers 的 _executeOrderAction 使用）
     */
    async executeOrderAction(orderId, url, options = {}) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        const {
            successMessage = '✅ 操作成功',
            failMessage = '❌ 操作失敗',
            errorMessage = '❌ 操作時發生錯誤',
            extraData = {},
        } = options;
        
        try {
            const finalUrl = url.replace('{orderId}', orderId);
            const result = await this.post(finalUrl, { order_id: orderId, ...extraData });
            
            await this.refreshAndNotify();
            
            this.showToast(successMessage, 'success');
            return true;
        } catch (error) {
            this.showToast(`${failMessage}: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 確認 FPS 付款
     */
    async confirmFpsPayment(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/api/fps/confirm-payment/${orderId}/`, {});
            
            await this.refreshAndNotify();
            
            document.dispatchEvent(new CustomEvent('fps_payment_confirmed', {
                detail: { 
                    order_id: orderId,
                    payment_status: 'paid',
                    status: result.status || 'waiting'
                }
            }));
            
            this.showToast(`✅ 訂單 #${orderId} FPS 付款已確認`, 'success');
            return { success: true, status: result.status || 'waiting' };
        } catch (error) {
            this.showToast(`❌ FPS 付款確認失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 確認現金付款
     */
    async confirmCashPayment(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/api/cash/confirm-payment/${orderId}/`, {});
            
            await this.refreshAndNotify();
            
            document.dispatchEvent(new CustomEvent('cash_payment_confirmed', {
                detail: { 
                    order_id: orderId,
                    payment_status: 'paid',
                    status: result.status || 'waiting'
                }
            }));
            
            this.showToast(`✅ 訂單 #${orderId} 現金付款已確認`, 'success');
            return { success: true, status: result.status || 'waiting' };
        } catch (error) {
            this.showToast(`❌ 現金付款確認失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
    
    /**
     * 切換優先處理狀態（toggle on/off）
     * @returns {Object|null} {is_expedited: boolean} 或 null（失敗時）
     */
    async markAsExpedited(orderId) {
        if (this.isProcessing) return null;
        this.isProcessing = true;

        try {
            const result = await this.post(`/eshop/api/orders/${orderId}/expedite/`, {});

            await this.refreshAndNotify();

            document.dispatchEvent(new CustomEvent('order_expedited', {
                detail: { 
                    order_id: orderId,
                    is_expedited: result.data?.is_expedited ?? true
                }
            }));

            return result.data || { is_expedited: true };
        } catch (error) {
            return null;
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * 取消訂單
     */
    async cancelOrder(orderId) {
        if (this.isProcessing) return false;
        this.isProcessing = true;
        
        try {
            const result = await this.post(`/eshop/api/cancel-order/${orderId}/`, {});
            
            await this.refreshAndNotify();
            
            document.dispatchEvent(new CustomEvent('order_cancelled', {
                detail: { order_id: orderId }
            }));
            
            this.showToast(`✅ 訂單 #${orderId} 已取消`, 'success');
            return { success: true };
        } catch (error) {
            this.showToast(`❌ 取消訂單失敗: ${error.message}`, 'error');
            return false;
        } finally {
            this.isProcessing = false;
        }
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    window.OrderActionService = OrderActionService;
    window.orderActionService = new OrderActionService();
    console.log('🌍 OrderActionService 已註冊到 window 對象');
}