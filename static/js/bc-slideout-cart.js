/**
 * bc-slideout-cart.js — Between Coffee 滑出購物車
 * Sprint 1: 一頁式結帳
 * 
 * 依賴: 無 (純 Vanilla JS)
 * 使用方式:
 *   const cart = new SlideoutCart();
 *   cart.open();   // 打開
 *   cart.close();  // 關閉
 *   cart.toggle(); // 切換
 */

class SlideoutCart {
  constructor(options = {}) {
    this.options = {
      overlaySelector: '#bc-cart-overlay',
      drawerSelector: '#bc-cart-drawer',
      itemsSelector: '#bc-cart-items',
      totalSelector: '#bc-cart-total',
      badgeSelector: '.bc-cart-count',
      ...options
    };

    this.overlay = document.querySelector(this.options.overlaySelector);
    this.drawer = document.querySelector(this.options.drawerSelector);
    this.itemsContainer = document.querySelector(this.options.itemsSelector);
    this.totalEl = document.querySelector(this.options.totalSelector);

    if (!this.drawer) return;

    this.isOpen = false;
    this.csrfToken = this._getCSRF();
    this._bindEvents();
  }

  // ===== 公開方法 =====

  open() {
    if (!this.drawer) return;
    this.isOpen = true;
    this.overlay?.classList.add('open');
    this.drawer.classList.add('open');
    this._lockScroll();
    this._loadItems();
  }

  close() {
    if (!this.drawer) return;
    this.isOpen = false;
    this.overlay?.classList.remove('open');
    this.drawer.classList.remove('open');
    this._unlockScroll();
  }

  toggle() {
    this.isOpen ? this.close() : this.open();
  }

  /**
   * 加入商品後重新載入購物車並打開面板
   */
  refreshAndOpen() {
    this._loadItems().then(() => {
      if (!this.isOpen) this.open();
    });
  }

  // ===== 內部方法 =====

  _bindEvents() {
    // 購物車按鈕切換
    document.querySelector('#bc-cart-toggle')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.toggle();
    });

    // 關閉按鈕
    this.drawer.querySelector('.bc-cart-close')?.addEventListener('click', () => this.close());

    // 點擊遮罩關閉
    this.overlay?.addEventListener('click', () => this.close());

    // ESC 鍵關閉
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) this.close();
    });

    // 監聽自定義事件：加入購物車後刷新
    document.addEventListener('cart:updated', () => this.refreshAndOpen());
  }

  async _loadItems() {
    if (!this.itemsContainer) return;

    try {
      const response = await fetch('/cart/count/');
      const data = await response.json();

      if (data.success) {
        this._renderItems(data);
        this._updateBadge(data.cart_total_items);
      } else {
        this._renderEmpty();
      }
    } catch (err) {
      console.error('購物車載入失敗:', err);
      this._renderEmpty();
    }
  }

  _renderItems(data) {
    if (!this.itemsContainer) return;

    const items = data.items || [];
    if (items.length === 0) {
      this._renderEmpty();
      return;
    }

    let html = '';
    items.forEach(item => {
      const optionsText = this._formatOptions(item);
      html += `
        <div class="bc-cart-item" data-key="${item.item_id}">
          <img src="${item.image || '/static/images/placeholder.png'}" alt="${item.name}" class="bc-cart-item-image">
          <div class="bc-cart-item-info">
            <p class="bc-cart-item-name">${this._escapeHtml(item.name)}</p>
            ${optionsText ? `<p class="bc-cart-item-options">${this._escapeHtml(optionsText)}</p>` : ''}
            <p class="bc-cart-item-price">$${item.total_price}</p>
            <div class="bc-cart-item-qty">
              <button class="bc-cart-item-qty-btn" data-action="decrease" data-key="${item.item_id}">−</button>
              <span class="bc-cart-item-qty-value">${item.quantity}</span>
              <button class="bc-cart-item-qty-btn" data-action="increase" data-key="${item.item_id}">+</button>
              <button class="bc-cart-item-remove" data-action="remove" data-key="${item.item_id}">✕</button>
            </div>
          </div>
        </div>
      `;
    });

    this.itemsContainer.innerHTML = html;

    // 綁定數量按鈕事件
    this.itemsContainer.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const action = btn.dataset.action;
        const key = btn.dataset.key;
        if (action === 'increase') this._updateQuantity(key, 1);
        else if (action === 'decrease') this._updateQuantity(key, -1);
        else if (action === 'remove') this._removeItem(key);
      });
    });

    // 更新總價
    if (this.totalEl) {
      this.totalEl.textContent = `$${data.cart_total_price || '0'}`;
    }
  }

  _renderEmpty() {
    if (!this.itemsContainer) return;
    this.itemsContainer.innerHTML = `
      <div class="bc-cart-empty">
        <div class="bc-cart-empty-icon"><i class="icon-shopping-cart" style="font-size:3rem;"></i></div>
        <p class="bc-cart-empty-sub">來一杯咖啡吧</p>
      </div>
    `;
    if (this.totalEl) this.totalEl.textContent = '$0';
  }

  async _updateQuantity(key, delta) {
    try {
      // 先找到當前數量
      const itemEl = this.itemsContainer.querySelector(`[data-key="${key}"]`);
      const qtyEl = itemEl?.querySelector('.bc-cart-item-qty-value');
      const currentQty = parseInt(qtyEl?.textContent || '1');
      const newQty = Math.max(1, currentQty + delta);

      const response = await fetch('/cart/update_cart/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this.csrfToken
        },
        body: JSON.stringify({ item_key: key, quantity: newQty })
      });
      const data = await response.json();

      if (data.success) {
        this._loadItems();
        this._updateBadge(data.cart_total_items);
      }
    } catch (err) {
      console.error('更新數量失敗:', err);
    }
  }

  async _removeItem(key) {
    try {
      const response = await fetch(`/cart/remove/${key}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': this.csrfToken }
      });
      if (response.ok) {
        this._loadItems();
        this._updateBadge();
      }
    } catch (err) {
      console.error('移除商品失敗:', err);
    }
  }

  _updateBadge(count) {
    document.querySelectorAll(this.options.badgeSelector).forEach(el => {
      el.textContent = count || '0';
    });
  }

  _formatOptions(item) {
    const parts = [];
    if (item.cup_level) {
      const map = { Small: '細', Medium: '中', Large: '大' };
      parts.push(`杯量:${map[item.cup_level] || item.cup_level}`);
    }
    if (item.milk_level) {
      const map = { Light: '少', Medium: '正常', Extra: '追加' };
      parts.push(`奶量:${map[item.milk_level] || item.milk_level}`);
    }
    if (item.weight) {
      parts.push(`重量:${item.weight}`);
    }
    if (item.grinding_level) {
      const map = { Non: '免研磨', Light: '細', Medium: '中', Deep: '粗' };
      parts.push(`研磨:${map[item.grinding_level] || item.grinding_level}`);
    }
    return parts.join(' | ');
  }

  _escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * 鎖定滾動 — 用 overflow:hidden + padding-right 補償滾動條寬度
   * 對 body 設 overflow:hidden 讓滾動條消失（同時 body 成為 position:absolute 元素的包含塊）
   * 對 body 設 padding-right 補償內容偏移
   * 對所有 position:absolute + right:0 的元素設 right 補償（因為它們的包含塊變成 body）
   */
  _lockScroll() {
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    if (scrollbarWidth === 0) {
      document.body.style.overflow = 'hidden';
      return;
    }
    document.body.style.overflow = 'hidden';
    document.body.style.paddingRight = scrollbarWidth + 'px';
    // 補償所有 position:absolute 且 right 為 0 的元素
    // 當 body overflow:hidden 時，這些元素的包含塊變成 body，right:0 相對於 body padding box
    document.querySelectorAll('.ftco-navbar-light, .ftco_navbar').forEach(el => {
      const right = window.getComputedStyle(el).right;
      if (right === '0px') {
        el.style.right = scrollbarWidth + 'px';
      }
    });
  }

  /**
   * 解鎖滾動 — 移除所有補償
   */
  _unlockScroll() {
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    // 移除 position:absolute 元素的 right 補償
    document.querySelectorAll('.ftco-navbar-light, .ftco_navbar').forEach(el => {
      el.style.right = '';
    });
  }

  _getCSRF() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + '=')) {
        return decodeURIComponent(c.substring(name.length + 1));
      }
    }
    return '';
  }
}

// 全域實例（延遲初始化）
let bcCartInstance = null;
document.addEventListener('DOMContentLoaded', () => {
  bcCartInstance = new SlideoutCart();
  window.bcCart = bcCartInstance;
});
