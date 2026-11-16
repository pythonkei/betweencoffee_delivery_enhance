/* ============================================================================
   Between Coffee — bc-coffee-title.js
   ----------------------------------------------------------------------------
   [用途] /coffee_menu/ 首屏 banner 的「COFFEE」巨型字（移植 und-ny.com/about/
          首屏 .pin-spacer ＋ .init-anim 拆字進場 ＋ 捲動時逐字往上跑掉）。
          本檔做三件事：
            ① 拆字 ＋ 觸發進場（對應原站 data-animation-type="chars"）
            ② 托住（pin）：捲動時給 __pin 反向 transform（見 CSS 檔頭 [5]）
            ③ 出場（scroll-out）：捲到一定高度後，每個字各自往上滾出畫面

   [拆字] 原始文案留在 h1 內（沒有 JS 時就是完整一行字），JS 讀出文字後換成
            <span class="bc-coffee-title__char"><span class="bc-coffee-title__char-inner">C</span></span>
          內外兩層＝原站的雙層 .char：外層負責「進場」位移（CSS transition），
          內層負責「出場」位移（本檔依 scrollY 直接寫 transform、不帶 transition），
          兩者互不干擾（inline transform 也不會壓過 .is-ready 的樣式表規則）。
            · h1 設 aria-label="COFFEE"（讀屏讀原文），內層 span 全 aria-hidden
            · 每字 inline transition-delay = 距首尾的距離 × 60ms
              （＝原站 stagger 0.06s from edges：首尾先起、中央字最後）

   [托住] 不使用 GSAP pin 的原因見 CSS 檔頭 [5]。公式：
             holdMax = banner 高度 ＋ 字高（＝托住總距離）
             d = clamp(頁面捲動量 scrollY, 0, holdMax)
             __pin.style.transform = translate3d(0, +d, 0)   ← 正號
          頁面往上跑了 d px，字就往下補 d px ⇒ 字停在 viewport 同一個位置
          （＝頁首時的位置，桌面約 126px）。d 到上限後 transform 固定不動 ⇒ 字
          改成隨頁面往上、與托住時完全連續，沒有跳動。
          ※ 托住距離＝banner 高度＋字高（桌機 948px，對應原站實測 1050px／字高
            510px）：字在 banner 底邊離開後仍會在商品區上方托住一段，商品從字
            後面滑過（＝原站的 .pin z-index:10 效果）。
          ※ 為什麼用 scrollY 而不是 -bannerRect.top：本頁 banner 頂端在 y=100
            （導覽列的佔位），用 rect 起算 d 會慢 100px，字早在 y=26 就被
            導覽列壓住。

   [出場] 原站實測（1440×900，2026-11-16）：托住期間外層 .char 不動，內層 .char
          隨捲動各自往上位移 —— 中央字先走、邊緣字落後約 190px 捲動距離，全部
          收在 y = -896px（≈ 1.54em），曲線是「起步慢→中段衝出→收尾」的
          power3.inOut 型。本頁照同樣邏輯以 scrollY 直接算：
             start   = holdMax × 0.30
             span    = holdMax − start
             p       = clamp01((scrollY − start) / span)
             off_i   = |i − 中心| / 中心 × 0.28      ← 中央字先走、邊緣字最晚
             local_i = clamp01((p − off_i) / 0.72)
             y_i     = lift × easeInOutCubic(local_i)
                     lift = −(banner 在頁面的 y ＋ 字在 banner 內的位移 ＋ 字高 ＋ 40)
          位移量只取「剛好讓整組字離開 viewport 頂端」的距離（桌機 ≈614、手機
          ≈380），不是固定的 banner 高度 —— 取太大（例如 948）字會在托住還沒
          結束就全部噴掉，節奏會比原站快一倍。
          ※ 位移掛在內層 __char-inner（沒有 transition），所以捲動時是 1:1 連動，
            不會被外層進場的 .95s transition 拖慢。
          ※ 捲回頂端時 p 回到 0，位移清除，字回到原位（可重播）。

   [效能] 捲動用 requestAnimationFrame 節流，且值沒變就不寫 style；幾何
          （banner 高度／字高）只在 init 與 resize 量測，不在捲動中讀 offsetHeight。

   [安全性] 沒有 JS／腳本被阻擋：不拆字、不托住、不出場，h1 靜態置中在 banner，
          版面與動畫終態相同。
          prefers-reduced-motion: reduce：整支跳過（不拆字、不監聽捲動）。
   ============================================================================ */
(function () {
  "use strict";

  // 進場：每字延遲 60ms（對應原站 stagger 0.06s from edges）
  var STAGGER_MS = 60;
  // 出場：起點＝托住距離的 30%（原站約 27%）
  var EXIT_START = 0.3;
  // 出場：中央字先走、邊緣字最晚，最多落後 28% 的出場區間（原站約 190px）
  var EXIT_SPREAD = 0.28;

  function clamp01(value) {
    return value < 0 ? 0 : value > 1 ? 1 : value;
  }

  // power3.inOut（≈ 原站實測曲線）：起步慢 → 中段衝出 → 收尾
  function easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function splitChars(word) {
    var text = word.textContent.replace(/\s+/g, " ").trim();
    if (!text) return [];

    var chars = [];
    var total = text.length;

    word.setAttribute("aria-label", text);
    word.textContent = "";

    for (var i = 0; i < total; i++) {
      var ch = text.charAt(i);

      if (ch === " ") {
        var space = document.createElement("span");
        space.className = "bc-coffee-title__space";
        space.setAttribute("aria-hidden", "true");
        space.textContent = "\u00a0";
        word.appendChild(space);
        continue;
      }

      // 外層：進場位移（CSS transition）／內層：出場位移（JS 直寫 transform）
      var outer = document.createElement("span");
      outer.className = "bc-coffee-title__char";
      outer.setAttribute("aria-hidden", "true");

      var inner = document.createElement("span");
      inner.className = "bc-coffee-title__char-inner";
      inner.textContent = ch;

      outer.appendChild(inner);

      // from edges：離首或尾越近越早（中央字最後）；起點位移由 CSS 給
      // （見 static/css/bc-coffee-title.css [D]：不可寫 inline transform）
      var edge = Math.min(i, total - 1 - i);
      outer.style.transitionDelay = edge * STAGGER_MS + "ms";

      word.appendChild(outer);
      chars.push(outer);
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

    /* ---- ② 出場：每字的起始偏移（中央 0 → 邊緣最大） ---- */
    var count = chars.length;
    var mid = (count - 1) / 2;
    var offsets = [];
    for (var i = 0; i < count; i++) {
      offsets.push(mid > 0 ? (Math.abs(i - mid) / mid) * EXIT_SPREAD : 0);
    }

    /* ---- ③ 幾何：只在 init／resize 量測（見檔頭 [效能]） ---- */
    var geo = { holdMax: 0, start: 0, span: 0, lift: 0 };
    var lastHold = -1;
    var lastP = -1;

    function measure() {
      var bannerH = banner.offsetHeight;
      var wordH = word.offsetHeight;
      // banner 在「頁面座標」的位置（不受捲動／pin 影響）
      var bannerTop = banner.getBoundingClientRect().top + (window.pageYOffset || 0);

      geo.holdMax = bannerH + wordH; // ＝托住總距離（見檔頭 [托住]）
      geo.start = geo.holdMax * EXIT_START;
      geo.span = geo.holdMax - geo.start;

      // 出場位移量：把字推離 viewport 頂端即可（＋40px 保險）。
      // 字托住時的 viewport y ＝ bannerTop ＋ 字在 banner 內的位移（offsetTop），
      // 故整組字要「完全看不到」需要走 bannerTop ＋ offsetTop ＋ 字高。
      // 桌機 100+26+448+40 ＝ 614、手機約 380（見檔頭 [6]）。
      geo.lift = -(bannerTop + word.offsetTop + wordH + 40);

      // 幾何變了 ⇒ 下一次 update 一定要重算
      lastHold = -1;
      lastP = -1;
    }

    var ticking = false;

    function update() {
      ticking = false;

      var scroll = Math.max(window.scrollY, 0);

      /* ① 托住：頁面往上跑了 d px，字就往下補 d px（正號，見檔頭 [托住]） */
      var hold = Math.min(scroll, geo.holdMax);
      if (hold !== lastHold) {
        lastHold = hold;
        if (hold > 0) {
          pin.style.transform = "translate3d(0, " + hold + "px, 0)";
        } else if (pin.style.transform) {
          pin.style.transform = "";
        }
      }

      /* ② 出場：每個字各自往上滾出（見檔頭 [出場]） */
      var p = geo.span > 0 ? clamp01((scroll - geo.start) / geo.span) : 0;
      if (p === lastP) return;
      lastP = p;

      for (var i = 0; i < count; i++) {
        var inner = chars[i].firstElementChild;
        if (!inner) continue;

        var local = clamp01((p - offsets[i]) / (1 - EXIT_SPREAD));
        var y = geo.lift * easeInOut(local);

        if (y < -0.05) {
          inner.style.transform = "translate3d(0, " + y.toFixed(2) + "px, 0)";
        } else if (inner.style.transform) {
          inner.style.transform = "";
        }
      }
    }

    function request() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }

    window.addEventListener("scroll", request, { passive: true });
    window.addEventListener("resize", function () {
      measure();
      request();
    });

    measure();
    update();
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
