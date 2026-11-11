/* ============================================================
   bc-next-link.js — 咖啡詳情頁底部「前往咖啡豆選單」面板互動
   2026-11-11 建立
   ------------------------------------------------------------------
   來源：daisheng.com.tw/business/ 的 .c-footer__section 模組
   （原站 footer.js 用 GSAP ScrollTrigger scrub ＋ observer 加
     .is-footerActive；本專案不引入 GSAP，改以
     IntersectionObserver ＋ requestAnimationFrame 做等價行為）。

   ①② 進場（原站 observer → .is-footerActive{opacity:1;scale(1)}）
        root 進入視口約 12% 即加 .is-active（只加一次）→ CSS 負責
        opacity 0→1、scale 1.3→1（1s）。hover 放大＝純 CSS。
        prefers-reduced-motion → 直接視為已完成，不註冊觀察器。

   ③ 視差（原站 GSAP scrub：trigger .c-footer__section、
        start "top bottom"、end "bottom bottom"，y 由 -70% → 0%）
        progress = (viewportHeight - rootRect.top) / rootRect.height
          · 0 ＝ root 頂端剛碰到視口底部
          · 1 ＝ root 底端碰到視口底部
        面板內媒體寫 --bc-nl-y：-14% → 0%（媒體高 160% ⇒
        換算舞台高 -22.4% → 0%，永遠小於 top:-30% 的餘裕 ⇒ 不露黑邊）。
        以 passive scroll ＋ rAF 節流，且只在面板接近視口時計算。

   ④ 「( Next )」文字上捲：純 CSS（.bc-next-link__loop 的 :hover 動畫），
       本檔不參與。

   影片（沿用首頁推薦頁面雙卡的作法）：
     preload="none"，接近視口（rootMargin 600px）才 load()；
     進到視口（10%）play、離開 pause；play() 失敗（省電模式等）靜默忽略。
   ============================================================ */
(function () {
    'use strict';

    var ROOT_SELECTOR = '[data-bc-next-link]';
    var ACTIVE = 'is-active';
    /* 視差位移範圍（單位：媒體自身高度的百分比）：
       與 bc-next-link.css 的 .bc-next-link__media 預設值一致 */
    var SHIFT_FROM = -14;
    var SHIFT_TO = 0;

    var roots = document.querySelectorAll(ROOT_SELECTOR);
    if (!roots.length) {
        return;
    }

    var reduceMotion =
        typeof window.matchMedia === 'function' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var canObserve = 'IntersectionObserver' in window;

    for (var i = 0; i < roots.length; i++) {
        init(roots[i]);
    }

    function init(root) {
        var anchor = root.querySelector('.bc-next-link__anchor');
        var media = root.querySelector('.bc-next-link__media');
        var video = root.querySelector('.bc-next-link__video');

        /* ① 進場放大淡入 */
        if (anchor) {
            if (reduceMotion || !canObserve) {
                anchor.classList.add(ACTIVE);
            } else {
                var enterIO = new IntersectionObserver(function (entries) {
                    for (var j = 0; j < entries.length; j++) {
                        if (entries[j].isIntersecting) {
                            anchor.classList.add(ACTIVE);
                            enterIO.disconnect();
                            return;
                        }
                    }
                }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
                enterIO.observe(root);
            }
        }

        if (video) {
            initVideo(root, video);
        }
        if (media && !reduceMotion) {
            initParallax(root, media);
        }
    }

    /* 影片：接近視口才下載，進到視口才播放 */
    function initVideo(root, video) {
        if (!canObserve) {
            return;
        }

        /* 2026-11-11：可見時 play() 可能因影片還沒載到資料而被拒（promise reject）→ 停在
           第一格不動。故記住「想播放」意圖，載到可播（canplay／loadeddata）時再試一次。 */
        var wantsPlay = false;

        function tryPlay() {
            if (!wantsPlay || !video.paused) {
                return;
            }
            var p = video.play();
            if (p && typeof p.catch === 'function') {
                p.catch(function () {
                    /* 自動播放被拒（省電模式／背景分頁）→ 停在第一格即可 */
                });
            }
        }

        var loadIO = new IntersectionObserver(function (entries) {
            for (var i = 0; i < entries.length; i++) {
                if (!entries[i].isIntersecting) {
                    continue;
                }
                loadIO.disconnect();
                if (video.getAttribute('preload') !== 'auto') {
                    video.setAttribute('preload', 'auto');
                    video.load();
                }
                return;
            }
        }, { rootMargin: '600px 0px' });
        loadIO.observe(root);

        var playIO = new IntersectionObserver(function (entries) {
            wantsPlay = !!(entries[0] && entries[0].isIntersecting);
            if (wantsPlay) {
                tryPlay();
            } else if (!video.paused) {
                video.pause();
            }
        }, { threshold: 0.1 });
        playIO.observe(root);

        /* 影片載到可播（canplay／loadeddata）時再試一次播放 */
        video.addEventListener('canplay', tryPlay);
        video.addEventListener('loadeddata', tryPlay);
    }

    /* ③ 視差：原站 GSAP scrub 的等價實作 */
    function initParallax(root, media) {
        var visible = false;
        var ticking = false;

        function apply(progress) {
            var y = SHIFT_FROM + (SHIFT_TO - SHIFT_FROM) * progress;
            media.style.setProperty('--bc-nl-y', y.toFixed(2) + '%');
        }

        function update() {
            ticking = false;
            if (!visible) {
                return;
            }
            var rect = root.getBoundingClientRect();
            var vh = window.innerHeight || document.documentElement.clientHeight;
            var h = rect.height || 1;
            var progress = (vh - rect.top) / h;
            if (progress < 0) {
                progress = 0;
            } else if (progress > 1) {
                progress = 1;
            }
            apply(progress);
        }

        function requestUpdate() {
            if (ticking) {
                return;
            }
            ticking = true;
            if (typeof window.requestAnimationFrame === 'function') {
                window.requestAnimationFrame(update);
            } else {
                update();
            }
        }

        if (canObserve) {
            var visIO = new IntersectionObserver(function (entries) {
                visible = !!(entries[0] && entries[0].isIntersecting);
                if (visible) {
                    requestUpdate();
                }
            }, { rootMargin: '100px 0px' });
            visIO.observe(root);
        } else {
            visible = true;
            requestUpdate();
        }

        window.addEventListener('scroll', requestUpdate, { passive: true });
        window.addEventListener('resize', requestUpdate);
    }
})();
