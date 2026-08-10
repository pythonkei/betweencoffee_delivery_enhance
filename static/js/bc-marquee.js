/* ============================================================
   bc-marquee.js — 水平跑馬燈（JS rAF 整數像素驅動 + 循環 buffer，無抖動無閃出）
   bean_menu banner 的 .bc-marquee（Mogra 品牌字跑馬燈）
   為什麼不用 CSS animation：
     CSS animation 線性插值產生非整數位移（如 -107.306px），
     文字在子像素位置渲染 → 每幀微振動（「抖動跳動」）。
   為什麼不用「模循環 x+=itemW」：
     x 從 -itemW 跳回 0 的瞬間，視窗開頭從「item1 結尾 •&nbsp; + item2 開頭 ROASTED」
     變成「item1 開頭 ROASTED（無前綴）」→ 「• 」前綴閃失 → 「第2段閃出接1段」。
   循環 buffer 方案（v2）：
     - 第一個 item 完全移出視窗（x <= -itemW）時，appendChild 移到 track 尾端，
       x += itemW 補償（視覺位置不變）→ track 成為環形，文字從左緣平滑滑入
     - 視窗任意時刻內容都連續（item 結尾 → 下一 item 開頭），無「起點裸露」
     - 確保 ≥3 個 item（視窗寬 < 2×itemW 時右側內容充足）
     - 每幀位移累積 + Math.round 整數像素 → 物理上不可能抖動
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

            // 確保至少 3 個 item（視窗寬 < 2×itemW 時，循環 buffer 右側需有內容）
            function ensureItems() {
                while (track.querySelectorAll('.bc-marquee__item').length < 3) {
                    var first = track.querySelectorAll('.bc-marquee__item')[0];
                    var clone = first.cloneNode(true);
                    track.appendChild(clone);
                }
                items = track.querySelectorAll('.bc-marquee__item');
            }
            ensureItems();

            function measure() {
                itemW = items[0].getBoundingClientRect().width;
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
                // 循環 buffer：第一個 item 完全移出視窗 → 移到尾端（環形連續）
                if (x <= -itemW) {
                    track.appendChild(items[0]);
                    items = track.querySelectorAll('.bc-marquee__item');
                    x += itemW;        // 補償位移 → 視覺位置不變
                    measure();
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