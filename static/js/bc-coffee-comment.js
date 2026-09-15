/* ============================================================
   bc-coffee-comment.js — 咖啡詳情頁照片上的 staff-comment 氣泡輪播
   2026-09-11 建立
   ------------------------------------------------------------------
   完全複製 about 頁 bc-sake-mv.js（原站 sake-shirakiku.jp common.js 的
   mvStaff）的邏輯，改 scoped 至 .bc-coffee-photo .bc-coffee-comment：
     1. 取所有 .staff-comment
     2. 隨機打亂順序（sort(() => Math.random() - Math.random())）
     3. 每 3 秒：切換 is-show（互斥輪替）
        － 進場：加上 is-show → CSS 播放彈出動畫（與原站相同）
        － 退場（2026-09-15 修正）：加 .is-hiding 讓氣泡「在原地縮小消失」，
          300ms 後移除；原寫法只移除 is-show，會讓 rotate / translate 瞬間
          跳回入場起點，看起來像往上跳一下才消失。
   is-show / is-hiding 皆由 bc-coffee-comment.css 驅動氣泡（.img）與頭部圖章
   （::after）。只有填了氣泡文字的咖啡頁才有這個區塊，其餘頁面直接 return。
   ============================================================ */
(function () {
  "use strict";

  function initCoffeeComment() {
    var root = document.querySelector(".bc-coffee-photo .bc-coffee-comment");
    if (!root) return;

    var els = Array.from(root.getElementsByClassName("staff-comment"));
    if (!els.length) return;

    // 2026-09-14：文字改由 CoffeeItem 欄位驅動 → 三顆氣泡可能只填 1~2 顆。
    // 只有 1 顆時不輪播（否則原本的 els.length < 2 直接 return 會讓它永遠不顯示）。
    if (els.length < 2) {
      els[0].classList.add("is-show");
      return;
    }

    // 與原站相同：隨機打亂順序後輪流切換 is-show
    var shuffled = els.slice().sort(function () {
      return Math.random() - Math.random();
    });

    // 初始狀態：先讓第一個顯示（避免 3 秒空窗）
    els.forEach(function (el) {
      el.classList.remove("is-show");
    });
    shuffled[0].classList.add("is-show");

    // 計數器從 1 起算：初始已顯示 shuffled[0]，
    // 若從 0 起算第一次輪替（3 秒後）會再顯示同一個 → 變成停 6 秒才換
    var t = 1;

    // 2026-09-15：退場改為「原地縮小消失」。
    // 收起時先加 .is-hiding（CSS 把 rotate / translate 固定在 0、只縮 scale），
    // 讓氣泡留在原本位置縮小，而不是瞬間跳回入場起點（translate 0 -40px）再縮小；
    // 動畫結束（300ms，與 CSS 一致）後移除 .is-hiding，元素回到入場前的起始狀態。
    var HIDE_MS = 300;

    setInterval(function () {
      els.forEach(function (el) {
        if (el.classList.contains("is-show")) {
          el.classList.add("is-hiding");
          el.classList.remove("is-show");
          window.setTimeout(function () {
            el.classList.remove("is-hiding");
          }, HIDE_MS);
        } else {
          el.classList.remove("is-show", "is-hiding");
        }
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
