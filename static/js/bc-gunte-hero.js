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

    var navButtons = root.querySelectorAll('#hero_nav button');
    var slides = root.querySelectorAll('.splide__slide');

    /* 2026-10-14（使用者指示）：環形照片列的驅動改由共用模組 BC_HAND_RING
       （static/js/bc-hand-ring.js）負責 —— 本 hero 與其下方 BC 動態 hero 的照片格
       （#bc-stage-photo-ring）註冊在同一個模組上，索引一律由本 hero 的 Splide 推播
       （見 updateSlideStates → goAll），兩邊因此永遠同一支咖啡。
       [為何註冊在 mount 之前] 'mounted' 事件就會呼叫 updateSlideStates → 屆時環必須已註冊，
         第一次的索引（start: 1）才會一起套上去。
       [旋轉公式/時機] 原本的 rotateHeroHand() 內容（rotate(index × -25deg) ＋ -current）
         已原封不動移進模組；過渡由模組的 .is-ready 控制（＝原 :has(.is-initialized)）。
       [載入順序] bc-hand-ring.js 於 index.html 緊接本檔之前載入（同步）→ 一定已存在；
         仍保留存在性檢查，模組缺失時只是不旋轉，不影響 Splide 本身。 */
    if (window.BC_HAND_RING) window.BC_HAND_RING.register(root.querySelector('.hero_hand'));

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
        } else if (current === (splideHero.index + 2 <= total ? splideHero.index + 2 : 1)) {
          slide.classList.add('state-next');
        } else if (current === (splideHero.index === 0 ? total : splideHero.index)) {
          slide.classList.add('state-prev');
        }
      });

      Array.prototype.forEach.call(navButtons, function (button, index) {
        button.classList.toggle('-current', index === splideHero.index);
      });

      // 環形照片列（hero ＋ 首頁照片格）跟到同一個索引
      if (window.BC_HAND_RING) window.BC_HAND_RING.goAll(splideHero.index);
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
