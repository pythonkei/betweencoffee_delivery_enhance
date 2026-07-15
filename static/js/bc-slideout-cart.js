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

    // ✅ 修復：初始化時立即從伺服器同步購物車 badge 數量
    // 確保從支付平台返回時，badge 能正確反映清空後的購物車狀態
    this._syncBadgeFromServer();
  }

  // ===== 公開方法 =====

  open() {
    if (!this.drawer) return;
    this.isOpen = true;
    this.overlay?.classList.add('open');
    this.drawer.classList.add('open');
    this._lockScroll();
    this._loadItems();
    // 打開購物車時隱藏浮動按鈕，避免覆蓋在面板上
    // 設定標記防止 _updateFloatingCartVisibility 重新顯示
    this._cartOpenHiddenFloating = true;
    this._hideFloatingCart();
  }

  close() {
    if (!this.drawer) return;
    this.isOpen = false;
    this.overlay?.classList.remove('open');
    this.drawer.classList.remove('open');
    this._unlockScroll();
    // 清除標記，允許 _updateFloatingCartVisibility 再次處理浮動按鈕
    this._cartOpenHiddenFloating = false;
    // 關閉購物車後，根據導覽列購物車可見性決定是否顯示浮動按鈕
    this._restoreFloatingCartAfterClose();
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

    // 浮動購物車按鈕切換
    document.querySelector('#bc-floating-cart-btn')?.addEventListener('click', (e) => {
      e.preventDefault();
      this.toggle();
    });

    // 關閉按鈕（所有 .bc-cart-close 元素）
    this.drawer.querySelectorAll('.bc-cart-close').forEach(btn => {
      btn.addEventListener('click', () => this.close());
    });

    // 清空購物車按鈕
    this.drawer.querySelector('#bc-cart-clear-btn')?.addEventListener('click', (e) => {
      e.preventDefault();
      this._clearCart();
    });

    // 點擊遮罩關閉
    this.overlay?.addEventListener('click', () => this.close());

    // ESC 鍵關閉
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) this.close();
    });

    // 監聽自定義事件：加入購物車後刷新（不自動打開面板）
    document.addEventListener('cart:updated', () => this._loadItems());

    // 滾動監聽：導覽列購物車不可見時顯示浮動按鈕
    this._initFloatingCartScrollListener();

    // 處理 bfcache（後退快取）恢復：從瀏覽器返回按鈕回到頁面時重新同步購物車數量
    // 即使 event.persisted 為 false（跨域 bfcache 恢復），也執行同步以確保 badge 正確
    // 使用 forceRefresh=true 避免瀏覽器快取 /cart/count/ 的舊響應
    window.addEventListener('pageshow', (event) => {
      this._syncBadgeFromServer(true);
    });
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
            <div class="bc-cart-item-name-row">
              <p class="bc-cart-item-name">${this._escapeHtml(item.name)}</p>
              <p class="bc-cart-item-price">$${item.total_price}</p>
            </div>
            ${optionsText ? `<p class="bc-cart-item-options">${optionsText}</p>` : ''}
            <div class="bc-cart-item-qty">
              <button class="bc-cart-item-qty-btn" data-action="decrease" data-key="${item.item_id}">−</button>
              <span class="bc-cart-item-qty-value">${item.quantity}</span>
              <button class="bc-cart-item-qty-btn" data-action="increase" data-key="${item.item_id}">+</button>
              <button class="bc-cart-item-remove" data-action="remove" data-key="${item.item_id}"><i class="icon-close"></i></button>
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
        // 如果在結帳頁（order/confirm），重新載入頁面以更新右側商品列表
        if (window.location.pathname.includes('/eshop/order/confirm/')) {
          window.location.href = '/coffee_menu/';
        }
      }
    } catch (err) {
      console.error('移除商品失敗:', err);
    }
  }

  /**
   * 清空購物車
   */
  async _clearCart() {
    try {
      const response = await fetch('/cart/clear/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      if (response.ok || response.redirected) {
        this._loadItems();
        this._updateBadge(0);
        // 如果在結帳頁（order/confirm），清空後重新導向到菜單頁面
        if (window.location.pathname.includes('/eshop/order/confirm/')) {
          window.location.href = '/coffee_menu/';
        }
      }
    } catch (err) {
      console.error('清空購物車失敗:', err);
    }
  }

  _updateBadge(count) {
    document.querySelectorAll(this.options.badgeSelector).forEach(el => {
      el.textContent = count || '0';
    });
    // 同步浮動購物車按鈕顯示狀態
    this._updateFloatingCartVisibility(count);
  }

  /**
   * 初始化滾動監聽：浮動購物車常駐顯示（有商品時始終顯示）
   */
  _initFloatingCartScrollListener() {
    this.floatingCart = document.getElementById('bc-floating-cart');
    this.navCartToggle = document.getElementById('bc-cart-toggle');
    if (!this.floatingCart || !this.navCartToggle) return;

    // 員工訂單管理頁面不需要顯示浮動購物車按鈕
    if (window.location.pathname.includes('/admin/eshop/ordermodel/staff-management/')) {
      this.floatingCart.style.display = 'none';
      return;
    }

    // 初始載入購物車數量，有商品時常駐顯示
    requestAnimationFrame(() => {
      this._syncBadgeFromServer();
    });
  }

  /**
   * 從伺服器同步購物車數量到 badge
   * @param {boolean} forceRefresh - 是否強制刷新（添加時間戳避免快取）
   */
  async _syncBadgeFromServer(forceRefresh = false) {
    try {
      const url = forceRefresh ? `/cart/count/?_=${Date.now()}` : '/cart/count/';
      const response = await fetch(url);
      const data = await response.json();
      if (data.success) {
        this._updateBadge(data.cart_total_items);
      }
    } catch (err) {
      // 靜默失敗，使用 HTML 初始值
    }
  }

  /**
   * 更新浮動購物車顯示狀態（根據購物車數量，有商品時常駐顯示）
   */
  _updateFloatingCartVisibility(count) {
    if (!this.floatingCart) return;
    // 購物車打開時不處理浮動按鈕顯示
    if (this._cartOpenHiddenFloating) return;
    const itemCount = count !== undefined ? parseInt(count) : null;
    if (itemCount !== null) {
      if (itemCount <= 0) {
        // 購物車為空時隱藏浮動按鈕
        this.floatingCart.style.display = 'none';
        this.floatingCart.classList.remove('show', 'hide');
        return;
      } else {
        // 購物車有商品時，常駐顯示浮動按鈕
        this._showFloatingCart();
      }
    }
  }

  /**
   * 顯示浮動購物車（從底部滑入）
   */
  _showFloatingCart() {
    if (!this.floatingCart) return;
    // 如果購物車為空，不顯示
    const badge = this.floatingCart.querySelector('.bc-floating-cart-badge');
    if (badge && parseInt(badge.textContent) <= 0) return;

    if (this.floatingCart.classList.contains('show')) return;

    // 確保元素可見（移除可能殘留的 display:none inline style）
    this.floatingCart.style.display = '';

    this.floatingCart.classList.remove('hide');
    // 強制 reflow 確保動畫重新觸發
    void this.floatingCart.offsetWidth;
    this.floatingCart.classList.add('show');
  }

  /**
   * 隱藏浮動購物車（向下滑出）
   */
  _hideFloatingCart() {
    if (!this.floatingCart) return;
    if (!this.floatingCart.classList.contains('show')) {
      // 如果沒有 show class，直接隱藏（確保 display:none）
      this.floatingCart.style.display = 'none';
      return;
    }

    this.floatingCart.classList.remove('show');
    this.floatingCart.classList.add('hide');
  }

  /**
   * 關閉購物車後，有商品時常駐顯示浮動按鈕
   */
  _restoreFloatingCartAfterClose() {
    if (!this.floatingCart) return;
    // 使用 requestAnimationFrame 確保 _unlockScroll 已完成
    requestAnimationFrame(() => {
      const badge = this.floatingCart.querySelector('.bc-floating-cart-badge');
      if (badge && parseInt(badge.textContent) > 0) {
        this._showFloatingCart();
      }
    });
  }

  _formatOptions(item) {
    const parts = [];
    if (item.type === 'coffee') {
      if (item.cup_level) {
        const map = { Small: '細', Medium: '中', Large: '大' };
        parts.push(`<i class="icon material-symbols-outlined">water_full</i> 杯量: ${map[item.cup_level] || item.cup_level}`);
      }
      if (item.milk_level) {
        const map = { Light: '少', Medium: '正常', Extra: '追加' };
        parts.push(`<i class="icon material-symbols-outlined">humidity_mid</i> 奶量: ${map[item.milk_level] || item.milk_level}`);
      }
    } else if (item.type === 'bean') {
      if (item.grinding_level) {
        const map = { Non: '免研磨', Light: '細', Medium: '中', Deep: '粗' };
        parts.push(`<i class="icon material-symbols-outlined">roller_shades</i> 研磨:${map[item.grinding_level] || item.grinding_level}`);
      }
      if (item.weight) {
        parts.push(`<i class="icon material-symbols-outlined">scale</i> 重量:${item.weight}`);
      }
    }
    return parts.join('<br>');
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
    // 補償浮動購物車按鈕的 right 值，防止 body padding-right 導致位移
    if (this.floatingCart) {
      this.floatingCart.style.right = (40 + scrollbarWidth) + 'px';
    }
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
    // 移除浮動購物車按鈕的 right 補償
    if (this.floatingCart) {
      this.floatingCart.style.right = '';
    }
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
