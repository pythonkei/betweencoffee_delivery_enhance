/* ============================================================================
   bc-top-art.js — loogg.jp「.top_art」sticky 堆疊卡片 scroll 縮放動畫（1:1 移植）
   ----------------------------------------------------------------------------
   2026-10-04 建立
   來源：loogg.jp 首頁 HTML 內嵌 <script>（Section 2 のアニメーション関連）。
   唯一必要的改寫（本站與原站的捲動模型不同）：
     原站把整個 TOP 放在 .top_wrap（max-height:100svh; overflow:hidden scroll）內
     部捲動，因此 $(".top_art").offset().top 實際量到的是「區塊頂端相對捲動埠
     頂端」的距離（可為負）；本站是一般 window 捲動，等價量測為
     element.getBoundingClientRect().top。兩者數值等價 → 觸發判斷 0 > trigger、
     scale 公式、0.6 下限、base 0.96 / 0.93、第 11 張不參與、transform-origin
     由 right top 切換 right center 等邏輯全部逐行照抄。
   jQuery → vanilla：$(elm).children(".top_art_item") 以「直接子元素」實作；
     innerHeight() 以 clientHeight（padding-box 高度，wrap 無 border）實作。
   ========================================================================= */
(function () {
  "use strict";

  /* 原站 var breakpoint = 1024（common.js） */
  var BREAKPOINT = 1024;
  /* 原站固定除數與下限 */
  var DIVISOR = 2000;
  var MIN_SCALE = 0.6;
  var BASE_SCALE_PC = 0.96;
  var BASE_SCALE_SP = 0.93;

  var art = document.querySelector(".bc-top-art");
  if (!art) {
    return;
  }

  /* 原站 $(".top_art > .top_art_item_wrap")：只取直接子元素，保持 DOM 順序 */
  var wraps = [];
  var i;
  for (i = 0; i < art.children.length; i++) {
    if (art.children[i].classList.contains("top_art_item_wrap")) {
      wraps.push(art.children[i]);
    }
  }
  if (!wraps.length) {
    return;
  }

  /* 原站 $(elm).children(".top_art_item")：直接子元素 .top_art_item */
  function findItem(wrap) {
    var k;
    for (k = 0; k < wrap.children.length; k++) {
      if (wrap.children[k].classList.contains("top_art_item")) {
        return wrap.children[k];
      }
    }
    return null;
  }

  var items = [];
  for (i = 0; i < wraps.length; i++) {
    items.push(findItem(wraps[i]));
  }

  function update() {
    /* 原站 var sec2TriggerBase = $(".top_art").offset().top;
       → 本站等價：區塊頂端相對視口頂端的距離（每次事件重新量測，同原站） */
    var sec2TriggerBase = art.getBoundingClientRect().top;
    /* 原站 var sec2ItemHeight = $(".top_art_item_wrap").innerHeight();
       → jQuery innerHeight = computed height + padding（有小數的 padding-box 高度）；
         clientHeight 會取整，getBoundingClientRect().height 才與 jQuery 等值
         （wrap 無 border / 無 transform，故 rect.height = padding-box 高度） */
    var sec2ItemHeight = wraps[0].getBoundingClientRect().height;
    var inWidth = window.innerWidth;
    var sec2NextBaseScale = inWidth <= BREAKPOINT ? BASE_SCALE_SP : BASE_SCALE_PC;

    /* 原站 $(".top_art > .top_art_item_wrap:not(:last-child)").each(...)
       → 最後一張卡不參與（它是永遠留在最上層的那張） */
    for (var n = 0; n < wraps.length - 1; n++) {
      var elm = wraps[n];
      var item = items[n];
      var nextItem = items[n + 1];
      var sec2Trigger = sec2TriggerBase + sec2ItemHeight * n;

      if (0 > sec2Trigger) {
        /* 拡縮流量計算 */
        var scaleVal = 1 - (sec2Trigger * -1 / DIVISOR);
        if (scaleVal < MIN_SCALE) {
          scaleVal = MIN_SCALE; /* 見えなくなったあとに処理を止めるための限界値 */
        }
        if (item) {
          item.style.transform = "scale(" + scaleVal + ")";
        }

        /* 少し小さい次のボックスの拡縮計算 */
        var nextScaleVal = sec2NextBaseScale + (sec2Trigger * -1 / DIVISOR);
        if (nextScaleVal >= 1) {
          nextScaleVal = 1;
          if (nextItem) {
            nextItem.style.transformOrigin = "right center";
          }
        } else if (nextItem) {
          nextItem.style.transformOrigin = "";
        }
        if (nextItem) {
          nextItem.style.transform = "scale(" + nextScaleVal + ")";
        }
      } else if (n === 0) {
        /* 一番目の要素だけ画面上部未到達時のリセットを別で記述 */
        if (item) {
          item.style.transform = "";
          item.style.filter = "";
        }
        if (nextItem) {
          nextItem.style.transform = "";
        }
      } else if (nextItem) {
        nextItem.style.transform = "";
      }
    }
  }

  /* rAF 合流：原站每個 scroll 事件同步計算，此處每 frame 至多算一次（數值相同） */
  var ticking = false;
  function requestUpdate() {
    if (ticking) {
      return;
    }
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      update();
    });
  }

  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", requestUpdate);
  window.addEventListener("orientationchange", requestUpdate);
  window.addEventListener("load", requestUpdate);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) {
      requestUpdate();
    }
  });

  /* 初回：原站靠容器上的 load 事件觸發，這裡直接跑一次 */
  update();
})();
