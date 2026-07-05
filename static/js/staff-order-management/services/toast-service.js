// static/js/staff-order-management/services/toast-service.js
// ==================== 統一 Toast 通知服務 ====================
// 功能：提供統一的 Toast 通知，防止重複顯示，支援多種通知類型
// 依賴：無（獨立運行）
//
// 使用方式：
//   ToastService.success('操作成功');
//   ToastService.error('操作失敗');
//   ToastService.warning('請注意');
//   ToastService.info('一般訊息');
//
// 整合方式：
//   在 HTML 中引入此文件後，即可在任何地方使用 ToastService
//   現有代碼中的 window.toast 也會被自動整合

class ToastService {
    constructor() {
        this.name = 'ToastService';
        this.recentlyShown = new Map();
        this.cooldown = 3000; // 3秒內不顯示相同訊息
        this.container = null;
        
        console.log('🔄 ToastService 初始化...');
        this._initContainer();
        this._integrateWithExisting();
        console.log('✅ ToastService 初始化完成');
    }
    
    /**
     * 初始化 Toast 容器
     */
    _initContainer() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-service-container';
            this.container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 1050;
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-width: 350px;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        }
    }
    
    /**
     * 整合現有的 window.toast（如果存在）
     */
    _integrateWithExisting() {
        if (window.toast) {
            console.log('🔄 整合現有的 window.toast 到 ToastService');
            // 保留現有 window.toast 的引用
            this._existingToast = window.toast;
        }
        
        // 註冊到全局
        window.toast = {
            success: (msg) => this.success(msg),
            error: (msg) => this.error(msg),
            warning: (msg) => this.warning(msg),
            info: (msg) => this.info(msg),
        };
        
        // 也暴露 ToastService 本身
        window.ToastService = ToastService;
    }
    
    /**
     * 檢查是否在冷卻期內（防止重複顯示）
     */
    _isOnCooldown(message, type) {
        const key = `${message}_${type}`;
        const now = Date.now();
        
        if (this.recentlyShown.has(key)) {
            const lastShown = this.recentlyShown.get(key);
            if (now - lastShown < this.cooldown) {
                console.log(`⏭️ ToastService: 跳過重複訊息 (冷卻中) - ${message}`);
                return true;
            }
        }
        
        this.recentlyShown.set(key, now);
        setTimeout(() => this.recentlyShown.delete(key), this.cooldown);
        return false;
    }
    
    /**
     * 顯示 Toast 通知
     */
    show(message, type = 'info', duration = 3000) {
        if (this._isOnCooldown(message, type)) return;
        
        const toast = document.createElement('div');
        toast.style.cssText = `
            pointer-events: auto;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: toastSlideIn 0.3s ease-out;
            transition: opacity 0.3s ease, transform 0.3s ease;
            word-wrap: break-word;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        `;
        
        // 根據類型設定樣式
        const styles = {
            success: { bg: '#28a745', color: '#fff', icon: '✅' },
            error: { bg: '#dc3545', color: '#fff', icon: '❌' },
            warning: { bg: '#ffc107', color: '#212529', icon: '⚠️' },
            info: { bg: '#17a2b8', color: '#fff', icon: 'ℹ️' },
        };
        
        const style = styles[type] || styles.info;
        toast.style.backgroundColor = style.bg;
        toast.style.color = style.color;
        
        toast.innerHTML = `
            <span>${style.icon}</span>
            <span style="flex-grow: 1;">${message}</span>
            <button style="
                background: none;
                border: none;
                color: ${style.color};
                cursor: pointer;
                font-size: 18px;
                padding: 0 4px;
                opacity: 0.8;
                line-height: 1;
            ">×</button>
        `;
        
        // 關閉按鈕
        toast.querySelector('button').addEventListener('click', () => {
            toast.remove();
        });
        
        this.container.appendChild(toast);
        
        // 自動移除
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    }
    
    success(message) { this.show(message, 'success'); }
    error(message) { this.show(message, 'error', 5000); }
    warning(message) { this.show(message, 'warning', 4000); }
    info(message) { this.show(message, 'info'); }
    
    /**
     * 清理所有 Toast
     */
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
    
    /**
     * 清理服務
     */
    cleanup() {
        this.clear();
        this.recentlyShown.clear();
        if (this.container && this.container.parentNode) {
            this.container.parentNode.removeChild(this.container);
        }
        this.container = null;
        console.log('🗑️ ToastService 已清理');
    }
}

// ==================== 添加 CSS 動畫 ====================
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes toastSlideIn {
            from {
                opacity: 0;
                transform: translateX(20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// ==================== 全局註冊 ====================
if (typeof window !== 'undefined') {
    // 創建全局實例
    window.toastService = new ToastService();
    console.log('🌍 ToastService 已註冊到 window 對象');
}
