/* ============================================================
   bc-photoarea.js — 首頁 hero「背景照片視差」的位移控制
   2026-11-07 建立（移植 hicard.studio 首頁的 Sticky1 / .fv__photoarea）

   來源：https://hicard.studio/ja 的 page.js（gsap + ScrollTrigger），行為如下：
     · 容器：gsap.to(area, { y: -(areaH - padH) × factor })
             trigger = 內容盒（本地對應 #bc-brand-stage），start "top top"、end "bottom top"、scrub:true
             原站 factor 桌面 1.7、≤768px 0.5
     · 每張圖：gsap.to(img, { y: data-para + "rem" })
             trigger = 容器本身，start "top top"、end "bottom top"、scrub:1
     ⇒ 兩層疊加：照片 = 容器位移 ＋ 自己的視差量 ⇒ 比內容（環形照／時鐘）更快往上。

   本地換算（只改單位、不改行為）
     · 容器位移：data-pa-shift（vh，模板給 -10）→ y = shift × vh × factor
     · 單張視差：data-para（vh，模板給 -8…-28，對應原站 -100…-500 的等比）→ y = para × vh
     · factor：沿用原站 0.5 的「≤768px 減半」規則（見 BREAKPOINT/factorAt()）
     · vh 一律用 window.innerHeight 現算，並在 ScrollTrigger refresh 時重算
       （invalidateOnRefresh + 函式型數值）⇒ 轉橫向／換視窗高度都會跟上

   守衛（比照 bc-sticky-mv.js / bc-popeye50.js）：
     · 找不到 #bc-brand-stage 或 .bc-photoarea／裡面沒有 data-para 元素 ⇒ 直接 return
     · gsap／ScrollTrigger 未載入（CDN 失效）⇒ 直接 return（照片停在 CSS 的 translate3d(0)，
       仍是正常靜態背景，不會空白）
     · prefers-reduced-motion: reduce ⇒ 不啟動任何位移、也不播影片

   影片格位（2026-11-09 使用者指示）
     · 第 3 格（原 .yoko 那張）由 <img> 改為 .bc-pa-video 容器＋內層 <video>
       （素材 media/hero_00.webm，poster 仍是 pa-3.webp，markup 見 bc_brand_stage_hero.html）
     · 位移對象改抓 [data-para]（img 與 .bc-pa-video 都算），影片自己不另外掛 transform
     · 播放只由下面的 setupVideos() 決定：進到視窗才 play、捲離就 pause、reduced-motion 不播
       （停在 poster）⇒ 刻意與 GSAP 解耦，CDN 掛掉時影片照樣正常播
   ============================================================ */
(function () {
  'use strict';

  var ROOT_ID = 'bc-brand-stage';
  var AREA_SELECTOR = '.bc-photoarea';
  var BREAKPOINT = 768; /* 原站同一組斷點 */
  var SMALL_FACTOR = 0.5; /* 原站 ≤768px 的位移減半 */
  var SCRUB_AREA = 1; /* 原站容器 scrub:1 */
  var SCRUB_IMG = 1; /* 原站單張 scrub:1 */

  var root = document.getElementById(ROOT_ID);
  if (!root) return;

  var area = root.querySelector(AREA_SELECTOR);
  if (!area) return;

  /* 參與視差的格位＝所有 [data-para] 元素（2026-11-09 起第 3 格是 .bc-pa-video 容器，
     不再只抓 img） */
  var tiles = area.querySelectorAll('[data-para]');
  if (!tiles.length) return;

  var mqReduce = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : { matches: false };

  /* 影片格位與 GSAP 無關 ⇒ 先處理（GSAP 的 CDN 掛掉時，播放／poster 照樣正常） */
  setupVideos(mqReduce);

  var gsap = window.gsap;
  var ScrollTrigger = window.ScrollTrigger;
  if (!gsap || !ScrollTrigger) return;

  if (mqReduce.matches) return; /* 使用者要求減少動態 ⇒ 這層就當靜態照片 */

  gsap.registerPlugin(ScrollTrigger);

  /* 原站「≤768px 位移減半」 */
  function factorAt() {
    return window.innerWidth <= BREAKPOINT ? SMALL_FACTOR : 1;
  }

  /* 1vh 的像素值（位移量的單位；每次 refresh 重算） */
  function vh() {
    return (window.innerHeight || 0) / 100;
  }

  /* 讀 data-* 的數字；缺值／壞值回 0（該張就只吃容器位移） */
  function num(el, name) {
    var v = parseFloat(el.getAttribute(name));
    return isNaN(v) ? 0 : v;
  }

  /* ---- 影片格位：只決定「播不播」，位移仍由下面的 GSAP 負責 ----
     ① prefers-reduced-motion:reduce ⇒ 一律不播，停在 poster（＝原本那張照片）
     ② 只在整片照片區進到視窗時播，捲離就 pause（不讓已經滾過去的 hero 一直解碼吃電）
     ③ 沒有 IntersectionObserver ⇒ 直接播；play() 被瀏覽器拒絕（iOS 省電模式／低電量）也靜默，
        poster 仍在，畫面不會破 */
  function setupVideos(mqReduce) {
    var vids = area.querySelectorAll('video');
    if (!vids.length) return;

    var visible = false;

    function sync() {
      var on = visible && !mqReduce.matches;
      Array.prototype.forEach.call(vids, function (v) {
        if (!on) {
          v.pause();
          return;
        }
        var p = v.play();
        if (p && p.catch) p.catch(function () {}); /* 被擋就維持 poster，不報錯 */
      });
    }

    if (!('IntersectionObserver' in window)) {
      visible = true; /* 極舊瀏覽器：直接播 */
      sync();
    } else {
      new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
        sync();
      }, { threshold: 0 }).observe(area);
    }

    /* 系統設定中途切換「減少動態」時即時跟上（舊版 Safari 只有 addListener） */
    if (mqReduce.addEventListener) mqReduce.addEventListener('change', sync);
    else if (mqReduce.addListener) mqReduce.addListener(sync);
  }

  var areaShift = num(area, 'data-pa-shift') * vh() * factorAt();

  /* ---- 容器層：整片照片額外上飄（原站 Sticky1 的容器位移） ---- */
  if (areaShift) {
    gsap.to(area, {
      y: function () {
        return num(area, 'data-pa-shift') * vh() * factorAt();
      },
      ease: 'none',
      scrollTrigger: {
        trigger: root,
        start: 'top top',
        end: 'bottom top',
        scrub: SCRUB_AREA,
        invalidateOnRefresh: true
      }
    });
  }

  /* ---- 單張層：各自的 data-para（單位 vh）；img 與影片容器一視同仁 ---- */
  tiles.forEach(function (tile) {
    var para = num(tile, 'data-para');
    if (!para) return;

    gsap.to(tile, {
      y: function () {
        return para * vh() * factorAt();
      },
      ease: 'none',
      scrollTrigger: {
        trigger: root,
        start: 'top top',
        end: 'bottom top',
        scrub: SCRUB_IMG,
        invalidateOnRefresh: true
      }
    });
  });

  /* 影像載入完成後版面不會變（全部 position:absolute），不需 refresh；
     但字型／視窗高度變化會影響 vh ⇒ 交給 ScrollTrigger 自己的 resize 事件
     （上面已開 invalidateOnRefresh，resize 時會重跑函式型數值）。 */
})();
