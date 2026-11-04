/* ============================================================
   bc-home-service.js — 首頁「咖啡豆製程」捲動模組（union-tec homeService 移植）
   2026-10-30 建立
   ------------------------------------------------------------------
   原站是什麼：
     section[x-data="homeService"]（Alpine）＋ Lenis 平滑捲動
     ＋ three.js 網格（PC）＋ GSAP MorphSVG。本檔以原生 JS 重寫，
     不引入 Alpine／GSAP／three.js（本站沒有，也不想為一區塊加入）。
   本模組做五件事（數值全部取自原站 bundle，非估算）：
     1) clip-path 膠囊放大 → 滿版
        enterScaleP = lerp(本身, easeInCirc(clamp01(invLerp(0.5,1,bgScrollP))), 0.15)
        每幀逼近（這是原站「滑順感」的來源，不是直接對應捲動量）。
        clipScale = lerp(minScale, maxCoverScale, enterScaleP)
        minScale：PC 463/1440 = 0.32153、SP 217/400 = 0.5425
        maxCoverScale：64 次二分搜尋 + SVGPathElement.isPointInFill（路徑四角
        都被填滿時的最小 scale），任何視窗比例都能「剛好滿版」。
        transform＝translate(0 0) translate(.5 .5) scale(sx, sx*yFactor)
                   translate(-.5 -.5) scale(1/463, 1/320)；yFactor＝vw*320/(vh*463)
     2) 影像輪播 3000ms、交叉淡入 800ms（.is-in／.is-out／.is-appearing），
        is-in 同時觸發 CSS 的 Ken Burns（transform 6s linear，1.04 → 1）
     3) 開場模糊→清晰：cover 與 -blur 圖 opacity = clamp01(invLerp(.75,1,bgScrollP))
     4) 收尾：leaveScrollP 讓背景上移 30%、放大到 1.25，右上小膠囊淡入
     5) 左側標籤 aria-current 跟著輪播切換（圓點放大 + 文字內縮 25/51px）；
        網格字母矩陣 1000ms tick、`(col*7 + row*13 + step) % len` 斜向波紋
        （原站 PC 用 three.js canvas；此處改 CSS 細線 + DOM 字母，
          與原站手機版同一套 DOM fallback 手法）
   效能：rAF 只在「捲動中且 enterScaleP 尚未收斂」時跑，收斂即停；
         輪播用 setTimeout（離開視窗／分頁隱藏會暫停並記住剩餘時間）。
   ============================================================ */
(function () {
    "use strict";

    var ROOT_SELECTOR = "[data-bc-home-service]";
    var SVG_NS = "http://www.w3.org/2000/svg";

    var PATH_SIZE = { width: 463, height: 320 }; // 原站 C9
    var MIN_SCALE_PC = 463 / 1440; // 原站 P9
    var MIN_SCALE_SP = 217 / 400; // 原站 A9
    var PC_MIN_WIDTH = 1024; // 原站 pc: = 64rem

    var ENTER_LERP = 0.15;
    var LEAVE_MAX_SCALE = 1.25;
    var LEAVE_MAX_TRANSLATE_Y = 30;
    var TIMER_DURATION = 3000;
    var HANDOVER_DELAY = 800;

    var LETTER_TEXT = "BETWEENCOFFEEBREWTHEMOMENTS";
    var LETTER_TICK = 1000;
    var LETTER_COEF_COL = 7;
    var LETTER_COEF_ROW = 13;

    // ---- 數學（對應原站 bn／pt／Pt／easeInCirc／easeOutSine） ----
    function clamp01(v) {
        return v < 0 ? 0 : v > 1 ? 1 : v;
    }
    function lerp(a, b, t) {
        return a + (b - a) * t;
    }
    function invLerp(a, b, v) {
        return a === b ? 0 : (v - a) / (b - a);
    }
    function easeInCirc(x) {
        return 1 - Math.sqrt(Math.max(0, 1 - x * x));
    }
    function easeOutSine(x) {
        return Math.sin((x * Math.PI) / 2);
    }

    // 錨點：頂端碰到視窗底部（0）→ 頂端碰到視窗頂部（1）
    function topProgress(el) {
        var vh = window.innerHeight || 1;
        return clamp01(1 - el.getBoundingClientRect().top / vh);
    }
    // 一般元素：進入視窗（0）→ 完全離開視窗頂部（1）
    function scrollProgress(el) {
        var vh = window.innerHeight || 1;
        var rect = el.getBoundingClientRect();
        var h = rect.height || 1;
        return clamp01((vh - rect.top) / (vh + h));
    }


    /* ------------------------------------------------------------
       clip-path 控制器（對應原站 Cn + P4 + M6 + so + S6 + A4）
       ------------------------------------------------------------ */
    function createClipController(pathEl, viewportEl) {
        var ghostSvg = document.createElementNS(SVG_NS, "svg");
        ghostSvg.style.cssText = "position:absolute;width:0;height:0;overflow:hidden;pointer-events:none;";
        var ghostPath = document.createElementNS(SVG_NS, "path");
        ghostSvg.appendChild(ghostPath);
        document.body.appendChild(ghostSvg);

        var maxCover = 1;

        function yFactor(vw, vh) {
            return (vw * PATH_SIZE.height) / (Math.max(vh, 1) * PATH_SIZE.width);
        }

        // 四個角都被填滿的最小 scale（原站 M6：先倍增找上界，再 64 次二分）
        function computeMaxCover(vw, vh) {
            var W = PATH_SIZE.width;
            var H = PATH_SIZE.height;
            var yf = yFactor(vw, vh);
            var corners = [[0, 0], [1, 0], [1, 1], [0, 1]];

            function covers(k) {
                if (!(k > 0)) return false;
                for (var i = 0; i < corners.length; i++) {
                    var px = W * ((corners[i][0] - 0.5) / k + 0.5);
                    var py = H * ((corners[i][1] - 0.5) / (k * yf) + 0.5);
                    var inside = false;
                    try {
                        inside = ghostPath.isPointInFill(new DOMPoint(px, py));
                    } catch (e) {
                        inside = false;
                    }
                    if (!inside) return false;
                }
                return true;
            }

            var hi = 1e-6;
            var guard = 0;
            while (!covers(hi) && hi < 1e9 && guard++ < 48) hi *= 2;
            if (!covers(hi)) return hi;
            var lo = 1e-9;
            if (covers(lo)) return lo;
            for (var n = 0; n < 64; n++) {
                var mid = (lo + hi) / 2;
                if (covers(mid)) hi = mid;
                else lo = mid;
            }
            return hi;
        }

        function refresh() {
            ghostPath.setAttribute("d", pathEl.getAttribute("d") || "");
            var vw = viewportEl.clientWidth || window.innerWidth;
            var vh = viewportEl.clientHeight || window.innerHeight;
            maxCover = Math.max(computeMaxCover(vw, vh), 1);
        }

        function apply(t) {
            var vw = viewportEl.clientWidth || window.innerWidth;
            var vh = viewportEl.clientHeight || window.innerHeight;
            var minScale = window.innerWidth >= PC_MIN_WIDTH ? MIN_SCALE_PC : MIN_SCALE_SP;
            var k = lerp(minScale, maxCover, clamp01(t));
            var yf = yFactor(vw, vh);
            // 原站 A4：scaleValue 先換成像素座標系（×vw/W），S6→so 再換回 bbox 單位，
            // 來回換算後 scaleX 恆等於 k（＝膠囊寬度 k×vw 像素）。此處照抄這個往返，
            // 避免兩套座標系混用（少乘 vw/W 的話整個膠囊會小 3.1 倍）。
            var u = k * (vw / PATH_SIZE.width);
            var scaleX = Math.max(
                (u * PATH_SIZE.width) / Math.max(vw, 1),
                ((u * PATH_SIZE.height) / Math.max(vh, 1)) / Math.max(yf, 1e-6)
            );
            pathEl.setAttribute(
                "transform",
                "translate(0 0) translate(0.5 0.5) scale(" + scaleX + " " + scaleX * yf + ") " +
                "translate(-0.5 -0.5) scale(" + 1 / PATH_SIZE.width + " " + 1 / PATH_SIZE.height + ")"
            );
        }

        refresh();
        return { refresh: refresh, apply: apply };
    }

    /* ------------------------------------------------------------
       網格字母矩陣（對應原站 w9；cell 尺寸與 CSS --hs-cell 同源）
       ------------------------------------------------------------ */
    function createLetterGrid(container) {
        var pool = [];
        var cols = 0;
        var rows = 0;
        var startTime = performance.now();
        var baseStep = 0;

        function cellSize() {
            return window.innerWidth >= PC_MIN_WIDTH
                ? (window.innerWidth * 12.222) / 100
                : (window.innerWidth * 24) / 100;
        }

        function cycle() {
            var len = LETTER_TEXT.length;
            if (!cols) return;
            for (var i = 0; i < pool.length; i++) {
                var col = i % cols;
                var row = Math.floor(i / cols);
                var offset = (col * LETTER_COEF_COL + row * LETTER_COEF_ROW) % len;
                pool[i].textContent = LETTER_TEXT[(baseStep + offset) % len];
            }
        }

        function rebuild() {
            var cell = cellSize();
            if (!isFinite(cell) || cell <= 0) return;
            var nextCols = Math.ceil(window.innerWidth / cell) + 2;
            var nextRows = Math.ceil(document.documentElement.clientHeight / cell) + 2;
            if (nextCols === cols && nextRows === rows) return;

            var total = nextCols * nextRows;
            while (pool.length < total) {
                var span = document.createElement("span");
                span.className = "letter";
                container.appendChild(span);
                pool.push(span);
            }
            while (pool.length > total) {
                var extra = pool.pop();
                if (extra && extra.parentNode) extra.parentNode.removeChild(extra);
            }
            cols = nextCols;
            rows = nextRows;
            for (var i = 0; i < total; i++) {
                pool[i].style.setProperty("--col", String(i % cols));
                pool[i].style.setProperty("--row", String(Math.floor(i / cols)));
            }
            cycle();
        }

        rebuild();
        window.setInterval(function () {
            if (document.hidden) return;
            baseStep = Math.floor((performance.now() - startTime) / LETTER_TICK);
            cycle();
        }, LETTER_TICK);

        return { rebuild: rebuild };
    }
    /* ------------------------------------------------------------
       初始化（對應原站 $1.data("homeService", ...)）
       ------------------------------------------------------------ */
    function initHomeService() {
        var root = document.querySelector(ROOT_SELECTOR);
        if (!root) return;

        var el = {
            anchor: root.querySelector("[data-hs-anchor]"),
            bg: root.querySelector("[data-hs-bg]"),
            bgItems: root.querySelector("[data-hs-items]"),
            media: root.querySelectorAll(".bc-hs__media"),
            blurImgs: root.querySelectorAll(".bc-hs__img-blur"),
            cover: root.querySelector("[data-hs-cover]"),
            clipContainer: root.querySelector("[data-hs-clip-images]"),
            clipImages: root.querySelectorAll(".bc-hs__clip-image"),
            labels: root.querySelectorAll("[data-hs-label]"),
            letters: root.querySelector("[data-hs-letters]"),
            leave: root.querySelector("[data-hs-leave]"),
            clipPath: root.querySelector("[data-hs-clip-path]")
        };
        if (!el.anchor || !el.bg || !el.bgItems || !el.leave || !el.clipPath || !el.cover) return;
        if (el.media.length < 2 || el.clipImages.length < 2) return;

        var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var controller = createClipController(el.clipPath, el.bg);
        var letterGrid = el.letters ? createLetterGrid(el.letters) : null;

        // 原站狀態物件（t.*）
        var enterScaleP = 0;
        var inView = false;

        // 輪播（原站 m0：loop、duration 3000、onComplete 換圖）
        var timerIndex = 0;
        var tickHandle = 0;
        var tickRemaining = TIMER_DURATION;
        var tickStartedAt = 0;
        var lastCycleAt = 0;

        function updateLabels() {
            for (var i = 0; i < el.labels.length; i++) {
                el.labels[i].setAttribute("aria-current", i === timerIndex ? "true" : "false");
            }
        }

        function cycleTo(next) {
            // 防連發：暫停／恢復（離開視窗、分頁切換）時剩餘時間可能趨近 0，
            // 造成兩次換圖間隔 < 800ms（交叉淡入還沒結束）。最短間隔＝交接時間。
            var now = performance.now();
            if (now - lastCycleAt < HANDOVER_DELAY) return;
            lastCycleAt = now;

            var current = timerIndex;
            var nextMedia = el.media[next];
            var currentMedia = el.media[current];
            var nextClip = el.clipImages[next];
            var currentClip = el.clipImages[current];

            if (nextMedia && currentMedia) {
                nextMedia.classList.remove("is-out");
                nextMedia.classList.add("is-in", "is-appearing");
                window.setTimeout(function () {
                    currentMedia.classList.remove("is-in");
                    currentMedia.classList.add("is-out");
                    nextMedia.classList.remove("is-appearing");
                }, HANDOVER_DELAY);
            }
            if (nextClip && currentClip) {
                nextClip.classList.remove("is-out");
                nextClip.classList.add("is-in", "is-appearing");
                window.setTimeout(function () {
                    currentClip.classList.remove("is-in");
                    currentClip.classList.add("is-out");
                    nextClip.classList.remove("is-appearing");
                }, HANDOVER_DELAY);
            }
            timerIndex = next;
            updateLabels();
        }

        function scheduleTick(ms) {
            window.clearTimeout(tickHandle);
            tickRemaining = Math.max(0, ms);
            tickStartedAt = performance.now();
            tickHandle = window.setTimeout(function () {
                tickHandle = 0;
                cycleTo((timerIndex + 1) % el.media.length);
                scheduleTick(TIMER_DURATION);
            }, tickRemaining);
        }

        function pauseTicker() {
            if (!tickHandle) return;
            window.clearTimeout(tickHandle);
            tickHandle = 0;
            tickRemaining = Math.max(0, tickRemaining - (performance.now() - tickStartedAt));
        }

        function resumeTicker() {
            if (tickHandle || !inView || document.hidden) return;
            scheduleTick(tickRemaining);
        }

        /* ---- 主要渲染（原站 nn 的 callback） ---- */
        var rafId = 0;

        function render() {
            var bgScrollP = topProgress(el.anchor);
            var leaveScrollP = scrollProgress(el.leave);

            // 1) 膠囊 → 滿版（easeInCirc + 每幀 lerp）
            var target = easeInCirc(clamp01(invLerp(0.5, 1, bgScrollP)));
            enterScaleP = reduceMotion ? target : enterScaleP + (target - enterScaleP) * ENTER_LERP;
            controller.apply(enterScaleP);

            // 2) 模糊 → 清晰（cover 與 -blur 圖同步）
            var dark = clamp01(invLerp(0.75, 1, bgScrollP));
            el.cover.style.opacity = String(dark);
            for (var i = 0; i < el.blurImgs.length; i++) {
                el.blurImgs[i].style.opacity = String(dark);
            }

            // 3) 收尾：右上小膠囊淡入
            if (el.clipContainer) {
                el.clipContainer.classList.toggle("is-in", leaveScrollP > 0);
            }

            // 4) 收尾：背景上移 30%、放大到 1.25
            var leaveYP = clamp01(invLerp(0.5, 1, leaveScrollP));
            var leaveY = leaveYP * LEAVE_MAX_TRANSLATE_Y;
            var leaveScaleP = easeOutSine(clamp01(invLerp(0, 1, leaveScrollP)));
            var leaveScale = 1 + leaveScaleP * (LEAVE_MAX_SCALE - 1);
            el.bgItems.style.transform =
                "translate3d(0, " + leaveY + "%, 0) scale(" + leaveScale + ")";

            return Math.abs(target - enterScaleP) > 0.0005;
        }

        function frame() {
            rafId = 0;
            if (!render()) return; // 收斂即停（滾動／resize 會再啟動）
            rafId = window.requestAnimationFrame(frame);
        }

        function requestFrame() {
            if (!rafId) rafId = window.requestAnimationFrame(frame);
        }



        /* ---- 事件：捲動 / resize / 可視範圍 / 分頁隱藏 ---- */
        function onScroll() {
            requestFrame();
            resumeTicker();
        }

        var resizeHandle = 0;
        function onResize() {
            window.clearTimeout(resizeHandle);
            resizeHandle = window.setTimeout(function () {
                controller.refresh();
                if (letterGrid) letterGrid.rebuild();
                render();
            }, 120);
        }

        function onVisibilityChange() {
            if (document.hidden) {
                pauseTicker();
                return;
            }
            resumeTicker();
            requestFrame();
        }

        // 可視範圍：進入 → 開始輪播；離開 → 暫停（原站 IntersectionObserver 同邏輯）
        if (typeof window.IntersectionObserver === "function") {
            var observer = new IntersectionObserver(
                function (entries) {
                    var entry = entries[0];
                    inView = !!(entry && entry.isIntersecting);
                    if (inView) {
                        resumeTicker();
                        requestFrame();
                        render();
                    } else {
                        pauseTicker();
                    }
                },
                { root: null, rootMargin: "0px", threshold: 0 }
            );
            observer.observe(root);
        } else {
            inView = true;
            resumeTicker();
        }

        window.addEventListener("scroll", onScroll, { passive: true });
        window.addEventListener("resize", onResize);
        document.addEventListener("visibilitychange", onVisibilityChange);

        // 初始狀態：第一張 is-in（markup 已帶，這裡確保 JS 也會設定）
        if (el.media[0]) el.media[0].classList.add("is-in");
        updateLabels();
        render();
    }

    function boot() {
        try {
            initHomeService();
        } catch (err) {
            // 模組失敗不可影響首頁其他區塊：僅記錄，背景維持第一張靜態圖
            if (window.console && console.warn) console.warn("[bc-home-service]", err);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
