/* ============================================================
   bc-who.js — About 頁面 sukima who section 滾動 scrub 動畫
   完全複製 sukima.tokyo.jp 的 setupWhoTextAnimation（GSAP
   ScrollTrigger scrub）：who section 進入視口時，依滾動進度
   逐字揭示（原站時間軸參數：元素間隔 0.5s、img/video scale
   延後 2.5s、circle 提前 1s），JS 直接設定元素屬性。
   - 未引入 GSAP，使用原生 scroll + rAF。
   - kicker 括號 (…) 為原站 CSS transition（.section.show
     觸發一次），由本檔 IO 加 .show。
   ============================================================ */
(function () {
    "use strict";

    function initWhoScrub() {
        var section = document.querySelector(".bc-who-section");
        if (!section) {
            return;
        }

        var spacer = section.querySelector(".wwa-first-spacer");
        var circleBrush = section.querySelector(".who-circle-svg .wwa-circle-brush");
        var arrowBrush = section.querySelector(".who-arrow-svg .reveal-brush-arrow-wwa");
        var video = section.querySelector(".wwa-visual-03 video");
        var videoPlayed = false;

        // 建構序列（原站 f 陣列邏輯；同元素重複出現時後者覆蓋）
        var itemsByEl = new Map();
        var idx = 0;
        function add(item) {
            itemsByEl.set(item.el, item);
            idx++;
        }
        if (spacer) {
            // 原站 dur=2s + lenis 平滑滾動；本地無 lenis，須拉長 dur。
            // 使用者持續要求「更慢」→ 40s（700px）→ 46s（=totalDur，
            // 縮排展開跨越 who 進入到滾完的整個 800px 過程）
            add({ type: "spacer", el: spacer, delay: idx * 0.5, dur: 46 });
        }
        section.querySelectorAll(".wwa-anim-char, .wwa-anim-visual, .sukima-anim-wwa, .video-anim-wwa")
            .forEach(function (r) {
                if (r.classList.contains("wwa-anim-char")) {
                    add({ type: "char", el: r, delay: idx * 0.5, dur: 0.3 });
                } else if (r.classList.contains("sukima-anim-wwa")) {
                    r.querySelectorAll(".wwa-anim-char").forEach(function (w) {
                        add({ type: "char", el: w, delay: idx * 0.5, dur: 0.3 });
                    });
                    if (circleBrush) {
                        add({ type: "circle", el: circleBrush, delay: idx * 0.5 - 1, dur: 1 });
                    }
                } else if (r.classList.contains("wwa-visual-01") || r.classList.contains("wwa-visual-02")) {
                    add({ type: "visual", el: r, delay: idx * 0.5, dur: 3 });
                    var img = r.querySelector("img");
                    if (img) {
                        add({ type: "img", el: img, delay: idx * 0.5 + 2.5, dur: 3 });
                    }
                } else if (r.classList.contains("video-anim-wwa")) {
                    r.querySelectorAll(".wwa-anim-char").forEach(function (w) {
                        add({ type: "char", el: w, delay: idx * 0.5, dur: 0.3 });
                    });
                    if (arrowBrush) {
                        add({ type: "arrow", el: arrowBrush, delay: idx * 0.5, dur: 1 });
                    }
                } else if (r.classList.contains("wwa-visual-03")) {
                    add({ type: "visual", el: r, delay: idx * 0.5, dur: 3 });
                    if (video) {
                        add({ type: "video", el: video, delay: idx * 0.5 + 2.5, dur: 3 });
                    }
                }
            });


        var items = Array.from(itemsByEl.values());
        var totalDur = items.reduce(function (m, it) {
            return Math.max(m, it.delay + it.dur);
        }, 0);

        // 讀取響應式目標寬度（CSS 變數，bc-who.css 依斷點設定）
        function getVar(name) {
            var v = getComputedStyle(section).getPropertyValue(name);
            return parseFloat(v) || 0;
        }
        function visualTarget(el) {
            return el.classList.contains("wwa-visual-03") ? getVar("--who-visual03-w") : getVar("--who-visual01-w");
        }

        // 初始狀態（與原站 JS 一致）
        if (spacer) {
            spacer.style.width = "0px";
        }
        if (video) {
            video.pause();
            video.currentTime = 0;
        }

        function easePower2Out(k) {
            return 1 - (1 - k) * (1 - k);
        }

        // GSAP ScrollTrigger scrub 平滑（原站 scrub:0.3）：
        // 動畫進度每幀向滾動目標逼近，滯後於滾動，讓 spacer 展開等
        // 前段動畫過程可感知（快速滾動不會瞬間跳過）
        var currentProgress = 0;
        var targetProgress = 0;
        var animating = false;

        function update() {
            currentProgress += (targetProgress - currentProgress) * 0.12;
            if (Math.abs(targetProgress - currentProgress) < 0.0005) {
                currentProgress = targetProgress;
            }
            var t = currentProgress * totalDur;

            items.forEach(function (it) {
                var k = Math.max(0, Math.min(1, (t - it.delay) / it.dur));
                switch (it.type) {
                    case "char":
                        it.el.style.opacity = String(0.5 + 0.5 * easePower2Out(k));
                        break;
                    case "spacer":
                        it.el.style.width = (getVar("--who-spacer-w") * easePower2Out(k)) + "px";
                        break;
                    case "visual":
                        it.el.style.width = (visualTarget(it.el) * easePower2Out(k)) + "px";
                        break;
                    case "img":
                        it.el.style.transform = "scale(" + easePower2Out(k) + ")";
                        break;
                    case "video":
                        it.el.style.transform = "scale(" + easePower2Out(k) + ")";
                        if (k >= 1 && !videoPlayed) {
                            videoPlayed = true;
                            video.play().catch(function () {});
                        } else if (k <= 0 && videoPlayed) {
                            videoPlayed = false;
                            video.pause();
                            video.currentTime = 0;
                        }
                        break;
                    case "circle":
                        it.el.style.strokeDashoffset = String(800 - (800 - 377) * easePower2Out(k));
                        break;
                    case "arrow":
                        it.el.style.strokeDashoffset = String(300 * (1 - easePower2Out(k)));
                        break;
                }
            });
        }

        function tick() {
            update();
            if (Math.abs(targetProgress - currentProgress) > 0.0005) {
                requestAnimationFrame(tick);
            } else {
                animating = false;
            }
        }

        function setTarget() {
            var rect = section.getBoundingClientRect();
            var vh = window.innerHeight;
            // 進度：section 頂部剛進視口底部（rect.top=vh）→ 0；
            //       section 頂部達視口頂部（rect.top=0）→ 1。
            // 使用者將 who 區塊滾到視口頂時，全部文字/圓圈/箭頭/影片完成
            targetProgress = (vh - rect.top) / vh;
            targetProgress = Math.max(0, Math.min(1, targetProgress));
            if (!animating) {
                animating = true;
                requestAnimationFrame(tick);
            }
        }

        function onScroll() {
            setTarget();
        }
        window.addEventListener("scroll", onScroll, { passive: true });
        window.addEventListener("resize", onScroll);
        setTarget();

        // kicker 括號（原站 .section-title.show CSS transition，進視口觸發一次）
        function showKicker() {
            if (section.classList.contains("show")) {
                return;
            }
            section.classList.add("show");
        }
        if (!("IntersectionObserver" in window)) {
            showKicker();
            return;
        }
        var rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            showKicker();
        }
        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        showKicker();
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );
        io.observe(section);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initWhoScrub);
    } else {
        initWhoScrub();
    }
})();
