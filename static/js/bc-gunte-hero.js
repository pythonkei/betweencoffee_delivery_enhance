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
      start: 3,
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

    Array.prototype.forEach.call(handItems, function (item, index) {
      item.addEventListener('click', function () {
        splideHero.go(index);
      });
    });

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
