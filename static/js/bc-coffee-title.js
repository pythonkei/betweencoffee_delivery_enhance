/* ============================================================================
   Between Coffee — bc-coffee-title.js
   ----------------------------------------------------------------------------
   [用途] /coffee_menu/ 首屏 banner 的「COFFEE」巨型字（移植 und-ny.com/about/
          首屏 ABOUT US 的 .pin-spacer ＋ .init-anim 拆字進場）。本檔做兩件事：
            ① 拆字 ＋ 觸發進場（對應原站 data-animation-type="chars"）
            ② 托住（pin）：捲動時給 __pin 反向 transform（見 CSS 檔頭 [5]）

   [拆字] 原始文案留在 h1 內（沒有 JS 時就是完整一行字），JS 讀出文字後
          換成 <span class="bc-coffee-title__char">，並：
            · h1 設 aria-label="COFFEE"（讀屏讀原文，內層 span 全 aria-hidden）
            · 每個字的起點位移寫在 CSS（[D]），JS 只給 inline transition-delay，
              下一帧加根節點 .is-ready ⇒ 由 CSS 的 transition 收回到 0
              （位移比例見 CSS 檔頭 [4]）
            · 每字 inline transition-delay = 距首尾的距離 × 60ms
              （＝原站 stagger 0.06s from edges：首尾先起、中央字最後）

   [托住] 不使用 GSAP pin 的原因見 CSS 檔頭 [5]。公式：
            d = clamp(頁面捲動量 scrollY, 0, banner 高度)
            __pin.style.transform = translate3d(0, +d, 0)   ← 正號
          頁面往上跑了 d px，字就往下補 d px ⇒ 字停在 viewport 同一個位置
          （＝頁首時的位置，桌面約 126px）。d 到上限（banner 高度：桌機
          500px／手機 82vw）後 transform 固定不動 ⇒ 字改成隨頁面往上、與
          托住時完全連續，沒有跳動。
          ※ 為什麼用 scrollY 而不是 -bannerRect.top：本頁 banner 頂端在 y=100
            （導覽列的佔位），用 rect 起算 d 會慢 100px，字早在 y=26 就被
            導覽列壓住。

   [效能] 捲動只做一次 getBoundingClientRect，並用 requestAnimationFrame
          節流；banner 離開視口（IntersectionObserver，rootMargin 200px）
          後直接 return，不參與其他區塊的捲動。

   [安全性] 沒有 JS／腳本被阻擋：不拆字、不托住，h1 靜態置中在 banner，
          版面與動畫終態相同。
          prefers-reduced-motion: reduce：整支跳過（不拆字、不監聽捲動）。
   ============================================================================ */
(function () {
  "use strict";

  // 進場參數（對應原站：stagger 0.06s from edges）
  var STAGGER_MS = 60;

  function splitChars(word) {
    var text = word.textContent.replace(/\s+/g, " ").trim();
    if (!text) return [];

    var chars = [];
    var total = text.length;

    word.setAttribute("aria-label", text);
    word.textContent = "";

    for (var i = 0; i < total; i++) {
      var ch = text.charAt(i);
      var span = document.createElement("span");
      span.className =
        ch === " " ? "bc-coffee-title__space" : "bc-coffee-title__char";
      span.setAttribute("aria-hidden", "true");
      span.textContent = ch === " " ? "\u00a0" : ch;

      if (ch !== " ") {
        // from edges：離首或尾越近越早（中央字最後）；起點位移由 CSS 給
        // （見 static/css/bc-coffee-title.css [D]：不可寫 inline transform）
        var edge = Math.min(i, total - 1 - i);
        span.style.transitionDelay = edge * STAGGER_MS + "ms";
        chars.push(span);
      }

      word.appendChild(span);
    }
    return chars;
  }

  function init(root) {
    var word = root.querySelector(".bc-coffee-title__word");
    var pin = root.querySelector(".bc-coffee-title__pin");
    var banner = root.closest ? root.closest(".subpage-banner-h500") : null;
    if (!word || !pin || !banner) return;

    if (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return; // 見檔頭 [安全性]
    }

    /* ---- ① 拆字 ＋ 進場 ---- */
    var chars = splitChars(word);
    if (chars.length) {
      // 強制一次樣式計算，確保起點位移已經生效，下一帧的 .is-ready 才會轉場
      void word.offsetWidth;
      requestAnimationFrame(function () {
        root.classList.add("is-ready");
      });
    }

    /* ---- ② 托住（pin）---- */
    var active = false;
    var ticking = false;

    function update() {
      ticking = false;
      if (!active) return;

      // 托住距離 d：上限＝banner 高度（桌機 500／手機 82vw）。
      // 以「頁面捲動量」為基準（不是 banner 的 rect）—— banner 頂端在 y=100，
      // 若用 -bannerRect.top，d 會從捲到 100px 才開始算，字早在 y=26 就被導覽列
      // 壓住；以 scrollY 起算則字停在頁首那個位置（桌面 126px，在 nav 下緣之下）。
      var hold = Math.min(Math.max(window.scrollY, 0), banner.offsetHeight);

      // 頁面往上跑了 d px，字就往下補 d px ⇒ 字停在 viewport 同一位置。
      // 捲過 banner 高度後 d 固定在上限：transform 不再變動 ⇒ 字改成隨頁面
      // 一起往上（與托住時完全連續，不會跳），商品列從字後面滑過。
      if (hold > 0) {
        pin.style.transform = "translate3d(0, " + hold + "px, 0)";
      } else if (pin.style.transform) {
        pin.style.transform = "";
      }
    }

    function request() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }

    // banner 在視口附近才參與捲動計算（banner 在頁首，離開後即停用）
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(
        function (entries) {
          active = entries[0].isIntersecting;
          if (active) request();
        },
        { rootMargin: "200px 0px" }
      ).observe(banner);
    } else {
      active = true;
    }

    window.addEventListener("scroll", request, { passive: true });
    window.addEventListener("resize", request);
    request();
  }

  function boot() {
    var roots = document.querySelectorAll("[data-bc-coffee-title]");
    Array.prototype.forEach.call(roots, init);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
