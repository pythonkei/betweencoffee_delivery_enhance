/* ============================================================
   bc-recommended-pages.js — 首頁「推薦頁面」雙卡互動
   2026-10-24 建立
   ------------------------------------------------------------------
   對應原站 union-tec.jp/capability 的 Alpine 元件
   Alpine.data('recommendedPages')（同一頁面的 index.js bundle）：
     - mouseenter：自己被 hover → is-hover-active，
                   其餘卡片 → is-hover-inactive
     - mouseleave：全部移除兩個 class
     - 桌機／行動版佈局切換（原站 watch $store.app.isPcLayout）
       → 清空 hover 狀態，避免殘留 2/3、1/3 寬度
   原站的 clip-path 形狀補間是 GSAP MorphSVG；本檔不重做補間
   —— 寬度／形狀的過渡全部由 bc-recommended-pages.css 的
   transition（clip-path / width / opacity / transform）負責，
   JS 只切 class，行為與原站一致。

   2026-10-25：卡片背景 webp → <video class="recommended-page__bg-video">；
   本檔另外負責「hover 播放、離開暫停」（clear/enter 內），
   以及接近視口才預載（preload 由 none 轉 auto），觸控裝置不下載。
   ============================================================ */
(function () {
  'use strict';

  var ROOT_SELECTOR = '[data-bc-recommended-pages]';
  var LINK_SELECTOR = '.recommended-pages__link';
  var VIDEO_SELECTOR = '.recommended-page__bg-video';
  var ACTIVE = 'is-hover-active';
  var INACTIVE = 'is-hover-inactive';

  /* 2026-10-25：卡片背景由 webp 圖改為 WebM 影片。
     影片只在「真的有 hover 的裝置」才預載／播放（觸控裝置沒有 hover，
     背景本來就不會淡入，不必下載 0.8MB＋2.2MB）；<video> 標記為
     preload="none"，接近視口（rootMargin 600px）才轉 auto 並 load()。 */
  var CAN_HOVER =
    typeof window.matchMedia === 'function'
      ? window.matchMedia('(hover: hover) and (pointer: fine)').matches
      : true;

  function videosOf(link) {
    return Array.prototype.slice.call(link.querySelectorAll(VIDEO_SELECTOR));
  }

  function warmVideo(video) {
    if (video.getAttribute('preload') === 'none') {
      video.setAttribute('preload', 'auto');
      video.load();
    }
  }

  function playVideo(video) {
    warmVideo(video);
    video.muted = true;
    var playing = video.play();
    /* 自動播放被政策擋掉時不要讓 promise rejection 變成 console error */
    if (playing && typeof playing.catch === 'function') {
      playing.catch(function () {});
    }
  }

  function setup(root) {
    if (root.getAttribute('data-rp-ready') === '1') {
      return;
    }
    root.setAttribute('data-rp-ready', '1');

    var links = Array.prototype.slice.call(
      root.querySelectorAll(LINK_SELECTOR)
    );
    if (!links.length) {
      return;
    }

    var videos = Array.prototype.slice.call(
      root.querySelectorAll(VIDEO_SELECTOR)
    );

    function clear() {
      links.forEach(function (link) {
        link.classList.remove(ACTIVE, INACTIVE);
      });
      videos.forEach(function (video) {
        video.pause();
      });
    }

    function enter(current) {
      links.forEach(function (link) {
        var isCurrent = link === current;
        link.classList.toggle(ACTIVE, isCurrent);
        link.classList.toggle(INACTIVE, !isCurrent);
        videosOf(link).forEach(function (video) {
          if (isCurrent) {
            playVideo(video);
          } else {
            video.pause();
          }
        });
      });
    }

    /* 接近視口才預載影片（同 #58 bc-steps-rive 的延遲載入做法） */
    function warmUp() {
      if (!CAN_HOVER || !videos.length) {
        return;
      }
      videos.forEach(warmVideo);
    }

    if (CAN_HOVER && videos.length) {
      if (typeof window.IntersectionObserver === 'function') {
        var io = new window.IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              warmUp();
              io.disconnect();
            }
          });
        }, { rootMargin: '600px 0px' });
        io.observe(root);
      } else {
        warmUp();
      }
    }

    links.forEach(function (link) {
      link.addEventListener('mouseenter', function () {
        enter(link);
      });
      link.addEventListener('mouseleave', clear);
    });

    /* 原站 $watch('$store.app.isPcLayout')：斷點切換時重置 */
    var mq = window.matchMedia('(min-width: 64rem)');
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', clear);
    } else if (typeof mq.addListener === 'function') {
      mq.addListener(clear);
    }
  }

  function init() {
    Array.prototype.forEach.call(
      document.querySelectorAll(ROOT_SELECTOR),
      setup
    );
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
