// static/js/staff-order-management/services/api-service.js
// ==================== 統一 API 服務 ====================
// 功能：提供統一的 API 調用接口，整合 CSRF token 獲取、錯誤處理、請求去重
// 依賴：無（獨立運行）
//
// 使用方式：
//   // POST 請求
//   ApiService.post('/eshop/api/fps/confirm-payment/123/', {})
//     .then(data => console.log(data))
//     .catch(error => console.error(error));
//
//   // GET 請求
//   ApiService.get('/eshop/api/orders/')
//     .then(data => console.log(data));
//
//   // 帶超時的請求
//   ApiService.post('/eshop/api/orders/', body, { timeout: 10000 });
//
// 整合方式：
//   在 HTML 中引入此文件後，即可在任何地方使用 ApiService
//   現有代碼中的 fetch 調用可逐步遷移到 ApiService

class ApiService {
    constructor() {
        this.name = 'ApiService';
        this.defaultTimeout = 15000; // 15秒超時
        this.pendingRequests = new Map(); // 請求去重
        this.retryCount = 1; // 失敗重試次數
        this.retryDelay = 1000; // 重試延遲
        
        console.log('🔄 ApiService 初始化...');
        console.log('✅ ApiService 初始化完成');
    }
    
    /**
     * 獲取 CSRF token（多種方法）
     */
    getCsrfToken() {
        let token = null;
        
        // 方法1：從 cookie 獲取
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === 'csrftoken=') {
                    token = decodeURIComponent(cookie.substring(10));
                    break;
                } else if (cookie.substring(0, 11) === 'csrf_token=') {
                    token = decodeURIComponent(cookie.substring(11));
                    break;
                } else if (cookie.substring(0, 8) === 'csrf=') {
                    token = decodeURIComponent(cookie.substring(8));
                    break;
                }
            }
        }
        
        // 方法2：從 meta 標籤獲取
        if (!token) {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                token = metaToken.getAttribute('content');
            }
        }
        
        // 方法3：從表單輸入獲取
        if (!token) {
            const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
            if (inputToken) {
                token = inputToken.value;
            }
        }
        
        // 方法4：從 Django 模板變量獲取
        if (!token && typeof django !== 'undefined' && django.csrf) {
            token = django.csrf.getToken();
        }
        
        return token;
    }
    
    /**
     * 生成請求唯一鍵（用於去重）
     */
    _getRequestKey(url, method, body) {
        return `${method}:${url}:${body ? JSON.stringify(body) : ''}`;
    }
    
    /**
     * 發送 API 請求
     * @param {string} url - API 端點
     * @param {Object} options - 請求選項
     * @param {string} options.method - HTTP 方法 (GET/POST/PUT/DELETE)
     * @param {Object} options.body - 請求體
     * @param {number} options.timeout - 超時時間（毫秒）
     * @param {boolean} options.deduplicate - 是否去重（預設 true）
     * @param {boolean} options.suppressErrors - 是否抑制錯誤 Toast（預設 false）
     * @returns {Promise<Object>} 響應數據
     */
    async request(url, options = {}) {
        const {
            method = 'GET',
            body = null,
            timeout = this.defaultTimeout,
            deduplicate = true,
            suppressErrors = false,
        } = options;
        
        const requestKey = this._getRequestKey(url, method, body);
        
        // 請求去重：如果相同請求正在進行中，返回已有的 Promise
        if (deduplicate && this.pendingRequests.has(requestKey)) {
            console.log(`⏭️ ApiService: 跳過重複請求 ${method} ${url}`);
            return this.pendingRequests.get(requestKey);
        }
        
        // 構建請求
        const fetchOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken(),
            },
        };
        
        if (body && method !== 'GET') {
            fetchOptions.body = JSON.stringify(body);
        }
        
        // 創建請求 Promise
        const requestPromise = this._executeWithRetry(url, fetchOptions, timeout, suppressErrors);
        
        // 記錄請求
        if (deduplicate) {
            this.pendingRequests.set(requestKey, requestPromise);
            // 請求完成後清理
            requestPromise.finally(() => {
                this.pendingRequests.delete(requestKey);
            });
        }
        
        return requestPromise;
    }
    
    /**
     * 執行請求（含重試邏輯）
     */
    async _executeWithRetry(url, fetchOptions, timeout, suppressErrors) {
        let lastError = null;
        
        for (let attempt = 0; attempt <= this.retryCount; attempt++) {
            try {
                const response = await this._executeWithTimeout(url, fetchOptions, timeout);
                return await this._handleResponse(response, url, suppressErrors);
            } catch (error) {
                lastError = error;
                
                // 最後一次嘗試失敗，不再重試
                if (attempt >= this.retryCount) break;
                
                // 某些錯誤不重試
                if (error.name === 'AbortError') {
                    console.warn(`⏱️ ApiService: 請求超時 ${url}，嘗試第 ${attempt + 2} 次`);
                } else if (error.status === 403) {
                    // 權限錯誤不重試
                    break;
                } else {
                    console.warn(`🔄 ApiService: 請求失敗 ${url}，嘗試第 ${attempt + 2} 次`);
                }
                
                // 等待後重試
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
            }
        }
        
        // 所有重試都失敗
        if (!suppressErrors) {
            this._showErrorToast(lastError);
        }
        throw lastError;
    }
    
    /**
     * 執行請求（含超時控制）
     */
    _executeWithTimeout(url, fetchOptions, timeout) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        fetchOptions.signal = controller.signal;
        
        return fetch(url, fetchOptions).finally(() => {
            clearTimeout(timeoutId);
        });
    }
    
    /**
     * 處理響應
     */
    async _handleResponse(response, url, suppressErrors) {
        console.log(`📡 ApiService: ${response.status} ${url}`);
        
        if (response.ok) {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return { success: true };
        }
        
        // 處理錯誤狀態碼
        let errorMessage;
        let errorData = null;
        
        try {
            errorData = await response.json();
            errorMessage = errorData.message || errorData.error || errorData.detail;
        } catch {
            try {
                errorMessage = await response.text();
            } catch {
                errorMessage = response.statusText;
            }
        }
        
        const error = new Error(errorMessage || `HTTP ${response.status}`);
        error.status = response.status;
        error.data = errorData;
        error.url = url;
        
        throw error;
    }
    
    /**
     * 顯示錯誤 Toast
     */
    _showErrorToast(error) {
        let message = error.message || '請求失敗';
        
        // 根據錯誤類型提供更友好的訊息
        if (error.name === 'AbortError') {
            message = '請求超時，請檢查網絡連接';
        } else if (error.status === 403) {
            message = '權限不足：請確認您有員工權限';
        } else if (error.status === 404) {
            message = '請求的資源不存在';
        } else if (error.status >= 500) {
            message = '伺服器錯誤，請稍後重試';
        }
        
        // 使用 ToastService 顯示錯誤（如果可用）
        if (window.toast && window.toast.error) {
            window.toast.error(`❌ ${message}`);
        }
    }
    
    // ==================== 便捷方法 ====================
    
    /**
     * GET 請求
     */
    get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }
    
    /**
     * POST 請求
     */
    post(url, body = {}, options = {}) {
        return this.request(url, { ...options, method: 'POST', body });
    }
    
    /**
     * PUT 請求
     */
    put(url, body = {}, options = {}) {
        return this.request(url, { ...options, method: 'PUT', body });
    }
    
    /**
     * DELETE 請求
     */
    delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
    
    // ==================== 專用 API 方法 ====================
    
    /**
     * 確認 FPS 付款
     */
    confirmFpsPayment(orderId) {
        return this.post(`/eshop/api/fps/confirm-payment/${orderId}/`, {});
    }
    
    /**
     * 確認現金付款
     */
    confirmCashPayment(orderId) {
        return this.post(`/eshop/api/cash/confirm-payment/${orderId}/`, {});
    }
    
    /**
     * 取消訂單
     */
    cancelOrder(orderId) {
        return this.post(`/eshop/api/cancel-order/${orderId}/`, {});
    }
    
    /**
     * 開始製作
     */
    startPreparation(orderId) {
        return this.post(`/eshop/api/start-preparation/${orderId}/`, {});
    }
    
    /**
     * 標記為就緒
     */
    markAsReady(orderId) {
        return this.post(`/eshop/api/mark-ready/${orderId}/`, {});
    }
    
    /**
     * 標記為已取餐
     */
    markAsCollected(orderId) {
        return this.post(`/eshop/api/mark-collected/${orderId}/`, {});
    }
    
    /**
     * 獲取訂單詳情
     */
    getOrderDetails(orderId) {
        return this.get(`/eshop/api/order-details/${orderId}/`);
    }
    
    /**
     * 獲取統一數據
     */
    getUnifiedData() {
        return this.get('/eshop/api/staff/unified-data/');
    }
    
    // ==================== 清理方法 ====================
    
    /**
     * 清理所有待處理請求
     */
    cleanup() {
        this.pendingRequests.clear();
        console.log('🗑️ ApiService: 待處理請求已清理');
    }
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    // 創建全局實例
    window.apiService = new ApiService();
    window.ApiService = ApiService;
    console.log('🌍 ApiService 已註冊到 window 對象');
}
