/* ============================================================
   bc-top-concept.js — hakujuji topConcept 整合（about.html）
   - 100% 複製 top.js 的 wrapCharSpan：每行文字逐字元包 <span>
   - 動畫與原站一致：scroll-scrub 逐字點亮
     ScrollTrigger: trigger .bc-top-concept, start 'top 60%',
     end 'bottom 50%', scrub 0.2；捲動時已過字元 opacity 1、
     未過字元 opacity 0.4（原站 top.js 完全相同邏輯）
   - 桌面/行動版本選擇依 CSS 斷點（≤767px）一致
   - GSAP defer 時序保護沿用 bc-attract.js 輪詢模式
   ============================================================ */
(function () {
    "use strict";

    var sec = document.querySelector(".bc-top-concept");
    if (!sec) return;

    // ---- 逐字元包 <span>（複製 hakujuji top.js wrapCharSpan）----
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

    var copyEls = sec.querySelectorAll(".csBlock__leaderTarget--text--p");
    Array.prototype.forEach.call(copyEls, function (p) {
        p.innerHTML = wrapCharSpan(p.textContent);
    });

    // 依 viewport 選擇可見版本的字元（與 CSS 斷點 767px 一致）
    var isSp = window.innerWidth <= 767;
    var selector = isSp
        ? ".partsSp .csBlock__leaderTarget--text--p span"
        : ".partsPc .csBlock__leaderTarget--text--p span";
    var conceptText = sec.querySelectorAll(selector);
    if (!conceptText.length) return;

    // 每個字元在 scrub 範圍內佔的進度百分比（原站 top.js 相同公式）
    var conceptNum = 100 / conceptText.length;

    function revealAll() {
        // 降級：無法建立 ScrollTrigger 時直接全部點亮
        Array.prototype.forEach.call(conceptText, function (span) {
            span.style.opacity = 1;
        });
    }

    function init() {
        if (!window.gsap) {
            setTimeout(init, 100);
            return;
        }
        if (!window.ScrollTrigger) {
            window.gsap.registerPlugin(window.ScrollTrigger);
        }
        if (!window.ScrollTrigger) {
            revealAll();
            return;
        }
        window.ScrollTrigger.create({
            trigger: sec,
            start: "top 60%",
            end: "bottom 50%",
            scrub: 0.2,
            invalidateOnRefresh: true,
            onUpdate: function (st) {
                // 原站 top.js：numElm = floor(progress*100/conceptNum) - 1
                var numElm = Math.floor((st.progress * 100) / conceptNum) - 1;
                for (var n = 0; n <= numElm; n++) {
                    if (conceptText[n]) conceptText[n].style.opacity = 1;
                }
                for (var m = numElm + 1; m < conceptText.length; m++) {
                    if (conceptText[m]) conceptText[m].style.opacity = 0.4;
                }
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
