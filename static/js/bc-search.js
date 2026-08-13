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
    var hideTimer = null;

    function show() {
        // 若上一個 hide 的計時器尚未觸發，先取消 → 快速 hover 進出不會被卡住
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
        // 移除 is-out，避免與 is-on 並存（CSS 中 is-out 後定義會勝出，背景圖會反向移出）
        searchLink.classList.remove('is-out');
        searchLink.classList.add('is-on');
        isShow = true;
    }

    function hide() {
        if (!isShow) {
            return;
        }
        // 移除 is-on 讓 is-out 獨立生效（避免同時存在時 is-out 後定義勝出）
        searchLink.classList.remove('is-on');
        searchLink.classList.add('is-out');
        // 等待 is-out 移出動畫完整播放後移除 class（回到初始隱藏狀態）
        // 以 setTimeout 為準（多圖 transition-delay 不同，transitionend 不可靠）
        hideTimer = setTimeout(function () {
            searchLink.classList.remove('is-on', 'is-out');
            isShow = false;
            hideTimer = null;
        }, 1000); // is-out 700ms + 最大 delay 300ms
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
