/* ============================================================
   bc-coffee-comment.js — 咖啡詳情頁照片上的 staff-comment 氣泡輪播
   2026-09-11 建立
   ------------------------------------------------------------------
   完全複製 about 頁 bc-sake-mv.js（原站 sake-shirakiku.jp common.js 的
   mvStaff）的邏輯，改 scoped 至 .bc-coffee-photo .bc-coffee-comment：
     1. 取所有 .staff-comment
     2. 隨機打亂順序（sort(() => Math.random() - Math.random())）
     3. 每 3 秒：清除全部 is-show → 加上目前這個的 is-show（互斥輪替）
   is-show 由 bc-coffee-comment.css 觸發氣泡（.img）與頭部圖章（::after）
   的彈出動畫。僅 /coffee/10/ 有這個區塊，其餘頁面直接 return。
   ============================================================ */
(function () {
  "use strict";

  function initCoffeeComment() {
    var root = document.querySelector(".bc-coffee-photo .bc-coffee-comment");
    if (!root) return;

    var els = Array.from(root.getElementsByClassName("staff-comment"));
    if (els.length < 2) return;

    // 與原站相同：隨機打亂順序後輪流切換 is-show
    var shuffled = els.slice().sort(function () {
      return Math.random() - Math.random();
    });
    var t = 0;

    // 初始狀態：先讓第一個顯示（避免 3 秒空窗）
    els.forEach(function (el) {
      el.classList.remove("is-show");
    });
    shuffled[0].classList.add("is-show");

    setInterval(function () {
      els.forEach(function (el) {
        el.classList.remove("is-show");
      });
      shuffled[t].classList.add("is-show");
      t = (t + 1) % shuffled.length;
    }, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(initCoffeeComment, 100);
    });
  } else {
    setTimeout(initCoffeeComment, 100);
  }
})();
