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
       （素材清單＝views.PA_VIDEOS，markup 見 bc_brand_stage_hero.html）
     · 位移對象改抓 [data-para]（img 與 .bc-pa-video 都算），影片自己不另外掛 transform
     · 播放只由下面的 setupVideoCarousel() 決定：進到視窗才 play、捲離就 pause、reduced-motion 不播
       （停在深色底）⇒ 刻意與 GSAP 解耦，CDN 掛掉時影片照樣正常播
     · 2026-11-09 同日改為「輪播容器」：容器內可放多支 <video>，照 DOM 順序循環播放
       （現況 3 支：hero_00 → hero_04 → hero_05），換片參數沿用 bc-sticky-mv.js
       （距結束 0.75s 開始換、0.6s 交叉淡入）；要加片只改 views.PA_VIDEOS
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

  /* 影片輪播參數（沿用 bc-sticky-mv.js／about 首屏那套：距結束 0.75s 換片、0.6s 交叉淡入） */
  var VIDEO_LEAD_S = 0.75; /* 距影片結束剩這麼多秒就開始換下一支 */
  var VIDEO_FADE_MS = 600; /* 交叉淡入時間，需與 CSS 的 transition 一致 */
  var VIDEO_PRIME_AFTER_S = 1; /* 當前這支播滿 1s 才預載下一支（別在開場就一次抓 3 支 2.2MB） */

  /* 影片格位與 GSAP 無關 ⇒ 先處理（GSAP 的 CDN 掛掉時，播放／換片照樣正常） */
  setupVideoCarousel(mqReduce);

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

  /* ---- 影片格位：輪播容器（可放多支 <video>；2026-11-09）----
     ① prefers-reduced-motion:reduce ⇒ 一律不播（停在深色底，無 poster）
     ② 只在整片照片區進到視窗時播，捲離／頁面切到背景就 pause（不讓滾過去的 hero 一直解碼吃電）
     ③ 多支時照 DOM 順序（＝views.PA_VIDEOS 的順序）循環：距結束 VIDEO_LEAD_S 秒讓下一支
        加 .is-on 淡入（CSS 0.6s），淡完才把舊支的 .is-on 拿掉並暫停歸零
     ④ 下一支還沒 ready ⇒ 這輪先不切（當前支有 loop，畫面不會凍住），順手補載它
     ⑤ 沒有 IntersectionObserver ⇒ 直接播；play() 被瀏覽器拒絕（iOS 省電／低電量）也靜默，
        該格就是空的，畫面不會破 */
  function setupVideoCarousel(mqReduce) {
    var vids = area.querySelectorAll('.bc-pa-video > video');
    if (!vids.length) return;

    var visible = false;
    var current = 0;
    var fadeTimer = null;
    var lastTime = 0; /* 當前那一支上一次的播放位置（用來判斷 loop 是否繞回開頭） */

    function play(v) {
      var p = v.play();
      if (p && p.catch) p.catch(function () {}); /* 被擋就維持現狀，不報錯 */
    }

    /* 把某支從 preload="none" 拉起來（起播／預載下一支都走這裡）
       force ⇒ 已標記 auto 但 readyState 掉下來（久未播、瀏覽器把 buffer 回收）時重新抓一次，
       否則會永遠卡在「等下一支 ready」不換片 */
    function prime(v, force) {
      if (v.getAttribute('preload') !== 'auto') {
        v.setAttribute('preload', 'auto');
        v.load();
        return;
      }
      if (force && v.readyState < 2) v.load();
    }

    function nextIndex() {
      return (current + 1) % vids.length;
    }

    /* 換片：下一支可播才切；否則留在當前支（loop 中）並補載，下一個 timeupdate 再試 */
    function advance() {
      if (vids.length < 2) return; /* 單支＝舊行為，loop 自己循環 */
      if (!visible || document.hidden || mqReduce.matches) return;

      var next = nextIndex();
      var nextVid = vids[next];
      if (nextVid.readyState < 2) {
        prime(nextVid, true);
        return;
      }

      var from = current;
      current = next;
      lastTime = 0;

      prime(nextVid);
      try {
        nextVid.currentTime = 0;
      } catch (err) {}
      nextVid.classList.add('is-on');
      play(nextVid);

      window.clearTimeout(fadeTimer);
      fadeTimer = window.setTimeout(function () {
        if (current !== next) return; /* 期間又換走了，交給下一輪收尾 */
        vids[from].classList.remove('is-on');
        vids[from].pause();
        try {
          vids[from].currentTime = 0;
        } catch (err) {}
      }, VIDEO_FADE_MS);
    }

    /* 只對「當前那一支」判斷換片（timeupdate 頻率約 4Hz，成本可忽略）
       除了「距結束 0.75s」之外，再加一條兜底：播放位置明顯倒退 ⇒ 已經 loop 繞回開頭
       （掉幀／seek 讓 timeupdate 跳過換片窗口時會發生）⇒ 立刻換，免得同一支多播一輪。 */
    Array.prototype.forEach.call(vids, function (v) {
      v.addEventListener('timeupdate', function () {
        if (vids[current] !== v) return;
        var ct = v.currentTime;
        var looped = ct + 0.5 < lastTime;
        lastTime = ct;

        var d = v.duration;
        if (!d || isNaN(d)) return;
        if (d - ct <= VIDEO_LEAD_S || looped) {
          advance();
        } else if (ct >= VIDEO_PRIME_AFTER_S && vids.length > 1) {
          prime(vids[nextIndex()]); /* 播穩了才抓下一支，換片時才不用等 */
        }
      });
    });

    function sync() {
      if (!visible || document.hidden || mqReduce.matches) {
        Array.prototype.forEach.call(vids, function (v) {
          v.pause();
        });
        return;
      }
      var cur = vids[current];
      prime(cur);
      play(cur);
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

    /* 分頁切到背景也停（手機換 App 回來不會接著燒電） */
    document.addEventListener('visibilitychange', sync);

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
