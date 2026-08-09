/* ============================================================
   bc-search.js — 首頁 SALON/STORE SEARCH 區塊動畫
   參考 demido.jp common.js 的 Search 類別邏輯：
   - 桌面 hover：mouseenter → is-on（背景圖浮入）、mouseleave → is-out（浮出）
   - 行動端（≤767px）：GSAP ScrollTrigger 進入/離開視窗 50% 觸發
   相依：GSAP + ScrollTrigger（CDN，見 index.html）
   ============================================================ */
(function () {
    'use strict';

    var searchLink = document.querySelector('.bc-search-link');
    if (!searchLink) {
        return;
    }

    var isShow = false;

    function show() {
        searchLink.classList.add('is-on');
        isShow = true;
    }

    function hide() {
        if (!isShow) {
            return;
        }
        searchLink.classList.add('is-out');
        // 等待背景圖（img-03）的 transition 完成後再移除 is-on/is-out，
        // 讓 is-out 移出動畫完整播放（對應 demido 等待 transitionend）
        var img03 = searchLink.querySelector('.bc-search-bg-img-03');
        var done = false;
        var onTransitionEnd = function () {
            if (done) {
                return;
            }
            done = true;
            searchLink.classList.remove('is-on', 'is-out');
            isShow = false;
            if (img03) {
                img03.removeEventListener('transitionend', onTransitionEnd);
            }
        };
        // transition 可能因 class 衝突而未啟動 → 用 setTimeout 保險移除
        if (img03) {
            img03.addEventListener('transitionend', onTransitionEnd);
            setTimeout(onTransitionEnd, 1500); // is-out 1000ms + delay 300ms
        } else {
            onTransitionEnd();
        }
    }

    // 桌面 hover
    searchLink.addEventListener('mouseenter', function () {
        if (!window.isMobile) {
            show();
        }
    });
    searchLink.addEventListener('mouseleave', function () {
        if (!window.isMobile) {
            hide();
        }
    });

    // 行動端：GSAP ScrollTrigger（進入 50% 顯示、離開隱藏）
    if (window.gsap && window.ScrollTrigger) {
        gsap.registerPlugin(ScrollTrigger);
        ScrollTrigger.matchMedia({
            '(max-width: 768px)': function () {
                ScrollTrigger.create({
                    trigger: searchLink,
                    start: 'top 50%',
                    end: 'bottom 50%',
                    onEnter: show,
                    onEnterBack: show,
                    onLeave: hide,
                    onLeaveBack: hide
                });
            }
        });
    }
})();
