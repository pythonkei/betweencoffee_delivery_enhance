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
    // 先隱藏浮動按鈕再鎖定滾動（避免 _lockScroll 對按鈕 right 補償造成點擊瞬間位移）
    this._cartOpenHiddenFloating = true;
    this._hideFloatingCart();
    this._lockScroll();
    this._loadItems();
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

  _updateBadge(count, animatedOverride) {
    const val = count || '0';
    const numeric = parseInt(val, 10) || 0;
    document.querySelectorAll(this.options.badgeSelector).forEach(el => {
      // 2026-08-14：值相同不重設 textContent（避免重繪造成文字閃爍）
      if (el.textContent !== val) {
        el.textContent = val;
      }
    });
    // 2026-09-21（使用者指示）：浮動鈕圖示常駐顯示，數量為 0 時只隱藏它上面的數字圓圈
    // （只針對浮動鈕的 badge；其他 .bc-cart-count（導覽列等）不受影響）
    const fcBadge = this.floatingCart ? this.floatingCart.querySelector('.bc-floating-cart-badge') : null;
    if (fcBadge) {
      fcBadge.style.display = numeric > 0 ? '' : 'none';
    }
    // 同步浮動購物車按鈕顯示狀態
    // 2026-08-14：頁面載入期（constructor + rAF 兩次初始同步）靜默顯示（無動畫）；
    // 延遲切換標記，確保所有初始同步皆靜默、之後操作（加入購物車等）才有滑入動畫
    // 2026-08-24：_syncBadgeFromServer（頁面載入/bfcache 恢復）傳 false 強制靜默，
    // 避免 async fetch 回應超過 500ms 時 _initialBadgeSync 已 false → 每次跳頁滑入動畫
    const animated = animatedOverride !== undefined ? animatedOverride : !this._initialBadgeSync;
    this._updateFloatingCartVisibility(count, animated);
    if (this._initialBadgeSync) {
      setTimeout(() => { this._initialBadgeSync = false; }, 500);
    }
  }

  /**
   * 初始化滾動監聽：浮動購物車常駐顯示（有商品時始終顯示）
   */
  _initFloatingCartScrollListener() {
    this.floatingCart = document.getElementById('bc-floating-cart');
    this.navCartToggle = document.getElementById('bc-cart-toggle');
    if (!this.floatingCart || !this.navCartToggle) return;

    // 2026-08-14：首次 badge 同步（頁面載入）靜默顯示浮動購物車（無滑入動畫），之後操作才動畫
    this._initialBadgeSync = true;

    // 員工訂單管理頁面不需要顯示浮動購物車按鈕
    if (window.location.pathname.includes('/admin/eshop/ordermodel/staff-management/')) {
      this.floatingCart.style.display = 'none';
      return;
    }

    // 2026-09-21：浮動購物車定位（量測 .bc-attract-buy 後寫入 CSS 變數）
    this._bindFloatingCartPlacement();

    // 初始載入購物車數量，有商品時常駐顯示
    requestAnimationFrame(() => {
      this._syncBadgeFromServer();
    });
  }

  /**
   * 2026-09-21：浮動購物車定位 —— 貼在 .bc-attract-buy 正上方、中心線對齊、圖示尺寸同按鈕寬
   * 座標以 CSS 變數寫入（--bc-fc-top / --bc-fc-right / --bc-fc-size），外觀仍由 CSS 控制。
   * 為何需用 JS 量測：首頁的 Buy 按鈕位置由 index.html 的 place() 以 inline top 對齊
   * navbar-brand（文件座標），其他頁面才是 CSS top:50% —— 只有在 DOM 上量測才能兩者一致。
   * Buy 按鈕不存在（咖啡／豆 詳情與選單頁、付款頁等 .bc-attract-nav 被隱藏者）→
   * 移除 inline 變數、交回 CSS 各斷點提供的「同軸線退化值」（不再回到右下角）。
   */
  _placeFloatingCart() {
    const el = this.floatingCart;
    if (!el) return;

    // 圖示字級：與 bc-components.css 各斷點一致（桌機 44 / 平板 40 / 手機 36；2026-09-21 兩度縮小）
    const size = window.matchMedia('(min-width: 992px)').matches ? 44
      : window.matchMedia('(min-width: 768px)').matches ? 40 : 36;
    el.style.setProperty('--bc-fc-size', size + 'px');
    // 實際佔位＝max(44px 透明點擊區下限, 字級)：定位要用「盒子」而不是字形大小
    // （手機是 40px 字形裝在 44px 盒子裡——只縮字形、點擊區不變）
    const fcBtn = el.querySelector('.bc-floating-cart-btn');
    const minBox = fcBtn ? parseFloat(getComputedStyle(fcBtn).minHeight) : NaN;
    const box = Math.max(size, isFinite(minBox) ? minBox : 0);

    const buy = document.querySelector('.bc-attract-buy');
    const buyVisible = !!(buy && getComputedStyle(buy).display !== 'none' && buy.getBoundingClientRect().width > 0);

    if (!buyVisible) {
      // Buy 按鈕不存在（咖啡／豆 詳情與選單頁、付款頁等 .bc-attract-nav 被隱藏者）
      // → 移除 inline 變數、交回 CSS 各斷點的同軸線退化值
      el.style.removeProperty('--bc-fc-top');
      el.style.removeProperty('--bc-fc-right');
      return;
    }

    // 對齊基準＝「可見長條」.bc-attract-buy__link（使用者實際看到的按鈕；
    // 外層 .bc-attract-buy 盒因 .c-attract 負 margin 而與可見長條差 24px）
    const bar = document.querySelector('.bc-attract-buy__link') || buy;
    const barRect = bar.getBoundingClientRect();
    const profile = document.querySelector('.bc-attract-profile');
    const profileRect = profile ? profile.getBoundingClientRect() : null;

    // 首選：長條正上方；上方空間不足（例如首頁把整組按鈕對齊 navbar-brand 頂邊，
    // 上方就是視窗上緣）→ 改放整組下方，維持同一軸線往下延伸（Buy → 個人圓鈕 → 購物車）
    // 與 Buy 按鈕的間距（2026-09-21 使用者指示「增加間距」；值定義在 bc-components.css 的 --bc-fc-gap）
    const gap = parseFloat(getComputedStyle(el).getPropertyValue('--bc-fc-gap')) || 0;
    const MIN_TOP = 8;
    let desiredTop = Math.round(barRect.top - box - gap);
    if (desiredTop < MIN_TOP) {
      desiredTop = Math.round(((profileRect && profileRect.height) ? profileRect.bottom : barRect.bottom) + gap);
    }
    const desiredCx = barRect.left + barRect.width / 2;

    // 初值：right 以 clientWidth 為基準——position:fixed 的 right 基準是 ICB（不含右側捲軸寬），
    // 用 window.innerWidth 會多算一個捲軸寬（實測 15px 偏差）
    el.style.setProperty('--bc-fc-top', desiredTop + 'px');
    el.style.setProperty('--bc-fc-right', Math.round(document.documentElement.clientWidth - desiredCx - box / 2) + 'px');

    // 自我修正：可見時量測實際位置再校正一次（吸收捲軸寬、transform 等平台差異）。
    // 進場動畫（bcFloatingIn 用 transform 位移）期間不量測，避免把動畫位移算進去。
    const animating = el.classList.contains('show') && !el.classList.contains('no-anim');
    const r = el.getBoundingClientRect();
    if (r.width > 0 && !animating) {
      const cs = getComputedStyle(el);
      const dx = desiredCx - (r.left + r.width / 2);   // >0 表偏左 → 需往右（right 變小）
      const dy = desiredTop - r.top;                    // >0 表偏高 → 需往下（top 變大）
      if (Math.abs(dx) >= 0.5) {
        const cur = parseFloat(cs.getPropertyValue('--bc-fc-right')) || 0;
        el.style.setProperty('--bc-fc-right', Math.round(cur - dx) + 'px');
      }
      if (Math.abs(dy) >= 0.5) {
        const cur = parseFloat(cs.getPropertyValue('--bc-fc-top')) || 0;
        el.style.setProperty('--bc-fc-top', Math.round(cur + dy) + 'px');
      }
    }
  }

  /**
   * 2026-09-21：註冊浮動購物車定位重算時機
   * （首頁 place() 會在 rAF 與 350ms 安定後各寫一次 inline top → 補兩次量測確保最後才量）
   */
  _bindFloatingCartPlacement() {
    const run = () => this._placeFloatingCart();
    run();
    requestAnimationFrame(run);
    window.addEventListener('load', run);
    window.addEventListener('pageshow', run);
    window.addEventListener('resize', run);
    window.addEventListener('orientationchange', run);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', run);
    }
    setTimeout(run, 400);
    setTimeout(run, 1200);

    // 2026-09-21：主動預載圖示字型。
    // 原因：購物車為空時浮動鈕是 display:none，瀏覽器不會為它載入 Material Icons，
    // 之後加入商品才顯示時會先渲染成文字（例如 "shopping_bag"，實測寬 346px）→ 文字閃現。
    // 這裡在頁面載入時就要求該字型（依目前使用的圖示字型家族）。
    if (document.fonts && document.fonts.load) {
      const icon = this.floatingCart.querySelector('.material-icons, .material-symbols-outlined');
      if (icon) {
        const fs = getComputedStyle(icon).fontSize || '52px';
        const family = icon.classList.contains('material-symbols-outlined')
          ? 'Material Symbols Outlined' : 'Material Icons';
        document.fonts.load(fs + ' "' + family + '"').catch(() => {});
      }
    }
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
        this._updateBadge(data.cart_total_items, false); // 2026-08-24：頁面載入/bfcache 恢復同步一律靜默（不觸發滑入動畫）
      }
    } catch (err) {
      // 靜默失敗，使用 HTML 初始值
    }
  }

  /**
   * 更新浮動購物車顯示狀態
   * 2026-09-21（使用者指示）：**空車也常駐顯示圖示**（只隱藏數字圓圈，見 _updateBadge），
   * 因此不再依數量隱藏整個浮動鈕。
   */
  _updateFloatingCartVisibility(count, animated = true) {
    if (!this.floatingCart) return;
    // 購物車打開時不處理浮動按鈕顯示
    if (this._cartOpenHiddenFloating) return;
    this._showFloatingCart(animated);
  }

  /**
   * 顯示浮動購物車（從底部滑入）
   */
  _showFloatingCart(animated = true) {
    if (!this.floatingCart) return;
    // 2026-09-21（使用者指示）：不再因「空車」而跳過顯示（空車仍顯示圖示、只隱藏數字圓圈）

    // 2026-08-24：已顯示（show）時直接返回——不移除 no-anim、不重播滑入動畫。
    // 否則加入商品時 animated=true 移除 no-anim → CSS 動畫從 none 變 bcFloatingIn → 每次重播
    if (this.floatingCart.classList.contains('show')) return;

    // 2026-08-14：頁面載入靜默顯示（no-anim 禁用滑入動畫）；操作後（animated=true）恢復動畫
    this.floatingCart.classList.toggle('no-anim', !animated);

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
      // 2026-09-21：關閉抽屜後 body padding-right 已還原（.bc-attract-buy 的水平位置會回復），
      // 故重新量測定位，避免浮動鈕停留在補償後的偏移位置
      this._placeFloatingCart();
      // 2026-09-21（使用者指示）：空車也顯示圖示 → 一律恢復顯示
      this._showFloatingCart();
    });
  }

  _formatOptions(item) {
    const parts = [];
    if (item.type === 'coffee') {
      if (item.cup_level) {
        const map = { Small: '細', Medium: '中', Large: '大' };
        parts.push(`<i class="icon material-symbols-outlined">water_full</i> 杯量: ${map[item.cup_level] || item.cup_level}`);
      }
      if (item.strength_level) {
        const map = { Normal: '預設', Extra: '特濃' };
        const label = map[item.strength_level] || item.strength_level;
        parts.push(`<i class="icon material-symbols-outlined">bolt</i> 濃度: ${label}`);
      }
      if (item.milk_level) {
        const map = { Light: '少', Medium: '正常', Extra: '追加' };
        const label = map[item.milk_level] || item.milk_level;
        parts.push(`<i class="icon material-symbols-outlined">humidity_mid</i> 奶量: ${label}`);
      }
      // 自訂選項組（2026-08-15）：API 已翻譯為中文（extra_options_cn）
      if (item.extra_options_cn) {
        const labelMap = { cup_level:'杯量', strength_level:'濃度', milk_level:'奶量', milk:'奶類', caramel:'焦糖', butter:'黃油', coconut:'椰奶', vanilla:'香草', special:'特調', oolong:'烏龍茶', jasmine:'茉莉花茶', matcha:'抹茶', green:'綠茶', hojicha:'焙茶', topping:'面層配料', bean_blend:'配豆' };
        Object.entries(item.extra_options_cn).forEach(([k, v]) => {
          parts.push(`${labelMap[k] || k}: ${v}`);
        });
      }
    } else if (item.type === 'bean') {
      // 咖啡豆自訂選項組（2026-09-21）：API 已回傳中文／圖示／標籤 → 直接使用，不再硬寫對照表
      const cn = item.extra_options_cn || {};
      const icons = item.extra_options_icons || {};
      const labels = item.extra_options_labels || {};
      Object.entries(cn).forEach(([k, v]) => {
        parts.push(`<i class="icon material-symbols-outlined">${icons[k] || 'add_circle'}</i> ${labels[k] || k}: ${v}`);
      });
      // 舊資料／未啟用研磨組：沿用既有欄位（研磨已在 extra_options_cn 時不重複顯示）
      if (item.grinding_level && !cn.grinding_level) {
        const map = { Non: '免研磨', Light: '細研磨', Medium: '中研磨', Deep: '粗研磨' };
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
    // 補償浮動購物車的右緣（2026-09-21：位置改由 CSS 變數 --bc-fc-right 決定
    // ——「貼在 .bc-attract-buy 正上方」——故以變數現值 + 捲軸寬補償，不再寫死 40px）
    if (this.floatingCart) {
      this.floatingCart.style.right = (this._floatingCartBaseRight() + scrollbarWidth) + 'px';
    }
  }

  /**
   * 2026-09-21：浮動購物車目前的基準 right（px）
   * 讀 CSS 變數 --bc-fc-right：JS 量測值（inline）優先，其次為各斷點退化值，都沒有則 40
   */
  _floatingCartBaseRight() {
    if (!this.floatingCart) return 40;
    const raw = getComputedStyle(this.floatingCart).getPropertyValue('--bc-fc-right');
    const v = parseFloat(raw);
    return isFinite(v) ? v : 40;
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
