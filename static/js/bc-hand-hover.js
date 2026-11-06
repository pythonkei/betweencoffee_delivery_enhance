/* ============================================================
   bc-hand-hover.js — 環形咖啡照的 hover 互動（移植 hub.ballaholic.jp 的 .embla）
   ------------------------------------------------------------
   2026-11-03 建立（使用者指示）：
     「使用 https://hub.ballaholic.jp/ .embla 模組內的 hover 效果（顯示更多細節互動效果），
      移植到 .hero bc-brand-stage-hero，當滑鼠懸停在咖啡照片上時顯示互動效果」

   [來源實作（2026-11-03 取得的該站 main.js／main.css，函式名 bC()）]
     · 卡片 <a class="nav-carousel-item"> 被 hover 時：
       mouseenter → 清掉計時器、把 #mouse-stalker 定位到游標、scale-0 移除／scale-100 加上、
       並開始監聽 mousemove 讓徽章跟著游標跑；
       mouseleave → 等 200ms 才收回（在卡片之間移動時不會閃）。
     · 徽章＝108px 圓、白框、主題色 90% 底、transition-transform .5s、
       --bounce-ease: cubic-bezier(.34,1.92,.53,.7)（回彈 overshoot）、內容 "view more"。
     · 觸控裝置（"ontouchstart" in window || navigator.maxTouchPoints > 0）直接 return，
       整段不啟動。
   [本專案照抄的行為] 200ms 的收尾延遲、以 left/top 追蹤（位移不吃過渡、只有縮放過渡）、
     觸控裝置不啟動、mouseenter 時清計時器（快速滑過多張照片不會殘留）。
   [本專案的差異]
     · 徽章內容原為「這杯咖啡的名稱 ＋ view more」（名稱讀 <a aria-label>／<img alt>
       ＝hero_coffees.N.name）⇒ hover 就看得到這杯是什麼。
     · 2026-11-05（使用者指示）：徽章下方那行字由 "view more" 改為 "Detail"（上方「來源實作」
       那段描述的是原站），並移除徽章白框（CSS 在 bc-hand-ring.css 的 .bc-hand-badge）；
       照片格的類別名 .hero_hand_item → .hero_bc_item（下面 ITEM_SELECTOR 已同步改）。
     · 2026-11-05 稍後（使用者指示）：圓內「只顯示 Detail，無需咖啡名稱」⇒ 移除
       [data-bc-hand-badge-name] 的讀取與填入（labelOf()／NAME_SELECTOR 已刪），
       徽章 markup 只剩 <span class="bc-hand-badge__more">Detail</span>。
       日後要恢復名稱：markup 加回該 span，並在 show() 內把
       badge.querySelector('[data-bc-hand-badge-name]').textContent 設為 <a aria-label>。
     · hover 期間暫停 5s 自動輪播（bc-hand-ring.js 的 startAuto／stopAuto）：
       否則照片會在游標底下轉走、徽章跟著亂跳；離開後 startAuto() 重新計時。
     · 拖曳（bc-hand-ring.js 的 bindDrag）與頁面捲動時立刻收回徽章。
     · CSS（.bc-hand-badge／照片放大）在 static/css/bc-hand-ring.css 檔尾；
       本檔只負責「什麼時候顯示、顯示在哪」。
   [範圍] 只作用於有 [data-bc-hand-ring] 的環（首頁品牌舞台的 #bc-stage-photo-ring；
     被 hidden 的 GUNTE hero 也同構，日後恢復時行為一致）；about 頁沒有環 → no-op。
   ============================================================ */
(function () {
  'use strict';

  var RING_SELECTOR = '[data-bc-hand-ring]';
  var ITEM_SELECTOR = '.hero_bc_item';
  var BADGE_SELECTOR = '[data-bc-hand-badge]';
  var ON = 'is-on';
  /* 與原站相同的 200ms 收尾延遲：離開一張照片後、進入下一張前不會先縮再放大 */
  var HIDE_DELAY = 200;

  /* 觸控裝置不做（與原站同一段判斷）。另外要求「真的有 hover」的指標
     （(hover: hover) and (pointer: fine)）—— 只有觸控筆電的觸控模式會落在灰區，
     那邊 CSS 的照片放大也不會生效，徽章同樣不啟動，兩者行為一致。 */
  function canHover() {
    if ('ontouchstart' in window) return false;
    if (navigator.maxTouchPoints > 0 || navigator.msMaxTouchPoints > 0) return false;
    if (typeof window.matchMedia !== 'function') return true;
    return window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  }

  function init() {
    if (!canHover()) return;

    var badge = document.querySelector(BADGE_SELECTOR);
    var rings = document.querySelectorAll(RING_SELECTOR);
    if (!badge || !rings.length) return;

    var hideTimer = null;   // 200ms 收尾延遲的計時器
    var frame = 0;          // rAF id（0＝沒有排隊中的更新）
    var x = 0;              // 游標的 viewport 座標
    var y = 0;
    var active = false;     // 徽章是否正跟著某張照片

    /* 追蹤：直接改 left/top（不吃過渡，與原站相同）⇒ 圓心即時跟著游標。
       2026-11-05（使用者回報「手形游標遮住 DETAIL 文字」）：圓心不再落在游標上，
       CSS 用 translate 偏移到游標右上方（--bc-hand-badge-dx／dy，見 bc-hand-ring.css）
       ⇒ 游標停在圓的左下緣、不會蓋住中央的文字；本檔只給游標座標，不需改。
       用 rAF 合併同一幀內的多個 mousemove，避免高頻事件造成多餘的樣式計算。 */
    function apply() {
      badge.style.left = x + 'px';
      badge.style.top = y + 'px';
    }

    function track(e) {
      x = e.clientX;
      y = e.clientY;
      if (frame) return;
      if (!window.requestAnimationFrame) {
        apply();
        return;
      }
      frame = window.requestAnimationFrame(function () {
        frame = 0;
        apply();
      });
    }

    function pauseRing() {
      if (window.BC_HAND_RING) window.BC_HAND_RING.stopAuto();
    }

    function resumeRing() {
      /* 不帶參數：沿用 bc-hand-ring.js 目前的間隔（首頁為 5000ms）。
         沒有環／有 hero 在推播／使用者要求減少動態時，它自己會回 false ⇒ 不硬轉。 */
      if (window.BC_HAND_RING) window.BC_HAND_RING.startAuto();
    }

    /* 2026-11-05（使用者指示）：圓內只顯示 "Detail" ⇒ 這裡不再讀取／填入咖啡名稱
       （原本的 labelOf(item) 讀 <a aria-label> → <img alt> 已移除）。 */
    function show(e) {
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      track(e);
      badge.classList.add(ON);
      apply();              // 立刻定位（不等下一幀），圓才不會從上一張的位置飛過來
      document.addEventListener('mousemove', track);
      if (!active) {
        active = true;
        pauseRing();          // hover 期間照片不轉走
      }
    }

    /* 立刻收回（拖曳、捲動、游標離開視窗、切到別的視窗） */
    function hideNow() {
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null; }
      if (!active) return;
      active = false;
      badge.classList.remove(ON);
      document.removeEventListener('mousemove', track);
      resumeRing();
    }

    /* 離開照片：等 200ms 才收回（與原站相同） */
    function hideSoft() {
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(hideNow, HIDE_DELAY);
    }

    function bind(root) {
      var items = root.querySelectorAll(ITEM_SELECTOR);
      for (var i = 0; i < items.length; i++) {
        (function (item) {
          item.addEventListener('mouseenter', function (e) { show(e); });
          item.addEventListener('mouseleave', hideSoft);
        })(items[i]);
      }
      /* 拖曳照片（bc-hand-ring.js 的 bindDrag）時不該有徽章跟著游標跑；
         放手後照片會吸附換位，新的 mouseenter 會依游標位置重新顯示。 */
      root.addEventListener('pointerdown', hideNow);
      root.addEventListener('pointercancel', hideNow);
    }

    for (var k = 0; k < rings.length; k++) bind(rings[k]);

    /* fixed 徽章不會跟著頁面捲走、也不會跟著視窗切換 → 主動收回 */
    window.addEventListener('scroll', hideNow, { passive: true });
    window.addEventListener('blur', hideNow);
    document.addEventListener('mouseleave', hideNow);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
