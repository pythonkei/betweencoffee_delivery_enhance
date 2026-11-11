/* ============================================================
   bc-next-link.js — 咖啡詳情頁底部「前往咖啡豆選單」面板互動
   2026-11-11 建立（同日更新：進場可重播、背景改靜態照片）
   ------------------------------------------------------------------
   來源：daisheng.com.tw/business/ 的 .c-footer__section 模組
   （原站 footer.js 用 GSAP ScrollTrigger scrub ＋ observer 加
     .is-footerActive；本專案不引入 GSAP，改以
     IntersectionObserver ＋ requestAnimationFrame 做等價行為）。

   ①② 進場（原站 observer → .is-footerActive{opacity:1;scale(1)}）
        root 進入視口 12%（底部再留 10%）就加 .is-active：CSS 負責
        opacity 0→1、scale 1.3→1（1s）。完全離開視口時先關掉
        transition 再移除 .is-active 歸位（畫面上看不到），所以
        「每次捲回面板都會重播一次」—— 2026-11-11 使用者指示，
        原站只播一次。hover 放大＝純 CSS。
        prefers-reduced-motion → 直接視為已完成，不註冊觀察器。

   ③ 視差（原站 GSAP scrub：trigger .c-footer__section、
        start "top bottom"、end "bottom bottom"，y 由 -70% → 0%）
        progress = (viewportHeight - rootRect.top) / rootRect.height
          · 0 ＝ root 頂端剛碰到視口底部
          · 1 ＝ root 底端碰到視口底部
        面板內媒體寫 --bc-nl-y：-14% → 0%（媒體高 160% ⇒
        換算舞台高 -22.4% → 0%，永遠小於 top:-30% 的餘裕 ⇒ 不露黑邊）。
        以 passive scroll ＋ rAF 節流，且只在面板接近視口時計算。

   ④ 「( NEXT )」文字上捲：純 CSS（.bc-next-link__loop 的 animation），
       2026-11-11 依使用者指示改為**常駐無限循環**（不再等 hover），本檔不參與。

   背景素材（2026-11-11 使用者指示：不用影片）：
     靜態照片 static/images/bean_menu.jpg（1920×1280），
     <img loading="lazy" decoding="async"> ＋ object-fit: cover；
     本檔因此不管影片載入／播放，只剩「進場」與「視差」兩件事。
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

        /* ① 進場放大淡入（可重播） */
        if (anchor) {
            if (reduceMotion || !canObserve) {
                anchor.classList.add(ACTIVE);
            } else {
                initEnter(root, anchor);
            }
        }

        if (media && !reduceMotion) {
            initParallax(root, media);
        }
    }

    /* ① 進場：每次捲進視口都從 scale(1.3)／opacity 0 重播一次 */
    function initEnter(root, anchor) {
        function resetAnchor() {
            /* 關掉 transition 直接歸位 → 不播反向動畫，也不會讓使用者快速
               來回捲動時停在半途的縮放值；因為在畫面外，肉眼看不到 */
            anchor.style.transition = 'none';
            anchor.classList.remove(ACTIVE);
            /* 強制 reflow，確保歸位在恢復 transition 之前生效 */
            void anchor.offsetWidth;
            anchor.style.transition = '';
        }

        var enterIO = new IntersectionObserver(function (entries) {
            for (var j = 0; j < entries.length; j++) {
                if (entries[j].isIntersecting) {
                    anchor.classList.add(ACTIVE);
                    return;
                }
            }
        }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });

        var resetIO = new IntersectionObserver(function (entries) {
            for (var k = 0; k < entries.length; k++) {
                /* 只要還有一點點在視口內就不歸位（避免底部 10% 被裁掉時閃動） */
                if (entries[k].intersectionRatio > 0) {
                    continue;
                }
                resetAnchor();
            }
        }, { threshold: 0 });

        enterIO.observe(root);
        resetIO.observe(root);
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
