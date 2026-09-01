/* ============================================================
   bc-ramen-product.js — ramenclub.jp c-sec-product-real「3つのリアル」整合
   2026-08-28 整合
   ------------------------------------------------------------------
   完整複製 ramenclub.jp/dev-script.js 的相關機制（vanilla 重現）：
   1. js-img：讀 data-image-d1x/d2x/mob/pre → 建立 <img> 填入 .js-img-poster，
      載入後加 is-image-loaded（CSS 處理淡入 + c-zoom 30s 慢縮放）
   2. is-acrive-1/2/3：scroll 進度切換 3 張圖堆疊（progress > .6666→3、> .3333→2、else→1）
   3. js-hover：pointerenter/leave → is-pointer-enter（CSS 展開白色詳情面板）
   4. c-cl 文字：section 加 is-loaded + 進視口 c-real-txt data-shown="1" → 文字 reveal
   5. c-iv（js-iv）：進視口 data-visible="1"（translateY 50px→0）
   6. is-any / is-not-any：視窗寬度 < 900 行動端（對應原站 body class）
   ============================================================ */
(function () {
  'use strict';

  var wrap = document.querySelector('.bc-product-real');
  if (!wrap) return;
  var section = wrap.querySelector('.c-sec-product-real');
  if (!section) return;

  /* ---- 1. js-img：data-image → <img> ---- */
  wrap.querySelectorAll('.js-img').forEach(function (el) {
    var d1 = el.getAttribute('data-image-d1x');
    var d2 = el.getAttribute('data-image-d2x');
    var mob = el.getAttribute('data-image-mob');
    var pre = el.getAttribute('data-image-pre');
    var src = null;
    if (window.innerWidth <= 680 && mob) src = mob;
    else if (window.devicePixelRatio >= 2 && d2) src = d2;
    else if (d1) src = d1;
    else src = pre || d2;
    if (!src) return;
    var poster = el.querySelector('.js-img-poster');
    if (!poster) return;
    var img = document.createElement('img');
    img.alt = '';
    img.decoding = 'async';
    img.src = src;
    poster.appendChild(img);
    img.addEventListener('load', function () {
      el.classList.add('is-image-loaded');
    });
  });

  /* ---- fixEls：pin 鎖定元素（圖片/背景/標題，原站 ScrollTrigger fixEls） ---- */
  var fixEls = Array.prototype.slice.call(section.querySelectorAll('.c-real-img'))
    .concat(Array.prototype.slice.call(section.querySelectorAll('.c-sec-bg-fix')))
    .concat(Array.prototype.slice.call(section.querySelectorAll('.c-sec-title')));
  var pinned = false;

  /* ---- 2. scroll：pin（鎖定螢幕）+ is-acrive 切換 + c-cl / c-iv 觸發 ---- */
  function update() {
    var vh = window.innerHeight;
    var sectionTop = wrap.offsetTop;
    var scrollRange = section.offsetHeight - vh;
    var start = sectionTop;
    var end = sectionTop + scrollRange;
    var sy = window.scrollY;
    var p = scrollRange > 0 ? (sy - start) / scrollRange : 0;
    p = Math.max(0, Math.min(1, p));

    var isAny = section.classList.contains('is-any');

    /* pin：進入視口（top top）→ fixEls fixed 鎖定螢幕；
       離開（bottom bottom）→ 釋放回 absolute（對應原站 onEnter/onLeave） */
    if (!isAny) {
      if (sy >= start && sy < end) {
        if (!pinned) {
          fixEls.forEach(function (el) { el.style.position = 'fixed'; });
          pinned = true;
        }
      } else if (pinned) {
        fixEls.forEach(function (el) { el.style.position = 'absolute'; });
        pinned = false;
      }
    } else if (pinned) {
      fixEls.forEach(function (el) { el.style.position = ''; });
      pinned = false;
    }

    /* is-acrive：progress > .6666→3、> .3333→2、else→1 */
    section.classList.toggle('is-acrive-3', p > 0.6666);
    section.classList.toggle('is-acrive-2', p > 0.3333 && p <= 0.6666);
    section.classList.toggle('is-acrive-1', p <= 0.3333);

    /* 進視口：c-cl 文字 reveal + c-iv 上移 */
    if (sy + vh > sectionTop && sy < end) {
      wrap.querySelectorAll('.c-real-txt').forEach(function (txt) {
        txt.setAttribute('data-shown', '1');
      });
      wrap.querySelectorAll('.js-iv').forEach(function (iv) {
        iv.setAttribute('data-visible', '1');
      });
    }
  }
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      update();
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);

  /* ---- 3. js-hover：is-pointer-enter + 點擊 toggle（平板/觸控可展開）---- */
  wrap.querySelectorAll('.js-hover').forEach(function (hover) {
    var enter = hover.querySelector('.js-hover-enter');
    var leave = hover.querySelector('.js-hover-leave');
    /* 2026-08-28 修復：click toggle 綁定在整個 .js-hover 容器——
       展開後白色詳情面板（.c-real-detail）覆蓋下半區域，點擊下半命中面板
       （非 .js-hover-enter）會無法關閉；綁容器讓點擊任何區域都能 toggle。
       平板 tap：pointerenter→pointerleave→click toggle 加回 → 展開保持。 */
    hover.addEventListener('click', function (e) {
      e.preventDefault();
      hover.classList.toggle('is-pointer-enter');
    });
    if (enter) {
      /* 2026-08-28 修復：pointerenter/leave 僅對滑鼠（hover）生效——
         touch tap 的 pointerenter 觸發加 is-pointer-enter 但 pointerleave 不觸發，
         會與 click toggle 衝突（加後又被 toggle 移除）。touch 統一由 click toggle 控制。 */
      enter.addEventListener('pointerenter', function (e) {
        if (!e.pointerType || e.pointerType === 'mouse') {
          hover.classList.add('is-pointer-enter');
        }
      });
      enter.addEventListener('pointerleave', function (e) {
        if (!e.pointerType || e.pointerType === 'mouse') {
          hover.classList.remove('is-pointer-enter');
        }
      });
    }
    if (leave) {
      leave.addEventListener('pointerenter', function (e) {
        if (!e.pointerType || e.pointerType === 'mouse') {
          hover.classList.add('is-pointer-enter');
        }
      });
    }
  });

  /* ---- 4. c-cl 觸發所需：section is-loaded ---- */
  section.classList.add('is-loaded');

  /* ---- 5. is-any / is-not-any（行動/桌面）---- */
  function applyAny() {
    var any = window.innerWidth < 768;
    section.classList.toggle('is-any', any);
    section.classList.toggle('is-not-any', !any);
  }
  applyAny();
  window.addEventListener('resize', applyAny);

  /* 初始狀態 */
  update();
})();
