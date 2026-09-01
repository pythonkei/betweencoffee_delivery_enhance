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
   依賴：GSAP（base.html 全域載入 3.12.5，defer → DOMContentLoaded 前就緒）。
   註：GSAP 為 defer，本檔（body 尾同步）執行時可能未載入 →
   需在 DOMContentLoaded 後才檢查 gsap 並啟動動畫。
   ============================================================ */
(function () {
  'use strict';

  function init() {
    var inner = document.querySelector('.reviewsInner');
    if (!inner || !window.gsap) return;
    var half = inner.scrollWidth / 2;
    if (!half) return;
    gsap.to('.reviewsInner', {
      repeat: -1,
      x: -half,
      duration: half / 80,
      ease: 'none',
      immediateRender: true,
      startAt: { x: 0 }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
