/* ============================================================
   bc-capabilities.js — About 頁面 sukima capabilities-gallery scroll scrub
   完全複製 sukima.tokyo.jp 的 setupCapabilitiesAnimation（GSAP ScrollTrigger）：
   - cgi-left/right 團隊照片初始位移 → scroll 前段（0-30%）歸位 + y 微移
   - capabilities-anim-char 36 幀逐幀切換（visibility，中段 30-80%）
   - surprise-anim-svg reveal-brush dashoffset 305→0（後段 80-100%）
   - 反向滾動重置（frame-1 + brush 305 + cgi 回復位）
   未引入 GSAP，使用原生 scroll + rAF。
   ============================================================ */
(function () {
    "use strict";

    function initCapabilities() {
        var wrapper = document.querySelector(".bc-capabilities");
        if (!wrapper) {
            return;
        }
        var gallery = wrapper.querySelector(".capabilities-gallery");
        var left = wrapper.querySelector(".cgi-left");
        var right = wrapper.querySelector(".cgi-right");
        var brush = wrapper.querySelector(".surprise-anim-svg .reveal-brush");
        var frames = Array.prototype.slice.call(wrapper.querySelectorAll(".capabilities-anim-char .anim-frame"));
        if (!gallery || !left || !right || !brush || !frames.length) {
            return;
        }

        // 響應式位移量（原站 c()：1920/834/base）
        function getOffset() {
            var w = window.innerWidth;
            return w >= 1920 ? { left: 24, right: -24 } : w >= 834 ? { left: 18, right: -17 } : { left: 10, right: -9 };
        }
        var m = getOffset();

        // 初始狀態（原站 u.set）
        left.style.transform = "translate3d(" + m.left + "px, 0, 0)";
        right.style.transform = "translate3d(" + m.right + "px, 0, 0)";
        brush.style.strokeDashoffset = "305";
        frames.forEach(function (f, i) {
            f.style.visibility = i === 0 ? "visible" : "hidden";
        });

        var ticking = false;
        function update() {
            ticking = false;
            var rect = gallery.getBoundingClientRect();
            var vh = window.innerHeight;
            var h = rect.height;
            // 範圍：進入視口（rect.top=vh）→ 完全通過（rect.top=-h）
            var p = (vh - rect.top) / (h + vh);
            p = Math.max(0, Math.min(1, p));

            // 分段（2026-08-25 使用者要求「！動畫消失」）：
            // - cgi 照片左右歸位：0.10-0.32
            // - frame 36 幀動畫：0.32-0.44
            // - brush「！」閃電：0.44-0.60 快速畫線完成（原 0.44-1 太長，
            //   使用者滾到 capabilities 頂部時「！」幾乎未顯示）
            var cgiStart = 0.10, cgiEnd = 0.32;
            var frameStart = 0.32, frameEnd = 0.44;
            var brushStart = 0.44, brushEnd = 0.60;

            // cgi 歸位：延遲開始（p < cgiStart 保持位移，cgiStart→cgiEnd 歸位）
            if (p <= cgiStart) {
                left.style.transform = "translate3d(" + m.left + "px, 0, 0)";
                right.style.transform = "translate3d(" + m.right + "px, 0, 0)";
            } else if (p <= cgiEnd) {
                var g = (cgiEnd - cgiStart) > 0 ? (p - cgiStart) / (cgiEnd - cgiStart) : 0;
                left.style.transform = "translate3d(" + (m.left * (1 - g)) + "px, 0, 0)";
                right.style.transform = "translate3d(" + (m.right * (1 - g)) + "px, 0, 0)";
            } else {
                left.style.transform = "translate3d(0, 0, 0)";
                right.style.transform = "translate3d(0, 0, 0)";
            }

            // 中段：36 幀逐幀切換（加快）；後段保持最後一幀
            if (p >= frameEnd) {
                frames.forEach(function (f, v) {
                    f.style.visibility = v === frames.length - 1 ? "visible" : "hidden";
                });
            } else if (p >= frameStart) {
                var g2 = (frameEnd - frameStart) > 0 ? (p - frameStart) / (frameEnd - frameStart) : 0;
                var L = Math.min(Math.floor(g2 * frames.length), frames.length - 1);
                frames.forEach(function (f, v) {
                    f.style.visibility = v === L ? "visible" : "hidden";
                });
            } else {
                // 前段：維持 frame-1
                frames.forEach(function (f, v) {
                    f.style.visibility = v === 0 ? "visible" : "hidden";
                });
            }

            // 後段：「！」reveal-brush 畫線（0.44-0.60 快速完成）
            if (p >= brushEnd) {
                brush.style.strokeDashoffset = "0";
            } else if (p >= brushStart) {
                var g3 = (brushEnd - brushStart) > 0 ? (p - brushStart) / (brushEnd - brushStart) : 0;
                brush.style.strokeDashoffset = String(305 * (1 - g3));
            } else {
                brush.style.strokeDashoffset = "305";
            }
        }

        function onScroll() {
            if (!ticking) {
                ticking = true;
                requestAnimationFrame(update);
            }
        }
        function onResize() {
            m = getOffset();
            update();
        }
        window.addEventListener("scroll", onScroll, { passive: true });
        window.addEventListener("resize", onResize);
        update();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initCapabilities);
    } else {
        initCapabilities();
    }
})();
