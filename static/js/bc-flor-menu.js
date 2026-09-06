/* Between Coffee — florporto 產品模組捲動動畫（bc-flor-menu）
   2026-09-06 移植。純 vanilla，無第三方依賴。
   行為（與原站一致）：
   A. 商品圖 crossfade：
      - 每個商品圖欄（.aspect-[4/5] 內多層 .absolute.inset-0）同一時間僅一層顯示，
        其餘 opacity-0（CSS transition duration-1000 = 1s 交叉淡化）
      - 顯示第幾層由「圖欄在視口中的捲動進度」決定：
        p=0（進入前）→ 第 0 層；p=1（完全通過）→ 最後一層；中間依 p 線性切層
      - 首層初始即顯示（HTML 未帶 opacity-0），JS 僅接管切換
   B. 右側時間軸指示器（.bc-flor-rail）：
      - 僅在模組進入/離開視口附近時顯示（原站為 scroll 觸發 mount/unmount）
      - active step = 最後一個「頂部已通過視口中線」的群組（.group-section）
      - 點擊 / Enter / Space → 平滑捲動至對應群組
   用法：容器帶 .bc-flor-menu。 */
(function () {
  'use strict';
  var root = document.querySelector('.bc-flor-menu');
  if (!root) return;

  /* ========== A. 商品圖層 crossfade ========== */
  // 依父元素收集圖層群組
  var groups = new Map();
  var layersSel = root.querySelectorAll('.absolute.inset-0');
  Array.prototype.forEach.call(layersSel, function (layer) {
    var parent = layer.parentElement;
    if (!groups.has(parent)) groups.set(parent, []);
    groups.get(parent).push(layer);
  });
  var frames = [];
  groups.forEach(function (layers, el) {
    frames.push({ el: el, layers: layers, cur: -1 });
  });

  function setFrameActive(frame, idx) {
    if (idx === frame.cur) return;
    frame.cur = idx;
    for (var i = 0; i < frame.layers.length; i++) {
      frame.layers[i].classList.toggle('opacity-0', i !== idx);
    }
  }

  /* ========== B. 右側時間軸指示器 ========== */
  var rail = root.querySelector('.bc-flor-rail');
  var groupEls = root.querySelectorAll('.group-section');
  var stepEls = rail ? rail.querySelectorAll('.step-indicator') : [];
  var curStep = -1;

  function setStep(idx) {
    if (idx === curStep) return;
    curStep = idx;
    Array.prototype.forEach.call(stepEls, function (st, i) {
      var on = i === idx;
      st.classList.toggle('active', on);
      if (on) st.setAttribute('aria-current', 'true');
      else st.removeAttribute('aria-current');
    });
  }

  function update() {
    var vh = window.innerHeight || document.documentElement.clientHeight;

    // --- A. crossfade ---
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      var r = f.el.getBoundingClientRect();
      var n = f.layers.length;
      if (r.top >= vh || r.bottom <= 0) continue; // 不在視口附近不動
      var p = (vh - r.top) / (vh + r.height);   // 0=剛進 1=剛出
      p = Math.max(0, Math.min(1, p));
      var idx = Math.min(n - 1, Math.floor(p * n));
      setFrameActive(f, idx);
    }

    // --- B. rail show/hide + active step ---
    if (!rail || !groupEls.length) return;
    var first = groupEls[0].getBoundingClientRect();
    var last = groupEls[groupEls.length - 1].getBoundingClientRect();
    // 顯示區間（等效原站 mount/unmount）：第一群組已進入視口上半，直到最後群組完全捲離視口上方
    var show = first.top < vh * 0.4 && last.bottom > 0;
    rail.classList.toggle('is-hidden', !show);
    if (!show) return;

    // active = 最後一個頂部已通過「視口中線」的群組（依原站切換點觀察）
    var line = window.pageYOffset + vh / 2;
    var active = 0;
    for (var g = 0; g < groupEls.length; g++) {
      var top = groupEls[g].getBoundingClientRect().top + window.pageYOffset;
      if (top <= line) active = g;
    }
    setStep(active);
  }

  var raf = 0;
  function onScroll() {
    if (raf) return;
    raf = requestAnimationFrame(function () { raf = 0; update(); });
  }

  function goToStep(idx) {
    if (!groupEls[idx]) return;
    var r = groupEls[idx].getBoundingClientRect();
    var y = r.top + window.pageYOffset + r.height / 2 - window.innerHeight / 2;
    window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
  }

  function bindRail() {
    if (!rail) return;
    Array.prototype.forEach.call(stepEls, function (st) {
      st.addEventListener('click', function () {
        goToStep(Number(st.getAttribute('data-step-index')) || 0);
      });
      st.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          goToStep(Number(st.getAttribute('data-step-index')) || 0);
        }
      });
    });
  }

  function start() {
    update();
    bindRail();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    // 圖載入後高度可能變化，重新量測
    var imgs = root.querySelectorAll('img');
    Array.prototype.forEach.call(imgs, function (img) {
      if (img.complete) return;
      img.addEventListener('load', onScroll, { once: true });
    });
  }

  if (document.readyState === 'complete') start();
  else window.addEventListener('load', start);
})();
