/**
 * bc-attract-place.js — 右側整組（浮動購物車／Buy & Order／個人圓鈕）定位
 *   2026-09-21 新增，全站共用（base.html 全域載入，於 bc-slideout-cart.js 之前）
 *
 * 使用者指示：「所有模板浮動購物車修改位置和 index 一樣」→
 *   把原本只寫在 index.html 的 place() 抽成全站共用腳本：
 *   所有頁面的排列都與 index 相同 —— 購物袋 → Order 長條 → 個人圓鈕，
 *   整組對齊 navbar-brand 頂邊（不再只有首頁如此、其餘頁面垂直置中）。
 *
 * 座標原理（沿用 index.html 原註解）：
 *   - .bc-attract-buy / .bc-attract-profile 為 position: fixed 且 CSS 有
 *     transform: translateY(-50%) → inline top 屬「中心座標」。
 *   - 對齊基準取 navbar-brand 的「文件座標」＝ br.top + scrollTop。
 *     navbar 在文件流內 absolute，捲動時 br.top 等量遞減 → 相加為定值，
 *     因此等同「固定在與頁面頂端 navbar 同一高度」（捲動時不跟著跑）。
 *     註：不可改用純 br.top（視窗座標）——捲動狀態下會量到負值，
 *     經防裁切下限後按鈕會被吸到視窗頂（已實測）。
 *   - 浮動購物車（--bc-fc-top 為「盒上緣」）由 bc-slideout-cart.js 依同一基準定位，
 *     本檔定位完會呼叫 bcCart._placeFloatingCart() 讓它跟著長條重算。
 *
 * 2026-09-21（使用者指示「bc-attract-buy and 個人 profile 增加間距」）：
 *   Order 長條與個人圓鈕原本「外盒上下相接、間距 0」→ 多讓一個 --bc-buy-profile-gap
 *   （定義在 bc-attract.css 的 .bc-attract-nav，預設 12px；各斷點 .bc-attract-profile
 *   的 CSS fallback top 亦 var() 引用同一值，JS 未執行時也一致）。
 *
 * 2026-09-21（使用者指示「手機端/平板端 整組三個一起向上移」）：
 *   anchorTop() 最後扣除 --bc-attract-lift（bc-attract.css：桌面 0px、≤991.98 8px），
 *   購物車／Order 長條／個人圓鈕皆由此基準推導 → 整組同步上移；
 *   上移後仍以 weather 下緣 + WEATHER_GAP 為下限（about 頁不會壓到天氣元件）。
 *
 * 避免載入瞬間位置跳動：base.html <head> 先對 <html> 加 .bc-attract-pending
 *   （bc-attract.css 讓 .bc-attract-nav 暫時 visibility: hidden），定位完成即移除；
 *   <head> 另有 1.2s 保險計時器，即使本檔未執行也會自動顯示，不會整組消失。
 */
(function () {
  'use strict';

  /* 防裁切下限（可見長條至少離視窗頂 6px） */
  var MIN_TOP = 6;
  /* 2026-09-21：weather 可見的頁面（僅 about）→ 浮動購物車與整組讓開天氣元件的下緣間距 */
  var WEATHER_GAP = 8;

  /** 對齊基準：navbar-brand 頂邊的文件座標（量不到時退回 weather，再退回 null）
   *  2026-09-21（使用者指示「浮動購物車所有模板位置和 index 一樣」＋「weather 只有 about 顯示」）：
   *  兩項一起生效時，about 頁的天氣元件（navbar 右上、與 Order 同軸線）正好落在
   *  浮動購物車的位置上 → 這裡讓整組往下讓開 weather 下緣，避免圖示被天氣/日期蓋住。
   *  其餘頁面 weather 為 visibility:hidden，量到的值不會超過 brand 頂邊 → 行為等同 index。 */
  function anchorTop() {
    var scrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
    var anchor = null;
    var brand = document.querySelector('#ftco-navbar .navbar-brand');
    if (brand) {
      var br = brand.getBoundingClientRect();
      if (br.height) anchor = br.top + scrollTop;
    }
    var w = document.querySelector('#ftco-navbar .weather');
    if (anchor === null && w) {
      /* fallback：weather 盒頂邊（weather 全站隱藏但仍在 navbar 排版中，仍可量測） */
      var wr0 = w.getBoundingClientRect();
      if (wr0.height) anchor = wr0.top + scrollTop;
    }
    if (anchor === null) return null;
    /* weather 可見（about 頁）→ 不可讓浮動鈕壓在它上面（此為下限，最後仍要守住） */
    var floor = null;
    if (w && getComputedStyle(w).visibility === 'visible') {
      var wr = w.getBoundingClientRect();
      if (wr.height) floor = wr.bottom + scrollTop + WEATHER_GAP;
    }
    if (floor !== null && floor > anchor) anchor = floor;
    /* 2026-09-21（使用者指示「手機端/平板端 整組三個一起向上移」）：
       整組上移 --bc-attract-lift（桌面 0、≤991.98 為 8px）；三者皆由此基準推導 → 一起平移。 */
    anchor -= lift();
    /* 上移後仍不可壓到 weather 元件 */
    if (floor !== null && anchor < floor) anchor = floor;
    return anchor;
  }

  /** 整組上移量（2026-09-21 使用者指示：手機/平板「整組三個一起向上移」）
   *  讀 bc-attract.css 的 --bc-attract-lift（桌面 0px、≤991.98 為 8px），單一來源。 */
  function lift() {
    var nav = document.querySelector('.bc-attract-nav');
    if (!nav) return 0;
    var v = parseFloat(getComputedStyle(nav).getPropertyValue('--bc-attract-lift'));
    return isFinite(v) ? v : 0;
  }

  /** 定位完成 → 顯示整組（並移除 <head> 的 pending 標記） */
  function reveal() {
    var nav = document.querySelector('.bc-attract-nav');
    if (nav) nav.classList.add('bc-attract-ready');
    document.documentElement.classList.remove('bc-attract-pending');
  }

  /** 整組移動後請浮動購物車重算（它貼著可見長條定位） */
  function syncCart() {
    if (window.bcCart && typeof window.bcCart._placeFloatingCart === 'function') {
      window.bcCart._placeFloatingCart();
    }
  }

  function place() {
    var buy = document.querySelector('.bc-attract-buy');
    var prof = document.querySelector('.bc-attract-profile');
    if (!buy || !prof) {
      reveal();
      return;
    }
    var anchor = anchorTop();
    if (anchor === null) {
      /* 量不到基準時清掉 inline top，交回 CSS（top: 50%），
         避免殘留上一個裝置算出的舊值造成永久位移。 */
      buy.style.top = '';
      prof.style.top = '';
      reveal();
      syncCart();
      return;
    }
    var hB = buy.getBoundingClientRect().height;
    var hP = prof.getBoundingClientRect().height;
    /* 浮動購物車佔位＝max(44px 透明點擊區下限, --bc-fc-size)，
       與 bc-slideout-cart.js 的 _placeFloatingCart() 算一致（皆直接讀 DOM/CSS，不寫死第二份常數）。 */
    var fcEl = document.getElementById('bc-floating-cart');
    var fcBtn = document.getElementById('bc-floating-cart-btn');
    var fcSize = fcEl ? parseFloat(getComputedStyle(fcEl).getPropertyValue('--bc-fc-size')) : NaN;
    var fcMin = fcBtn ? parseFloat(getComputedStyle(fcBtn).minHeight) : NaN;
    var fcBox = Math.max(isFinite(fcSize) ? fcSize : 0, isFinite(fcMin) ? fcMin : 0);
    var attract = parseFloat(getComputedStyle(buy).getPropertyValue('--attract'));
    if (!isFinite(attract)) attract = 0;
    var fcGap = fcEl ? parseFloat(getComputedStyle(fcEl).getPropertyValue('--bc-fc-gap')) : NaN;
    if (!isFinite(fcGap)) fcGap = 0;
    /* Order 長條與個人圓鈕之間的間距（2026-09-21 使用者指示「增加間距」；
       定義在 bc-attract.css 的 .bc-attract-nav，CSS fallback top 亦引用同一變數） */
    var profileGap = parseFloat(getComputedStyle(buy).getPropertyValue('--bc-buy-profile-gap'));
    if (!isFinite(profileGap)) profileGap = 0;
    /* 購物袋 top = anchor → 購物袋底緣 = anchor + fcBox = 可見長條頂端需再讓 --attract(熱區負 margin)
       → 外層盒中心 top = anchor + fcBox + fcGap + --attract + hB/2（CSS translateY(-50%)） */
    var buyTop = Math.max(anchor + fcBox + fcGap + attract + hB / 2, Math.ceil(hB / 2) + MIN_TOP);
    buy.style.top = Math.round(buyTop) + 'px';
    /* 個人圓鈕中心 = buy 中心 + (hB + hP)/2（兩者邊緣相接）＋ profileGap（使用者指定的間距） */
    prof.style.top = Math.round(buyTop + (hB + hP) / 2 + profileGap) + 'px';
    reveal();
    syncCart();
  }

  var rAF = 0;
  var settleTimer = 0;
  function onResize() {
    if (!rAF) {
      rAF = requestAnimationFrame(function () {
        rAF = 0;
        place();
      });
    }
    /* 切換裝置當下 navbar 版面（字級/圖片）可能仍在重排，
       rAF 那次會量到中間值 → 安定後再對齊一次。 */
    clearTimeout(settleTimer);
    settleTimer = setTimeout(place, 350);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', place);
  } else {
    place();
  }
  window.addEventListener('load', place);
  window.addEventListener('resize', onResize);
  /* 旋轉螢幕／手機網址列伸縮／網頁字型載入完成後各再對齊一次 */
  window.addEventListener('orientationchange', onResize);
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', onResize);
  }
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(place).catch(function () {});
  }
  /* 其他頁面（非首頁）的內容／延遲載入資源可能晚於 DOMContentLoaded 才改變版面 */
  setTimeout(place, 400);
  setTimeout(place, 1200);

  /* 供 bc-slideout-cart.js 共用（Buy 按鈕被隱藏時，浮動購物車也要對齊同一基準） */
  window.bcAttractPlace = { place: place, anchorTop: anchorTop, reveal: reveal };
})();
