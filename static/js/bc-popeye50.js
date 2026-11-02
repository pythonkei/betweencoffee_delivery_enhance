/* ============================================================
   bc-popeye50.js — popeyemagazine.jp/50interviews/ 首屏動畫移植（about.html 第一屏）
   2026-11-02 建立（使用者指示：把該站最上方的動畫 1:1 搬到 about 頁最上方）

   來源：https://popeyemagazine.jp/wp-content/themes/popeyemagazine-v4/
         dist/special/50interviews/script.js（1,251 行、vanilla、零外部依賴）

   保留（動畫參數完全不改，逐值照抄）
     INTRO_CONFIG 時間軸（600／200／3000／300／1200／600／520／1000／600／560／180）
     年份 rolling ＋ 細線伸出／抹除 ＋ 年份滑到角落的排版切換
     轉輪物理：AUTO_SPEED 0.05deg/frame、FRICTION 0.92、IDLE_DELAY 1200ms、
               MIN_VEL 0.001、wheel 事件 WHEEL_K 0.25、pointer 拖曳慣性
     圓周權重 buildAngles／spacingWeight、行動端 fitMobileWordSize
   移除
     🎉 彩帶（CELEBRATION_CONFIG／confetti／balloon）、ABOUT／INDEX 面板、
     人像燈箱（modal）—— 使用者只要視覺 hero
   改寫（不動動畫行為）
     1. document.body.classList → 模組 root（.bc-popeye50）的 class，不污染 <body>
     2. 尺寸一律取 .cw-stage 實際 rect（原站讀 window.innerWidth/Height）
     3. 資料來源 <script id="bc-popeye50-data" type="application/json">
        （Django json_script；資料由 About view 以 CoffeeItem 組出）
     4. 年份區間讀 data-year-start / data-year-end（預設 2020→2026）
     5. 捲出視窗時暫停 rAF（本頁下方還有很長內容，避免長駐耗電）
     6. prefers-reduced-motion：開場直接到終態、轉輪不自動旋轉
   ============================================================ */
(function () {
  'use strict';

  // 開場時間軸（毫秒）。年份由 HTML 的 data-year-start / data-year-end 提供。
  var INTRO_CONFIG = {
    years: { start: 2020, end: 2026 },
    timing: {
      initialFade: 600,
      initialHold: 200,
      travel: 3000,
      endHold: 300,
      erase: 1200,
      leftYearFade: 600,
      yearMove: 520,
      backgroundFade: 1000,
      wheelFade: 600,
      logoDelayAfterWheel: 0,
      logoFade: 560,
      titleDelayAfterLogo: 180,
      titleFade: 560
    },
    easing: 'easeInOutCubic'
  };

  var INTRO_EASING = {
    linear: function (t) { return t; },
    easeInOutSine: function (t) { return -(Math.cos(Math.PI * t) - 1) / 2; },
    easeOutCubic: function (t) { return 1 - Math.pow(1 - t, 3); },
    easeInOutCubic: function (t) {
      return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
  };

  // 字輪最少圈位數：商品筆數少時重複排列，避免圓周過鬆（原站約 11 筆）。
  var WHEEL_MIN_ITEMS = 10;
  var WHEEL_MAX_ITEMS = 24;

  function init() {
    var root = document.querySelector('.bc-popeye50');
    if (!root) return;

    var stage = root.querySelector('.cw-stage');
    var wheel = root.querySelector('.cw-wheel');
    var loader = root.querySelector('.cw-loader');
    var yearEl = root.querySelector('.cw-loader-moving-year');
    var startYearEl = root.querySelector('.cw-loader-start-year');
    var lineFill = root.querySelector('.cw-loader-line-fill');
    var titleEl = root.querySelector('.cw-title-sub');
    var emptyEl = root.querySelector('.cw-empty');
    var dataEl = document.getElementById('bc-popeye50-data');

    // 缺節點（例如資料未輸出）→ 直接顯示終態，不讓 loader 蓋住畫面
    if (!stage || !wheel || !loader || !yearEl || !startYearEl || !lineFill || !titleEl || !dataEl) {
      root.classList.remove('is-loading');
      root.classList.add('is-ready');
      if (loader) loader.classList.add('is-complete');
      if (titleEl) titleEl.classList.add('is-visible');
      return;
    }

    var imgEl = stage.querySelector('.cw-center-img');
    var nameEl = stage.querySelector('.cw-center-name');
    var centerWebpSource = stage.querySelector('.cw-center-source-webp');
    if (!imgEl || !nameEl) return;

    var reduceMotion = false;
    if (window.matchMedia) {
      reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    // 年份區間（可於模板用 data-year-start / data-year-end 覆寫）
    var yearStartAttr = parseInt(root.getAttribute('data-year-start'), 10);
    var yearEndAttr = parseInt(root.getAttribute('data-year-end'), 10);
    INTRO_CONFIG.years.start = isFinite(yearStartAttr) ? yearStartAttr : INTRO_CONFIG.years.start;
    INTRO_CONFIG.years.end = isFinite(yearEndAttr) ? yearEndAttr : INTRO_CONFIG.years.end;

    // ---------------- 資料 ----------------
    var items = [];
    try {
      var parsed = JSON.parse(dataEl.textContent || '[]');
      if (!Array.isArray(parsed)) throw new Error('bc-popeye50-data is not an array');
      items = parsed.filter(function (it) {
        return it && typeof it.word === 'string' && it.word.length > 0;
      });
    } catch (e) {
      console.warn('[bc-popeye50] invalid JSON', e);
      items = [];
    }

    // 圈位：不足 WHEEL_MIN_ITEMS 筆時重複排列補滿（只影響圓周密度，不改資料）
    var wheelItems = items.slice();
    while (wheelItems.length && wheelItems.length < WHEEL_MIN_ITEMS) {
      wheelItems = wheelItems.concat(items);
    }
    if (wheelItems.length > WHEEL_MAX_ITEMS) {
      wheelItems = wheelItems.slice(0, WHEEL_MAX_ITEMS);
    }

    function imageUrl(it) {
      return it && typeof it.image === 'string' ? it.image : '';
    }

    function setPictureImage(img, sourceEl, it, altText) {
      var src = imageUrl(it);
      if (src) {
        img.src = src;
        img.alt = altText || '';
      } else {
        if (sourceEl) sourceEl.removeAttribute('srcset');
        img.removeAttribute('src');
        img.alt = '';
      }
    }

    function showEmptyState() {
      loader.classList.add('is-complete');
      root.classList.remove('is-loading');
      root.classList.add('is-ready');
      titleEl.classList.add('is-visible');
      stage.classList.add('is-empty');
      var center = stage.querySelector('.cw-center');
      var hitarea = stage.querySelector('.cw-wheel-hitarea');
      if (center) center.hidden = true;
      if (hitarea) hitarea.hidden = true;
      wheel.hidden = true;
      if (emptyEl) emptyEl.hidden = false;
    }

    if (wheelItems.length === 0) {
      showEmptyState();
      return;
    }

    // ---------------- 圓周角度（權重演算法與原站相同） ----------------
    var N = wheelItems.length;
    var START_ANGLE = -90;
    var CURRENT_ANGLE = 0;

    function spacingWeight(it, i) {
      var len = it.word.length;
      var lengthWeight = 1 + Math.max(-0.14, Math.min(0.28, (len - 5) * 0.045));
      var rhythm = [0.04, -0.06, 0.08, -0.03, 0.05, -0.04, 0.02][i % 7];
      return Math.max(0.72, lengthWeight + rhythm);
    }

    function buildAngles(list) {
      var weights = list.map(spacingWeight);
      var total = weights.reduce(function (sum, value) { return sum + value; }, 0);
      var scale = 360 / total;
      var cursor = START_ANGLE;
      return weights.map(function (weight) {
        var angle = cursor;
        cursor += weight * scale;
        return angle;
      });
    }

    function angleDelta(a, b) {
      var d = (a - b) % 360;
      if (d > 180) d -= 360;
      if (d < -180) d += 360;
      return d;
    }

    var angles = buildAngles(wheelItems);
    var wordEls = [];

    var frag = document.createDocumentFragment();
    wheelItems.forEach(function (it, i) {
      var span = document.createElement('span');
      span.className = 'cw-word';
      span.style.setProperty('--angle', angles[i].toFixed(3) + 'deg');
      span.textContent = it.word;
      wordEls.push(span);
      frag.appendChild(span);
    });
    wheel.appendChild(frag);

    wheelItems.forEach(function (it) {
      var preloadSrc = imageUrl(it);
      if (preloadSrc) {
        var im = new Image();
        im.decoding = 'async';
        im.src = preloadSrc;
      }
    });

    // ---------------- 尺寸換算 ----------------
    function rootRemSize() {
      return parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
    }

    function toRem(value) {
      return value / rootRemSize();
    }

    function remValue(value) {
      return toRem(value).toFixed(4).replace(/\.?0+$/, '') + 'rem';
    }

    function remToViewportValue(value) {
      return value * rootRemSize();
    }

    // 原站讀 window.innerWidth/Height；本站模組是頁面中的一個區塊 → 讀 stage 實測尺寸
    function stageSize() {
      var r = stage.getBoundingClientRect();
      return {
        width: r.width || window.innerWidth || document.documentElement.clientWidth,
        height: r.height || window.innerHeight || document.documentElement.clientHeight
      };
    }

    var finalYearsAffectWheel = false;
    var finalYearsUseBottom = false;
    var finalYearsBottomReserve = 0;

    function baseWheelSize(width, height) {
      return Math.max(remToViewportValue(7.5), Math.min(width, height) * 0.92);
    }

    function angleGapAt(index) {
      var previous = index === 0 ? angles[N - 1] - 360 : angles[index - 1];
      var next = index === N - 1 ? angles[0] + 360 : angles[index + 1];
      return Math.max(1, Math.min(angles[index] - previous, next - angles[index]));
    }

    function fitMobileWordSize(width, height, wheelSize) {
      var target = Math.max(10, Math.min(13, Math.min(width, height) * 0.031));
      var minReadable = 8;
      var radius = wheelSize / 2;
      var fitted = target;

      stage.style.setProperty('--cw-word-size', target.toFixed(2) + 'px');

      wordEls.forEach(function (el, index) {
        var wordWidth = el.offsetWidth || ((wheelItems[index].word || '').length * target * 0.58);
        var sampleRadius = Math.max(radius * 0.48, radius - wordWidth * 0.62);
        var gapRad = angleGapAt(index) * Math.PI / 180;
        var allowed = sampleRadius * gapRad * 0.78;
        if (Number.isFinite(allowed) && allowed > 0) fitted = Math.min(fitted, allowed);
      });

      return Math.max(minReadable, Math.min(target, fitted));
    }

    // ---------------- 開場（loader 時間軸；參數與原站相同） ----------------
    function runIntro() {
      var intro = INTRO_CONFIG;
      var timing = intro.timing;
      var ease = INTRO_EASING[intro.easing] || INTRO_EASING.easeInOutCubic;
      loader.style.setProperty('--cw-loader-bg-fade', timing.backgroundFade + 'ms');
      loader.style.setProperty('--cw-loader-year-fade', timing.initialFade + 'ms');
      titleEl.style.setProperty('--cw-title-sub-fade', timing.titleFade + 'ms');
      stage.style.setProperty('--cw-stage-fade', timing.wheelFade + 'ms');

      function wait(ms) {
        return new Promise(function (resolve) { window.setTimeout(resolve, ms); });
      }

      function animate(duration, onFrame, easing) {
        return new Promise(function (resolve) {
          var startAt = performance.now();

          function tick(now) {
            var raw = Math.min(1, (now - startAt) / duration);
            var eased = easing ? easing(raw) : raw;
            onFrame(eased, raw);
            if (raw < 1) {
              requestAnimationFrame(tick);
              return;
            }
            resolve();
          }

          requestAnimationFrame(tick);
        });
      }

      var finalYearLayoutEnabled = false;
      var finalYearResizeBound = false;
      var finalYearLayoutFrame = 0;
      var movingYearX = '0%';
      var yearY = '-50%';

      function finalYearTop(useBottom) {
        return useBottom ? 'calc(100% - var(--cw-loader-year-bottom-offset, 1rem))' : '50%';
      }

      function applyYearTransforms(useBottom) {
        yearY = useBottom ? '-100%' : '-50%';
        var top = finalYearTop(useBottom);
        startYearEl.style.top = top;
        yearEl.style.top = top;
        startYearEl.style.transform = 'translateY(' + yearY + ')';
        yearEl.style.transform = 'translate(' + movingYearX + ', ' + yearY + ')';
      }

      function finalYearBottomReserve() {
        var labelHeight = Math.max(startYearEl.offsetHeight || 0, yearEl.offsetHeight || 0);
        return labelHeight + remToViewportValue(2);
      }

      function shouldUseBottomFinalYears() {
        var size = stageSize();
        var wheelSize = baseWheelSize(size.width, size.height);
        var sideSpace = Math.max(0, (size.width - wheelSize) / 2);
        var sideGap = remToViewportValue(1);
        var startWidth = startYearEl.offsetWidth || 0;
        var endWidth = yearEl.offsetWidth || 0;
        return sideSpace < Math.max(startWidth, endWidth) + sideGap;
      }

      function syncFinalYearLayout(animated) {
        if (!finalYearLayoutEnabled) return 0;

        var useBottom = shouldUseBottomFinalYears();
        var changed = finalYearsUseBottom !== useBottom;
        finalYearsUseBottom = useBottom;
        finalYearsAffectWheel = useBottom;
        finalYearsBottomReserve = useBottom ? finalYearBottomReserve() : 0;

        if (animated && !reduceMotion) {
          loader.style.setProperty('--cw-loader-year-position-dur', timing.yearMove + 'ms');
          loader.classList.add('is-year-layout-animated');
          void loader.offsetWidth;
        } else {
          loader.style.setProperty('--cw-loader-year-position-dur', '0ms');
          loader.classList.remove('is-year-layout-animated');
        }

        if (useBottom) {
          loader.classList.add('is-years-bottom');
        } else {
          loader.classList.remove('is-years-bottom');
        }
        applyYearTransforms(useBottom);
        applySize();
        return changed && useBottom && animated && !reduceMotion ? timing.yearMove : 0;
      }

      function scheduleFinalYearLayout() {
        if (!finalYearLayoutEnabled) return;
        if (finalYearLayoutFrame) cancelAnimationFrame(finalYearLayoutFrame);
        finalYearLayoutFrame = requestAnimationFrame(function () {
          finalYearLayoutFrame = 0;
          syncFinalYearLayout(true);
        });
      }

      function bindFinalYearResize() {
        if (finalYearResizeBound) return;
        finalYearResizeBound = true;
        window.addEventListener('resize', scheduleFinalYearLayout);
        if (window.visualViewport && typeof window.visualViewport.addEventListener === 'function') {
          window.visualViewport.addEventListener('resize', scheduleFinalYearLayout);
        }
      }

      function enableFinalYearLayout(animated) {
        finalYearLayoutEnabled = true;
        bindFinalYearResize();
        return syncFinalYearLayout(animated);
      }

      function getLineWidthToYear() {
        var loaderRect = loader.getBoundingClientRect();
        var yearRect = yearEl.getBoundingClientRect();
        return Math.max(0, Math.min(loaderRect.width, yearRect.left - loaderRect.left));
      }

      function setProgress(progress) {
        var p = Math.max(0, Math.min(1, progress));
        var year = Math.round(intro.years.start + (intro.years.end - intro.years.start) * p);
        yearEl.textContent = String(year);
        yearEl.style.left = (p * 100).toFixed(3) + '%';
        movingYearX = (-p * 100).toFixed(3) + '%';
        yearEl.style.transform = 'translate(' + movingYearX + ', ' + yearY + ')';
        lineFill.style.width = remValue(getLineWidthToYear());
        lineFill.style.clipPath = 'inset(0 0 0 0)';
      }

      function revealEndState() {
        root.classList.remove('is-loading');
        root.classList.add('is-ready');
        loader.classList.add('is-complete');
        titleEl.classList.add('is-visible');
      }

      function showFinalState() {
        startYearEl.textContent = String(intro.years.start);
        startYearEl.classList.add('is-visible');
        yearEl.classList.add('is-visible');
        yearEl.textContent = String(intro.years.end);
        yearEl.style.left = '100%';
        movingYearX = '-100%';
        yearEl.style.transform = 'translate(' + movingYearX + ', ' + yearY + ')';
        lineFill.style.width = remValue(getLineWidthToYear());
        lineFill.style.clipPath = 'inset(0 0 0 100%)';
        enableFinalYearLayout(false);
        revealEndState();
      }

      async function play() {
        startYearEl.textContent = String(intro.years.start);
        yearEl.textContent = String(intro.years.start);
        yearEl.style.left = '0';
        movingYearX = '0%';
        applyYearTransforms(false);
        lineFill.style.width = '0';
        lineFill.style.clipPath = 'inset(0 0 0 0)';

        yearEl.classList.add('is-visible');
        await wait(timing.initialFade + timing.initialHold);
        await animate(timing.travel, setProgress, ease);
        await wait(timing.endHold);

        lineFill.style.width = remValue(getLineWidthToYear());
        await animate(timing.erase, function (progress) {
          lineFill.style.clipPath = 'inset(0 0 0 ' + (progress * 100).toFixed(3) + '%)';
        }, ease);

        loader.style.setProperty('--cw-loader-year-fade', timing.leftYearFade + 'ms');
        startYearEl.classList.add('is-visible');
        await wait(timing.leftYearFade);
        var finalYearMoveWait = enableFinalYearLayout(true);
        if (finalYearMoveWait > 0) {
          await wait(finalYearMoveWait);
        }
        revealEndState();
        await wait(Math.max(timing.wheelFade, timing.backgroundFade) + timing.logoDelayAfterWheel);
        await wait(timing.titleDelayAfterLogo);
        titleEl.classList.add('is-visible');
      }

      async function playReduced() {
        loader.style.setProperty('--cw-loader-year-fade', '0ms');
        startYearEl.textContent = String(intro.years.start);
        yearEl.textContent = String(intro.years.start);
        yearEl.style.left = '0';
        movingYearX = '0%';
        applyYearTransforms(false);
        lineFill.style.width = '0';
        lineFill.style.clipPath = 'inset(0 0 0 0)';

        yearEl.classList.add('is-visible');
        await wait(Math.min(timing.initialFade + timing.initialHold, 700));

        yearEl.textContent = String(intro.years.end);
        yearEl.style.left = '100%';
        movingYearX = '-100%';
        applyYearTransforms(false);
        lineFill.style.width = remValue(getLineWidthToYear());
        lineFill.style.clipPath = 'inset(0 0 0 100%)';
        startYearEl.classList.add('is-visible');
        await wait(300);

        enableFinalYearLayout(false);
        revealEndState();
        await wait(Math.min(timing.backgroundFade, 400));
        titleEl.classList.add('is-visible');
      }

      var introPlayer = reduceMotion ? playReduced : play;
      introPlayer().catch(function (e) {
        console.warn('[bc-popeye50] intro failed', e);
        showFinalState();
      });

      // 保險：若時間軸因任何原因卡住（例如分頁被節流），15 秒後直接落到終態
      window.setTimeout(function () {
        if (!root.classList.contains('is-ready')) showFinalState();
      }, 15000);
    }

    // ---------------- 尺寸套用 ----------------
    function applySize() {
      var size = stageSize();
      var w = size.width;
      var h = size.height;
      var minSize = remToViewportValue(7.5);
      var s = baseWheelSize(w, h);
      if (finalYearsAffectWheel && finalYearsUseBottom) {
        var maxWheelBottom = h - finalYearsBottomReserve;
        var maxSizeFromBottom = (maxWheelBottom - h / 2) * 2;
        s = Math.max(minSize, Math.min(s, maxSizeFromBottom));
      }
      stage.style.setProperty('--cw-size', remValue(s));
      stage.style.setProperty('--cw-radius', remValue(s / 2));
      if (w <= 767) {
        stage.style.setProperty('--cw-word-size', fitMobileWordSize(w, h, s).toFixed(2) + 'px');
      } else {
        stage.style.removeProperty('--cw-word-size');
      }
    }
    applySize();
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(applySize).observe(stage);
    } else {
      window.addEventListener('resize', applySize);
    }
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(applySize).catch(function () {});
    }

    // ---------------- 轉輪物理（數值與原站相同） ----------------
    var AUTO_SPEED = 0.05;
    var FRICTION = 0.92;
    var IDLE_DELAY = 1200;
    var MIN_VEL = 0.001;
    var WHEEL_K = 0.25;

    var rotation = 0;
    var velocity = 0;
    var lastInteract = -Infinity;
    var rafId = 0;
    var currentIdx = -1;

    function getCurrentIndex() {
      var target = CURRENT_ANGLE - rotation;
      var bestIdx = 0;
      var bestDelta = Infinity;
      for (var i = 0; i < N; i++) {
        var d = Math.abs(angleDelta(angles[i], target));
        if (d < bestDelta) {
          bestDelta = d;
          bestIdx = i;
        }
      }
      return bestIdx;
    }

    function updateCurrent() {
      var idx = getCurrentIndex();
      if (idx === currentIdx) return;
      if (currentIdx >= 0 && wordEls[currentIdx]) {
        wordEls[currentIdx].classList.remove('is-current');
      }
      currentIdx = idx;
      if (wordEls[currentIdx]) {
        wordEls[currentIdx].classList.add('is-current');
      }
      var it = wheelItems[idx];
      nameEl.textContent = it.name || it.word || '';
      if (imageUrl(it)) {
        imgEl.classList.remove('is-loaded');
        imgEl.onload = function () { imgEl.classList.add('is-loaded'); };
        setPictureImage(imgEl, centerWebpSource, it, it.name || it.word || '');
      } else {
        if (centerWebpSource) centerWebpSource.removeAttribute('srcset');
        imgEl.removeAttribute('src');
        imgEl.alt = '';
        imgEl.classList.remove('is-loaded');
      }
    }

    function frame() {
      var now = performance.now();
      var idle = (now - lastInteract) > IDLE_DELAY;
      if (idle && Math.abs(velocity) < MIN_VEL) {
        rotation += AUTO_SPEED;
        velocity = 0;
      } else {
        rotation += velocity;
        velocity *= FRICTION;
        if (Math.abs(velocity) < MIN_VEL) velocity = 0;
      }
      wheel.style.setProperty('--cw-rotation', rotation.toFixed(3) + 'deg');
      updateCurrent();
      rafId = requestAnimationFrame(frame);
    }

    // reduceMotion：不自動旋轉、不跑 rAF（畫面維持靜止）
    function start() {
      if (reduceMotion) return;
      if (!rafId) rafId = requestAnimationFrame(frame);
    }
    function stop() {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = 0;
      }
    }

    // ---------------- 互動：滾輪 / 拖曳（同原站，含慣性） ----------------
    function isInWheelCircle(clientX, clientY) {
      var r = stage.getBoundingClientRect();
      var cx = r.left + r.width / 2;
      var cy = r.top + r.height / 2;
      var dx = clientX - cx;
      var dy = clientY - cy;
      var size = Math.max(r.width, r.height);
      return (dx * dx + dy * dy) <= Math.pow(size / 2, 2);
    }

    stage.addEventListener('wheel', function (e) {
      // 原站在字輪圓周內一律 preventDefault（該站只有這一屏）。本頁下方還有很長的內容，
      // 若照抄會讓滑鼠停在圓圈上時整頁無法捲動 → 只有「水平」滾動才轉字輪
      // （Shift＋滾輪 / 觸控板橫向），垂直滾動交還瀏覽器捲頁。
      if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;
      if (!isInWheelCircle(e.clientX, e.clientY)) return;
      e.preventDefault();
      var d = e.deltaX * WHEEL_K;
      rotation += d;
      velocity = d * 0.4;
      lastInteract = performance.now();
    }, { passive: false });

    var dragging = false;
    var lastAngle = 0;
    var dragPointerId = null;

    function pointerAngle(clientX, clientY) {
      var r = stage.getBoundingClientRect();
      var cx = r.left + r.width / 2;
      var cy = r.top + r.height / 2;
      return Math.atan2(clientY - cy, clientX - cx) * 180 / Math.PI;
    }

    stage.addEventListener('pointerdown', function (e) {
      if (!isInWheelCircle(e.clientX, e.clientY)) return;
      dragging = true;
      dragPointerId = e.pointerId;
      try { stage.setPointerCapture(e.pointerId); } catch (_) {}
      stage.classList.add('is-dragging');
      lastAngle = pointerAngle(e.clientX, e.clientY);
      velocity = 0;
      lastInteract = performance.now();
    });

    stage.addEventListener('pointermove', function (e) {
      if (!dragging || e.pointerId !== dragPointerId) return;
      var a = pointerAngle(e.clientX, e.clientY);
      var d = a - lastAngle;
      if (d > 180) d -= 360;
      if (d < -180) d += 360;
      rotation += d;
      velocity = d * 0.6;
      lastAngle = a;
      lastInteract = performance.now();
    });

    function endDrag(e) {
      if (dragPointerId !== null && e && e.pointerId !== dragPointerId) return;
      dragging = false;
      dragPointerId = null;
      stage.classList.remove('is-dragging');
    }
    stage.addEventListener('pointerup', endDrag);
    stage.addEventListener('pointercancel', endDrag);
    stage.addEventListener('pointerleave', endDrag);

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });

    // 捲出視窗時暫停（本頁下方還有很長內容，避免長駐 rAF 吃 CPU）
    var inView = true;
    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          inView = entry.isIntersecting;
          if (inView) start(); else stop();
        });
      }, { threshold: 0 }).observe(root);
    }

    // ---------------- 啟動 ----------------
    updateCurrent();
    start();
    runIntro();

    window.addEventListener('pagehide', stop);
    window.addEventListener('pageshow', function () {
      if (inView) start();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
