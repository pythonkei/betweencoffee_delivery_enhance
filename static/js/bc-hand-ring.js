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
   [2026-10-16 使用者指示]「關於咖啡名稱和 Highlight 文本，時間點不正確 —— 當相關咖啡旋轉到中心時，
   才顯示相關名稱和 Highlight 文本」。
   [原因] 索引來源是 Splide 的 'move'（＝那一格「開始」移動的瞬間，bc-gunte-hero.js），而 go()
     原本一到就把文字切到新索引；圓盤的旋轉是 CSS 過渡（--bc-hand-ease，預設 1.2s）⇒ 文字比
     照片早 1.2 秒出現（照片還在弧上、還沒到中心）。
   [修法] 文字改成「等圓盤的旋轉過渡跑完才切」：
     · go() 當下：先在文字容器加 .-hidden（以 visibility 隱藏 → 仍佔滿原本文字高度，列的總高
       不變、下方時鐘列與整頁內容不會被抽動），並記下 pending 索引；
     · 圓盤過渡結束（.hero_hand_list 的 transitionend 且 propertyName === 'transform'）
       或保險計時器（--bc-hand-ease + 60ms）先到者 → 切新的 -current 並移除 .-hidden。
     · 索引沒變（cur === 目標）時不經動畫、維持現狀；第一次定位且目標是第 1 張（圓盤本來就是
       rotate(0deg)、沒有過渡）→ 立即對齊。
   ⇒ 文字永遠與「此刻真正在圓弧頂點（＝畫面中心）的那杯」一致，不會提前也不會落後。
     （--bc-hand-ease 是 computed 讀值，日後調過渡長度文字會自動跟上；計時器只是 transitionend
      的保險，例如分頁被節流／元素不可見而收不到事件時。）
   ============================================================ */
(function () {
  'use strict';

  var STEP = -25;      // 每格旋轉角度（與 markup 的 --angle 步進 25 一致）
  var SETTLE_CUSHION = 60;     // 保險計時器比過渡長度多等的毫秒（讓 transitionend 先到）
  var FALLBACK_EASE_MS = 1200; // --bc-hand-ease 讀不到時的預設值（＝bc-hand-ring.css 的 1.2s）
  var instances = [];  // 已註冊的環
  var lastIndex = null; // 最後一次 goAll() 的索引（晚註冊者的會合依據）

  /* 圓盤旋轉過渡的長度（ms）：直接讀 computed 的 --bc-hand-ease（'1.2s'／'800ms' 皆可解析），
     讀不到就回預設值 —— 不寫死，改 bc-hand-ring.css 的過渡長度時文字的時機會自動跟上。 */
  function easeMs(el) {
    var raw = '';
    try { raw = (getComputedStyle(el).getPropertyValue('--bc-hand-ease') || '').trim(); }
    catch (e) { /* ignore */ }
    var m = /^([0-9.]+)(ms|s)?$/.exec(raw);
    if (!m) return FALLBACK_EASE_MS;
    var n = parseFloat(m[1]);
    if (isNaN(n)) return FALLBACK_EASE_MS;
    return m[2] === 'ms' ? n : n * 1000;
  }

  function Ring(root, caption) {
    this.root = root;
    this.list = root.querySelector('.hero_hand_list');
    this.items = this.list ? this.list.querySelectorAll('.hero_hand_item') : [];
    this.captionBox = caption || null;
    this.captions = caption ? caption.querySelectorAll('[data-bc-ring-caption-item]') : [];
    this.cur = -1;
    this.pending = null;  // 待顯示的文字索引（旋轉中；null ＝文字已與圓盤對齊）
    this.timer = null;    // 保險計時器
    this.easeMs = easeMs(root);
    // 2026-10-14：加上 .is-ready → 才啟用 transform/scale 過渡（見 bc-hand-ring.css）
    root.classList.add('is-ready');
    // 2026-10-16：文字的切換時機改綁圓盤旋轉的過渡結束（見檔頭註解）
    if (this.captions.length && this.list) {
      var self = this;
      this._onEnd = function (e) {
        if (e && e.propertyName !== 'transform') return;  // 只認圓盤的旋轉，忽略 img 的 scale
        self.settle();
      };
      this.list.addEventListener('transitionend', this._onEnd);
    }
  }

  Ring.prototype.count = function () { return this.items.length; };
  Ring.prototype.index = function () { return this.cur; };

  /* 文字：只讓第 i 筆是 -current（i < 0 ＝全部不顯示，用於「圓盤還在轉」的期間） */
  Ring.prototype.setCaptions = function (i) {
    for (var k = 0; k < this.captions.length; k++) {
      this.captions[k].classList.toggle('-current', k === i);
    }
  };

  /* 圓盤到定位了：把待顯示的那筆文字切上去（transitionend 與保險計時器都呼叫這裡；
     重複呼叫是安全的 —— pending 為 null 就什麼都不做）。 */
  Ring.prototype.settle = function () {
    if (this.timer) { clearTimeout(this.timer); this.timer = null; }
    if (this.pending === null) return;
    var i = this.pending;
    this.pending = null;
    if (this.captionBox) this.captionBox.classList.remove('-hidden');
    this.setCaptions(i);
  };

  /* 旋轉期間：先把整組文字隱形（.-hidden 用 visibility ⇒ 仍佔滿原本的文字高度、不跳版），
     等那杯真的轉到中心（settle）才顯示它自己的名稱/highlight。 */
  Ring.prototype.holdCaptions = function (i) {
    if (this.captionBox) this.captionBox.classList.add('-hidden');
    this.pending = i;
    if (this.timer) clearTimeout(this.timer);
    var self = this;
    this.timer = setTimeout(function () { self.settle(); }, this.easeMs + SETTLE_CUSHION);
  };

  /* 把索引正規化到 [0, n) 後套用：旋轉轉盤、切換 -current（照片立即、文字等置中） */
  Ring.prototype.go = function (i) {
    var n = this.items.length;
    if (!n || typeof i !== 'number' || isNaN(i)) return this.cur;
    var idx = ((Math.round(i) % n) + n) % n;
    // 圓盤這次是否真的會轉：第一次定位時 markup 的 transform 就是 rotate(0deg)，故只有目標不是
    // 第 1 張才有過渡；之後只要索引變了就會轉。
    var rotates = (this.cur === -1) ? (idx !== 0) : (idx !== this.cur);
    if (this.list) this.list.style.transform = 'rotate(' + (idx * STEP) + 'deg)';
    var k;
    for (k = 0; k < n; k++) this.items[k].classList.toggle('-current', k === idx);
    if (this.captions.length) {
      if (rotates) {
        this.holdCaptions(idx);            // 有過渡 ⇒ 文字等它轉完（見檔頭：只顯示置中的那杯）
      } else if (this.pending === null && this.cur !== idx) {
        this.setCaptions(idx);             // 沒有過渡（首次定位到第 1 張）⇒ 立即對齊
      }
      // 其餘情況（索引沒變、且文字還在等前一輪的過渡）＝維持 pending，不動它。
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
