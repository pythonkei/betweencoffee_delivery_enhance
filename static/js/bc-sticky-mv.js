/* ============================================================
   bc-sticky-mv.js — About 頁首屏「sticky 影片背景 + 產品照弧形輪播」
   2026-11-03 建立（移植 yurumaru.life 首頁 .page-top__mv__wrap / .sticky-bg）

   來源：yurumaru.life（Shopify 主題）—— sticky 影片由純 CSS 完成（見
         static/css/bc-sticky-mv.css 檔頭），本檔只負責兩件事：
         ① 產品列輪播（原站用 Splide；此處以原生 rAF + CSS transition 重寫，
            不引入 Splide／GSAP → CDN 失效也能運作）
         ② 影片播放控制（進入視口才 play、離開暫停；respects reduced-motion）

   Splide 參數對照（原站 data-splide 原值，逐值照抄）
     type: loop        → 前後各複製一組 slide 做無縫接續（pos 超出 [n,2n) 時瞬移一組）
     speed: 1750       → DURATION_MS（交給 CSS transition: var(--mv-dur)）
     easing: cubic-bezier(.83,0,.17,1) → CSS var(--mv-ease)
     autoplay: 4000    → AUTOPLAY_MS
     perPage/gap/padding → 由 CSS 變數 --mv-per/--mv-gap/--mv-pad 決定（斷點 680）
     focus: center     → 每次都以「當前張中心 = 視窗中心」計算 translateX
     flickPower: 200   → FLICK_POWER（拖曳超過即前進一張）

   分層上浮（translateY -18% / -6% / 0）全在 CSS，本檔只切換
   .is-active-logical / .is-prev-logical / .is-next-logical。

   守衛：找不到 #bc-sticky-mv 或輪播節點時立即 return（比照 bc-popeye50.js）。
   ============================================================ */
(function () {
  'use strict';

  var AUTOPLAY_MS = 4000; /* 原站 autoplay:4000 */
  var DURATION_MS = 1750; /* 原站 speed:1750 */
  var FLICK_POWER = 200; /* 原站 flickPower:200 */
  var DRAG_CLICK_GUARD = 8; /* 位移超過此值視為拖曳，攔掉隨後的 click */

  var mqReduce = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: false };

  /* ---------------- 影片層 ---------------- */
  function initVideo(root) {
    var video = root.querySelector('.sticky-bg__bg video');
    if (!video) return;

    function play() {
      var p = video.play();
      if (p && typeof p.catch === 'function') p.catch(function () {});
    }

    if (mqReduce.matches) {
      video.removeAttribute('autoplay');
      video.pause();
      return;
    }

    if (!('IntersectionObserver' in window)) {
      play();
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            if (!document.hidden) play();
          } else {
            video.pause();
          }
        });
      },
      { threshold: 0.01 }
    );
    io.observe(root);

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) video.pause();
      else play();
    });
  }

  /* ---------------- 產品列輪播 ---------------- */
  function initCarousel(root) {
    var product = root.querySelector('.page-top__mv__product');
    var list = product ? product.querySelector('.mv-product__list') : null;
    if (!product || !list) return;

    var originals = Array.prototype.slice.call(list.children);
    var n = originals.length;
    if (!n) return; /* 空資料 → CSS 的 .bc-mv-empty 顯示提示 */

    /* 前後各複製一組 slide：loop 時 pos 超出 [n, 2n) 就瞬移一組（原站 type:loop）。
       前面那組是必要的——pos = 第一張時左側仍有鄰卡，弧形排列才兩邊都滿。 */
    function makeClone(slide) {
      var clone = slide.cloneNode(true);
      clone.setAttribute('aria-hidden', 'true');
      Array.prototype.forEach.call(clone.querySelectorAll('a, button'), function (el) {
        el.setAttribute('tabindex', '-1');
      });
      return clone;
    }

    var leadFrag = document.createDocumentFragment();
    originals.forEach(function (slide) {
      leadFrag.appendChild(makeClone(slide));
    });
    list.insertBefore(leadFrag, list.firstChild);

    originals.forEach(function (slide) {
      list.appendChild(makeClone(slide));
    });

    var slides = Array.prototype.slice.call(list.children);
    var OFFSET = n; /* 第一張原始 slide 在 slides 中的索引 */
    var step = 1;
    var base = 0;
    var vw = 0;
    var pos = 0;
    var wrapTimer = 0;
    var autoTimer = 0;
    var resizeTimer = 0;
    var inView = true;
    var dragging = false;
    var startX = 0;
    var startPos = 0;
    var deltaX = 0;
    var suppressClick = false;
    var captured = false;

    function measure() {
      var cs = window.getComputedStyle(list);
      var gap = parseFloat(cs.columnGap || cs.gap) || 0;
      var pad = parseFloat(cs.paddingLeft) || 0;
      var w = originals[0].getBoundingClientRect().width || 0;
      vw = document.documentElement.clientWidth;
      step = w + gap || 1;
      base = pad + w / 2;
    }

    function translateX() {
      return vw / 2 - base - pos * step;
    }

    /* 一般位移（animate=false 供拖曳中即時跟手） */
    function setX(animate) {
      list.style.transition = animate ? '' : 'none';
      list.style.transform = 'translate3d(' + translateX() + 'px, 0, 0)';
    }

    /* 無動畫瞬移（loop 歸位或 resize 重算；需強制 reflow 才不會補間） */
    function jump() {
      list.style.transition = 'none';
      list.style.transform = 'translate3d(' + translateX() + 'px, 0, 0)';
      void list.offsetWidth;
      list.style.transition = '';
    }

    function updateClasses() {
      for (var i = 0; i < slides.length; i++) {
        var d = i - pos;
        slides[i].classList.toggle('is-active-logical', Math.abs(d) < 0.5);
        slides[i].classList.toggle('is-prev-logical', d < -0.5 && d > -1.5);
        slides[i].classList.toggle('is-next-logical', d > 0.5 && d < 1.5);
      }
    }

    function normalize() {
      var changed = false;
      while (pos >= OFFSET + n) {
        pos -= n;
        changed = true;
      }
      while (pos < OFFSET) {
        pos += n;
        changed = true;
      }
      if (changed) {
        jump();
        updateClasses();
      }
    }

    function moveTo(target, animate) {
      pos = target;
      setX(animate !== false);
      updateClasses();
      clearTimeout(wrapTimer);
      if (animate === false) normalize();
      else wrapTimer = setTimeout(normalize, DURATION_MS + 60);
    }

    /* 自動輪播（原站 autoplay:4000） */
    function stopAuto() {
      clearInterval(autoTimer);
      autoTimer = 0;
    }

    function startAuto() {
      stopAuto();
      if (mqReduce.matches) return; /* 減少動態 → 不自動播放 */
      autoTimer = setInterval(function () {
        if (dragging || document.hidden || !inView) return;
        moveTo(Math.round(pos) + 1, true);
      }, AUTOPLAY_MS);
    }

    /* 拖曳（原站 flickPower:200） */
    function onDown(e) {
      if (e.button !== undefined && e.button > 0) return;
      dragging = true;
      captured = false;
      startX = e.clientX;
      startPos = pos;
      deltaX = 0;
      stopAuto();
      product.classList.add('is-dragging');
      list.style.transition = 'none';
    }

    function onMove(e) {
      if (!dragging) return;
      deltaX = e.clientX - startX;

      /* 位移超過門檻才鎖定 pointer：太早 setPointerCapture 會讓 click 全部落在容器上，
         商品連結就永遠點不到（實測 bug）。 */
      if (!captured && Math.abs(deltaX) > DRAG_CLICK_GUARD) {
        captured = true;
        if (product.setPointerCapture && e.pointerId !== undefined) {
          try {
            product.setPointerCapture(e.pointerId);
          } catch (err) {
            /* 忽略：部分瀏覽器不支援 */
          }
        }
      }

      pos = startPos - deltaX / step;
      setX(false);
      updateClasses();
    }

    function onUp() {
      if (!dragging) return;
      dragging = false;
      product.classList.remove('is-dragging');

      var target = Math.round(pos);
      if (Math.abs(deltaX) >= FLICK_POWER && target === Math.round(startPos)) {
        target = Math.round(startPos) + (deltaX < 0 ? 1 : -1);
      }
      moveTo(target, true);
      startAuto();

      if (Math.abs(deltaX) > DRAG_CLICK_GUARD) {
        suppressClick = true;
        setTimeout(function () {
          suppressClick = false;
        }, 350);
      }
    }

    /* 拖曳結束後不要誤觸商品連結 */
    product.addEventListener(
      'click',
      function (e) {
        if (suppressClick) {
          e.preventDefault();
          e.stopPropagation();
        }
      },
      true
    );

    product.addEventListener('pointerdown', onDown);
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    window.addEventListener('pointercancel', onUp);

    /* 鍵盤（list 在 markup 帶 tabindex="0"） */
    list.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') {
        moveTo(Math.round(pos) - 1, true);
        e.preventDefault();
      } else if (e.key === 'ArrowRight') {
        moveTo(Math.round(pos) + 1, true);
        e.preventDefault();
      }
    });

    /* 尺寸變動 → 重新量測（slide 寬度是 CSS 計算值，換斷點會變） */
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(function () {
        measure();
        jump();
      }, 150);
    });
    window.addEventListener('orientationchange', function () {
      setTimeout(function () {
        measure();
        jump();
      }, 300);
    });

    /* 離開視口暫停自動輪播 */
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            inView = entry.isIntersecting;
          });
        },
        { threshold: 0 }
      ).observe(root);
    }

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stopAuto();
      else startAuto();
    });

    /* ---------------- 啟動 ---------------- */
    measure();
    pos = OFFSET; /* 從第一張原始 slide 開始（前面那組是複製品） */
    setX(false);
    updateClasses();
    startAuto();
  }

  function init() {
    var root = document.getElementById('bc-sticky-mv');
    if (!root) return;
    initVideo(root);
    initCarousel(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

