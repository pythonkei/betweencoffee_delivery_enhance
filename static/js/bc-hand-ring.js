/* ============================================================
   bc-hand-ring.js — 「手套圓」環形照片列的共用驅動（BC_HAND_RING）
   ------------------------------------------------------------
   2026-10-14（使用者指示）：把 GUNTE hero 的環形照片（.hero_hand）抽成可註冊的模組，
   讓首頁 hero 與下方 BC 動態 hero 的照片格（#bc-clock-photos）共用同一個索引。
   [為何是「模組 + 註冊」而不是「同步層」]
     hero 的腳本是非 defer（index.html extra_scripts 內、緊接 Splide 之後），照片格所在的
     bc-bg-footer.js 是 defer → 兩者誰先執行不保證。與其互相監聽、互推狀態，改成：
     唯一的索引來源＝hero 的 Splide（updateSlideStates → goAll(index)），模組只記住最後一次
     的索引（lastIndex），晚註冊的環在 register() 當下直接會合到該索引 ⇒ 載入順序無關、
     狀態只有一個數字。沒有任何輪詢、計時器或事件橋接。
   [hero 仍然只用它自己的 Splide 換張，模組不碰 Splide]
   API：
     BC_HAND_RING.register(root, caption?) → { go(i), index(), count() }
       root    ＝ .hero_hand 元素；caption ＝ 選填，內含 [data-bc-ring-caption-item] 時
                 會跟著同步 -current（照片格用它顯示「當前那支咖啡」的名稱/highlight）。
     BC_HAND_RING.goAll(i)  → 把索引推給所有已註冊的環（含之後才註冊的）
     BC_HAND_RING.index()   → 最後一次 goAll 的索引（未推播過為 null）
     BC_HAND_RING.count()   → 已註冊的環數
   ============================================================ */
(function () {
  'use strict';

  var STEP = -25;      // 每格旋轉角度（與 markup 的 --angle 步進 25 一致）
  var instances = [];  // 已註冊的環
  var lastIndex = null; // 最後一次 goAll() 的索引（晚註冊者的會合依據）

  function Ring(root, caption) {
    this.root = root;
    this.list = root.querySelector('.hero_hand_list');
    this.items = this.list ? this.list.querySelectorAll('.hero_hand_item') : [];
    this.captions = caption ? caption.querySelectorAll('[data-bc-ring-caption-item]') : [];
    this.cur = -1;
    // 2026-10-14：加上 .is-ready → 才啟用 transform/scale 過渡（見 bc-hand-ring.css）
    root.classList.add('is-ready');
  }

  Ring.prototype.count = function () { return this.items.length; };
  Ring.prototype.index = function () { return this.cur; };

  /* 把索引正規化到 [0, n) 後套用：旋轉轉盤、切換 -current（照片與文字） */
  Ring.prototype.go = function (i) {
    var n = this.items.length;
    if (!n || typeof i !== 'number' || isNaN(i)) return this.cur;
    var idx = ((Math.round(i) % n) + n) % n;
    if (this.list) this.list.style.transform = 'rotate(' + (idx * STEP) + 'deg)';
    var k;
    for (k = 0; k < n; k++) this.items[k].classList.toggle('-current', k === idx);
    for (k = 0; k < this.captions.length; k++) {
      this.captions[k].classList.toggle('-current', k === idx);
    }
    this.cur = idx;
    return idx;
  };

  function register(root, caption) {
    if (!root) return null;
    var ring = new Ring(root, caption || null);
    instances.push(ring);
    // 會合：goAll() 若已跑過（hero 較早註冊/換張），這裡直接套上同一索引
    ring.go(lastIndex === null ? 0 : lastIndex);
    return ring;
  }

  function goAll(i) {
    if (typeof i !== 'number' || isNaN(i)) return;
    lastIndex = i;
    for (var k = 0; k < instances.length; k++) instances[k].go(i);
  }

  window.BC_HAND_RING = {
    register: register,
    goAll: goAll,
    index: function () { return lastIndex; },
    count: function () { return instances.length; },
    instances: function () { return instances.slice(); }
  };
})();
