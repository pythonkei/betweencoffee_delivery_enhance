/* ============================================================
   bc-steps-rive.js — 首頁「四步咖啡旅程」Rive 圖示（intro / hover）
   2026-10-22 建立
   ------------------------------------------------------------------
   背景：四顆圖示沿用 deltacafes.com 的 .riv（ciclo_café-picto_*），
        每個檔案內含數條「線性時間軸」（名稱以檔案為準）：
          intro     — 從空白線稿「畫進」完整圖示的入場動畫
          hover     — 游標移入時播放的一次性小動作
          hover out — 只有 torra 有；本站不使用（見下方實測結論）
          off       — 第 0 幀是空白線稿，最後一格才是完整圖示
        （另有 State Machine 1，但本站不使用：時間軸用法更單純、也更省。）

   【2026-10-22 實測結論（改動前請先讀完）】
   以畫布 alpha 覆蓋量（sig＝alpha > 8 的像素數）逐格取樣，在 2.35.2 得到：
   - intro 是唯一會把畫布帶到「絕對完整圖示」的時間軸
     （實測自然播完：origens 1032 / torra 922 / blend 1131 / consumo 873）。
   - hover 的結束姿勢＝它開始時的姿勢。從完整圖示起播會回到完整圖示；
     從空白起播就回到空白（origens 166 → 播完仍是 166）。因此 hover 必須
     接在 intro 之後起播，而且不可中途 stop（stop 會凍結在中間格）。
   - off 的第 0 幀就是空白線稿（origens 只有一條斜線，166）→ 不可當靜止狀態。
   - scrub(intro, 1) 完全不可靠：動畫實例被 stop／移除後，scrub 是「靜默的
     空操作」，畫布留在舊姿勢；即使實例還在，實測也常停在半途（torra 只到
     667，圖示明顯缺角）。→ 本檔完全不使用 scrub。
   結論：靜止狀態＝「intro 自然播完後留下來的姿勢」。達到之後不要再對畫布下
   任何指令（不 stop、不 scrub），否則圖示會缺角或整顆消失。

   行為：
   1. 版面一進入視口上下 600px 才動態載入 rive.js（296KB）→ 再由
      RuntimeLoader.setWasmUrl() 指向自架的 rive.wasm（1.7MB，static/library/），
      完全不連外網 CDN。
   2. 每個 canvas 一個 Rive 實例（autoplay: false，由本檔手動 play）。
      載入完成 → 播 intro；intro 播完（EventType.Stop）→ 停在完整圖示。
   3. 【2026-10-23 使用者指示】自動循環：intro 自然播完後靜止 4 秒（REPLAY_MS），
      再重播一次 intro，持續循環。重播時畫布保持可見，圖示會再「畫進」一次。
   4. 游標移入 → 播 hover（一次性，收尾自動回到完整圖示）；游標移出「不做任何
      事」，讓 hover 自然播完即回到完整圖示。觸控裝置（pointerType = touch）
      點一下播 hover（沒有 hover 概念）。游標停在圖示上（或 hover 還在播）時，
      該輪循環會跳過，游標離開後才重新排下一輪（避免打斷 hover）。
   5. prefers-reduced-motion: reduce → 完全不播 hover、也不自動循環（停在完整
      圖示）；intro 改在畫布「尚未顯示」時播完（見 finishIntro 的 reveal），
      使用者只看到完整圖示、看不到動態。
   6. 顏色：.riv 內建暖白線稿，由 bc-steps.css 的
      filter: brightness(0) invert(1) 統一轉為純白（線稿形狀、抗鋸齒不變）。

   實作注意（Rive runtime 行為，已對 2.35.2 原始碼確認）：
   - 「單次播放」動畫（loopValue = 0）播完時，runtime 會自動刪除該動畫實例，
     並發出 EventType.Stop（不是 Loop），且 event.data 是「被移除的動畫名稱陣列」。
     故 intro 結束用 Stop 事件判斷；另備 6s 保險計時器（intro 若被設成循環播放
     就永遠等不到 Stop，至少要把畫布顯示出來）。
   - play() 對「已實例化」的動畫只會把 playing 設回 true、不會重設時間；
     對「已播完被移除」的動畫則重新實例化、從第 0 幀開始。兩者都符合本檔需求，
     所以切換時間軸不必先 stop（先 stop 反而會把圖示凍結在中間格）。
   - 模組離開視口 → pause() 並清掉循環計時器（看不到時不重播）；回來 → 續播
     當前時間軸，若已靜止則重新排下一輪循環。
   - 任何一步失敗（腳本 404、wasm 不支援、檔案損壞）都靜默結束；
     canvas 保持 visibility: hidden（bc-steps.css），版面間距不變、不破版。
   ============================================================ */
(function () {
  'use strict';

  var INTRO = 'intro';
  var HOVER = 'hover';

  // 靜止狀態的內部標記（不是時間軸名稱）：intro 已自然播完，畫布停在完整圖示。
  // 標記成 REST 的意義就是「不要再對這張畫布下任何指令」。
  var REST = 'rest';

  // intro 保險上限（正常情況由 Stop 事件收尾）
  var INTRO_FALLBACK_MS = 6000;

  // 自動循環：intro 播完後靜止 4 秒再重播（2026-10-23 使用者指示）
  var REPLAY_MS = 4000;

  var root = null;
  var icons = [];
  var runtimeState = 'idle'; // idle | loading | ready | failed
  var reduceMotion = false;
  var resizeRaf = 0;

  /* ---------- 啟動 ---------- */

  function init() {
    root = document.querySelector('[data-bc-steps]');
    if (!root) {
      return;
    }

    var canvases = root.querySelectorAll('canvas[data-riv]');
    if (!canvases.length) {
      return;
    }

    reduceMotion = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

    Array.prototype.forEach.call(canvases, function (canvas) {
      icons.push({
        canvas: canvas,
        src: canvas.getAttribute('data-riv'),
        rive: null,
        names: [],
        current: '',
        introDone: false,
        introTimer: 0,
        replayTimer: 0,
        paused: false,
        hovering: false
      });
    });

    bindResize();
    bindIconEvents();

    if (!('IntersectionObserver' in window)) {
      // 舊瀏覽器：直接載入（4 顆圖示都在同一段，本來就會同時初始化）
      loadRuntime();
      return;
    }

    // 只在接近視口時才下載 runtime（首屏不必付 2MB 的代價）
    var boot = new IntersectionObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          boot.disconnect();
          loadRuntime();
          return;
        }
      }
    }, { rootMargin: '600px 0px 600px 0px' });
    boot.observe(root);

    // 常駐：離開視口暫停時間軸，回到視口續播
    var live = new IntersectionObserver(function (entries) {
      for (var i = 0; i < entries.length; i++) {
        setPaused(!entries[i].isIntersecting);
      }
    }, { rootMargin: '200px 0px 200px 0px' });
    live.observe(root);
  }

  /* ---------- runtime 載入 ---------- */

  function loadRuntime() {
    if (runtimeState === 'loading' || runtimeState === 'ready' || runtimeState === 'failed') {
      return;
    }

    if (window.rive && window.rive.Rive) {
      configureRuntime();
      return;
    }

    var src = root.getAttribute('data-rive-runtime');
    if (!src) {
      runtimeState = 'failed';
      return;
    }

    runtimeState = 'loading';

    var script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.setAttribute('data-bc-rive-runtime', '1');
    script.onload = configureRuntime;
    script.onerror = function () {
      runtimeState = 'failed';
    };
    document.head.appendChild(script);
  }

  function configureRuntime() {
    if (runtimeState === 'ready') {
      return;
    }

    var api = window.rive;
    if (!api || !api.Rive) {
      runtimeState = 'failed';
      return;
    }

    // 必須在第一個 new Rive() 之前指定；否則 runtime 會去打 unpkg 的預設路徑
    if (api.RuntimeLoader && typeof api.RuntimeLoader.setWasmUrl === 'function') {
      api.RuntimeLoader.setWasmUrl(root.getAttribute('data-rive-wasm'));
    }

    runtimeState = 'ready';

    for (var i = 0; i < icons.length; i++) {
      createIcon(icons[i], api);
    }
  }

  /* ---------- 單顆圖示 ---------- */

  function createIcon(icon, api) {
    if (!icon.src) {
      return;
    }

    try {
      icon.rive = new api.Rive({
        src: icon.src,
        canvas: icon.canvas,
        autoplay: false,
        layout: new api.Layout({
          fit: api.Fit.Contain,
          alignment: api.Alignment.Center
        }),
        onLoad: function () {
          onIconLoad(icon, api);
        },
        onLoadError: function () {
          // 單一檔案失敗就讓該格保持隱藏，其餘三格照常
          icon.rive = null;
        }
      });
    } catch (err) {
      icon.rive = null;
    }
  }

  function onIconLoad(icon, api) {
    if (!icon.rive) {
      return;
    }

    icon.names = icon.rive.animationNames || [];

    // intro 播完時 runtime 會發出 Stop（單次播放動畫會被自動移除）
    icon.rive.on(api.EventType.Stop, function (event) {
      var names = (event && event.data) || [];

      // hover 是一次性動畫，播完即停在完整圖示，只需清掉狀態標記
      if (names.indexOf(HOVER) >= 0 && icon.current === HOVER) {
        icon.current = REST;
        // hover 收尾＝回到完整圖示；游標已離開就接著排下一輪循環
        if (!icon.hovering) {
          scheduleReplay(icon);
        }
      }

      if (icon.introDone || names.indexOf(INTRO) < 0) {
        return;
      }

      // 延後一輪：避免在 runtime 的逐幀迴圈中增刪動畫實例
      window.setTimeout(function () {
        finishIntro(icon);
      }, 0);
    });

    resizeIcon(icon);

    if (icon.names.indexOf(INTRO) >= 0) {
      // 一律播 intro（含 reduced-motion）：它是唯一能把畫布帶到「絕對完整圖示」
      // 的時間軸，沒播完就沒有可靠的靜止姿勢可用。
      icon.rive.play(INTRO);
      icon.current = INTRO;
      icon.introTimer = window.setTimeout(function () {
        finishIntro(icon);
      }, INTRO_FALLBACK_MS);

      // 一般模式：立刻顯示，讓使用者看到「畫進」的入場動畫。
      // reduced-motion：先不顯示，等 intro 播完（姿勢已完整）才顯示 → 全程看不到動態。
      if (!reduceMotion) {
        reveal(icon);
      }
    } else {
      // 沒有 intro 的檔案：初始畫面本身就是完整圖示（實測 torra / blend / consumo 如此）
      icon.introDone = true;
      icon.current = REST;
      reveal(icon);
    }
  }

  /* 顯示畫布（CSS：.bc-steps__icon:not([data-riv-ready="1"]) 為 visibility: hidden） */
  function reveal(icon) {
    icon.canvas.setAttribute('data-riv-ready', '1');
  }

  function finishIntro(icon) {
    if (icon.introDone) {
      return;
    }
    window.clearTimeout(icon.introTimer);
    icon.introTimer = 0;
    icon.introDone = true;
    icon.current = REST; // intro 的自然收尾＝靜止姿勢，畫布已經停在完整圖示

    reveal(icon);

    // 使用者在 intro 期間就把游標移到圖示上 → 補播 hover
    if (icon.hovering) {
      toHover(icon);
    }

    // 自動循環：靜止 4 秒後重播 intro
    scheduleReplay(icon);
  }

  /* 回到靜止＝「什麼都不做」。
     hover 這條時間軸的結束姿勢＝它開始時的姿勢，而它一定是從 intro 留下的完整
     圖示起播，所以只要讓它自然播完，就會回到完整圖示。
     絕對不要在 hover 途中 stop()（會凍結在中間格），也不要用 scrub()
     （實例被移除時是空操作，畫布留在半途 → 圖示缺角）。 */
  function toRest(icon) {
    icon.hovering = false;

    // hover 已自然播完（回到完整圖示）→ 重新排下一輪循環；
    // hover 還在播就交給 Stop 事件處理。
    if (icon.current === REST) {
      scheduleReplay(icon);
    }
  }

  function toHover(icon) {
    icon.hovering = true;

    if (!icon.rive || reduceMotion) {
      return; // reduced-motion：完全不播 hover
    }
    if (!icon.introDone) {
      return; // intro 還在跑，交給 finishIntro 接手
    }
    if (icon.current === HOVER || icon.names.indexOf(HOVER) < 0) {
      return; // 已在播（play 只會續播、不重設時間），或該檔案沒有 hover
    }

    // 直接 play：其他時間軸都已自然播完並被 runtime 移除，不需先 stop
    icon.rive.play(HOVER);
    icon.current = HOVER;
  }

  /* ---------- 自動循環（每 4 秒重播 intro） ---------- */

  /* 這顆圖示現在適合自動重播嗎？
     - reduced-motion：不重播（使用者只該看到靜止的完整圖示）
     - 不在視口（paused）：不重播（看不到就別浪費電）
     - 檔案沒有 intro：沒有東西可重播 */
  function canLoop(icon) {
    return !reduceMotion && !icon.paused && !!icon.rive && icon.names.indexOf(INTRO) >= 0;
  }

  function clearReplay(icon) {
    window.clearTimeout(icon.replayTimer);
    icon.replayTimer = 0;
  }

  /* 排下一輪重播，delay 預設 REPLAY_MS（＝靜止 4 秒）。
     計時器只負責「時間到」，實際能不能播再檢查一次（游標可能剛好停在圖示上）。 */
  function scheduleReplay(icon, delay) {
    clearReplay(icon);
    if (!canLoop(icon)) {
      return;
    }
    icon.replayTimer = window.setTimeout(function () {
      icon.replayTimer = 0;
      // 游標停在圖示上或 hover 還在播 → 這一輪跳過；
      // 游標離開時 toRest() / hover 的 Stop 事件會重新排。
      if (icon.paused || icon.hovering || icon.current === HOVER) {
        return;
      }
      replayIntro(icon);
    }, typeof delay === 'number' ? delay : REPLAY_MS);
  }

  /* 重播 intro：單次播放的動畫播完後已被 runtime 移除，play() 會重新實例化並從
     第 0 幀開始，所以圖示會再「畫進」一次（不呼叫 stop / scrub）。 */
  function replayIntro(icon) {
    if (!canLoop(icon)) {
      return;
    }
    icon.introDone = false;
    icon.current = INTRO;
    icon.rive.play(INTRO);
    window.clearTimeout(icon.introTimer);
    icon.introTimer = window.setTimeout(function () {
      finishIntro(icon);
    }, INTRO_FALLBACK_MS);
  }

  /* ---------- 尺寸 ---------- */

  function resizeIcon(icon) {
    if (!icon.rive) {
      return;
    }
    // display: none 時量不到尺寸，跳過（避免把畫布設成 0 × 0）
    if (!icon.canvas.getClientRects().length) {
      return;
    }
    icon.rive.resizeDrawingSurfaceToCanvas(Math.min(window.devicePixelRatio || 1, 2));
  }

  function bindResize() {
    window.addEventListener('resize', function () {
      if (resizeRaf) {
        return;
      }
      resizeRaf = window.requestAnimationFrame(function () {
        resizeRaf = 0;
        for (var i = 0; i < icons.length; i++) {
          resizeIcon(icons[i]);
        }
      });
    }, false);
  }

  /* ---------- 進出視口暫停 / 續播 ---------- */

  function setPaused(paused) {
    for (var i = 0; i < icons.length; i++) {
      var icon = icons[i];
      if (!icon.rive) {
        continue;
      }
      if (paused) {
        icon.paused = true;
        clearReplay(icon); // 離開視口：別在使用者看不到時重播
        icon.rive.pause();
      } else {
        icon.paused = false;
        if (icon.current && icon.current !== REST) {
          icon.rive.play(icon.current); // 中途離開 → 續播當前時間軸
        } else if (icon.introDone) {
          scheduleReplay(icon); // 靜止狀態回到視口 → 4 秒內重播一輪
        }
      }
    }
  }

  /* ---------- 事件 ---------- */

  function bindIconEvents() {
    for (var i = 0; i < icons.length; i++) {
      bindIconEvent(icons[i]);
    }
  }

  function bindIconEvent(icon) {
    var canvas = icon.canvas;

    canvas.addEventListener('pointerenter', function (event) {
      if (event.pointerType === 'touch') {
        return; // 觸控由 pointerdown 處理
      }
      if (!icon.rive) {
        return; // runtime 尚未就緒：略過（intro 會在載入後自己播）
      }
      toHover(icon); // 內部會處理「intro 還在跑」與「已在播」兩種情況
    }, false);

    canvas.addEventListener('pointerleave', function (event) {
      if (event.pointerType === 'touch' || !icon.rive) {
        return;
      }
      // 只清狀態，不對時間軸下指令：讓 hover 自然播完即回到完整圖示
      toRest(icon);
    }, false);

    // 觸控：點一下播 hover（沒有 hover 概念，播完即回完整圖示）
    canvas.addEventListener('pointerdown', function (event) {
      if (event.pointerType === 'mouse' || !icon.rive) {
        return;
      }
      toHover(icon);
    }, false);

    // 觸控收尾：觸控不一定會發 pointerleave，若不清掉 hovering，自動循環會
    // 永遠以為「游標還在圖示上」而停擺。放開 / 取消一律回到靜止狀態。
    canvas.addEventListener('pointerup', function (event) {
      if (event.pointerType === 'mouse' || !icon.rive) {
        return;
      }
      toRest(icon);
    }, false);

    canvas.addEventListener('pointercancel', function (event) {
      if (event.pointerType === 'mouse' || !icon.rive) {
        return;
      }
      toRest(icon);
    }, false);
  }

  /* ---------- 進入點 ---------- */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
