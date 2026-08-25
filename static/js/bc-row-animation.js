/* ============================================================
   bc-row-animation.js — About 頁面 sukima row-animation video scrub
   完全複製 sukima.tokyo.jp 的 videoScrubber 機制（GSAP ScrollTrigger）：
   - ScrollTrigger start "top 90%"（頂部對齊視口 90%）→
     end "bottom 25%"（底部對齊視口 25%）、scrub 0.2 平滑
   - video.currentTime = 進度 × duration（30fps 節流，可前進/後退）
   - 進入視口前 preload（原站 preloadVideo）
   ⚠️ 適配：Django dev server 不支援 Range 請求，直接 <source> 載入會
   導致 video seek（currentTime）失敗（moov 在尾部 + 無 Range）→ 改用
   fetch → Blob 載入（完全在記憶體，seek 可靠），所有環境通用。
   未引入 GSAP，使用原生 scroll + rAF。
   ============================================================ */
(function () {
    "use strict";

    function initRowAnimation() {
        var wrapper = document.querySelector(".bc-row-animation");
        var video = document.querySelector(".row-animation__video");
        if (!wrapper || !video) {
            return;
        }

        // 取得影片來源
        var src = "";
        var sourceEl = video.querySelector("source");
        if (sourceEl && sourceEl.src) {
            src = sourceEl.src;
        } else if (video.getAttribute("src")) {
            src = video.getAttribute("src");
        }

        // 初始狀態（原站 videoScrubber.add 行為）
        video.pause();
        video.currentTime = 0;
        video.setAttribute("muted", "");
        video.setAttribute("playsinline", "");
        video.removeAttribute("autoplay");

        var FRAME = 1 / 30; // 30fps 節流（原站 frameRate:30）
        var currentProgress = 0;
        var targetProgress = 0;
        var animating = false;
        var duration = 0;
        var started = false;

        function setFrame(progress) {
            if (!duration || isNaN(duration) || duration <= 0) {
                duration = video.duration;
                if (isNaN(duration) || duration <= 0) {
                    return;
                }
            }
            var t = progress * duration;
            if (Math.abs(video.currentTime - t) > FRAME) {
                video.currentTime = t;
            }
        }

        function tick() {
            // scrub 平滑（原站 scrub:0.2 → 每幀逼近 20%）
            currentProgress += (targetProgress - currentProgress) * 0.2;
            if (Math.abs(targetProgress - currentProgress) < 0.001) {
                currentProgress = targetProgress;
            }
            setFrame(currentProgress);
            if (Math.abs(targetProgress - currentProgress) > 0.001) {
                requestAnimationFrame(tick);
            } else {
                animating = false;
            }
        }

        function setTarget() {
            var rect = wrapper.getBoundingClientRect();
            var vh = window.innerHeight;
            var h = rect.height;
            // start "top 90%"：元素頂部對齊視口 90% → rect.top = 0.9*vh
            // end "bottom 25%"：元素底部對齊視口 25% → rect.top = 0.25*vh - h
            var startTop = 0.9 * vh;
            var endTop = 0.25 * vh - h;
            var denom = startTop - endTop; // 0.65*vh + h
            targetProgress = denom > 0 ? (startTop - rect.top) / denom : 0;
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

        // 等 video metadata 載入取得 duration（原站等待邏輯）
        function startScrub() {
            if (started) {
                return;
            }
            started = true;
            function initFrame() {
                duration = video.duration;
                if (isNaN(duration) || duration <= 0) {
                    return;
                }
                setTarget();
            }
            if (video.readyState >= 1) {
                initFrame();
            } else {
                video.addEventListener("loadedmetadata", function () {
                    initFrame();
                });
            }
        }

        // Blob 載入：Django dev server 不支援 Range，直接 <source> 會導致
        // seek 失敗 → fetch 整個影片到記憶體（452KB）後用 Blob URL 播放，
        // seek 不需伺服器支援，所有環境通用
        function loadAsBlob() {
            if (!src) {
                startScrub();
                return;
            }
            fetch(src)
                .then(function (r) {
                    return r.arrayBuffer();
                })
                .then(function (buf) {
                    var blob = new Blob([buf], { type: "video/mp4" });
                    video.src = URL.createObjectURL(blob);
                    video.preload = "auto";
                    startScrub();
                })
                .catch(function () {
                    // fallback：直接使用原始 source（生產 nginx 支援 Range 時亦可）
                    video.src = src;
                    video.preload = "auto";
                    startScrub();
                });
        }

        loadAsBlob();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initRowAnimation);
    } else {
        initRowAnimation();
    }
})();

