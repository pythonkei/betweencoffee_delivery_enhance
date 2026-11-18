/* ============================================================
   bc-reviews.js — special.hakujuji-g.co.jp/waffle/ .reviews 水平跑馬燈動畫
   2026-08-28 整合
   ------------------------------------------------------------------
   完全複製原站 GSAP 跑馬燈邏輯（common.js 內 gsap.to('.reviewsInner')）：
   - x: 0 → -reviewsInner 半寬（內容重複 2 份 → 無縫循環）
   - repeat: -1（無限）
   - ease: 'none'（線性，原站均速）
   - duration = 半寬 / 80（原站 4311.8px ÷ 53.9s ≈ 80px/s 線性速度）
   - immediateRender: true + startAt: { x: 0 }
   2026-09-06：支援水平反向——若 section.bc-reviews-section 帶 data-bc-reviews-reverse
   （首頁 feed 下方複製版），改為從 x:-半寬 向右捲回 x:0（鏡像方向），其餘參數相同。

   2026-11-13：修正「捲到一半跳回第一個 reviewsTarget／部分內文永遠看不到」
   ------------------------------------------------------------------
   原站前提是 .reviewsInner 內容「重複 2 份」，所以 x 只走「半寬」、接縫兩側相同 → 無縫。
   但本站 index.html 的 28 組 .reviewsTarget 是「28 組不同文案」（前後兩半內容不同），
   於是 (a) 捲到 -半寬 時接縫文字與開頭不一致 → 視覺上像「跳回第一組」；
   (b) x 只走半寬 → 最後約 1/4 內容永遠不會進入視窗（內文沒顯示完）。
   改法：啟動前先判斷「前後兩半是否完全相同」——
     · 相同（about.html）→ 照舊以半寬為循環距離。
     · 不同（index.html）→ 先把整份 strip 自我複製一份（28 → 56 組），
       循環距離即等於「一份 strip 寬」→ 接縫內容一致，且每一組都會被捲過。
   另外改為逐個 .reviewsInner 各自建立 tween（原本用 selector 字串，
   多個區塊時會共用第一個的寬度）。

   2026-11-13（b）：字級可變 → 循環距離需重量
   ------------------------------------------------------------------
   同日把內文放大約 10%（bc-reviews.css：桌機 15→16.5px，768/480 斷點同步），
   文字變寬 → scrollWidth 改變。但 tween 的 half/duration 只在啟動時量一次，
   因此 webfont（Noto Serif TC）晚載入、或視窗跨 768/480px 重排後，
   舊 half 會與實際寬度不符 → 接縫又會錯位。
   → 抽出 start()（kill 舊 tween 後依現況重量，並用 progress 保留播放進度），
     在 document.fonts.ready 與 resize（debounce 150ms）後對所有已初始化的
     .reviewsInner 重新量測啟動。速度仍固定 80px/s，duration = half / 80。

   依賴：GSAP（base.html 全域載入 3.12.5，defer → DOMContentLoaded 前就緒）。
   註：GSAP 為 defer，本檔（body 尾同步）執行時可能未載入 →
   需在 DOMContentLoaded 後才檢查 gsap 並啟動動畫。
   ============================================================ */
(function () {
  'use strict';

  // 線性速度（原站 4311.8px ÷ 53.9s ≈ 80px/s）；字級放大只會改變 duration，不改速度
  var PX_PER_SEC = 80;
  var targets = []; // 已初始化的 .reviewsInner（字型載入／跨斷點時重新量測用）

  // 內容是否已「重複 2 份」（前半與後半完全相同）＝原站無縫循環的前提
  function halvesMatch(inner) {
    var kids = inner.children;
    var n = kids.length;
    if (n < 2 || n % 2 !== 0) return false;
    var h = n / 2;
    for (var i = 0; i < h; i++) {
      if (kids[i].innerHTML !== kids[i + h].innerHTML) return false;
    }
    return true;
  }

  // 依「現況寬度」啟動（或重量）單一 .reviewsInner 的 tween。
  // 重量時保留播放進度，避免字型載入完成／視窗跨斷點時畫面跳一下。
  function start(inner) {
    var half = inner.scrollWidth / 2;
    if (!half) return;

    var section = inner.closest('.bc-reviews-section');
    var reverse = !!(section && section.hasAttribute('data-bc-reviews-reverse'));

    var prev = inner._bcReviewsTween;
    var progress = prev ? prev.progress() : 0;
    if (prev) prev.kill();

    inner._bcReviewsTween = gsap.to(inner, {
      repeat: -1,
      x: reverse ? 0 : -half,
      duration: half / PX_PER_SEC,
      ease: 'none',
      immediateRender: true,
      startAt: { x: reverse ? -half : 0 }
    });
    if (progress) inner._bcReviewsTween.progress(progress);
  }

  function refreshAll() {
    targets.forEach(start);
  }

  function init() {
    if (!window.gsap) return;
    targets = [];
    Array.prototype.forEach.call(document.querySelectorAll('.reviewsInner'), function (inner) {
      // 只複製一次（避免重複執行時一直複製內容）
      if (!inner.hasAttribute('data-bc-reviews-ready')) {
        if (!halvesMatch(inner)) {
          // 單一份內容 → 自我複製一份，讓「半寬」= 一份 strip 寬且接縫內容相同
          inner.insertAdjacentHTML('beforeend', inner.innerHTML);
        }
        inner.setAttribute('data-bc-reviews-ready', '');
      }
      targets.push(inner);
      start(inner);
    });

    // 字型晚載入（Noto Serif TC）會改變文字寬度 → 重新量測循環距離
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(refreshAll);
    }
    // 視窗跨 768 / 480px 斷點（字級與膠囊尺寸改變）→ 同上
    var rt;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(refreshAll, 150);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
