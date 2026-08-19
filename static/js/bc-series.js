/* ============================================================
   bc-series.js — About 頁面 SERIES 滑桿（支援多組）
   - 滑鼠/觸控拖動滑桿（--js-x transform），
     標題 [data-blurred] 切換模糊。
   - 左右箭頭移動 --js-x。
   - .bc-series-bracket（第二組）：每張照片一格，鬆開時吸附到最近格。
   ============================================================ */
(function () {
    "use strict";

    var heros = document.querySelectorAll(".bc-series-hero");
    for (var h = 0; h < heros.length; h++) {
        initSlider(heros[h]);
    }

    function initSlider(hero) {
        var heading = hero.querySelector(".bc-series-heading");
        var scrolling = hero.querySelector(".bc-series-scrolling");
        var listContainer = hero.querySelector(".bc-series-list-container");
        if (!scrolling || !listContainer) {
            return;
        }

        var snap = hero.classList.contains("bc-series-bracket");

        function getJsX() {
            return parseFloat(listContainer.style.getPropertyValue("--js-x")) || 0;
        }

        function setJsX(x) {
            listContainer.style.setProperty("--js-x", x + "px");
        }

        function maxLeft() {
            var list = scrolling.querySelector(".bc-series-list");
            if (!list) return -10000;
            if (snap) {
                // 每張照片一格：允許最後一張照片居中（一格一步）
                var slides = scrolling.querySelectorAll(".bc-series-slide");
                return -(slides.length - 1) * stepSize();
            }
            var hw = heading ? heading.getBoundingClientRect().width : 0;
            return Math.min(0, hero.clientWidth - hw - list.scrollWidth);
        }

        function stepSize() {
            var slide = scrolling.querySelector(".bc-series-slide");
            if (!slide) return 350;
            var gap = parseFloat(getComputedStyle(slide).marginRight) || 0;
            return slide.offsetWidth + gap;
        }

        function syncBlur() {
            if (!heading) return;
            heading.setAttribute("data-blurred", getJsX() < -2 ? "true" : "false");
        }

        // 左右箭頭
        var arrows = hero.querySelectorAll(".bc-series-arrow");
        for (var i = 0; i < arrows.length; i++) {
            (function (btn) {
                btn.addEventListener("click", function () {
                    var dir = btn.getAttribute("data-direction") === "left" ? -1 : 1;
                    var nx = Math.max(maxLeft(), Math.min(0, getJsX() + dir * stepSize()));
                    setJsX(nx);
                    syncBlur();
                });
            })(arrows[i]);
        }

        // 拖動
        var isDragging = false;
        var startX = 0;
        var startJsX = 0;

        scrolling.addEventListener("pointerdown", function (e) {
            isDragging = true;
            startX = e.clientX;
            startJsX = getJsX();
            try {
                scrolling.setPointerCapture(e.pointerId);
            } catch (err) {}
            scrolling.classList.add("bc-series-dragging");
            scrolling.style.cursor = "grabbing";
            e.preventDefault();
        });

        window.addEventListener("pointermove", function (e) {
            if (!isDragging) return;
            var dx = e.clientX - startX;
            var nx = Math.max(maxLeft(), Math.min(0, startJsX + dx));
            setJsX(nx);
            syncBlur();
        });

        window.addEventListener("pointerup", function () {
            if (!isDragging) return;
            isDragging = false;
            scrolling.classList.remove("bc-series-dragging");
            scrolling.style.cursor = "grab";
            if (snap) {
                // 每張照片一格：鬆開時依拖動方向移動「一格」（下一張/上一張），未達門檻回彈
                var step = stepSize();
                var dx = getJsX() - startJsX;
                var threshold = step * 0.2;
                var nx;
                if (dx < -threshold) {
                    nx = startJsX - step;
                } else if (dx > threshold) {
                    nx = startJsX + step;
                } else {
                    nx = startJsX;
                }
                nx = Math.max(maxLeft(), Math.min(0, nx));
                setJsX(nx);
                syncBlur();
            }
        });

        scrolling.style.cursor = "grab";
        syncBlur();
    }
})();
