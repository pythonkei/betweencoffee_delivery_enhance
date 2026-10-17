/* ============================================================================
   BC brand footer — animation ported from bleibtgleich.dev (Slater / slater615.js)
   ----------------------------------------------------------------------------
   2026-10-07: 只移植 footer 需要的部分（reveal / goo 文字揭示 / 時間 / logo / 連結 hover），
   範圍限縮於 #bc-bg-footer，且不依賴 Barba / Lenis / 站內轉場。
   需要全域：gsap + ScrollTrigger + SplitText + CustomEase（由 about.html extra_scripts 載入）。
   若動畫庫缺失，會立即還原 [data-reveal] 可見狀態，並照常啟動時間 / logo。
   ============================================================================ */
(function () {
  'use strict';

  var root = document.getElementById('bc-bg-footer');
  if (!root) return;

  var DUR_XS = 0.2, DUR_S = 0.4, DUR_M = 0.8, DUR_L = 1.2;
  var STAGGER = 0.1, DELAY_REVEAL = 0.2;

  function revealFallback() {
    var els = root.querySelectorAll('[data-reveal]');
    for (var i = 0; i < els.length; i++) { els[i].style.visibility = 'visible'; }
  }

  /* ---------------- 動態時間（原 initFooterTime） ---------------- */
  function initFooterTime(scope) {
    var h = scope.querySelector('[data-footer-time="hours"]');
    var m = scope.querySelector('[data-footer-time="minutes"]');
    if (!h && !m) return;
    if (window.__footerTimeInterval) { clearInterval(window.__footerTimeInterval); window.__footerTimeInterval = null; }
    var pad = function (n) { return String(n).padStart(2, '0'); };
    var tick = function () {
      var d = new Date(), hh = pad(d.getHours()), mm = pad(d.getMinutes());
      if (h && h.textContent !== hh) h.textContent = hh;
      if (m && m.textContent !== mm) m.textContent = mm;
    };
    tick();
    window.__footerTimeInterval = setInterval(tick, 1000);
  }

  /* ---------------- Logo 輪播（原 initFooterLogo；BC 5 張 deco 自動輪播） ---------------- */
  function initFooterLogo(scope) {
    var list = scope.querySelector('[data-footer-logo="list"]');
    if (!list) return;
    var wrap = scope.querySelector('[data-footer-logo="wrap"]') || list;
    var items = Array.prototype.slice.call(list.querySelectorAll('[data-footer-logo="item"]'));
    // 2026-10-14（使用者指示）：首頁照片格已改為「環形照片列」（見下方 initClockHandRing），
    // 不再有 [data-footer-logo="item"] → 這裡提前結束：首頁不會起 5 秒輪播、
    // window.__footerLogoInterval 也不會被設起來（該計時器僅剩 /about/ 真頁尾使用）。
    if (!items.length) return;

    var show = function (el) { el.style.position = 'relative'; el.style.display = 'block'; };
    var hide = function (el) { el.style.position = 'absolute'; el.style.display = 'none'; };

    if (window.__footerLogoInterval) { clearInterval(window.__footerLogoInterval); window.__footerLogoInterval = null; }
    if (wrap._footerLogoClick) { wrap.removeEventListener('click', wrap._footerLogoClick); wrap._footerLogoClick = null; }

    // 保險：不足 2 張時不輪播，只顯示第一張
    if (items.length < 2) { items.forEach(function (el, i) { i ? hide(el) : show(el); }); return; }

    var cur = 0;
    items.forEach(function (el, i) { i === 0 ? show(el) : hide(el); });
    var setActive = function (next) { if (next !== cur) { hide(items[cur]); show(items[next]); cur = next; } };
    var next = function () { setActive((cur + 1) % items.length); };
    var start = function () {
      if (window.__footerLogoInterval) clearInterval(window.__footerLogoInterval);
      window.__footerLogoInterval = setInterval(next, 5000);
    };
    wrap._footerLogoClick = function () { next(); start(); };
    wrap.addEventListener('click', wrap._footerLogoClick);
    start();
  }

  /* ---------------- 首頁照片格的環形照片列（2026-10-14 使用者指示） ----------------
     標的＝partials/bc_hero.html 內 #bc-clock-photos 的 .footer-logo-cell：一格 .hero_hand
     （7 筆咖啡照的圓弧）＋ 一組「當前那支咖啡」的名稱/highlight（[data-bc-ring-caption]）。
     [同步] 本檔只「註冊」；索引一律由 GUNTE hero 的 Splide 推播
       （bc-gunte-hero.js 的 updateSlideStates → BC_HAND_RING.goAll），模組會讓晚註冊的環
       直接會合到 hero 當下的索引 ⇒ 本檔（defer）與 hero 腳本（非 defer）誰先執行都對，
       不需要任何互推/輪詢（見 static/js/bc-hand-ring.js 的說明）。
     [範圍] /about/ 沒有 [data-bc-hand-ring] → 直接結束（該頁真頁尾的 deco 輪播不受影響）。 */
  function initClockHandRing(scope) {
    var ringRoot = scope.querySelector('[data-bc-hand-ring]');
    if (!ringRoot || !window.BC_HAND_RING) return;
    window.BC_HAND_RING.register(ringRoot, scope.querySelector('[data-bc-ring-caption]'));
  }

  /* ====================== GSAP reveal engine (原 Slater) ====================== */
  function initGsap(scope) {
    var gsap = window.gsap, ScrollTrigger = window.ScrollTrigger, SplitText = window.SplitText, CustomEase = window.CustomEase;
    if (!gsap || !ScrollTrigger || !SplitText || !CustomEase) { revealFallback(); return; }

    gsap.registerPlugin(ScrollTrigger, CustomEase, SplitText);
    CustomEase.create('InOut', '0.76,0,0.24,1');
    CustomEase.create('Out', '0.25,1,0.5,1');
    CustomEase.create('In', '0.5,0,0.75,0');

    var NS = 'http://www.w3.org/2000/svg';

    /* -- goo 文字揭示（原 animateTextReveal；goo 濾鏡掛在 body 上，跨元素引用） -- */
    function gooDefs() {
      var svg = document.querySelector('svg#goo-defs');
      if (!svg) {
        svg = document.createElementNS(NS, 'svg');
        svg.setAttribute('id', 'goo-defs');
        svg.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden';
        document.body.prepend(svg);
      }
      return svg;
    }
    var STD = 50, AMP = 20, OFF = -8;
    var mat = function (a, o) { return '1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 ' + a + ' ' + o; };
    function addFilter(line) {
      if (line.dataset.filterId) return;
      var id = 'goo-' + Math.random().toString(36).slice(2, 11);
      line.dataset.filterId = id;
      var f = document.createElementNS(NS, 'filter');
      f.setAttribute('id', id);
      f.setAttribute('x', '-25%'); f.setAttribute('y', '-25%');
      f.setAttribute('width', '150%'); f.setAttribute('height', '150%');
      f.setAttribute('color-interpolation-filters', 'sRGB');
      f.innerHTML = '<feGaussianBlur in="SourceGraphic" stdDeviation="' + STD + '" result="blur"></feGaussianBlur>' +
        '<feColorMatrix in="blur" mode="matrix" values="' + mat(AMP, OFF) + '" result="goo"></feColorMatrix>';
      gooDefs().appendChild(f);
      line.style.filter = 'url(#' + id + ')';
    }
    var blurOf = function (line) { return document.querySelector('#' + line.dataset.filterId + ' feGaussianBlur'); };
    var matOf = function (line) { return document.querySelector('#' + line.dataset.filterId + ' feColorMatrix'); };

    function animateTextReveal(target, mode, delay) {
      var els = gsap.utils.toArray(target);
      if (!els.length) return;
      els.forEach(function (el, k) {
        if (mode === 'reveal' || mode === 'initial') el.style.display = '';
        if (!el._split) el._split = new SplitText(el, { type: 'lines' });
        el._split.lines.forEach(addFilter);
        var dly = k * STAGGER;
        if (mode === 'initial') {
          el._split.lines.forEach(function (line) {
            var b = blurOf(line), m = matOf(line);
            if (b) b.setAttribute('stdDeviation', STD);
            if (m) m.setAttribute('values', mat(AMP, OFF));
            line.style.filter = 'url(#' + line.dataset.filterId + ')';
          });
        } else if (mode === 'reveal') {
          /* 2026-10-17：同一元素可能被重複 reveal（首頁咖啡名稱每次換張都跑一次）→
             先殺掉前一次的時間軸，避免兩個 tween 同時寫同一組 SVG 濾鏡屬性而抖動。 */
          if (el._revealTl) el._revealTl.kill();
          gsap.set(el, { autoAlpha: 1 });
          var tl = gsap.timeline();
          el._split.lines.forEach(function (line, i) {
            var b = blurOf(line), m = matOf(line);
            if (!b || !m) return;
            b.setAttribute('stdDeviation', STD);
            m.setAttribute('values', mat(AMP, OFF));
            line.style.filter = 'url(#' + line.dataset.filterId + ')';
            var d = i === 0 ? (delay == null ? DELAY_REVEAL : delay) + dly : 0;
            tl.to(b, { attr: { stdDeviation: 0 }, duration: DUR_L, delay: d, ease: 'Out' }, i * STAGGER);
            var g = { amp: AMP, off: OFF };
            tl.to(g, { amp: 1, off: 0, duration: .35 * DUR_L, ease: 'none',
              onUpdate: function () { m.setAttribute('values', mat(g.amp, g.off)); },
              onComplete: function () { m.setAttribute('values', mat(1, 0)); line.style.filter = ''; }
            }, '>-' + .35 * DUR_L);
          });
          el._revealTl = tl;
        } else if (mode === 'hide') {
          var tl2 = gsap.timeline({ onComplete: function () { gsap.set(el, { autoAlpha: 0 }); el.style.display = 'none'; } });
          el._split.lines.forEach(function (line, i) {
            var b = blurOf(line), m = matOf(line);
            if (!b || !m) return;
            b.setAttribute('stdDeviation', 0);
            m.setAttribute('values', mat(1, 0));
            line.style.filter = 'url(#' + line.dataset.filterId + ')';
            var g = { amp: 1, off: 0 };
            tl2.to(g, { amp: AMP, off: OFF, duration: .3 * DUR_S, ease: 'none',
              onUpdate: function () { m.setAttribute('values', mat(g.amp, g.off)); } }, i * STAGGER * .5);
            tl2.to(b, { attr: { stdDeviation: STD }, duration: DUR_S, ease: 'In' }, i * STAGGER * .5);
          });
        }
      });
    }

    /* 2026-10-17（使用者指示）：首頁 hero 的「咖啡名稱 / Highlight」換張時，也要跑同一套
       data-reveal 文字揭示（與右側的 Fresh / Beans 完全相同 —— 同一支 animateTextReveal）。
       [為何掛到 window] 換張的判斷在 static/js/bc-hand-ring.js（本檔之外）：
       環轉到定位、切完 -current 後呼叫 window.BC_TEXT_REVEAL(...) 即可，本檔不需反向依賴它。
       [參數] target 可為 Element 或 NodeList／陣列；多個元素依序 k * STAGGER 錯開
       （＝原引擎對多元素的行為：名稱 0.1s、highlight 0.2s）。
       [降級] GSAP／SplitText 缺失時 initGsap 直接 return ⇒ 這個 API 不存在，
       bc-hand-ring.js 就只是「文字直接出現」（與改動前相同）。 */
    window.BC_TEXT_REVEAL = function (target, delay) {
      if (!target) return;
      animateTextReveal(target, 'reveal', delay == null ? DELAY_REVEAL : delay);
    };

    /* -- div / clip 揭示（原 animateDivReveal / animateClipReveal） -- */
    function animateDivReveal(target, mode, delay) {
      var els = gsap.utils.toArray(target);
      if (!els.length) return;
      if (mode === 'initial') gsap.set(els, { opacity: 0, filter: 'blur(20px)' });
      else if (mode === 'reveal') gsap.to(els, { opacity: 1, filter: 'blur(0px)', duration: DUR_L, delay: delay == null ? DELAY_REVEAL : delay, stagger: STAGGER, ease: 'power2.out', overwrite: true });
      else if (mode === 'hide') gsap.to(els, { opacity: 0, filter: 'blur(20px)', duration: DUR_S, delay: delay == null ? 0 : delay, stagger: .5 * STAGGER, ease: 'power2.in', overwrite: true });
    }
    function animateClipReveal(target, dir, mode, delay) {
      var els = gsap.utils.toArray(target);
      if (!els.length) return;
      var map = {
        'top-down': { hidden: 'inset(0% 0% 100% 0%)', visible: 'inset(0% 0% 0% 0%)' },
        'left-right': { hidden: 'inset(0% 100% 0% 0%)', visible: 'inset(0% 0% 0% 0%)' },
        'right-left': { hidden: 'inset(0% 0% 0% 100%)', visible: 'inset(0% 0% 0% 0%)' },
        'down-top': { hidden: 'inset(100% 0% 0% 0%)', visible: 'inset(0% 0% 0% 0%)' }
      }[dir];
      if (!map) return;
      if (mode === 'initial') gsap.set(els, { clipPath: map.hidden, webkitClipPath: map.hidden });
      else if (mode === 'reveal') gsap.to(els, {
        clipPath: map.visible, webkitClipPath: map.visible, duration: DUR_L,
        delay: delay == null ? DELAY_REVEAL : delay, stagger: STAGGER, ease: 'power2.out',
        overwrite: true, onComplete: function () { releaseRingClip(els); }
      });
      else if (mode === 'hide') gsap.to(els, { clipPath: map.hidden, webkitClipPath: map.hidden, duration: DUR_S, delay: delay == null ? 0 : delay, stagger: .5 * STAGGER, ease: 'power2.in', overwrite: true });
    }

    /* 2026-10-14（使用者指示「展示咖啡動畫不是 footer-logo-list-wrap，區域太小了，動畫展示是
       使用整個頁面的。參考 hero_hand」）：進場裁切（animateClipReveal）只是一次性的揭示效果，
       但 GSAP 會把 clip-path 留在 `inset(0%)` —— 那等於一個「永久把內容框在元素邊界內」的裁切框。
       首頁照片格的環形照片列是**整頁扇形**：側邊鄰居本來就會跑到 .footer-logo-cell 之外
       （照片格不裁、由 #bc-bg-footer 的 overflow:hidden 裁），留著這個裁切框會把左右鄰居整張
       切掉（實測：鄰居 rect 存在、圖片 complete、但 elementFromPoint 命中的是 #bc-clock ⇒
       被 clip 切到 0 可見）。
       故揭示跑完就釋放「內含環形照片列（[data-bc-hand-ring]）」容器的 clip-path：
       視覺上 inset(0%) 與 none 完全相同，只有「允許內容超出格子」這件事會生效。
       其餘 data-reveal="clip-*" 的容器（/about/ 的 deco 釘牌、hero 的天氣元件）一律不動，
       進場動畫與裁切行為完全不變。 */
    function releaseRingClip(els) {
      els.forEach(function (el) {
        if (el.querySelector && el.querySelector('[data-bc-hand-ring]')) {
          gsap.set(el, { clipPath: 'none', webkitClipPath: 'none' });
        }
      });
    }

    /* -- 逐字 hover 連結（原 animateLink / initLinks） -- */
    function animateLink(target, mode, delay, tl, pos) {
      var els = gsap.utils.toArray(target);
      if (!els.length) return;
      els.forEach(function (el, k) {
        if (el._split && el._split.revert) el._split.revert();
        el._split = new SplitText(el, {
          type: 'lines,words,chars', tag: 'span',
          linesClass: 'split-line', wordsClass: 'split-word', charsClass: 'split-char'
        });
        if (!el._split.chars || !el._split.chars.length) return;
        el._split.lines.forEach(function (l) { l.style.display = 'block'; l.style.overflow = 'clip'; });
        el._split.words.forEach(function (w) { w.style.overflow = 'clip'; });
        var chars = el._split.chars, host = tl || gsap, at = pos || '>';
        var dly = k * STAGGER;
        if (mode === 'reveal') { gsap.killTweensOf(chars); host.fromTo(chars, { yPercent: 100 }, { yPercent: 0, duration: DUR_S, delay: tl ? 0 : (delay == null ? DELAY_REVEAL : delay) + dly, stagger: { amount: .075 }, ease: 'InOut', overwrite: true }, tl ? at : undefined); }
        else if (mode === 'hide') { gsap.killTweensOf(chars); host.to(chars, { yPercent: -100, duration: DUR_S, delay: tl ? 0 : (delay == null ? 0 : delay), stagger: { amount: .075 }, ease: 'InOut', overwrite: true }, tl ? at : undefined); }
        else if (mode === 'initial') { gsap.killTweensOf(chars); gsap.set(chars, { yPercent: 100 }); }
      });
    }
    function initLinks(scope) {
      var inners = gsap.utils.toArray('.link-inner', scope);
      if (!inners.length) return;
      inners.forEach(function (inner) {
        var label = inner.querySelector('[data-link="label"]');
        var shadow = inner.querySelector('[data-link="shadow"]');
        if (!label || !shadow) return;
        gsap.set(shadow, { display: 'block' });
        animateLink(shadow, 'initial');
        var tl = gsap.timeline({ paused: true });
        animateLink(label, 'hide', 0, tl, 0);
        animateLink(shadow, 'reveal', 0, tl, 0);
        var play = function () { tl.play(); }, rev = function () { tl.reverse(); };
        inner.addEventListener('mouseenter', play);
        inner.addEventListener('mouseleave', rev);
        var trigger = inner.closest('[data-link-trigger]');
        if (trigger) { trigger.addEventListener('mouseenter', play); trigger.addEventListener('mouseleave', rev); }
      });
    }

    /* -- 掃描 footer 內的 data-reveal（原 initElementsReveal 的 footer 子集） -- */
    function initElementsReveal(scope) {
      // 先統一還原所有 [data-reveal] 的可見性（含作為 trigger 用的 data-reveal="w" 群組容器；
      // 原站 CSS 對 [data-reveal] 一律 visibility:hidden，但 w 容器不會被動畫設為 visible）
      gsap.set(scope.querySelectorAll('[data-reveal]'), { visibility: 'visible' });
      scope.querySelectorAll('[data-reveal="text"]').forEach(function (el) {
        gsap.set(el, { visibility: 'visible' });
        ScrollTrigger.create({ trigger: el, start: 'top bottom', once: true, onEnter: function () { animateTextReveal(el, 'reveal', .1); } });
        animateTextReveal(el, 'initial');
      });
      var clipMap = { 'clip-down': 'top-down', 'clip-left': 'left-right', 'clip-right': 'right-left', 'clip-top': 'down-top' };
      Object.keys(clipMap).forEach(function (key) {
        scope.querySelectorAll('[data-reveal="' + key + '"]').forEach(function (el) {
          gsap.set(el, { visibility: 'visible' });
          animateClipReveal(el, clipMap[key], 'initial');
          ScrollTrigger.create({ trigger: el, start: 'top bottom', once: true, onEnter: function () { animateClipReveal(el, clipMap[key], 'reveal', .1); } });
        });
      });
      scope.querySelectorAll('[data-reveal="div"]').forEach(function (el) {
        var trig = el.closest('[data-reveal="w"]');
        gsap.set(el, { visibility: 'visible' });
        ScrollTrigger.create({ trigger: trig || el, start: 'top bottom', once: true, onEnter: function () { animateDivReveal(el, 'reveal', .1); } });
        animateDivReveal(el, 'initial');
      });
    }

    // 等字型載入後再 SplitText 分行（避免字型未就緒造成行高量測錯誤 / 警示）；
    // 逾時 3s 保險啟動，避免字型載入異常時內容永久隱藏。
    whenFontsReady(function () {
      initElementsReveal(scope);
      initLinks(scope);
      if (ScrollTrigger.refresh) ScrollTrigger.refresh();
    });
  }

  /* 等 document.fonts.ready（含保險逾時） */
  function whenFontsReady(cb) {
    var done = false;
    var run = function () { if (done) return; done = true; cb(); };
    try {
      if (document.fonts && document.fonts.ready && document.fonts.ready.then) {
        document.fonts.ready.then(run);
      }
    } catch (e) { /* ignore */ }
    setTimeout(run, 3000);
  }

  /* ====================== bootstrap ====================== */
  function boot() {
    initFooterTime(root);
    initFooterLogo(root);
    initClockHandRing(root);
    initGsap(root);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();

