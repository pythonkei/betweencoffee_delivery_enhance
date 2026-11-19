/* ============================================================
   bc-coffee-dirs.js — /coffee/<id>/ 首屏「上一杯／下一杯」帶的捲動淡出
   2026-11-19 建立（bc-coffee-dirs.css 第七版搭配檔）
   ------------------------------------------------------------------
   [用途] 使用者指示：「如果捲動出 .ftco-subpage-section
          ftco-section-single-product bc-section-with-bg-text 這部分，
          新增淡出動畫；捲動入則反向淡入。」
          該帶是 position:fixed（見 CSS 檔頭 ①），本身不會隨頁面捲走，
          所以「捲出」是用**商品主區是否還在視窗內**判定：

            · 主區完全離開視窗  → 對 .bc-coffee-dirs 加 .is-out
                                  （CSS：opacity 1→0，.45s；visibility
                                   於淡出結束才 hidden）
            · 主區回到視窗內    → 移除 .is-out（反向淡入）

   [為什麼用 isIntersecting 就夠]
          主區（照片＋名稱＋選項）比視窗高，幾乎整個捲動過程都與視窗
          有交集，只有真正捲過頭（捲到頁尾 next-link 面板）或捲回上方
          hero 時才失效 ⇒ 不需要 threshold／rootMargin 微調。

   [退化]  沒有 IntersectionObserver → scroll + rAF 手算 rect
          （等價條件：rect.bottom <= 0 || rect.top >= 視窗高）。
   [無 JS] 帶子永遠顯示（＝第六版行為）。
   [範圍]  /bean/<id>/ 雖有同名主區 class 但沒有這條帶 → 找不到
          .bc-coffee-dirs 就直接 return，不會註冊觀察器。
   [動態偏好] prefers-reduced-motion 由 CSS 關掉過渡，本檔照樣切 class
          （狀態與畫面一致，只是瞬間完成）。
   ============================================================ */
(function () {
  "use strict";

  var BAND_SELECTOR = ".bc-coffee-dirs";
  var SECTION_SELECTOR = ".ftco-subpage-section.ftco-section-single-product";
  var OUT = "is-out";

  var band = document.querySelector(BAND_SELECTOR);
  if (!band) {
    return;
  }

  var section = document.querySelector(SECTION_SELECTOR);
  if (!section) {
    return;
  }

  /* 目前狀態（null＝尚未初始化），避免每次回呼都重寫 class */
  var current = null;

  function setOut(isOut) {
    if (isOut === current) {
      return;
    }
    current = isOut;
    band.classList.toggle(OUT, isOut);
  }

  if ("IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        var last = entries[entries.length - 1];
        setOut(!last.isIntersecting);
      },
      { threshold: 0 }
    );
    observer.observe(section);
    return;
  }

  /* 退化路徑：舊瀏覽器（scroll + rAF，passive 不阻塞捲動） */
  var ticking = false;

  function check() {
    ticking = false;
    var rect = section.getBoundingClientRect();
    var viewportH =
      window.innerHeight || document.documentElement.clientHeight;
    setOut(rect.bottom <= 0 || rect.top >= viewportH);
  }

  function request() {
    if (ticking) {
      return;
    }
    ticking = true;
    window.requestAnimationFrame(check);
  }

  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", request, { passive: true });
  check();
})();
