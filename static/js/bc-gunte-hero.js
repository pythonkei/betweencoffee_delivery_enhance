/* ============================================================
   bc-gunte-hero.js — GUNTE Lab. hero 動畫移植
   來源：/js/home.js（set_hero_slider）+ /js/common.js（body.-load 觸發進場）
   移植重點：
   - 僅初始化 .bc-gunte-hero 內的 Splide（選項與原站完全相同）
   - Splide 移動時同步 state-active/prev/next、手套圓旋轉、hero_nav -current
   - 原站以 body.-load 觸發進場 → 改加在 wrapper 的 .-load
   ============================================================ */
(function () {
  'use strict';
  var root = document.querySelector('.bc-gunte-hero');
  if (!root) return;

  function loadClass() {
    root.classList.add('-load');
  }

  function initHero() {
    var splideEl = root.querySelector('.hero_slide .splide');
    if (!splideEl || typeof Splide === 'undefined') { loadClass(); return; }

    var splideHero = new Splide(splideEl, {
      type: 'slide',
      focus: 'center',
      arrows: false,
      rewind: true,
      pagination: false,
      pauseOnHover: true,
      pauseOnFocus: true,
      autoplay: true,
      interval: 5000,
      speed: 1200,
      rewindSpeed: 2400,
      // 2026-10-13（使用者指示：載入時就要看得到環形字）：環形字只有 DOM 第 2 張
      // （BUTTER KING，aria-label「2 of 7」，path #bc-gunte-06-path）顯示 —— 其餘 6 張是
      // <text class="bc-ring-hide">，由 bc-gunte-hero.css 的 display:none 隱藏；而
      // .hero_slide_item_ttl 又只在 .state-active（＝置中那張）時 opacity 1 → start 必須指到
      // 第 2 張，載入當下才會出現環形字。
      // ⚠ Splide 的 start 是 **0-based 索引**（不是「第幾張」）：實測 start: 2 置中的是
      //   aria-label「3 of 7」＝ 第 3 張「果香浅煎」（環形字被隱藏）；原 start: 3 → 第 4 張。
      //   因此第 2 張（aria-label「2 of 7」）＝ start: 1；start: 0 才是第 1 張 BLACK BLEND
      //   （環形字同樣被隱藏 → 那三個值的載入畫面都不會有環形字）。
      start: 1,
      easing: 'ease'
    });

    var handList = root.querySelector('#hero_hand_list');
    var handItems = handList ? handList.querySelectorAll('.hero_hand_item') : [];
    var navButtons = root.querySelectorAll('#hero_nav button');
    var slides = root.querySelectorAll('.splide__slide');

    function rotateHeroHand(index) {
      if (!handList || !handItems.length) return;
      var targetAngle = index * -25;
      handList.style.transform = 'rotate(' + targetAngle + 'deg)';
      Array.prototype.forEach.call(handItems, function (item, i) {
        item.classList.toggle('-current', i === index);
      });
    }

    function updateSlideStates() {
      Array.prototype.forEach.call(slides, function (slide) {
        slide.classList.remove('state-prev', 'state-next', 'state-active');
        var ariaLabel = slide.getAttribute('aria-label');
        if (!ariaLabel) return;

        var parts = ariaLabel.split(' of ').map(Number);
        var current = parts[0];
        var total = parts[1];

        if (current === splideHero.index + 1) {
          slide.classList.add('state-active');
          rotateHeroHand(splideHero.index);
        } else if (current === (splideHero.index + 2 <= total ? splideHero.index + 2 : 1)) {
          slide.classList.add('state-next');
        } else if (current === (splideHero.index === 0 ? total : splideHero.index)) {
          slide.classList.add('state-prev');
        }
      });

      Array.prototype.forEach.call(navButtons, function (button, index) {
        button.classList.toggle('-current', index === splideHero.index);
      });
    }

    Array.prototype.forEach.call(navButtons, function (button, index) {
      button.addEventListener('click', function () {
        splideHero.go(index);
      });
    });

    splideHero.on('mounted', updateSlideStates);
    splideHero.on('move', updateSlideStates);

    splideHero.mount();

    // 進場：window load 後才顯示（等效原站 body.-load）
    if (document.readyState === 'complete') {
      loadClass();
    } else {
      window.addEventListener('load', loadClass);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHero);
  } else {
    initHero();
  }
})();
