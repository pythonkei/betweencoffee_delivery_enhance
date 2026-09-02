/* ============================================================
   bc-fujiya-photo.js — www.fujiya-peko.co.jp/cakebrand/
   #photo_area 鎖定頁面動畫（完整複製原站 bin/page/top/js/script.min.js
   photo_area 部分，scoped 至 .bc-fujiya-photo）

   動畫構成（與原站一致）：
     1. #photo_slide 高度 = windowH − #photo_ttl 高度（+80 PC），由 resize 設定
     2. GSAP ScrollTrigger × 3：
        trigger .photo_line1/2/3、start "top 100%"、end "bottom 0%"（SP +=0.7H）
        scrub → onUpdate 依 progress 設定 inner 的 mask-position（windowH→0）
        與 mask-size（progress>.85 時 100%→100+t%（PC t=85 / SP t=200））
     3. jQuery Waypoint × 6：
        photo_line1/2/3 於 offset=.79*(windowH−copyH) 切換 showPhoto/closePhoto、
        於 offset="10%" 切換 .photo_slide_item 的 .open（picture.b 淡出）
     4. showPhoto/closePhoto：標語 copy 淡入淡出 + 逐字上滑
        （span 依序 22ms 間隔、CSS transition 0.133s cubic-bezier(.61,1,.88,1)）
     5. bc-other-members（原 .mark 更改，2026-09-01）：
        置 title 層一份、文字 z-index 置圓形正中央；跟隨「第一組文字」——
        copy1 顯示時顯示（showPhoto(1)，每次重新進入重播手繪動畫）；
        向下捲 copy1→2→3 常駐（showPhoto/closePhoto 2/3 不影響）；
        向上回捲到 copy1 消失（closePhoto(1)）時一起消失（.hide）

   依賴：jQuery（base.html body 尾）、Waypoints 4.0.0（base.html 已載入）、
   GSAP 3.12.5 + ScrollTrigger（base.html head defer）。
   transform 設定用 gsap.set（inline style，CSS transition 驅動過渡，
   效果與原站 jQuery.css({y}) + GSAP 自動整合一致）。

   時序：本檔於 body 尾同步執行，早於 head defer 的 GSAP → 所有初始化
   必須在 DOMContentLoaded 後（boot）才檢查 gsap / ScrollTrigger。
   ============================================================ */
(function () {
  "use strict";

  if (typeof jQuery === "undefined" || typeof Waypoint === "undefined") return;

  var $ = jQuery;

  function boot() {
    // GSAP/ScrollTrigger 於 base.html head 以 defer 載入，執行順序在
    // body 尾同步 script 之後 → 必須在 DOMContentLoaded 後檢查
    if (typeof gsap === "undefined" || typeof ScrollTrigger === "undefined") return;

    var $root = $(".bc-fujiya-photo");
    if (!$root.length) return;

    var copyTimers = {};

    function spview() {
      return window.innerWidth <= 767;
    }

    /* ---- 取得 bc-other-members（title 層一份） ---- */
    function otherMembers() {
      return $root.find("#photo_ttl > .bc-other-members");
    }

    /* ---- 觸發 bc-other-members 動畫（重新進入 copy1 時重播） ---- */
    function playOtherMembers() {
      var $om = otherMembers();
      if (!$om.length) return;
      $om.removeClass("hide");
      if ($om.hasClass("show")) {
        // 移除 .show → reflow → 重新加回 → CSS animation 重播
        $om.removeClass("show");
        void $om[0].offsetWidth;
      }
      $om.addClass("show");
    }
    /* ---- 隱藏 bc-other-members（copy1 文字消失時一起消失） ---- */
    function hideOtherMembers() {
      otherMembers().addClass("hide");
    }

    /* ---- showPhoto：切換標語 copy（複製原站 Manager.showPhoto） ---- */
    function showPhoto(n) {
      if (copyTimers[n]) { clearTimeout(copyTimers[n]); copyTimers[n] = null; }
      // 全部 copy 淡出、目標 copy 淡入
      $root.find("#photo_ttl .copy").css({ opacity: 0 });
      $root.find("#photo_copy" + n).css({ opacity: 1 });
      // 2026-09-01：bc-other-members 跟隨第一組文字——copy1 顯示時
      // 顯示並重播手繪動畫（向下捲 copy1→2→3 常駐，copy2/3 不影響）
      if (n === 1) {
        playOtherMembers();
      }
      // 逐字上滑：span 依序 22ms 間隔 y:0
      var spans = $root.find("#photo_copy" + n + " .t > span");
      spans.each(function (i) {
        gsap.set(spans[i], { y: "102%" });
        copyTimers[n] = setTimeout(function () {
          gsap.set(spans[i], { y: 0 });
        }, 22 * (i + 1));
      });
    }

    /* ---- closePhoto：關閉標語 copy（複製原站 Manager.closePhoto） ---- */
    function closePhoto(n) {
      if (copyTimers[n]) { clearTimeout(copyTimers[n]); copyTimers[n] = null; }
      $root.find(".photo_slide_item" + n).removeClass("open");
      // 2026-09-01：向上回捲到第一組文字（copy1）消失時，
      // bc-other-members 與它一起消失；copy2/3 消失不影響（常駐）
      if (n === 1) {
        hideOtherMembers();
      }
      $root.find("#photo_copy" + n + " .t > span").each(function () {
        gsap.set(this, { y: "102%" });
      });
      if (n > 1) {
        $root.find("#photo_copy" + (n - 1)).css({ opacity: 1 });
      }
    }

    /* ---- resize：#photo_slide 高度 + mask 初始位置（複製原站 resize） ---- */
    function photoResize() {
      var windowH = window.innerHeight;
      var ttlH = $root.find("#photo_ttl").height() || 0;
      var h = spview() ? windowH - ttlH : windowH - ttlH + 80;
      $root.find("#photo_slide").css({ height: h });
      [1, 2, 3].forEach(function (i) {
        $root.find(".photo_slide_item" + i + " .inner").css({
          "-webkit-mask-position": "50% " + windowH + "px",
          "mask-position": "50% " + windowH + "px"
        });
      });
    }

    /* ---- GSAP ScrollTrigger：mask 揭示（複製原站 scrollTrigger onUpdate） ---- */
    function initScrollTriggers() {
      gsap.registerPlugin(ScrollTrigger);
      var end = spview() ? "+=" + 0.7 * window.innerHeight : "bottom 0%";
      var t = spview() ? 200 : 85;
      [1, 2, 3].forEach(function (i) {
        gsap.to("#photo_slide_item" + i, {
          y: "0%",
          scale: 1,
          duration: 1,
          scrollTrigger: {
            trigger: ".bc-fujiya-photo .photo_line" + i,
            start: "top 100%",
            end: end,
            scrub: true,
            onUpdate: function (e) {
              var inner = document.getElementById("photo_slide_item" + i + "_inner");
              if (!inner) return;
              var wh = window.innerHeight;
              var mp = "50% " + (wh - wh * e.progress) + "px";
              inner.style.setProperty("-webkit-mask-position", mp);
              inner.style.setProperty("mask-position", mp);
              inner.style.setProperty("-webkit-mask-size", "100%");
              inner.style.setProperty("mask-size", "100%");
              if (e.progress > 0.85) {
                var sz = 100 + (t * (e.progress - 0.85)) / 0.15;
                inner.style.setProperty("-webkit-mask-size", sz + "%");
                inner.style.setProperty("mask-size", sz + "%");
              }
            }
          }
        });
      });
    }

    /* ---- Waypoint：photo_line 刻度觸發 copy / .open 切換 ---- */
    function initWaypoints() {
      function el(sel) {
        return document.querySelector(".bc-fujiya-photo " + sel);
      }
      function photoOffset(n) {
        var copyH = $root.find("#photo_copy" + n).height() || 0;
        return 0.79 * (window.innerHeight - copyH);
      }

      // photo_line1
      new Waypoint({
        element: el(".photo_line1"),
        handler: function (dir) {
          if (dir === "down") showPhoto(1); else closePhoto(1);
        },
        offset: photoOffset(1)
      });
      new Waypoint({
        element: el(".photo_line1"),
        handler: function (dir) {
          if (dir === "down") $root.find(".photo_slide_item1").addClass("open");
          else $root.find(".photo_slide_item1").removeClass("open");
        },
        offset: "10%"
      });

      // photo_line2
      new Waypoint({
        element: el(".photo_line2"),
        handler: function (dir) {
          if (dir === "down") showPhoto(2);
          else { closePhoto(2); $root.find("#photo_copy1").addClass("active"); }
        },
        offset: photoOffset(2)
      });
      new Waypoint({
        element: el(".photo_line2"),
        handler: function (dir) {
          if (dir === "down") $root.find(".photo_slide_item2").addClass("open");
          else $root.find(".photo_slide_item2").removeClass("open");
        },
        offset: "10%"
      });

      // photo_line3
      new Waypoint({
        element: el(".photo_line3"),
        handler: function (dir) {
          if (dir === "down") showPhoto(3);
          else { closePhoto(3); $root.find("#photo_copy2").addClass("active"); }
        },
        offset: photoOffset(3)
      });
      new Waypoint({
        element: el(".photo_line3"),
        handler: function (dir) {
          if (dir === "down") $root.find(".photo_slide_item3").addClass("open");
          else $root.find(".photo_slide_item3").removeClass("open");
        },
        offset: "10%"
      });
    }

    function init() {
      photoResize();
      initScrollTriggers();
      initWaypoints();
      $(window).on("resize", function () {
        photoResize();
        if (typeof ScrollTrigger !== "undefined") ScrollTrigger.refresh();
      });
      // 圖片載入後刷新 ScrollTrigger 計算
      $(window).on("load", function () {
        if (typeof ScrollTrigger !== "undefined") ScrollTrigger.refresh();
      });
    }

    // 執行鎖定頁面動畫初始化
    init();
  }

  // boot 於 DOMContentLoaded 後執行（GSAP defer 已就緒）
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setTimeout(boot, 50); });
  } else {
    setTimeout(boot, 50);
  }
})();
