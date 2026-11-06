/* ============================================================
   bc-sticky-mv.js — About 頁首屏「sticky 影片背景 + 產品照弧形輪播」
   2026-11-03 建立（移植 yurumaru.life 首頁 .page-top__mv__wrap / .sticky-bg）

   來源：yurumaru.life（Shopify 主題）—— sticky 影片由純 CSS 完成（見
         static/css/bc-sticky-mv.css 檔頭），本檔只負責兩件事：
         ① 產品列輪播（原站用 Splide；此處以原生 rAF + CSS transition 重寫，
            不引入 Splide／GSAP → CDN 失效也能運作）
         ② 背景影片控制（2026-11-06 起為多層輪播：可載入多支、依序交叉淡入；進入視口才 play、離開暫停；respects reduced-motion → 見 initVideo）

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

  /* ---------------- 影片層（多層輪播） ----------------
     2026-11-06（使用者指示）：背景影片從「單支」升級為「可載入多支、依序輪播」
     → 機制移植 weekday.co.jp 首頁 .p-hero__videos（原站 JS 反組譯後的行為）：
       · 同時存在最多 MV_MAX 層 <video>：第 0 層＝模板渲染（首屏 poster 就是它），
         第 1 層之後由本檔建立並 append 到 .sticky-bg__bg —— 必須是直接子元素，
         才吃得到 CSS 的「> * { position:absolute; inset:0; object-fit:cover }」。
       · 影片池＝About view 的 views.MV_VIDEOS（json_script "bc-sticky-mv-videos"）：
         第 0 層固定用第一筆（poster 已顯示，避免一載入就換片），第 1 層之後
         每次載入洗牌決定（原站 GLOBAL.methods.util.shuffleArray）。
       · 先只載入前兩層；canplaythrough 後第 0 層淡入（.is-on），之後才可能換片。
       · 當前層播到「距結束 MV_LEAD_S 秒」→ 找下一個「已載入且沒壞掉」的層 →
         加 .is-on（CSS 0.6s 淡入、z-index 3）→ 淡入完成才暫停舊層並歸零 →
         再補載下一個還沒載入的層（原站 a()：每次換片後補一格）。
       · 只有 1 支影片時完全等於舊行為（不建層、不換片、單片 loop）。
     與原站的三處差異（都刻意）：
       ① 原站 z-index 是累加的（1,2,3…），此處固定「最新＝3、其餘＝0」，
          因為黑遮罩 .sticky-bg__bg::before（z-index:10）必須永遠在最上層。
       ② 原站找下一層的 do…while 沒有上限（只剩 1 支載好時會無限迴圈），此處加上限。
       ③ 所有層都保留 loop：下一支還沒載好時不會停在最後一幀（原站靠 ended 歸零）。
     ------------------------------------------------------------------ */
  var MV_LEAD_S = 0.75; /* 原站 i = .75：距結束 0.75s 就開始換片 */
  var MV_FADE_MS = 600; /* 原站 gsap duration = .8 * i = 0.6s（需與 CSS transition 一致） */
  var MV_MAX_ITER = 8; /* 找下一層的防呆上限（層數最多 5） */

  /* 讀 json_script（<script type="application/json">） */
  function readJson(id, fallback) {
    var el = document.getElementById(id);
    if (!el) return fallback;
    try {
      return JSON.parse(el.textContent || el.innerHTML);
    } catch (err) {
      return fallback;
    }
  }

  /* Fisher–Yates（原站 GLOBAL.methods.util.shuffleArray 的等效實作） */
  function shuffle(list) {
    var arr = list.slice();
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr;
  }

  /* 同一支影片（同 webm+mp4 組合）視為重複 → 用來把第 0 層從洗牌池中排除 */
  function itemKey(item) {
    if (!item) return '';
    return (item.webm || '') + '|' + (item.mp4 || '');
  }

  function initVideo(root) {
    var bg = root.querySelector('.sticky-bg__bg');
    var firstEl = bg ? bg.querySelector('.mv-video') : null;
    if (!firstEl) return;

    /* reduced-motion：維持舊行為（不播、停在 poster），也不建立其他層 */
    if (mqReduce.matches) {
      firstEl.removeAttribute('autoplay');
      firstEl.pause();
      return;
    }

    var playlist = readJson('bc-sticky-mv-videos', []);
    var limit = readJson('bc-sticky-mv-max', 5);
    limit = limit > 0 ? Math.floor(limit) : 1;

    var layers = []; /* [{ el, item, loaded, failed, loading }] */
    var current = 0; /* 目前顯示（正在播）的層 */
    var started = false;
    var inView = true;

    function playLayer(layer) {
      if (!layer || !layer.el) return;
      var p = layer.el.play();
      if (p && typeof p.catch === 'function') p.catch(function () {});
    }

    function pauseLayer(layer) {
      if (layer && layer.el && !layer.el.paused) layer.el.pause();
    }

    /* 補載「第一個還沒載入」的層（原站 a()） */
    function loadNextUnloaded() {
      for (var i = 0; i < layers.length; i++) {
        if (!layers[i].loaded && !layers[i].failed && !layers[i].loading) {
          loadLayer(i);
          return;
        }
      }
    }

    /* 把某層的來源掛上去並開始下載。
       手法同原站 initRawVideo：先掛 <source data-src>（不會下載），
       再一次複製成 src 後 video.load()。 */
    function loadLayer(index) {
      var layer = layers[index];
      if (!layer || !layer.item) return;
      layer.loading = true;
      var el = layer.el;
      var formats = [
        ['webm', 'video/webm'],
        ['mp4', 'video/mp4'],
      ];
      for (var f = 0; f < formats.length; f++) {
        var src = layer.item[formats[f][0]];
        if (!src) continue;
        var source = document.createElement('source');
        source.type = formats[f][1];
        source.setAttribute('data-src', src);
        el.appendChild(source);
      }
      if (layer.item.poster) el.setAttribute('poster', layer.item.poster);
      var sources = el.querySelectorAll('source');
      for (var s = 0; s < sources.length; s++) {
        sources[s].setAttribute('src', sources[s].getAttribute('data-src'));
        sources[s].removeAttribute('data-src');
      }
      if (!sources.length) layer.failed = true;
      el.load();
    }

    /* 前兩層就緒才起播（原站 Promise.all → spinner 淡出 → 第 0 層淡入）。
       第 0 層由模板帶 poster + .is-on，所以這裡只負責 play。
       force＝第二層下載失敗時仍要起播（否則整頁背景會永遠停在 poster）。 */
    function maybeStart(force) {
      if (started) return;
      if (!force && layers.length > 1 && !layers[1].loaded) return;
      started = true;
      firstEl.classList.add('is-on');
      if (inView && !document.hidden) playLayer(layers[0]);
    }

    /* 換片：原站 timeupdate 內的 do…while → 找下一個已載入的層 */
    function advance() {
      if (layers.length < 2) return;
      var from = current;
      var next = from;
      var found = false;
      for (var i = 0; i < MV_MAX_ITER; i++) {
        next = next + 1 >= layers.length ? 0 : next + 1;
        if (next === from) break;
        if (layers[next].loaded && !layers[next].failed) {
          found = true;
          break;
        }
      }
      /* 下一層還沒好 → 留在當前層（它保留 loop，畫面不會凍住） */
      if (!found) return;

      current = next;
      layers[next].el.classList.add('is-on');
      playLayer(layers[next]);

      window.setTimeout(function () {
        /* 淡入完成才收掉舊層：原站靠 z-index 覆蓋而不暫停，
           此處順手暫停並歸零，省一個 decoder（畫面完全相同）。 */
        if (layers[current] !== layers[next]) return;
        layers[from].el.classList.remove('is-on');
        pauseLayer(layers[from]);
        try {
          layers[from].el.currentTime = 0;
        } catch (err) {}
      }, MV_FADE_MS);

      loadNextUnloaded();
    }

    function makeLayer(el, item, alreadyLoaded) {
      var layer = {
        el: el,
        item: item,
        loaded: !!alreadyLoaded,
        failed: false,
        loading: false,
      };

      el.addEventListener('canplaythrough', function () {
        layer.loaded = true;
        layer.loading = false;
        maybeStart();
      });

      /* 所有 <source> 都失敗時 video 會發 error → 標記壞層，換片時跳過 */
      el.addEventListener('error', function () {
        if (!layer.loaded) {
          layer.loading = false;
          layer.failed = true;
          maybeStart(true); /* 壞層不要拖住起播 */
        }
      });

      el.addEventListener('timeupdate', function () {
        if (layers[current] !== layer) return; /* 只管當前層 */
        var d = layer.el.duration;
        if (!d || isNaN(d)) return;
        if (d - layer.el.currentTime <= MV_LEAD_S) advance();
      });

      /* 原站：ended 時歸零。此處每層都有 loop，正常走不到；
         留著只是兜底（避免任何情況下停在最後一幀）。 */
      el.addEventListener('ended', function () {
        layer.el.currentTime = 0;
        if (layers[current] === layer && inView && !document.hidden) {
          playLayer(layer);
        }
      });

      layers.push(layer);
      return layer;
    }

    /* 第 0 層＝模板已渲染的那個（來源、poster 都來自 views.MV_VIDEOS[0]） */
    makeLayer(firstEl, playlist.length ? playlist[0] : null, true);

    /* 第 1 層之後：洗牌（排除與第 0 層同片者）後依序建立，總數上限 limit 層 */
    if (playlist.length > 1) {
      var firstKey = itemKey(playlist[0]);
      var pool = [];
      for (var p = 1; p < playlist.length; p++) {
        if (itemKey(playlist[p]) !== firstKey) pool.push(playlist[p]);
      }
      pool = shuffle(pool);
      var extra = Math.min(pool.length, limit - 1);
      for (var c = 0; c < extra; c++) {
        var clone = document.createElement('video');
        clone.className = 'mv-video';
        clone.muted = true;
        clone.defaultMuted = true;
        clone.setAttribute('muted', '');
        clone.setAttribute('playsinline', '');
        clone.setAttribute('aria-hidden', 'true');
        clone.preload = 'none';
        clone.loop = true;
        clone.setAttribute('data-index', String(c + 1));
        bg.appendChild(clone);
        makeLayer(clone, pool[c], false);
      }
      /* 原站只先載前兩支：第 3 支起等每次換片後 loadNextUnloaded() 才補 */
      if (layers.length > 1) loadLayer(1);
    }

    /* 進/出視口（舊行為：進入才播、離開暫停）＋ 分頁切換 */
    if (!('IntersectionObserver' in window)) {
      playLayer(layers[current]);
    } else {
      new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            inView = entry.isIntersecting;
            if (inView) {
              if (started && !document.hidden) playLayer(layers[current]);
            } else {
              pauseLayer(layers[current]);
            }
          });
        },
        { threshold: 0.01 }
      ).observe(root);
    }

    document.addEventListener('visibilitychange', function () {
      if (document.hidden) pauseLayer(layers[current]);
      else if (started) playLayer(layers[current]);
    });

    maybeStart();
  }

  /* ---------------- 產品列輪播 ---------------- */
  function initCarousel(root) {
    var product = root.querySelector('.page-top__mv__product');
    var list = product ? product.querySelector('.mv-product__list') : null;
    if (!product || !list) return;

    /* 產品列在 CSS 預設是 opacity:0（避免 JS 定位前先畫出 -18% 的錯誤位置），
       任何一條「不跑輪播」的退場路徑都必須把它揭露，否則商品會永遠看不到。 */
    function reveal() {
      product.classList.add('is-mv-ready');
    }

    var originals = Array.prototype.slice.call(list.children);
    var n = originals.length;
    if (!n) {
      reveal(); /* 空資料 → CSS 的 .bc-mv-empty 顯示提示 */
      return;
    }

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

    /* 無動畫瞬移（loop 歸位或 resize 重算；需強制 reflow 才不會補間）
       2026-11-04（使用者回報「繞完一圈回到 Coffee 01 後，卡片異常往上抖一下再回原位」
       ／「手動左右滑動時同樣發生」）：
       原本只瞬移 .mv-product__list，slide 的 translateY（-18% / -6% / 0）仍走
       var(--mv-dur) = 1.75s 過渡 → 歸位那一幀新聚焦的那張正從 -73.5px（-18%）
       慢慢爬回 0，看起來就是「歸位後卡片自己往上抖一下」。
       修法：加 .is-jumping 讓 CSS 把 slide／img 的 transition 關掉，在「無過渡」狀態下
       先切換焦點角色、再改 list 位移，強制 reflow 後才移除 → 一幀內換好、畫面完全不變
       （歸位後聚焦的是複製品對應的本尊，視覺完全等價）。 */
    function jump() {
      list.classList.add('is-jumping');
      list.style.transition = 'none';
      updateClasses();
      list.style.transform = 'translate3d(' + translateX() + 'px, 0, 0)';
      void list.offsetWidth;
      list.classList.remove('is-jumping');
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

    /* 桌面滑鼠拖曳：商品卡是 <a>，按住往左右拖會觸發瀏覽器原生 HTML5 drag-and-drop
       → 送出 pointercancel，輪播拖到 30px 就被中斷（實測 dragstart 後只剩 1 次 pointermove）。
       直接擋掉 dragstart（圖片本身也已是 draggable="false"）；觸控不會觸發 dragstart，不受影響。 */
    product.addEventListener('dragstart', function (e) {
      e.preventDefault();
    });

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

    /* ---------------- 啟動 ----------------
       2026-11-04（使用者回報「初始顯示時產品列往下移動」，第二次修）：
       第一次修把 setX(false) + updateClasses() 換成 jump()（先關過渡、一幀內換好狀態），
       但那只能讓「換狀態」本身無動畫 —— 瀏覽器在 JS 執行前就已經把「全部 -18%」
       畫出來了（實測 t≈500ms 已繪製、t≈1383ms 才換狀態，1280px 差 72px），
       所以仍會看到整排往下跳。這次改成：CSS 先把整列 opacity:0，定位完成才 reveal()。 */
    measure();
    pos = OFFSET; /* 從第一張原始 slide 開始（前面那組是複製品） */
    jump();
    reveal();
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

