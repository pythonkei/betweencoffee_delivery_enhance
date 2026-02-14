// static/js/toast-manager.js

/**
 * 全局 Toast 提示系統
 * 使用方式：
 * 1. window.toast.success('操作成功');
 * 2. window.toast.error('發生錯誤');
 * 3. window.toast.info('提示信息');
 * 4. window.toast.warning('警告信息');
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.nextId = 1;
        this.autoCloseDuration = 4000; // 默認自動關閉時間（毫秒）
        this.maxToasts = 5; // 最多顯示的 Toast 數量
        
        // 初始化容器
        this.initContainer();
        
        // 綁定方法到 window 對象
        this.bindToWindow();
        
        console.log('Toast 管理器已初始化');
    }
    
    /**
     * 初始化 Toast 容器
     */
    initContainer() {
        // 檢查是否已存在容器
        this.container = document.getElementById('toast-container');
        
        if (!this.container) {
            // 創建容器
            this.container = document.createElement('div');
            this.container.id = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99998;
                display: flex;
                flex-direction: column;
                gap: 10px;
                pointer-events: none;
            `;
            
            // 添加到文檔
            document.body.appendChild(this.container);
        }
    }
    
    /**
     * 將方法綁定到 window 對象
     */
    bindToWindow() {
        window.toast = {
            success: (message, title = '成功') => this.show({ title, message, type: 'success' }),
            error: (message, title = '錯誤') => this.show({ title, message, type: 'error' }),
            info: (message, title = '提示') => this.show({ title, message, type: 'info' }),
            warning: (message, title = '警告') => this.show({ title, message, type: 'warning' }),
            show: (options) => this.show(options),
            hide: (id) => this.hide(id),
            clearAll: () => this.clearAll()
        };
    }
    
    /**
     * 顯示 Toast
     * @param {Object} options - Toast 選項
     * @param {string} options.title - 標題
     * @param {string} options.message - 消息內容
     * @param {string} options.type - 類型: success, error, info, warning
     * @param {number} options.duration - 顯示時間（毫秒），0 表示不自動關閉
     * @param {boolean} options.icon - 是否顯示圖標
     * @param {boolean} options.progressBar - 是否顯示進度條
     * @param {boolean} options.closeButton - 是否顯示關閉按鈕
     * @returns {string} Toast ID
     */
    show(options) {
        const {
            title = '',
            message = '',
            type = 'info',
            duration = this.autoCloseDuration,
            icon = true,
            progressBar = true,
            closeButton = true
        } = options;
        
        // 限制同時顯示的 Toast 數量
        if (this.toasts.size >= this.maxToasts) {
            // 移除最舊的 Toast
            const oldestId = Array.from(this.toasts.keys())[0];
            this.hide(oldestId);
        }
        
        const toastId = `toast-${this.nextId++}`;
        
        // 創建 Toast 元素
        const toast = this.createToastElement(toastId, { title, message, type, icon, progressBar, closeButton });
        
        // 添加到容器
        this.container.appendChild(toast);
        
        // 觸發動畫
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // 存儲引用
        this.toasts.set(toastId, { element: toast, duration });
        
        // 設置自動關閉
        let progressInterval;
        let timeoutId;
        
        if (duration > 0) {
            // 進度條動畫
            if (progressBar) {
                const progressEl = toast.querySelector('.toast-progress');
                if (progressEl) {
                    progressEl.style.animation = `toastProgress ${duration}ms linear forwards`;
                }
            }
            
            // 自動關閉計時器
            timeoutId = setTimeout(() => {
                this.hide(toastId);
            }, duration);
        }
        
        // 存儲定時器
        this.toasts.get(toastId).timeoutId = timeoutId;
        this.toasts.get(toastId).progressInterval = progressInterval;
        
        return toastId;
    }
    
    /**
     * 創建 Toast 元素
     */
    createToastElement(toastId, options) {
        const { title, message, type, icon, progressBar, closeButton } = options;
        
        // 圖標映射
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };
        
        // 圖標顏色
        const iconColorMap = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8',
            warning: '#ffc107'
        };
        
        const iconHtml = icon ? 
            `<div class="toast-icon" style="color: ${iconColorMap[type]};">
                <i class="fas ${iconMap[type]}"></i>
            </div>` : '';
        
        const titleHtml = title ? `<div class="toast-title">${title}</div>` : '';
        const closeBtnHtml = closeButton ? 
            `<button class="toast-close" onclick="window.toast.hide('${toastId}')">
                <i class="fas fa-times"></i>
            </button>` : '';
        
        const progressHtml = progressBar ? 
            `<div class="toast-progress" style="position: absolute; bottom: 0; left: 0; height: 3px; background: ${iconColorMap[type]}; border-radius: 0 0 0 4px;"></div>` : '';
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `custom-toast ${type}`;
        toast.innerHTML = `
            ${iconHtml}
            <div class="toast-content">
                ${titleHtml}
                <div class="toast-message">${message}</div>
            </div>
            ${closeBtnHtml}
            ${progressHtml}
        `;
        
        // 添加點擊事件（點擊Toast區域也可以關閉）
        toast.addEventListener('click', (e) => {
            if (e.target.classList.contains('toast-close') || 
                e.target.closest('.toast-close')) {
                return;
            }
            this.hide(toastId);
        });
        
        return toast;
    }
    
    /**
     * 隱藏指定的 Toast
     */
    hide(toastId) {
        const toastData = this.toasts.get(toastId);
        
        if (toastData) {
            const { element, timeoutId, progressInterval } = toastData;
            
            // 清除定時器
            if (timeoutId) clearTimeout(timeoutId);
            if (progressInterval) clearInterval(progressInterval);
            
            // 添加消失動畫
            element.classList.remove('show');
            element.style.opacity = '0';
            element.style.transform = 'translateX(120%)';
            
            // 延遲移除元素
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
                this.toasts.delete(toastId);
            }, 300);
        }
    }
    
    /**
     * 清除所有 Toast
     */
    clearAll() {
        this.toasts.forEach((toastData, toastId) => {
            this.hide(toastId);
        });
        this.toasts.clear();
    }
    
    /**
     * 設置全局配置
     */
    setConfig(config) {
        if (config.autoCloseDuration !== undefined) {
            this.autoCloseDuration = config.autoCloseDuration;
        }
        if (config.maxToasts !== undefined) {
            this.maxToasts = config.maxToasts;
        }
    }
    
    /**
     * 獲取當前狀態
     */
    getStatus() {
        return {
            activeToasts: this.toasts.size,
            maxToasts: this.maxToasts,
            autoCloseDuration: this.autoCloseDuration
        };
    }
}

// 自動初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.toastManager = new ToastManager();
    });
} else {
    window.toastManager = new ToastManager();
}



/**
 * 
// 在具體頁面中使用 Toast, 在任意頁面中都可以使用：

// 1. 簡單使用
window.toast.success('操作成功！');
window.toast.error('發生錯誤！');
window.toast.info('這是一條提示信息');
window.toast.warning('警告！請注意');

// 2. 完整選項
window.toast.show({
    title: '自定義標題',
    message: '這是一條詳細的消息內容...',
    type: 'success', // success, error, info, warning
    duration: 5000, // 5秒後自動關閉，0表示不自動關閉
    icon: true, // 是否顯示圖標
    progressBar: true, // 是否顯示進度條
    closeButton: true // 是否顯示關閉按鈕
});

// 3. 手動控制
const toastId = window.toast.info('這條消息不會自動關閉', '手動控制示例', 0);
setTimeout(() => {
    window.toast.hide(toastId); // 3秒後手動關閉
}, 3000);

// 4. 清除所有 Toast
window.toast.clearAll();

// 5. 獲取狀態
console.log(window.toastManager.getStatus());

// 6. 修改配置
window.toastManager.setConfig({
    autoCloseDuration: 3000, // 設置為3秒
    maxToasts: 3 // 最多同時顯示3個
});

**/