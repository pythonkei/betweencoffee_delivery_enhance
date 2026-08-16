// static/js/bc-series.js
// ==================== BETWEEN SERIES 橫向滑動系列（2026-08-16）====================
// 參考 https://designing.jp/series/（--js-x 水平位移 + pager + 箭頭）
// 桌面：箭頭/pager 更新 --bc-series-x（translateX）
// 行動：scroll-snap 原生捲動（不需 JS，pager/箭頭隱藏）
(function ($) {
    "use strict";

    var $stage = $(".bc-series-stage");
    if (!$stage.length) return;

    var $list = $stage.find(".bc-series-list");
    var $pager = $(".bc-series-pager");
    var STEP = 326; // slide 300 + gap 26
    var count = $list.children().length;
    var current = 0;
    var maxIndex = 0;

    var isDesktop = function () {
        return window.innerWidth >= 768;
    };

    var buildPager = function () {
        $pager.empty();
        for (var i = 0; i <= maxIndex; i++) {
            $("<li>").attr("data-index", i).appendTo($pager);
        }
    };

    var apply = function () {
        if (!isDesktop()) {
            $list.css("transform", "none");
            return;
        }
        $list.css("transform", "translateX(" + -current * STEP + "px)");
        $pager.find("li").removeClass("active").eq(current).addClass("active");
    };

    var calc = function () {
        var perView = Math.max(1, Math.floor($stage.width() / STEP));
        maxIndex = Math.max(0, count - perView);
        if (current > maxIndex) current = maxIndex;
        buildPager();
        apply();
    };

    // 箭頭
    $stage.on("click", ".bc-series-arrow-prev", function (e) {
        e.preventDefault();
        if (current > 0) { current--; apply(); }
    });
    $stage.on("click", ".bc-series-arrow-next", function (e) {
        e.preventDefault();
        if (current < maxIndex) { current++; apply(); }
    });
    // 分頁點
    $pager.on("click", "li", function () {
        current = +$(this).data("index");
        apply();
    });

    // resize 重算（防抖）
    var resizeTimer;
    $(window).on("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(calc, 200);
    });

    calc();
})(jQuery);
