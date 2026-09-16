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

    /* 5. 2026-09-16：iOS／行動瀏覽器底部工具列遮擋修正
       問題：position:fixed 的模組以「layout viewport」定位，而行動 Safari 的
             分頁列／工具列／首頁指示列會蓋在 layout viewport 底部 →
             bottom:20~24px 的元素實機只露出上緣（iPad 實測遮住約 120px、iPhone 約 58px）。
       解法：以 visualViewport 量測「layout viewport 與實際可視區」的差（＝被遮住的高度），
             寫入 CSS 變數 --bc-vis-gap，CSS 端 tax-nav / header-bot 的 bottom 加上它。
             桌機（無遮擋）差值為 0 → 位置完全不變。 */
    if (window.visualViewport) {
      var syncVisGap = function () {
        var vv = window.visualViewport;
        var gap = window.innerHeight - vv.height - vv.offsetTop;
        if (!isFinite(gap) || gap < 0) gap = 0;
        if (gap > 200) gap = 200;   /* 螢幕鍵盤等極端情況的上限保護 */
        document.documentElement.style.setProperty('--bc-vis-gap', Math.round(gap) + 'px');
      };
      syncVisGap();
      window.visualViewport.addEventListener('resize', syncVisGap);
      window.visualViewport.addEventListener('scroll', syncVisGap);
      window.addEventListener('orientationchange', syncVisGap);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
