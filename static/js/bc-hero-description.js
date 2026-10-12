/* ============================================================
   bc-hero-description.js — About 頁面 hero-description-wrapper 動畫
   ------------------------------------------------------------
   2026-10-12：完整移植自 https://bkkdw26.greydientlab.com/ 主題 bkkdw
   acf/blocks/hero/js/script.js 的 textColorAnimation()。

   原站行為（本檔 1:1 保留，未增減任何參數）：
   - SplitType（0.3.3）把 .hero-description 切成 words + chars（tagName: span）
   - gsap.set(chars, {color:'#616161'}) 先全部轉灰
   - gsap.timeline({scrollTrigger:{trigger:'.hero-description-wrapper',
       start: isTablet ? 'top 54%' : 'top 80%', end:'bottom 50%', scrub:1}})
       逐字 tl.to(char,{color: target, duration:0.1, ease:'none'}, index*0.02)
       → 一般文字 to #FFFFFF、.number 內的字 to #e2fc07
   - setTimeout(() => ScrollTrigger.refresh(), 100)

   依賴（全域）：gsap + ScrollTrigger（base.html <head> 以 defer 載入）、
   SplitType（本模組以 vendor/split-type.min.js 以 defer 於本檔前載入）。
   若任一函式庫缺失，安全跳過（文字維持原色，不影響閱讀）。
   ============================================================ */
(function () {
    'use strict';

    var isTablet = window.innerWidth >= 768 && window.innerWidth <= 1023;

    function textColorAnimation() {
        var heroDescription = document.querySelector('.hero-description-wrapper .hero-description');

        if (!heroDescription) {
            return;
        }

        if (typeof SplitType === 'undefined' || typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
            return;
        }

        var split = new SplitType(heroDescription, {
            types: 'words, chars',
            tagName: 'span',
        });

        gsap.set(split.chars, {
            color: '#616161',
        });

        var tl = gsap.timeline({
            scrollTrigger: {
                trigger: '.hero-description-wrapper',
                start: isTablet ? 'top 54%' : 'top 80%',
                end: 'bottom 50%',
                scrub: 1,
            },
        });

        split.chars.forEach(function (char, index) {
            var isYellowText = char.closest('.number') !== null;

            var targetColor = isYellowText ? '#e2fc07' : '#FFFFFF';

            tl.to(char, {
                color: targetColor,
                duration: 0.1,
                ease: 'none',
            }, index * 0.02);
        });

        setTimeout(function () {
            ScrollTrigger.refresh();
        }, 100);
    }

    function init() {
        textColorAnimation();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
