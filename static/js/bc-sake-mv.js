/* ============================================================
   bc-sake-mv.js — sake-shirakiku.jp/products/vibran
   product-mv 的 staff-comment 輪播動畫（is-show 切換）
   2026-08-31 建立（與原站 common.js 的 mvStaff 一致）

   原站邏輯（common.js）：
     mvStaff:function(){
       let e=Array.from(document.getElementsByClassName("staff-comment"));
       e=e.slice().sort((()=>Math.random()-Math.random()));
       let t=0;
       setInterval((()=>{
         e.forEach((e=>e.classList.remove("is-show"))),
         e[t].classList.add("is-show"),
         t=(t+1)%e.length
       }),3e3)
     }
   本整合 scoped 至 .bc-sake-mv 內，避免影響其他區塊。
   ============================================================ */
(function () {
  "use strict";

  function initMvStaff() {
    var root = document.querySelector(".bc-sake-mv .product-mv");
    if (!root) return;

    var els = Array.from(root.getElementsByClassName("staff-comment"));
    if (els.length < 2) return;

    // 與原站相同：隨機打亂順序後每 3 秒輪流切換 is-show
    var shuffled = els.slice().sort(function () {
      return Math.random() - Math.random();
    });
    var t = 0;

    setInterval(function () {
      els.forEach(function (el) {
        el.classList.remove("is-show");
      });
      shuffled[t].classList.add("is-show");
      t = (t + 1) % shuffled.length;
    }, 3000);
  }

  // 原站於 product.init 中 setTimeout(100) 啟動；此處 DOM ready 後啟動
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(initMvStaff, 100);
    });
  } else {
    setTimeout(initMvStaff, 100);
  }
})();
