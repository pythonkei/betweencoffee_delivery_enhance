/* ============================================================
   bc-series.js — About 頁面 SERIES 滑桿（支援多組）
   - 滑鼠/觸控拖動滑桿（--js-x transform），
     標題 [data-blurred] 切換模糊。
   - 左右箭頭移動 --js-x。
   - .bc-series-bracket（第二組）：每張照片一格，鬆開時吸附到最近格。
   - 2026-11-02：項目改為 <a href> 商品詳情頁連結 → 拖曳位移超過 8px 時
     攔掉那次 click（避免轉滑桿時誤觸導頁）。
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
                    // 2026-10-28 修正：方向改回一般輪播慣例（原本寫反，左鈕其實在往前推、右鈕在退回）
                    //   左箭頭 data-direction="left"／aria-label="Prev" ＝ 上一張 → --js-x 往 0 增加
                    //   右箭頭 data-direction="right"／aria-label="Next" ＝ 下一張 → --js-x 往負值減少
                    //   （照片本身是往左推，所以「下一張」才對應負值；拖曳方向不受影響）
                    var dir = btn.getAttribute("data-direction") === "left" ? 1 : -1;
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
        // 2026-11-02：.bc-series-item 加上詳情頁連結後，拖曳放手不能誤觸導頁
        // → 位移超過 8px 就算拖曳，該次 click 直接吃掉（capture 階段攔）。
        var dragStartClientX = 0;
        var dragMoved = false;
        var DRAG_CLICK_TOLERANCE = 8;

        scrolling.addEventListener("pointerdown", function (e) {
            isDragging = true;
            startX = e.clientX;
            startJsX = getJsX();
            dragStartClientX = e.clientX;
            dragMoved = false;
            scrolling.classList.add("bc-series-dragging");
            scrolling.style.cursor = "grabbing";
            // 2026-11-02：不再 e.preventDefault()／setPointerCapture()
            //   preventDefault 會讓外層 <a> 的 click 無法完成導頁；
            //   capture 會把 click 的 target 換成 scrolling（同樣導不了頁）。
            //   原生拖曳改由 bc-series.css 的 .bc-series-picture > img{pointer-events:none}
            //   與 .bc-series-slide{user-select:none;touch-action:none} 壓住，
            //   pointermove / pointerup 都掛在 window 上，不需 capture 也收得到。
        });

        window.addEventListener("pointermove", function (e) {
            if (!isDragging) return;
            if (!dragMoved && Math.abs(e.clientX - dragStartClientX) > DRAG_CLICK_TOLERANCE) {
                dragMoved = true;
            }
            var dx = e.clientX - startX;
            var nx = Math.max(maxLeft(), Math.min(0, startJsX + dx));
            setJsX(nx);
            syncBlur();
        });

        // 連結在 pointerdown 已被 preventDefault 的情況下仍可能收到 click
        // → 只要判定為拖曳就阻止預設行為（不導頁）
        scrolling.addEventListener(
            "click",
            function (e) {
                if (!dragMoved) return;
                e.preventDefault();
                e.stopPropagation();
                dragMoved = false;
            },
            true
        );

        // 2026-11-02：<a href> 預設可被「拖出連結」，一旦觸發原生拖曳，
        // 後續 pointermove / pointerup 會被瀏覽器吃掉（滑桿卡住、click 也不會來）
        // → 一律擋掉預設拖曳（圖片另由 CSS pointer-events:none 處理）
        scrolling.addEventListener("dragstart", function (e) {
            e.preventDefault();
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

    // sukima hero-title-svg 手繪圓形畫線動畫觸發（2026-08-24）：
    // 進入視口時加 .show（CSS .bc-series-hero.show .leaf-flow-reveal-stream
    // 與原站 .hero.show 規則一致：2s ease-in-out forwards、延遲 1s）。
    // 初始即在視口內的 hero（如首屏第一組）立即觸發，滾動進入的由 IO 觸發。
    function initLeafFlowReveal() {
        var heroes = document.querySelectorAll(".bc-series-hero");
        if (!heroes.length) {
            return;
        }
        function inViewport(el) {
            var r = el.getBoundingClientRect();
            return r.top < window.innerHeight && r.bottom > 0;
        }
        function showHero(el) {
            el.classList.add("show");
        }
        if (!("IntersectionObserver" in window)) {
            for (var i = 0; i < heroes.length; i++) {
                showHero(heroes[i]);
            }
            return;
        }
        // 初始檢查：已在視口內的 hero 立即加 .show（不依賴 IO 首次回調）
        for (var k = 0; k < heroes.length; k++) {
            if (inViewport(heroes[k])) {
                showHero(heroes[k]);
            }
        }
        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        showHero(entry.target);
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );
        for (var j = 0; j < heroes.length; j++) {
            io.observe(heroes[j]);
        }
    }

    initLeafFlowReveal();

    // sukima arrow-recruit-svg 手繪箭頭動畫觸發（2026-08-24）：
    // way 區塊（.col-main.way）進入視口加 .show
    // （CSS .col-main.way.show .comet-tail-reveal-stream 與原站一致）。
    function initArrowReveal() {
        var ways = document.querySelectorAll(".col-main.way");
        if (!ways.length) {
            return;
        }
        function showWay(el) {
            el.classList.add("show");
        }
        if (!("IntersectionObserver" in window)) {
            for (var i = 0; i < ways.length; i++) {
                showWay(ways[i]);
            }
            return;
        }
        for (var k = 0; k < ways.length; k++) {
            var r = ways[k].getBoundingClientRect();
            if (r.top < window.innerHeight && r.bottom > 0) {
                showWay(ways[k]);
            }
        }
        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        showWay(entry.target);
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );
        for (var j = 0; j < ways.length; j++) {
            io.observe(ways[j]);
        }
    }

    initArrowReveal();

    // sukima other-members-svg 手繪圓形動畫觸發（2026-08-24）：
    // topConcept 區塊（.bc-top-concept）進入視口加 .show
    // （CSS .bc-top-concept.show .organic-reveal-brush444）。
    function initTopConceptReveal() {
        var tops = document.querySelectorAll(".bc-top-concept");
        if (!tops.length) {
            return;
        }
        function showTop(el) {
            el.classList.add("show");
        }
        if (!("IntersectionObserver" in window)) {
            for (var i = 0; i < tops.length; i++) {
                showTop(tops[i]);
            }
            return;
        }
        for (var k = 0; k < tops.length; k++) {
            var r = tops[k].getBoundingClientRect();
            if (r.top < window.innerHeight && r.bottom > 0) {
                showTop(tops[k]);
            }
        }
        var io = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        showTop(entry.target);
                        io.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15 }
        );
        for (var j = 0; j < tops.length; j++) {
            io.observe(tops[j]);
        }
    }

    initTopConceptReveal();
})();
