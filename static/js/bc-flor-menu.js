/* Between Coffee — florporto 產品模組捲動動畫（bc-flor-menu）
   2026-09-06 移植。純 vanilla，無第三方依賴。
   行為（與原站一致）：
   - 每個商品圖欄（.aspect-[4/5] 內多層 .absolute.inset-0）同一時間僅一層顯示，
     其餘 opacity-0（CSS transition duration-1000 = 1s 交叉淡化）
   - 顯示第幾層由「圖欄在視口中的捲動進度」決定：
     p=0（進入前）→ 第 0 層；p=1（完全通過）→ 最後一層；中間依 p 線性切層
   - 首層初始即顯示（HTML 未帶 opacity-0），JS 僅接管切換
   用法：容器帶 .bc-flor-menu。 */
(function () {
  'use strict';
  var root = document.querySelector('.bc-flor-menu');
  if (!root) return;

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
  if (!frames.length) return;

  function setActive(frame, idx) {
    if (idx === frame.cur) return;
    frame.cur = idx;
    for (var i = 0; i < frame.layers.length; i++) {
      frame.layers[i].classList.toggle('opacity-0', i !== idx);
    }
  }

  function update() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      var r = f.el.getBoundingClientRect();
      var n = f.layers.length;
      if (r.top >= vh || r.bottom <= 0) continue; // 不在視口附近不動
      var p = (vh - r.top) / (vh + r.height);   // 0=剛進 1=剛出
      p = Math.max(0, Math.min(1, p));
      var idx = Math.min(n - 1, Math.floor(p * n));
      setActive(f, idx);
    }
  }

  var raf = 0;
  function onScroll() {
    if (raf) return;
    raf = requestAnimationFrame(function () { raf = 0; update(); });
  }

  function start() {
    update();
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
