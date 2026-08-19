/* ============================================================
   bc-leader.js — hakujuji csBlock__leader 整合（about.html）
   - 100% 複製 concept.js 的 wrapCharSpan：每行文字逐字元包 <span>
   - 動畫效果與原站一致：逐字 opacity 0.3 → 1（stagger 0.02s）
   - 以 ScrollTrigger（once）在區塊進入視窗時觸發，確保使用者看得到；
     原站 ScrollTrigger 版本已註解、只保留載入觸發，但本區塊位於
     about 頁下方，載入觸發將無法觀看到動畫，故採用進入視窗觸發。
   ============================================================ */
(function () {
    "use strict";

    var leader = document.querySelector(".bc-leader");
    if (!leader) return;

    // ---- 逐字元包 <span>（複製 hakujuji concept.js wrapCharSpan）----
    function wrapCharSpan(html) {
        return html.split(/(<br\s*\/?>)/i).map(function (part) {
            if (/<br\s*\/?>/i.test(part)) return part;
            return Array.from(part).map(function (char) {
                // 「ー」加 tb-elm class（原站邏輯，中文文案用不到但保留）
                var cls = char === "\u30FC" ? ' class="tb-elm"' : "";
                return "<span" + cls + ">" + char + "</span>";
            }).join("");
        }).join("");
    }

    var copyEls = leader.querySelectorAll(".csBlock__leaderTarget--text--p");
    Array.prototype.forEach.call(copyEls, function (p) {
        p.innerHTML = wrapCharSpan(p.textContent);
    });

    // 依 viewport 選擇可見版本的字元（與 CSS 斷點 767px 一致）
    var isSp = window.innerWidth <= 767;
    var selector = isSp
        ? ".partsSp .csBlock__leaderTarget--text--p span"
        : ".partsPc .csBlock__leaderTarget--text--p span";
    var conceptText = leader.querySelectorAll(selector);
    if (!conceptText.length) return;

    function reveal() {
        window.gsap.to(conceptText, {
            opacity: 1,
            ease: "power2.inOut",
            duration: 0.1,
            stagger: { each: 0.02 }
        });
    }

    // ---- 初始化（GSAP defer 時序保護，沿用 bc-attract.js 的輪詢模式）----
    function init() {
        if (!window.gsap) {
            setTimeout(init, 100);
            return;
        }
        if (window.ScrollTrigger) {
            window.gsap.registerPlugin(window.ScrollTrigger);
            window.gsap.to(conceptText, {
                opacity: 1,
                ease: "power2.inOut",
                duration: 0.1,
                stagger: { each: 0.02 },
                scrollTrigger: {
                    trigger: leader,
                    start: "top 85%",
                    once: true
                }
            });
        } else {
            reveal();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
