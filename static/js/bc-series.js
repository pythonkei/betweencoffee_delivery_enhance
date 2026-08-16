// static/js/bc-series.js
// ==================== SERIES 滑桿（2026-08-16）====================
// 完全一致複製 designing.jp/series：照片滑桿水平滾動時，
// 左側標題 backdrop blur（scrolling scroll 事件切換 heading[data-blurred]）
(function ($) {
    "use strict";

    var $scrolling = $(".bc-series-scrolling");
    if (!$scrolling.length) return;

    var $heading = $(".bc-series-heading");

    var onScroll = function () {
        var blurred = $scrolling[0].scrollLeft > 2;
        $heading.attr("data-blurred", blurred ? "true" : "false");
    };

    $scrolling.on("scroll", onScroll);
    onScroll();
})(jQuery);
