/* ============================================================
   bc-recommended-pages.js — 首頁「推薦頁面」雙卡互動
   2026-10-24 建立
   ------------------------------------------------------------------
   對應原站 union-tec.jp/capability 的 Alpine 元件
   Alpine.data('recommendedPages')（同一頁面的 index.js bundle）：
     - mouseenter：自己被 hover → is-hover-active，
                   其餘卡片 → is-hover-inactive
     - mouseleave：全部移除兩個 class
     - 桌機／行動版佈局切換（原站 watch $store.app.isPcLayout）
       → 清空 hover 狀態，避免殘留 2/3、1/3 寬度
   原站的 clip-path 形狀補間是 GSAP MorphSVG；本檔不重做補間
   —— 寬度／形狀的過渡全部由 bc-recommended-pages.css 的
   transition（clip-path / width / opacity / transform）負責，
   JS 只切 class，行為與原站一致。
   ============================================================ */
(function () {
  'use strict';

  var ROOT_SELECTOR = '[data-bc-recommended-pages]';
  var LINK_SELECTOR = '.recommended-pages__link';
  var ACTIVE = 'is-hover-active';
  var INACTIVE = 'is-hover-inactive';

  function setup(root) {
    if (root.getAttribute('data-rp-ready') === '1') {
      return;
    }
    root.setAttribute('data-rp-ready', '1');

    var links = Array.prototype.slice.call(
      root.querySelectorAll(LINK_SELECTOR)
    );
    if (!links.length) {
      return;
    }

    function clear() {
      links.forEach(function (link) {
        link.classList.remove(ACTIVE, INACTIVE);
      });
    }

    function enter(current) {
      links.forEach(function (link) {
        var isCurrent = link === current;
        link.classList.toggle(ACTIVE, isCurrent);
        link.classList.toggle(INACTIVE, !isCurrent);
      });
    }

    links.forEach(function (link) {
      link.addEventListener('mouseenter', function () {
        enter(link);
      });
      link.addEventListener('mouseleave', clear);
    });

    /* 原站 $watch('$store.app.isPcLayout')：斷點切換時重置 */
    var mq = window.matchMedia('(min-width: 64rem)');
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', clear);
    } else if (typeof mq.addListener === 'function') {
      mq.addListener(clear);
    }
  }

  function init() {
    Array.prototype.forEach.call(
      document.querySelectorAll(ROOT_SELECTOR),
      setup
    );
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
