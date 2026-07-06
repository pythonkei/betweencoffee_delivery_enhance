/**
 * bc-toast.js — Between Coffee 取餐通知 Toast 系統
 * Sprint 1: 取餐通知
 * 
 * 使用方式:
 *   BcToast.show('訂單已就緒！', '您的咖啡可以取了 ☕', 'ready');
 *   BcToast.show('資訊', '這是一則通知', 'info');
 *   BcToast.show('錯誤', '發生錯誤', 'error');
 */

const BcToast = {
  container: null,

  init() {
    if (this.container) return;
    this.container = document.createElement('div');
    this.container.className = 'bc-toast-container';
    document.body.appendChild(this.container);
  },

  /**
   * 顯示 Toast 通知
   * @param {string} title - 標題
   * @param {string} message - 內容
   * @param {'ready'|'info'|'error'} type - 類型
   * @param {number} duration - 自動消失時間（ms），0 則不自動消失
   */
  show(title, message, type = 'info', duration = 5000) {
    this.init();

    const icons = {
      ready: '☕',
      info: 'ℹ️',
      error: '⚠️'
    };

    const toast = document.createElement('div');
    toast.className = `bc-toast`;
    toast.innerHTML = `
      <span class="bc-toast-icon ${type}">${icons[type] || 'ℹ️'}</span>
      <div class="bc-toast-content">
        <p class="bc-toast-title">${this._escape(title)}</p>
        <p class="bc-toast-message">${this._escape(message)}</p>
      </div>
      <button class="bc-toast-close" aria-label="關閉">✕</button>
    `;

    // 關閉按鈕
    toast.querySelector('.bc-toast-close').addEventListener('click', () => {
      this._remove(toast);
    });

    this.container.appendChild(toast);

    // 自動消失
    if (duration > 0) {
      setTimeout(() => this._remove(toast), duration);
    }
  },

  _remove(toast) {
    if (!toast || toast.classList.contains('removing')) return;
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => {
      toast.remove();
    });
  },

  _escape(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

// 自動初始化
document.addEventListener('DOMContentLoaded', () => BcToast.init());
