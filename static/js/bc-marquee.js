/* ============================================================
   bc-marquee.js — 水平跑馬燈（JS rAF 整數像素驅動，無抖動）
   bean_menu banner 的 .bc-marquee（Mogra 品牌字跑馬燈）
   為什麼不用 CSS animation：
     CSS animation 線性插值產生非整數位移（如 -107.306px），
     文字在子像素位置渲染 → 每幀微振動（「抖動跳動」）。
   本 JS 方案：
     - 每幀位移累積（SPEED px/frame），Math.round 到整數像素
     - 文字永遠在整數像素位置 → 物理上不可能抖動
     - 位移達 -itemW 時 +itemW（模循環）→ 跨迭代邊界連續無縫
     - resize / 字體載入後重算 itemW
     - prefers-reduced-motion 時停用
   用法：.bc-marquee > .bc-marquee__track > 2×.bc-marquee__item（相同內容）
   ============================================================ */
(function () {
    'use strict';

    function init() {
        var marquees = document.querySelectorAll('.bc-marquee');
        if (!marquees.length) return;

        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        marquees.forEach(function (marquee) {
            var track = marquee.querySelector('.bc-marquee__track');
            if (!track || track.__bcMarqueeReady) return;
            var items = track.querySelectorAll('.bc-marquee__item');
            if (items.length < 2) return;
            track.__bcMarqueeReady = true;

            // 關閉 CSS animation fallback（避免與 JS transform 衝突）
            track.style.animation = 'none';

            var SPEED = 0.35;          // px / frame（60fps → ~21px/s，與 CSS 28s 接近）
            var x = 0;
            var itemW = 0;

            function measure() {
                itemW = items[0].getBoundingClientRect().width;
                // 尺寸變化後確保 x 在有效範圍，避免錯位
                if (itemW > 0 && x <= -itemW) x = 0;
            }
            measure();
            window.addEventListener('resize', measure);
            // Mogra webfont 載入完成後重算寬度（字體切換會改變 item 寬）
            if (document.fonts && document.fonts.ready) {
                document.fonts.ready.then(measure);
            }

            function tick() {
                if (!track.__bcMarqueeReady) return;
                if (itemW <= 0) { measure(); }
                x -= SPEED;
                // 模循環：位移達一個 item 寬時回到等效位置（item2 對齊 item1）
                if (x <= -itemW) {
                    x += itemW;
                }
                // 整數像素位移 → 無子像素抖動
                track.style.transform = 'translateX(' + Math.round(x) + 'px)';
                requestAnimationFrame(tick);
            }
            requestAnimationFrame(tick);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();