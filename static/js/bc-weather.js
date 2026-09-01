/* ============================================================
   bc-weather.js — 橫濱 Timber Wharf 天氣元件（about 頁右上角）
   2026-08-26 整合
   ------------------------------------------------------------------
   完整複製 yokohama-timberwharf.com/wp-content/themes/ytw/assets/js/main.js
   的 weather 邏輯（minified 反推還原，行為一致）：
   1. XMLHttpRequest → OpenWeatherMap API（原站 URL + 公開 key，完全一致）
   2. icon 對映：weather[0].icon → header_weather_*.svg，建立 <img width=80 height=40>
   3. 日期填充：month(Jan..Dec) / day(補零) / year(4位)，溫度 Math.round + °C
   4. 動畫：3 元素循環 時鐘 → icon → 溫度，每 5 秒滑動切換
      （GSAP，duration .8, easeInOut；原站 rAF 計時）
   5. 時鐘：每秒刷新 HH:MM（24 小時制）
   依賴：GSAP（base.html 已全域載入 3.12.5）。
   圖示路徑：/static/images/（STATIC_URL=/static/）。
   ============================================================ */
(function () {
  'use strict';

  /* 原站快取（避免重複 API 呼叫，行為與原站一致） */
  var cachedData = null;
  var hasCached = false;
  /* 動畫循環順序（2026-08-26 新增時鐘）：時鐘 → 天氣 icon → 溫度 */
  var ORDER = ['clock', 'icon', 'temperature'];
  var currentIndex = 0;

  /* 圖示對映（原站三元鏈完整對應） */
  var ICON_MAP = {
    '01d': 'header_weather_sunny.svg', '01n': 'header_weather_sunny.svg',
    '02d': 'header_weather_partlycloudy.svg', '02n': 'header_weather_partlycloudy.svg',
    '03d': 'header_weather_partlycloudy.svg', '03n': 'header_weather_partlycloudy.svg',
    '04d': 'header_weather_cloudy.svg', '04n': 'header_weather_cloudy.svg',
    '09d': 'header_weather_rainy.svg', '09n': 'header_weather_rainy.svg',
    '10d': 'header_weather_rainy.svg', '10n': 'header_weather_rainy.svg',
    '11d': 'header_weather_thunderstorm.svg', '11n': 'header_weather_thunderstorm.svg',
    '13d': 'header_weather_snowy.svg', '13n': 'header_weather_snowy.svg',
    '50d': 'header_weather_foggy.svg', '50n': 'header_weather_foggy.svg'
  };

  /* img alt 對映（原站 r()，缺省 SUNNY） */
  var ALT_MAP = {
    '01d': 'SUNNY', '01n': 'SUNNY',
    '02d': 'PARTLY CLOUDY', '02n': 'PARTLY CLOUDY',
    '03d': 'PARTLY CLOUDY', '03n': 'PARTLY CLOUDY',
    '04d': 'CLOUDY', '04n': 'CLOUDY',
    '09d': 'RAINY', '09n': 'RAINY',
    '10d': 'RAINY', '10n': 'RAINY',
    '11d': 'THUNDERSTORM', '11n': 'THUNDERSTORM',
    '13d': 'SNOWY', '13n': 'SNOWY',
    '50d': 'FOGGY', '50n': 'FOGGY'
  };

  /* 圖示基礎路徑：本地 static/images/（原站為 origin + /wp-content/themes/ytw/assets/img/） */
  function iconBase() {
    return window.BC_WEATHER_IMG || '/static/images/';
  }

  /* 原站 i()：icon 填入（建立/更新 <img>） */
  function fillIcon(data, nodes) {
    nodes.forEach(function (c) {
      var u = c.querySelector('.icon');
      if (!u) return;
      var m = data.weather[0].icon;
      var h = ICON_MAP[m] || 'header_weather_sunny.svg';
      var src = iconBase() + h;
      var f = u.querySelector('img');
      if (!f) {
        f = document.createElement('img');
        u.appendChild(f);
      }
      f.src = src;
      f.width = 80;
      f.height = 40;
      f.alt = ALT_MAP[m] || 'SUNNY';
    });
  }

  /* 原站 e()：日期 + 溫度填充 */
  function fillDate(data, nodes) {
    var now = new Date();
    var monthNum = (now.getMonth() + 1).toString();
    var day = now.getDate().toString().padStart(2, '0');
    var year = now.getFullYear().toString();
    var MONTHS = { 1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec' };
    /* 2026-08-27：weekday 香港真實星期（本地 getDay） */
    var WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    var weekday = WEEKDAYS[now.getDay()];

    nodes.forEach(function (c) {
      var d = c.querySelector('.day');
      if (d) d.textContent = day;
      var m = c.querySelector('.month');
      if (m) m.textContent = MONTHS[monthNum];
      var y = c.querySelector('.year');
      if (y) y.textContent = year;
      var wd = c.querySelector('.weekday');
      if (wd) wd.textContent = weekday;
    });
    nodes.forEach(function (c) {
      /* 注意：時鐘加入後 DOM 有兩個 .value（.clock .value / .temperature .value），
         必須用精確 selector，否則會選中時鐘 */
      var t = c.querySelector('.temperature');
      var v = c.querySelector('.temperature .value');
      var u = c.querySelector('.temperature .unit');
      if (t) {
        if (v) v.textContent = Math.round(data.main.temp);
        if (u) u.textContent = '\u00B0C';
      }
    });
  }

  /* 立即定位（2026-08-28：不依賴 GSAP/defer 時序——script 在 body 尾、首 paint 前
     執行，直接設 style.transform，首幀即依 sessionStorage 的上次狀態，
     無需 opacity 隱藏，weather 保持可見不消失彈出） */
  function applyPositions(nodes) {
    nodes.forEach(function (l) {
      ORDER.forEach(function (n, i) {
        var el = l.querySelector('.' + n);
        if (el) el.style.transform = 'translateX(' + (i === currentIndex ? 0 : 80) + 'px)';
      });
    });
  }

  /* 動畫循環（API 回應後啟動）：3 元素 時鐘 → icon → 溫度，每 5 秒滑動切換
     當前滑出左側（x:-80）、下一個從右側滑入（x:80→0）、
     上上個（在左側）悄悄回右側待命（不可見時調整，無視覺跳動） */
  function startLoop() {
    var last = 0;
    var EASE = 'power2.inOut';

    function toggle() {
      var curName = ORDER[currentIndex];
      var nextName = ORDER[(currentIndex + 1) % ORDER.length];
      var otherName = ORDER[(currentIndex + 2) % ORDER.length];
      document.querySelectorAll('.weather').forEach(function (c) {
        var cur = c.querySelector('.' + curName);
        var next = c.querySelector('.' + nextName);
        var other = c.querySelector('.' + otherName);
        if (window.gsap) {
          if (cur) gsap.to(cur, { x: -80, duration: 0.8, ease: EASE });
          if (next) gsap.fromTo(next, { x: 80 }, { x: 0, duration: 0.8, ease: EASE });
          if (other) gsap.set(other, { x: 80 });
        }
      });
      currentIndex = (currentIndex + 1) % ORDER.length;
      /* 2026-08-28：記錄目前動畫狀態，轉跳頁面時恢復（不重播回時鐘） */
      try { sessionStorage.setItem('bcWeatherIndex', String(currentIndex)); } catch (e) {}
    }

    function tick(now) {
      if (now - last >= 5000) {
        last = now;
        toggle();
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* 2026-08-28：轉跳防重播——恢復上次動畫狀態已保證轉跳不重置為時鐘，
     循環延遲 5 秒啟動：足夠避免轉跳瞬間切換的干擾，
     且 weather 不會停在單一狀態太久。 */
  function maybeStartLoop() {
    var now = Date.now();
    var last = parseInt(sessionStorage.getItem('bcWeatherLastVisit') || '0', 10);
    sessionStorage.setItem('bcWeatherLastVisit', String(now));
    setTimeout(startLoop, 5000);
  }

  /* 時鐘：每秒刷新 HH:MM（24 小時制，原站 -font_en 數字風格） */
  function updateClock() {
    var now = new Date();
    var h = now.getHours().toString().padStart(2, '0');
    var m = now.getMinutes().toString().padStart(2, '0');
    document.querySelectorAll('.weather').forEach(function (c) {
      var v = c.querySelector('.clock .value');
      if (v) v.textContent = h + ':' + m;
    });
  }

  /* 主邏輯：script 在 body 尾、首 paint 前同步執行——立即定位與填充，
     首幀即依 sessionStorage 的上次狀態顯示，weather 全程可見（無消失彈出）。
     註：weather 元素位於 navbar（body 開頭），執行時已存在。 */
  function main() {
    var nodes = document.querySelectorAll('.weather');
    if (!nodes || nodes.length === 0) return;

    /* 時鐘：立即填入一次 + 每秒更新（與天氣/溫度動畫獨立） */
    updateClock();
    setInterval(updateClock, 1000);

    /* 立即定位：恢復上次動畫狀態（sessionStorage），首 paint 即正確狀態 */
    var savedIdx = parseInt(sessionStorage.getItem('bcWeatherIndex') || '-1', 10);
    if (savedIdx >= 0 && savedIdx < ORDER.length) {
      currentIndex = savedIdx;
    }
    applyPositions(nodes);

    /* 2026-08-28：sessionStorage 天氣快取——轉跳頁面時立即顯示正確溫度/icon，
       避免溫度元素在 API 回應前顯示空/舊值（nav.html 預設已清空）造成抖動 */
    var stored = null;
    try { stored = JSON.parse(sessionStorage.getItem('bcWeatherData') || 'null'); } catch (e) { stored = null; }
    var filled = false;
    if (stored && stored.main && stored.weather) {
      fillIcon(stored, nodes);
      fillDate(stored, nodes);
      filled = true;
    }

    /* OpenWeatherMap API（2026-08-26 需求：改為香港葵涌天氣；原站 Yokohama） */
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
      try {
        if (this.readyState === 4 && this.status === 200) {
          cachedData = this.response;
          hasCached = true;
          fillIcon(cachedData, nodes);
          fillDate(cachedData, nodes);
          /* 2026-08-28：寫入 sessionStorage 快取，下次轉跳即時顯示 */
          try { sessionStorage.setItem('bcWeatherData', JSON.stringify(cachedData)); } catch (e) {}
          if (!filled) { maybeStartLoop(); filled = true; }
        }
      } catch (e) {
        console.error('\u5929\u6C17UI\u306E\u66F4\u65B0\u4E2D\u306B\u30A8\u30E9\u30FC\u304C\u767A\u751F\u3057\u307E\u3057\u305F:', e);
      }
    };
    xhr.open('GET', 'https://api.openweathermap.org/data/2.5/weather?q=Kwai Chung&units=metric&lang=ja&appid=6db833ee3b72a69a8ca7ba2676850f74', true);
    xhr.responseType = 'json';
    xhr.send();

    /* 快取已填充 → 啟動循環（延遲 5 秒）；API 回應路徑由 filled flag 防重複 */
    if (filled) maybeStartLoop();
  }

  main();
})();

