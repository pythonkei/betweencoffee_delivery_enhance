/* ============================================================
   bc-feed-video.js — 首頁第二組 .feed（.feed--video）底層影片控制
   2026-09-11 建立
   ------------------------------------------------------------------
   背景：複製一組 .feed，並將底層「背景圖片」（index_feed_image.png）
        改為影片容器（<video> roasting.webm）。蒙版層（.feed__layer-parts
        反相 clip-path 挖洞）不變 → 形狀輪廓內由靜態照片變成烘焙影片。

   作法：
   - 影片標記 muted / playsinline / loop / preload="none"
     （首屏不下載 2.2MB；poster 使用原照片，未播放時外觀與第一組相同）
   - 本檔以 IntersectionObserver 控制：
       進入視口（上下各 200px 提前量）→ preload="auto" + play()
       離開視口 → pause()（省 CPU / 電力，已下載的資料保留）
   - play() 被瀏覽器拒絕（省電模式等）時忽略 → 維持 poster，不報錯
   - 不支援 IntersectionObserver 或腳本未載入 → 只顯示 poster，
     版面與第一組 .feed 完全相同，不會破版
   ============================================================ */
(function () {
  'use strict';

  function init() {
    var videos = document.querySelectorAll('.feed--video video[data-feed-video]');
    if (!videos.length) {
      return;
    }

    /* 開始播放：首次進入視口才把 preload 由 none 改為 auto 並下載 */
    function start(video) {
      if (video.getAttribute('data-feed-loaded') !== '1') {
        video.setAttribute('data-feed-loaded', '1');
        video.preload = 'auto';
        if (video.readyState < 2) {
          // preload 變更後需 load() 才會重新選取資源並開始下載
          video.load();
        }
      }
      if (video.paused) {
        var p = video.play();
        if (p && typeof p.catch === 'function') {
          p.catch(function () { /* autoplay 被拒時忽略（維持 poster） */ });
        }
      }
    }

    function stop(video) {
      if (!video.paused) {
        video.pause();
      }
    }

    if (!('IntersectionObserver' in window)) {
      // 舊瀏覽器：直接載入播放（與首頁輪播影片行為一致）
      Array.prototype.forEach.call(videos, start);
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          start(entry.target);
        } else {
          stop(entry.target);
        }
      });
    }, { rootMargin: '200px 0px 200px 0px' });

    Array.prototype.forEach.call(videos, function (video) {
      io.observe(video);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
