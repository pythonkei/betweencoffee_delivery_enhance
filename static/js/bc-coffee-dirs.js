/* ============================================================
   bc-coffee-dirs.js — /coffee/<id>/ 首屏「上一杯／下一杯」帶的捲動淡出
   2026-11-19 建立（bc-coffee-dirs.css 第七版搭配檔）
   2026-11-19 第九版：淡出條件改為「主區已填不滿視窗」（見下）
   ------------------------------------------------------------------
   [用途] 使用者指示：「如果捲動出 .ftco-subpage-section
          ftco-section-single-product bc-section-with-bg-text 這部分，
          新增淡出動畫；捲動入則反向淡入。」
          該帶是 position:fixed（見 CSS 檔頭 ①），本身不會隨頁面捲走，
          所以「捲出」用**商品主區在視窗中的可見範圍**判定。

   [第九版為什麼改條件（使用者指示「修正捲動淡出淡入，不包含頁腳
    footer section」）]
          第七版用 IntersectionObserver，條件是 `isIntersecting === false`
          （主區完全離開視窗才淡出）。但主區很高（1440×900 實測
          y190–1492），頁腳（y1610 起）與 next-link 面板（y2248 起）
          都被算進「主區還看得到」的範圍 ⇒ 帶子一路掛在頁腳上，
          直到頁尾（scrollY 1698）才淡出。
          第九版改成：

            · 主區下緣已升進視窗底之內（`rect.bottom <= 視窗高`）
              ＝ 主區填不滿一個視窗 ⇒ 已捲出主區 → 加 .is-out（淡出）
            · 主區下緣回到視窗底之下       ⇒ 捲回主區 → 移除（反向淡入）

          1440×900 實測：scrollY 592（捲到數量／加入購物車）就淡出，
          頁腳出現（scrollY 810）時帶子已淡完；頁腳因此不被包含。

   [為什麼不用 IntersectionObserver]
          要比較的是「section.bottom 與視窗高」的大小關係，IO 的
          threshold／rootMargin 只能表達交集比例，無法表達這條界線；
          故改為 scroll + rAF（passive，不阻塞捲動）。

   [退化]  主區比視窗矮時（罕見：超高視窗／內容很短的單品）退回第七版
          條件（`rect.bottom <= 0 || rect.top >= 視窗高`＝完全捲出才淡出），
          否則一捲動就整組消失。
   [無 JS] 帶子永遠顯示（＝第六版行為）。
   [範圍]  /bean/<id>/ 雖有同名主區 class 但沒有這條帶 → 找不到
          .bc-coffee-dirs 就直接 return，不會註冊捲動監聽。
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

  function viewportHeight() {
    return window.innerHeight || document.documentElement.clientHeight;
  }

  var ticking = false;

  function check() {
    ticking = false;
    var rect = section.getBoundingClientRect();
    var viewportH = viewportHeight();
    var isOut;

    if (rect.height <= viewportH) {
      /* 主區比視窗矮：維持「完全捲出才淡出」（避免一捲動就消失） */
      isOut = rect.bottom <= 0 || rect.top >= viewportH;
    } else {
      /* 第九版：主區下緣進入視窗（填不滿視窗）＝已捲出主區；頁腳不列入 */
      isOut = rect.bottom <= viewportH;
    }

    setOut(isOut);
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
  /* 圖片／字型載入完成後主區高度會變，再校正一次 */
  window.addEventListener("load", request, { passive: true });
  check();
})();
