/* ============================================================
   bc-hand-ring.js — 「手套圓」環形照片列的共用驅動（BC_HAND_RING）
   ------------------------------------------------------------
   2026-10-14（使用者指示）：把 GUNTE hero 的環形照片（.hero_hand）抽成可註冊的模組，
   讓首頁 hero 與下方 BC 動態 hero 的照片格（#bc-stage-photo-ring）共用同一個索引。
   [為何是「模組 + 註冊」而不是「同步層」]
     hero 的腳本是非 defer（index.html extra_scripts 內、緊接 Splide 之後），照片格所在的
     bc-brand-stage.js 是 defer → 兩者誰先執行不保證。與其互相監聽、互推狀態，改成：
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
       或計時器（--bc-hand-ease - 80ms；見 SETTLE_LEAD）先到者 → 切新的 -current 並移除 .-hidden。
     · 索引沒變（cur === 目標）時不經動畫、維持現狀；第一次定位且目標是第 1 張（圓盤本來就是
       rotate(0deg)、沒有過渡）→ 立即對齊。
   ⇒ 文字永遠與「此刻真正在圓弧頂點（＝畫面中心）的那杯」一致（切換點提前 80ms，最後這段位移肉眼不可見）。
     （--bc-hand-ease 是 computed 讀值，日後調過渡長度文字會自動跟上；計時器同時是 transitionend
      的保險 —— 例如分頁被節流／元素不可見而收不到事件時。）
   [2026-10-17 使用者指示]：名稱 / Highlight 換張時要有「進場動畫」。
   [作法] settle() 切完 -current 後呼叫 revealCaption()：直接沿用 hero 右側
     Fresh / Beans 的同一支 data-reveal 文字揭示（SplitText ＋ goo 濾鏡），
     引擎在 bc-brand-stage.js，透過 window.BC_TEXT_REVEAL(el, delay, duration, stagger) 取得
     ⇒ 兩處的視覺一致（模糊→清晰的 goo 揭示；首頁 caption 現在名稱與 highlight 完全同步）。
     [2026-10-18 使用者指示]「咖啡名稱和 Highlight 文本，動畫顯示時間點略慢，加快一點點」：
       只加速這組呼叫（引擎的預設值不動，Fresh / Beans 與時鐘數字仍是 1.2s）：
         起始延遲 0.1s → 0.04s（圓盤一到位幾乎立刻開始）、時長 1.2s → 0.9s（快 25%）。
       文字仍然只在「圓盤轉完、那一杯在中心」時才切換（時機不變，只是揭示更俐落）。
     [2026-10-19 使用者指示]「咖啡已經轉到中心，名稱 / Highlight 的揭示仍略慢，再加快一點點」：
       首度收緊為延遲 0.02s、時長 0.65s、兩筆錯開 0.06s；稍後依同一指示再收緊（見下）：
       延遲 0s、時長 0.45s、stagger 0s（名稱與 highlight 同步），切換點再提前 80ms（SETTLE_LEAD）
       ⇒ 圓盤視覺到位後 0.45s 內收斂（前版 0.67～0.73s，且兩筆相差 0.06s）。時機仍以「那一杯在中心」為準。
     引擎不存在時（GSAP 未載入）＝文字直接出現，與改動前相同。
   [2026-10-20 回歸修正（使用者回報「bc-stage-photo-ring 整個模組包括旋轉動畫都無法運作」）]
     [原因] 本模組自己不會換張 —— 唯一的索引來源是 GUNTE hero 的 Splide
       （bc-gunte-hero.js 的 updateSlideStates → BC_HAND_RING.goAll）。2026-10-19 首頁效能 P0
       移除了 splide.min.js 與 bc-gunte-hero.js（GUNTE hero 仍 hidden）⇒ 沒有任何東西再呼叫
       goAll()：環形照片列 register() 時被定位到第 1 張後就永遠靜止（不旋轉、名稱/Highlight
       也不再換）。markup、CSS、GSAP 揭示與 caption 全都正常，缺的只是「換張的節拍」。
     [解法] 本模組新增一組「自帶節拍」的 API（仍然只有一個索引來源，不新增第二套狀態）：
       BC_HAND_RING.startAuto(ms) → 沒有其他環（＝沒有 hero 在推播）時，每 ms 毫秒
                                     goAll(index + 1)；回傳是否真的啟動。
       BC_HAND_RING.stopAuto()    → 停掉自帶節拍（hero 回來推播時會自動停，見 register）。
     [為何不會與 hero 打架] startAuto() 在 instances.length > 1（hero 的環已註冊）時直接拒絕；
       而 register() 一旦收到第 2 個環（＝bc-gunte-hero.js 有載入）就 stopAuto()。
       ⇒ 之後恢復 GUNTE hero（拿掉 hidden ＋ 加回 splide／bc-gunte-hero.js）時，
         hero 的 Splide 自動接手，本檔不需再改。
     [範圍] 只有「沒有 hero 驅動」的頁面／情境才會啟動（目前＝首頁第一屏的品牌舞台）；
       尊重 prefers-reduced-motion: reduce（純靜態，使用者已要求減少動態時不自動轉）。
   [2026-10-24 使用者指示]「bc-stage-photo-ring-list 第一個咖啡現在初始是從小到放大動畫，
     修改為 bc-stage-headline-fresh-beans 'Follow Your Rhythm' 文字相同的動畫」。
     · 原因：register() → go() 的第一次定位是在 .is-ready 已加上的狀態下做的 ⇒ 第 1 張
       從 .hero_hand_item img 的預設 scale 0.5 過渡到 -current 的 scale 1（＝那段「放大」）。
     · 修法：第一次定位期間改為同時加上 .is-snap（bc-hand-ring.css：把圓盤旋轉與 img 的
       scale 過渡關掉）⇒ 第 1 張直接以最終尺寸就位；定位完成後由 revealPhoto() 播放
       「與 Fresh / Beans 相同」的 goo 揭示（引擎＝bc-brand-stage.js 的 window.BC_MEDIA_REVEAL，
       同一組 STD／AMP／OFF 濾鏡與同樣的 1.2s / 'Out' 時間軸）。
     · 之後換張完全不變：仍是圓盤旋轉 ＋ scale 0.5 ⇄ 1 過渡；.is-snap 只在第一次定位時存在。
   ============================================================ */
(function () {
  'use strict';

  var STEP = -25;      // 每格旋轉角度（與 markup 的 --angle 步進 25 一致）
  /* 2026-10-19：文字的切換點提前 80ms —— 1.2s 過渡（預設 ease）的最後 80ms 只剩不到 0.15°
     （圓半徑 100vw 時約 2～3px）的位移，肉眼看已完全靜止；提早切換可消除「圓盤已到中心、
     文字還沒開始」的空窗。transitionend 仍會呼叫 settle()（pending 已清空時直接 return）。 */
  var SETTLE_LEAD = 80;
  var FALLBACK_EASE_MS = 1200; // --bc-hand-ease 讀不到時的預設值（＝bc-hand-ring.css 的 1.2s）
  /* 2026-10-19（使用者指示「咖啡已經轉到中心，名稱 / Highlight 的揭示仍略慢 → 再加快一點點」）：
     這三個值只給「換張時的 caption 揭示」用（引擎 bc-brand-stage.js 的預設 1.2s / 0.1s 不動，
     Fresh / Beans 與時鐘數字不受影響）：
       CAPTION_REVEAL_DELAY   0s（圓盤一到就開始；前版 0.02s）
       CAPTION_REVEAL_DUR     0.45s（比 0.65s 再快 31%、比最初 1.2s 快 63%）
       CAPTION_REVEAL_STAGGER 0s（名稱與 highlight 完全同步；引擎預設 0.1s）
     ⇒ 兩筆同在 0.45s 收斂（前版 0.67／0.73s），不再有名稱先、highlight 後的 0.06s 落差。 */
  var CAPTION_REVEAL_DELAY = 0;
  var CAPTION_REVEAL_DUR = 0.45;
  var CAPTION_REVEAL_STAGGER = 0;
  var instances = [];  // 已註冊的環
  var lastIndex = null; // 最後一次 goAll() 的索引（晚註冊者的會合依據）
  /* 2026-10-20：沒有 hero（Splide）推播時的自帶節拍（見檔頭「2026-10-20 回歸修正」）。 */
  var autoTimer = null;          // setTimeout id；null ＝沒在跑
  var autoInterval = 5000;       // 與 GUNTE hero Splide 的 interval 相同

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
    // 2026-10-24（使用者指示「第一張咖啡不要從小放大」）：第一次定位另外加上 .is-snap
    //   把過渡關掉 ⇒ 第 1 張直接以 scale 1 就位，進場改由 revealPhoto() 的 goo 揭示負責
    //   （見檔頭 2026-10-24 與 releaseSnap()；go() 以 cur === -1 判斷「這是第一次」）。
    root.classList.add('is-ready');
    root.classList.add('is-snap');
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

  /* 2026-10-17（使用者指示）：名稱 / Highlight 換張時加上與 hero 右側「Fresh / Beans」
     **完全相同**的 data-reveal 文字揭示（SplitText ＋ goo 濾鏡；引擎在
     static/js/bc-brand-stage.js，透過 window.BC_TEXT_REVEAL 呼叫）。
     [時機] 一定要在 setCaptions() 之後 —— 那時新的一筆已是 display:block，
       SplitText 才量得到真正的排版（對 display:none 的元素分行會量成 0 寬）。
     [速度] 2026-10-18（使用者指示「動畫顯示時間點略慢，加快一點點」）：
       起始延遲 0.1 → 0.04s、時長 1.2 → 0.9s（引擎的第三個參數；預設值仍是 1.2s，
       故 hero 右側 Fresh / Beans 與時鐘數字不受影響）。
     2026-10-19（使用者指示「咖啡已經轉到中心，文字揭示仍略慢，再加快一點點」）：
       首度收緊：延遲 0.04 → 0.02s、時長 0.9 → 0.65s、元素錯開 0.1 → 0.06s（引擎第 4 個參數）；
       稍後二度收緊：延遲 0.02 → 0s、時長 0.65 → 0.45s、錯開 0.06 → 0s
       ⇒ 名稱與 highlight 同步、0.45s 收斂（前版 0.67／0.73s）。時機完全不變：
       仍然只在圓盤到位、那一杯在中心時才切換與揭示（切換點提前 80ms，見 SETTLE_LEAD）。
     [高度] SplitText 只是把原本的文字包成行內區塊，行高不變 ⇒ 文字區高度仍等於
       --bc-hero-caption-h，下方時鐘列不會被抽動。
     [降級] 取不到引擎（GSAP/SplitText 未載入、或 /about/ 沒有本檔的 captions）
       → 什麼都不做，文字照常直接出現（與改動前相同）。 */
  Ring.prototype.revealCaption = function (i) {
    if (!window.BC_TEXT_REVEAL || !this.captionBox) return;
    var item = this.captionBox.querySelectorAll('[data-bc-ring-caption-item]')[i];
    if (!item) return;
    var els = item.querySelectorAll('.bc-series-caption-name, .bc-series-caption-highlight');
    if (!els.length) return;
    window.BC_TEXT_REVEAL(els, CAPTION_REVEAL_DELAY, CAPTION_REVEAL_DUR, CAPTION_REVEAL_STAGGER);
  };

  /* 2026-10-24（使用者指示）：第一張照片的進場改為與 bc-stage-headline-fresh-beans
     「Follow Your Rhythm」相同的 goo 文字揭示（引擎＝bc-brand-stage.js 的
     window.BC_MEDIA_REVEAL，同一組 STD／AMP／OFF 濾鏡與同樣的 1.2s／'Out' 時間軸）。
     [時機] 只在第一次 go()（register 當下的定位）呼叫一次，且此時 .is-snap 仍生效
       ⇒ 照片先以最終尺寸就位（不再從 scale 0.5 放大），緊接著從 STD 的模糊收斂成清晰。
     [之後] 換張仍是圓盤既有的 scale 0.5 ⇄ 1 過渡，不受影響。
     [降級] 取不到引擎（GSAP 未載入）→ 不做事，照片直接以最終尺寸出現。 */
  Ring.prototype.revealPhoto = function (i) {
    if (!window.BC_MEDIA_REVEAL) return;
    var item = this.items[i];
    var media = item ? item.querySelector('img') : null;
    if (media) window.BC_MEDIA_REVEAL(media);
  };

  /* 移除 .is-snap：等兩個 frame 再移除 —— 要讓瀏覽器先把「無過渡」的 scale 1／rotate 算完並上色，
     否則同一個 frame 內移除會讓這些值又被當成「剛發生的變化」而補播一段過渡（＝放大動畫復活）。 */
  Ring.prototype.releaseSnap = function () {
    var root = this.root;
    var off = function () { root.classList.remove('is-snap'); };
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () { window.requestAnimationFrame(off); });
    } else {
      setTimeout(off, 32);
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
    this.revealCaption(i);   // 2026-10-17：新那筆用與 Fresh / Beans 相同的文字揭示進場
  };

  /* 旋轉期間：先把整組文字隱形（.-hidden 用 visibility ⇒ 仍佔滿原本的文字高度、不跳版），
     等那杯真的轉到中心（settle）才顯示它自己的名稱/highlight。 */
  Ring.prototype.holdCaptions = function (i) {
    if (this.captionBox) this.captionBox.classList.add('-hidden');
    this.pending = i;
    if (this.timer) clearTimeout(this.timer);
    var self = this;
    this.timer = setTimeout(function () { self.settle(); }, Math.max(0, this.easeMs - SETTLE_LEAD));
  };

  /* 把索引正規化到 [0, n) 後套用：旋轉轉盤、切換 -current（照片立即、文字等置中） */
  Ring.prototype.go = function (i) {
    var n = this.items.length;
    if (!n || typeof i !== 'number' || isNaN(i)) return this.cur;
    var idx = ((Math.round(i) % n) + n) % n;
    // 第一次定位（register 當下的 go）：決定是否要用 .is-snap 的「無過渡」定位 ＋ 照片揭示。
    var first = (this.cur === -1);
    // 圓盤這次是否真的會轉：第一次定位時 .is-snap 把過渡關掉（直接跳到定位點），不會有旋轉動畫，
    // 文字也不必等過渡結束；之後只要索引變了就會轉。
    var rotates = first ? false : (idx !== this.cur);
    if (this.list) this.list.style.transform = 'rotate(' + (idx * STEP) + 'deg)';
    var k;
    for (k = 0; k < n; k++) this.items[k].classList.toggle('-current', k === idx);
    if (this.captions.length) {
      if (rotates) {
        this.holdCaptions(idx);            // 有過渡 ⇒ 文字等它轉完（見檔頭：只顯示置中的那杯）
      } else if (this.pending === null && this.cur !== idx) {
        this.setCaptions(idx);             // 沒有過渡（首次定位到第 1 張）⇒ 立即對齊
        /* 2026-10-24：第一次定位（register 當下）不跑 caption 揭示 —— 那時 document.fonts
           還沒就緒，SplitText 會發 "called before fonts loaded" 警告且分行量測用的是
           fallback 字型。第一張照片的進場仍由下方 revealPhoto()（純濾鏡、不需字型）負責；
           之後每次換張仍照舊揭示（字型早已載入）。 */
        if (!first) this.revealCaption(idx);   // 2026-10-17：同一套進場揭示（見 revealCaption）
      }
      // 其餘情況（索引沒變、且文字還在等前一輪的過渡）＝維持 pending，不動它。
    }
    this.cur = idx;
    // 2026-10-24：第一次定位完成（照片已在最終尺寸）→ 開回過渡，並用與標題文字相同的揭示進場。
    if (first) {
      this.releaseSnap();
      this.revealPhoto(idx);
    }
    return idx;
  };

  function register(root, caption) {
    if (!root) return null;
    var ring = new Ring(root, caption || null);
    instances.push(ring);
    // 2026-10-20：有第 2 個環＝GUNTE hero 的腳本已載入（它會用 Splide 推播索引）
    // → 停掉自帶節拍，索引改回單一來源（見檔頭「2026-10-20 回歸修正」）。
    if (instances.length > 1) stopAuto();
    // 會合：goAll() 若已跑過（hero 較早註冊/換張），這裡直接套上同一索引
    ring.go(lastIndex === null ? 0 : lastIndex);
    return ring;
  }

  function goAll(i) {
    if (typeof i !== 'number' || isNaN(i)) return;
    lastIndex = i;
    for (var k = 0; k < instances.length; k++) instances[k].go(i);
  }

  /* ---------- 2026-10-20：自帶節拍（沒有 hero Splide 時的換張來源） ----------
     用 setTimeout 鏈（不是 setInterval）：每次等「換張 + 圓盤轉完」後才排下一次，
     不會因為主執行緒卡住而補跑好幾張。分頁隱藏時只重新排隊、不推進索引。 */
  function autoTick() {
    autoTimer = null;
    if (!instances.length) return;                 // 環被移掉 → 自然停掉
    if (document.hidden) { autoTimer = setTimeout(autoTick, autoInterval); return; }
    var n = instances[0].count();
    if (!n) return;
    goAll((lastIndex === null ? 0 : lastIndex + 1) % n);
    autoTimer = setTimeout(autoTick, autoInterval);
  }

  /* 啟動自帶節拍：只有「已註冊且僅有一個環」時才成立（有 hero 的環就交給 Splide）；
     使用者若要求減少動態（prefers-reduced-motion: reduce）則不自動轉。 */
  function startAuto(ms) {
    if (autoTimer) return true;                    // 已在跑
    if (instances.length !== 1) return false;      // 0＝沒有環；>1＝hero 的 Splide 正在推播
    if (ms > 0) autoInterval = ms;
    try {
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
    } catch (e) { /* ignore */ }
    autoTimer = setTimeout(autoTick, autoInterval);
    return true;
  }

  function stopAuto() {
    if (autoTimer) { clearTimeout(autoTimer); autoTimer = null; }
  }

  window.BC_HAND_RING = {
    register: register,
    goAll: goAll,
    startAuto: startAuto,
    stopAuto: stopAuto,
    index: function () { return lastIndex; },
    count: function () { return instances.length; },
    instances: function () { return instances.slice(); }
  };
})();
