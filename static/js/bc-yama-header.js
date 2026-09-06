/* ============================================================
   bc-yama-header.js — yama-beer.com .header-bot(_pc) + .tax-nav 動畫
   2026-09-04
   -----------------------------------------------------------------
   複刻 yama-beer common.js 的對應機制（vanilla 重現）：
   1. tax-nav：DOMContentLoaded 後 transitionDelay 0.7s → 加 init 淡入
      （50ms 後移除 transitionDelay 還原）；
      IntersectionObserver(footer)：進入視口移除 init（隱藏）、
      離開加回 init（顯示）
   2. header-bot：首次 scroll（once）加 is-view 淡入；
      footer 進入視口加 is-hide、離開移除
   3. Cart 連結：點擊開啟既有滑出購物車（#bc-cart-toggle 同款 handler），
      不新增 UI
   僅於 index.html 載入，且 .bc-yama 不存在時自動 return（他頁安全）。
   ============================================================ */
(function () {
  'use strict';

  function init() {
    var tax = document.querySelector('.bc-yama .tax-nav');
    var bot = document.querySelector('.bc-yama .header-bot');
    if (!tax && !bot) return;

    var footer = document.querySelector('footer');
    var navToggle = document.getElementById('bc-cart-toggle');

    /* 1. tax-nav init 淡入（延遲 0.7s） */
    if (tax) {
      tax.style.transitionDelay = '0.7s';
      tax.classList.add('init');
      setTimeout(function () {
        tax.style.transitionDelay = '0s';
      }, 50);
    }

    /* 2. header-bot：首次 scroll 加 is-view */
    if (bot) {
      var showOnce = function () {
        bot.classList.add('is-view');
        window.removeEventListener('scroll', showOnce);
      };
      window.addEventListener('scroll', showOnce, { passive: true });
    }

    /* 3. footer 交會：tax-nav 移除 init / header-bot is-hide；離開時還原 */
    if (footer && (tax || bot)) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          var inView = entry.isIntersecting;
          if (tax) {
            if (inView) tax.classList.remove('init');
            else tax.classList.add('init');
          }
          if (bot) bot.classList.toggle('is-hide', inView);
        });
      });
      io.observe(footer);
    }

    /* 4. Cart：開既有滑出購物車 */
    if (bot && navToggle) {
      var cartLink = bot.querySelector('.account .cart a');
      if (cartLink) {
        cartLink.addEventListener('click', function (e) {
          e.preventDefault();
          navToggle.click();
        });
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
