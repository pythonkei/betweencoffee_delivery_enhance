/* ============================================================================
   Between Coffee — bc-coffee-title.js
   ----------------------------------------------------------------------------
   [用途] /coffee_menu/ 首屏 banner 的「COFFEE」巨型字（移植 und-ny.com/about/
          首屏 .pin-spacer ＋ 捲動時逐字往上跑掉）。
          本檔做三件事：
            ① 拆字（原站的 .init-anim 進場已於 2026-11-18 移除，見下方 [拆字]）
            ② 托住（pin）：捲動時給 __pin 反向 transform（見 CSS 檔頭 [5]）
            ③ 出場（scroll-out）：捲到一定高度後，每個字各自往上滾出畫面

   [拆字] 原始文案留在 h1 內（沒有 JS 時就是完整一行字），JS 讀出文字後換成
            <span class="bc-coffee-title__char"><span class="bc-coffee-title__char-inner">C</span></span>
          內外兩層＝原站的雙層 .char：外層原本負責「進場」位移，內層負責「出場」
          位移（本檔依 scrollY 直接寫 transform、不帶 transition）。
          ⚠ 2026-11-18 使用者指示「title_bg_img_01.svg 與 COFFEE 文字移除初始時的
            從下到上的動畫效果」⇒ 外層進場（.16em 位移／transition／60ms from edges
            的 stagger 延遲）全部取消，外層現在只是出場位移的容器。拆字仍保留，
            因為「出場」是逐字各自往上滾掉、需要逐字節點。詳見 css 檔頭 [4]。
            · h1 設 aria-label="COFFEE"（讀屏讀原文），內層 span 全 aria-hidden

   [托住] 不使用 GSAP pin 的原因見 CSS 檔頭 [5]。公式：
             holdMax = banner 高度 ＋ 字高（＝托住總距離）
             d = clamp(頁面捲動量 scrollY, 0, holdMax)
             __pin.style.transform = translate3d(0, +d, 0)   ← 正號
          頁面往上跑了 d px，字就往下補 d px ⇒ 字停在 viewport 同一個位置
          （＝頁首時的位置，桌面約 171px）。d 到上限後 transform 固定不動 ⇒ 字
          改成隨頁面往上、與托住時完全連續，沒有跳動。
          ※ 托住距離＝banner 高度＋字高（桌機 858px，對應原站實測 1050px／字高
            510px）：字在 banner 底邊離開後仍會在商品區上方托住一段，商品從字
            後面滑過（＝原站的 .pin z-index:10 效果）。
          ※ 為什麼用 scrollY 而不是 -bannerRect.top：本頁 banner 頂端在 y=100
            （導覽列的佔位），用 rect 起算 d 會慢 100px，字早在 y=71 就被
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
          位移量只取「剛好讓整組字離開 viewport 頂端」的距離（桌機 ≈569、手機
          ≈320），不是固定的 banner 高度 —— 取太大（例如 858）字會在托住還沒
          結束就全部噴掉，節奏會比原站快一倍。
          ※ 位移掛在內層 __char-inner（沒有 transition），所以捲動時是 1:1 連動，
            不會被外層進場的 .95s transition 拖慢。
          ※ 捲回頂端時 p 回到 0，位移清除，字回到原位（可重播）。

   [裝飾] 背景插畫（title_bg_img_01.svg，標記 data-bc-coffee-title-bg）吃同一套
          互動：
            進場 = 已取消（2026-11-18 與字同步移除，見上）；插畫載入即定位，
                   不再有 .bc-coffee-title-bg--anim／.is-ready 這兩個 class。
            托住＋出場 = 同一支 JS 直接寫 inline transform
                   translate3d(0, hold' ＋ y, 0)
                   · hold' = 插畫在 __pin 之外時才等於 hold（＝托住距離）；
                     在 __pin 之內時為 0 —— 見下方 ⚠
                   · y 與「插畫對齊的那個字」相同 ⇒ 一路保持對齊（預設第 0 個字
                     ＝C，因為插畫就是以 C 為中心對位；可用根的
                     data-bc-ct-bg-char="1" 改成跟第 2 個字一起走）
            用 `translate`（進場）＋ `transform`（捲動）兩條屬性相加，所以插畫
            不需要像字那樣拆內外兩層。
            ⚠ 托住位移只能算一次（2026-11-18 修正）：插畫搬進
              .bc-coffee-title__stage（＝__pin 內）之後，① 寫在 __pin 上的
              translate3d 已經把整組（含插畫）一起托住；若這裡再加一次 hold，
              插畫會比字多滑一段（捲動時看起來像「互動反轉」）。
              故以 pin.contains(bg) 判斷：在 __pin 內 ⇒ 只補出場位移 y；
              插畫若搬回 __pin 外（banner 內其他位置）⇒ 由本檔補回 hold，
              行為與搬動前相同。
            ⚠ 不要改成在 CSS 給插畫 `transform` 起點位移：JS 的 inline transform
              會整組覆蓋，進場就消失。`.noise_animation` 自己的
              transform: translate3d(0,0,0)（animate-custom.css:186）會被 inline
              蓋掉，不影響。

   [kicker] 左上角「( Line Up )」小標（2026-11-17 使用者指示，仿 index.html 的
          .section-title--left (About)）：外觀與展開動畫全在 CSS（bc-coffee-title.css
          [H]，載入即播一次，不需要 JS）。本檔只負責「出場」：
            它在 __pin 內 ⇒ 已隨 ① 被托住，這裡只要補 ② 的位移，
            沿用第 0 個字（＝最左邊的 C、最外側最早出發）的 local／y
            ⇒ 字的 C 往上飛時，小標也跟著一起離開畫面，不會單獨留在托住的字上。
          ⚠ 位移寫在 `transform`，CSS 的位置用 `translate` 屬性（兩條屬性相加）
            ⇒ 不會互相覆蓋（跟 [裝飾] 同一招）。

   [效能] 捲動用 requestAnimationFrame 節流，且值沒變就不寫 style；幾何
          （banner 高度／字高）只在 init 與 resize 量測，不在捲動中讀 offsetHeight。

   [安全性] 沒有 JS／腳本被阻擋：不拆字、不托住、不出場，h1 靜態置中在 banner，
          版面與動畫終態相同。
          prefers-reduced-motion: reduce：整支跳過（不拆字、不監聽捲動）。
   ============================================================================ */
(function () {
  "use strict";

  // 出場：起點＝托住距離的 30%（原站約 27%）
  var EXIT_START = 0.3;
  // 出場：中央字先走、邊緣字最晚，最多落後 28% 的出場區間（原站約 190px）
  var EXIT_SPREAD = 0.28;
  // 裝飾層（banner 內背景插畫）的標記，見檔頭 [裝飾]
  var BG_SELECTOR = "[data-bc-coffee-title-bg]";

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

      word.appendChild(outer);
      chars.push(outer);
    }
    return chars;
  }

  function init(root) {
    var word = root.querySelector(".bc-coffee-title__word");
    var pin = root.querySelector(".bc-coffee-title__pin");
    var kicker = root.querySelector(".bc-coffee-title__kicker");
    var banner = root.closest ? root.closest(".subpage-banner-h500") : null;
    if (!word || !pin || !banner) return;

    if (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      return; // 見檔頭 [安全性]
    }

    /* ---- ① 拆字（只為出場：進場已於 2026-11-18 移除，見檔頭 [拆字]） ---- */
    var chars = splitChars(word);

    /* ---- ①b 裝飾層：進場已於 2026-11-18 移除 ⇒ 這裡只取節點，交給下方
       ②b／③ 做出場位移（不再加 .bc-coffee-title-bg--anim／.is-ready）。 ---- */
    var bgs = banner.querySelectorAll(BG_SELECTOR);

    /* ---- ② 出場：每字的起始偏移（中央 0 → 邊緣最大） ---- */
    var count = chars.length;
    var mid = (count - 1) / 2;
    var offsets = [];
    for (var i = 0; i < count; i++) {
      offsets.push(mid > 0 ? (Math.abs(i - mid) / mid) * EXIT_SPREAD : 0);
    }

    /* ---- ②b 裝飾層跟哪一個字一起出場（預設第 0 個＝C，見檔頭 [裝飾]） ---- */
    var bgCount = bgs.length;
    var bgOffset = 0;
    if (bgCount && count) {
      var bgChar = parseInt(root.getAttribute("data-bc-ct-bg-char") || "0", 10);
      if (isNaN(bgChar) || bgChar < 0 || bgChar > count - 1) bgChar = 0;
      bgOffset = offsets[bgChar];
    }

    /* ---- ②c 裝飾層是否在 __pin 內（2026-11-18 插畫搬進 __stage 之後） ----
       在 __pin 內 ⇒ 托住位移已由 ① 寫在 __pin 上（整組一起被托住），本檔不可
       再加一次 hold，否則插畫會比字多滑一段（看起來像互動反轉）；
       在 __pin 外 ⇒ 由本檔補 hold。見檔頭 [裝飾] 的 ⚠。 */
    var bgInPin = [];
    for (var bq = 0; bq < bgCount; bq++) bgInPin.push(pin.contains(bgs[bq]));

    /* ---- ③ 幾何：只在 init／resize 量測（見檔頭 [效能]） ---- */
    var geo = { holdMax: 0, start: 0, span: 0, lift: 0 };
    var lastHold = -1;
    var lastP = -1;
    var lastBg = [];  // 每個裝飾層上一次寫入的位移（逐元素，見檔頭 [裝飾]）

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
      lastBg = [];
      for (var r = 0; r < bgCount; r++) lastBg.push(null);
    }

    var ticking = false;

    function update() {
      ticking = false;

      var scroll = Math.max(window.scrollY, 0);

      /* ① 托住：頁面往上跑了 d px，字就往下補 d px（正號，見檔頭 [托住]） */
      var hold = Math.min(scroll, geo.holdMax);
      var holdChanged = hold !== lastHold;
      if (holdChanged) {
        lastHold = hold;
        if (hold > 0) {
          pin.style.transform = "translate3d(0, " + hold + "px, 0)";
        } else if (pin.style.transform) {
          pin.style.transform = "";
        }
      }

      /* ② 出場：每個字各自往上滾出（見檔頭 [出場]） */
      var p = geo.span > 0 ? clamp01((scroll - geo.start) / geo.span) : 0;
      var pChanged = p !== lastP;

      if (pChanged) {
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

        /* ④ 左上角 kicker（見檔頭 [kicker]）：跟第 0 個字（C）一起出場。
              它在 __pin 內，托住已由 ① 負責 ⇒ 這裡只補出場位移；
              local 直接取最外側那個字的值，不再另外算一次。 */
        if (kicker && count) {
          var kLocal = clamp01((p - offsets[0]) / (1 - EXIT_SPREAD));
          var kY = geo.lift * easeInOut(kLocal);

          if (kY < -0.05) {
            kicker.style.transform = "translate3d(0, " + kY.toFixed(2) + "px, 0)";
          } else if (kicker.style.transform) {
            kicker.style.transform = "";
          }
        }
      }

      /* ③ 裝飾層：出場位移 ＋（只有在 __pin 之外才需要的）托住位移，兩者相加
            寫在同一個 transform（見檔頭 [裝飾]）；hold 或 p 任一變了就要重算 */
      if (bgCount && (holdChanged || pChanged)) {
        var bgLocal = clamp01((p - bgOffset) / (1 - EXIT_SPREAD));
        var bgY = geo.lift * easeInOut(bgLocal);

        for (var b = 0; b < bgCount; b++) {
          /* 在 __pin 內 ⇒ 托住已由 ① 的 pin transform 帶著走，再加一次會雙倍 */
          var bgTotal = (bgInPin[b] ? 0 : hold) + bgY;

          if (lastBg[b] != null && Math.abs(bgTotal - lastBg[b]) <= 0.01) continue;
          lastBg[b] = bgTotal;

          var bgTransform =
            Math.abs(bgTotal) < 0.05
              ? ""
              : "translate3d(0, " + bgTotal.toFixed(2) + "px, 0)";

          if (bgs[b].style.transform !== bgTransform) {
            bgs[b].style.transform = bgTransform;
          }
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
