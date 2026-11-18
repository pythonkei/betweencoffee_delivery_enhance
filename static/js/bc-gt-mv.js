/* ============================================================================
   Between Coffee — bc-gt-mv.js
   ----------------------------------------------------------------------------
   [用途] global-tree 首屏主視覺（圖片 3 條切片 ＋ 文字 3 條切片）的「起播 ＋ 換片」。
          進場動畫全部由 CSS 負責（bc-gt-mv.css），本檔只做兩件事：
          ① 模組進視口（25% 可見）時，把 .is-on 加到第一片 ⇒ 觸發進場動畫
          ② 之後每 5s 把 .is-on 從目前這片搬到下一片 —— 搬 class 會讓該片的
             bc-pa-wipe／bc-pa-slice／bc-pa-image 動畫重新從 0% 開始，
             效果等同原站 Splide 換片時重播 .layeredImage。

   [為什麼要等進視口] 模組位於首頁 who section（第一屏看不到）。若在 markup 就先帶
          .is-on，動畫會在載入時播完，捲到那裡只剩靜態照片。

   [安全性] 沒有 JS／腳本被阻擋時：.is-on／.is-live 都不會出現 ⇒ CSS 讓第一片維持可見
          （`.bc-gtmv__item.-index-1`），文字與照片都停在動畫終態，不會空白、不會破版。
          系統要求減少動態（prefers-reduced-motion: reduce）時：只加 is-on（顯示第一片）
          不換片，且動畫都包在 no-preference 媒體查詢內 ⇒ 完整靜態顯示。
   ============================================================================ */
(function () {
  "use strict";

  var INTERVAL = 5000; // ms（原站 Splide 自動輪播間隔同級）

  function init(root) {
    var items = Array.prototype.slice.call(
      root.querySelectorAll("[data-bc-gtmv-item]")
    );
    if (!items.length) return;

    var reduce =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
    var index = 0;
    var started = false;

    function tick() {
      if (reduce && reduce.matches) return;
      if (document.hidden) return;
      if (items.length < 2) return;

      var prev = items[index];
      index = (index + 1) % items.length;
      var next = items[index];

      if (prev) prev.classList.remove("is-on");
      next.classList.add("is-on");
    }

    function start() {
      if (started) return;
      started = true;
      // .is-live：切換成「只有 is-on 的那片可見」（CSS 端第一片預設可見，供無 JS 時使用）
      root.classList.add("is-live");
      items[index].classList.add("is-on");
      if (reduce && reduce.matches) return; // 靜態完成態：只留 is-on，不播不動畫、不換片
      if (items.length > 1) window.setInterval(tick, INTERVAL);
    }

    // 沒有 IntersectionObserver（極舊瀏覽器）⇒ 直接起播，行為與改版前相同
    if (!("IntersectionObserver" in window)) {
      start();
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          start();
          io.disconnect();
        });
      },
      { threshold: 0.25 }
    );
    io.observe(root);
  }

  function boot() {
    var roots = document.querySelectorAll("[data-bc-gtmv]");
    Array.prototype.forEach.call(roots, init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
