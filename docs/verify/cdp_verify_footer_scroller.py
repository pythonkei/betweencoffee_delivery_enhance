#!/usr/bin/env python3
"""CDP 驗證：/about/ footer 的 .footer-mail-inner（email CTA）已改為共用 partial 的 .scroller-box 跑馬燈
（與 base.html ftco 頁尾逐字相同；2026-10-09 起首頁 / 亦改用同一 partial 的 #bc-brand-stage 版本）。

改動背景（2026-10-08）
  templates/.../about.html：刪 <div class="footer-mail-inner">（"Write directly to:" + mailto hello@betweencoffee.hk），
  同層插入與 base.html footer 逐字相同的 .scroller-box（2 個 BETWEEN <li>）。
  static/css/bc-brand-stage.css：移除 .footer-mail-inner 規則，新增 scoped 補償
  （#bc-brand-stage .scroller-box/.scroller/.scroller__inner/.tag-list li），
  因為 `#bc-brand-stage div,ul,li{margin:0;padding:0}`（ID 特異度）會蓋掉
  .scroller__inner{padding-block:2rem} 與 .tag-list li{padding:.1rem}。

檢查項目
  A. 舊結構已移除：.footer-mail-inner 不存在、footer 內已無 mailto:hello@betweencoffee.hk
  B. 新結構存在：.foooter-mail > .scroller-box > .scroller > ul.tag-list.scroller__inner，2 個 li（原始）
  C. JS 生效：.scroller[data-animated=true]、.scroller__inner 子節點 = 4（正本複製成 4）、aria-hidden 2 個
  D. 動畫：animation-name == scroll、animation-duration 60s / timing-function linear、play-state == running；
     取樣前先以 1×1 截圖強制產生 BeginFrame（headless tab 若無 frame producer，CSS animation 會停在
     pending：startTime=null / currentTime=0，屬驗證環境因素而非 CSS 缺陷），再驗 animation.currentTime
     前進 + transform 隨時間位移（向左、負值）；最後 pause + seek(50%) 驗 keyframes 可解析
     （to = translate(calc(-50% - 0.1rem))），且位移量 = -(inner 寬/4 + 0.1rem/2)
     （0.1rem 的 px 值各斷點不同，由 keyframe 反推，linear 內插）。
  E. 補償生效（保真基準法）：在**同一 viewport** 另開 /coffee_menu/ 量測 base.html 的 ftco 頁尾
     （.ftco-footer .scroller-box .scroller —— 2026-10-09 起這是全站唯一仍渲染靜態 ftco 頁尾的頁面），
     逐項比對 .scroller__inner padding-block、.tag-list li padding、li font-size/width、flex-wrap、
     animation（name / duration / timing-function）必須完全一致；
     桌面額外驗絕對值 32px / 1.6px / 1108px / 22px。
     （2026-10-09：首頁 / 的頁尾已改為共用 partial 的 #bc-brand-stage，基準頁因此由 / 移往 /coffee_menu/；
       首頁自身的保真度改由 J 項驗。）
  F. 幾何：.scroller 寬 <= .foooter-mail 寬 + 1；.scroller overflow == hidden；無水平溢出；
     F5/F6（2026-10-08 新增）「.foooter-mail 未撐破所屬 grid」＋「寬 <= viewport 寬」——
     舊版只驗 scroller <= mail，當 .foooter-mail 走 shrink-to-fit 被 .scroller{max-width:2000px}
     撐到 2000px（平板 1108px）時兩邊同步變大、照樣 PASS，抓不到「跑馬燈橫貫 footer」的缺陷。
  G. 相鄰文字仍在：.foooter-mail 內 .p1 仍含 "Available for" / "takeaway & Relaxing"
  H. base.html ftco 頁尾無回歸（/coffee_menu/）：.ftco-footer .scroller-box 仍 data-animated + 4 子節點
     + padding-block 32px + li 桌面值 1108px / 22px + 動畫 scroll / 60s / linear（H1–H7）
  J. 首頁 / 的 #bc-brand-stage 跑馬燈保真（2026-10-09 新增，配合首頁頁尾置換）：與 H 的 base.html 基準
     在同一 viewport 逐項一致（data-animated / 4 子節點 / padding-block / li 尺寸字級 / overflow /
     animation），且 / 已無 .ftco-footer（置換未留殘骸）。
  J11–J15（2026-10-09 新增；2026-10-13 首頁順序反轉；2026-10-18 再次改回品牌舞台第一屏）：
     2026-10-18（使用者指示）：品牌舞台（原 bc-bg-footer，現名 .bc-brand-stage-hero）回到第一屏、
     GUNTE hero 暫時 hidden（markup 與 JS 保留）。
     本檔 DOM 順序：① <section hidden class="bc-reviews-section">
     ② <section class="hero bc-brand-stage-hero">（內含 #bc-brand-stage）
     ③ <section hidden class="hero bc-gunte-hero">。
     J11 第一個「可見」section（以 computed display／visibility 判定）＝ .bc-brand-stage-hero，
         且 DOM 第一個 section 是 .bc-reviews-section 且 display:none；
     J12 .bc-brand-stage-hero 在文件順序上位於 .bc-gunte-hero 之前，且前者內仍含 #bc-brand-stage；
     J13 載入時（未捲動）品牌舞台由視口頂端開始（scrollY 0 且 0 <= rect.top <= 8
         → 與 navbar 之間沒有 100px 空隙），且 GUNTE hero computed display == none；
     J14 兩塊 hero 的 computed margin-top 皆 0px（品牌舞台由 index extra_css 的 class 規則壓為 0、
         GUNTE 由 bc-gunte-hero.css 的 class 規則壓為 0，皆不依賴 first-of-type 序位）；
     J15 / 已無 footer 元素（querySelectorAll('footer').length == 0）——置頂模組最外層改用 div
         （partials/bc_brand_stage_hero.html），bc-yama-header.js 的 document.querySelector('footer')
          因此為 null、footer 交會邏輯 no-op（否則一載入就把 tax-nav／header-bot 藏起來）。
  K1–K4（2026-10-13 新增）：GUNTE hero 的環形字（曲線標題）markup 修正 —— 使用者原先把 6 張
     不顯示的環形字開啟標籤手寫成不存在的 <hidden>（而且以 </text> 收尾，開／閉不成對）
     → 改為合法 <text class="bc-ring-hide">，由 bc-gunte-hero.css 的 display:none 隱藏
     （只有第 2 張 BUTTER KING 顯示）。
     K1 全頁已無 <hidden> 元素（getElementsByTagName('hidden') == 0）；
     K2 7 張 slide 的 .hero_slide_item_ttl SVG 各自 1 個 <text>（開／閉成對 ＝ 7）；
     K3 6 個 text.bc-ring-hide 的 computed display ＝ none；
     K4 只有 1 個環形字可見，且其文案含 "BUTTER KING"。
  K5–K7（2026-10-13 稍後，使用者指示「尺寸改動」＋「載入時就要看得到環形字」）：
     K5 環形字 computed font-size ＝ 30px（＝ calc(24px * 540/432)：把「432 參考圖寬下的 24px」
        換算成 SVG viewBox 單位 → 與 cap 14／en 12 同一套 --bc-item-k 基準）且 stroke-width
        ＝ 1.875px（＝ calc(1.5 * 540/432)，與字級同步 ×1.25）。
        ⚠ Chromium 對 SVG 幾何屬性（stroke-width）的 computed style 會保留 calc() 字面
        （回傳 "calc(1.875px)"；font-size 則解析成單一值）→ 斷言比對剝除外層 calc() 的值，
        原始字串另存 ttl_stroke_width_raw 一起印出。
        ⚠ 不可寫成 calc(var(--bc-item-k) * 24)：SVG 本身已隨 --bc-item-w 縮放 → 會與自身縮放
        重複相乘（渲染值變 24k²，短視窗桌機縮到 9.1px、手機 7.0px，比同層 cap 10px 還小）。
     K6 環形字 SVG 框寬 ＝ 投影片圖片寬（＝ --bc-item-w；本腳本量測的 1280×800 屬短視窗層
        → --bc-gunte-scale 0.55 → 297px）→ 渲染字級 ＝ 30 × 框寬/540 ＝ 24 × 框寬/432
        ＝ 16.5px（改動前 13.2px，×1.25；高 >900px 的滿版桌機框寬 432 則為 19.2 → 24px）；
     K7 載入時（未捲動）置中的 slide 是 BUTTER KING（DOM 第 2 張：aria-label「2 of 7」、
        索引 1），且該張環形字 reveal 後 computed opacity ＝ 1、display ≠ none。
        ⚠ Splide 的 start 是 **0-based 索引**（不是「第幾張」）：實測 start: 2 置中的是
        aria-label「3 of 7」＝第 3 張「果香浅煎」（環形字被隱藏）、原 start: 3 是第 4 張、
        start: 0 是第 1 張 BLACK BLEND（同樣被隱藏）→ 正解為 start: 1。
        ⚠ 量測分兩段（皆為實測踩到假 FAIL 後才加）：① 先在「.state-active 一出現、尚未逼 frame」
        時用 HERO_LOAD_JS 記下載入時置中的那張（index 存到 window.__bcHeroLoadIndex，斷言讀
        *_at_load 欄位）—— 這階段不逼 frame，否則 autoplay（interval 5000ms）會先換張；
        ② 再用 Page.captureScreenshot 逼 frame 讓 CSS transition 前進（本機 CDP 的 compositor
        不一定產 frame → transition 停在 pending：playState=running、startTime=null、
        currentTime=0，computed opacity 一直停在過渡起點 0，等 15 秒也不動；逼 frame 後
        實測 0 → 0.30 → 1，約 1 秒），等「記錄的那張」opacity 為 1 才讀值。
  J16–J19（2026-10-09，配合「置頂 hero 去掉頁尾感」）：index.html extra_css 新增
     `.bc-brand-stage-hero #bc-brand-stage{background:transparent}` / `.bc-brand-stage-hero #bc-brand-stage .footer{同上}` /
     `.bc-brand-stage-hero #bc-brand-stage .grid.is-footer{border-top:0 none}`（只覆寫首頁、不動
     bc-brand-stage.css，故 about 真頁尾不受影響）——
     J16 置頂 hero 的頂部分隔線已移除：.grid.is-footer computed border-top-width 0px / style none
         （原本 bc-brand-stage.css:152 的 1px solid rgba(255,255,255,.08)，實測繪出 y=14 的
         rgb(32,32,32) 線），且 padding-top 仍非 0；
         2026-10-18（使用者指示「距離頂部太多、主要內容要置中」）：首頁 ≥992px 的
         padding-top 改由 index.html extra_css 的置中算式提供（1440×900 → 63.8px、
         1280×800 → 52.91px；≤991px 仍是 bc-brand-stage.css 的 u-72）→ 本項只守門「非 0」；
     J17 自帶黑底已移除：#bc-brand-stage 與 .footer computed background-color 皆 rgba(0,0,0,0)
         → 由頁面自身底色穿透（body 的固定背景照片 bg_4.jpg，style-bootstrap.css:3118，
         與首頁其餘區塊一致）；
     J18 作用域錨點正確：首頁 #bc-brand-stage 的父層是 SECTION.hero.bc-brand-stage-hero（about 頁為 BODY）
         → 覆寫只命中首頁；
     J19 反向守門：同一腳本 goto /about/ 量 about 的真頁尾仍保有 1px solid 分隔線 +
         #0e0e0e 黑底、父層為 BODY（首頁覆寫未波及 about）。
  I. prefers-reduced-motion: reduce 時：不設 data-animated、仍無水平溢出（驗證防護 overflow:hidden）、
     I5/I6 同一 grid / viewport 越欄防線（2026-10-08 新增：無動畫時 li{width:1108px} 更容易撐爆欄位）
多個 viewport：桌面 1280×800 / 平板 768×1024 / 行動 390×844，各存一張 about footer 截圖。
（CDP 連線後會啟用 Network.setCacheDisabled，避免量到舊版 CSS。）
"""
import asyncio, base64, json, re, urllib.request
import websockets

BASE = "http://localhost:8081"
ROOT = "/home/kei/Desktop/betweencoffee_delivery_enhance"
CDP = "http://localhost:9222"

MEASURE_JS = r"""
(function(){
  var out = {};

  // A. 舊結構
  out.old_el_exists = !!document.querySelector('.footer-mail-inner');
  out.old_rule_refs = document.querySelectorAll('.footer-mail-inner').length;
  out.mailto_hrefs = Array.prototype.slice.call(document.querySelectorAll('a[href^="mailto:"]'))
      .map(function(a){ return a.getAttribute('href'); });

  var mail = document.querySelector('.foooter-mail');
  out.foooter_mail_found = !!mail;

  // B. 新結構
  var box = mail ? mail.querySelector('.scroller-box') : null;
  out.scroller_box_found = !!box;
  var sc = box ? box.querySelector('.scroller') : null;
  out.scroller_found = !!sc;
  var inner = sc ? sc.querySelector('.scroller__inner') : null;
  out.inner_found = !!inner;
  out.inner_is_taglist = inner ? inner.classList.contains('tag-list') : null;
  out.li_raw_count = inner ? inner.querySelectorAll(':scope > li').length : 0;
  // 原始 li = 排除 main.js 複製出的 aria-hidden 分身（正本才代表 HTML 內容）
  var origLis = inner ? Array.prototype.slice.call(inner.querySelectorAll(':scope > li'))
      .filter(function(li){ return li.getAttribute('aria-hidden') !== 'true'; }) : [];
  out.li_orig_count = origLis.length;
  out.li_texts = origLis.map(function(li){ return li.textContent.trim(); });

  // C. JS 生效
  out.data_animated = sc ? sc.getAttribute('data-animated') : null;
  out.inner_child_count = inner ? inner.children.length : 0;
  out.aria_hidden_count = inner ? inner.querySelectorAll('[aria-hidden="true"]').length : 0;

  // D. 動畫
  if (inner) {
    var ics = getComputedStyle(inner);
    out.anim_name = ics.animationName;
    out.anim_state = ics.animationPlayState;
    out.anim_duration = ics.animationDuration;
    out.anim_timing_function = ics.animationTimingFunction;
    out.transform_now = ics.transform;
    // 動畫時鐘（headless tab 無 BeginFrame 時 startTime 會停留 null = pending）
    out.anim_start_time = null;
    out.anim_current_time = null;
    var anims = inner.getAnimations ? inner.getAnimations() : [];
    out.anim_count = anims.length;
    if (anims.length) {
      out.anim_start_time = anims[0].startTime;
      out.anim_current_time = anims[0].currentTime;
    }
    out.inner_rect_w = inner.getBoundingClientRect().width;
  }
  // E. 補償
  if (inner) {
    var cs = getComputedStyle(inner);
    out.inner_pad_top = cs.paddingTop;
    out.inner_pad_bottom = cs.paddingBottom;
    out.inner_display = cs.display;
    out.inner_flex_wrap = cs.flexWrap;
    var li = inner.querySelector(':scope > li');
    if (li) {
      var lcs = getComputedStyle(li);
      out.li_pad = lcs.padding;
      out.li_width_css = lcs.width;
      out.li_font_size = lcs.fontSize;
      out.li_text_align = lcs.textAlign;
    }
  }
  // F. 幾何
  if (sc && mail) {
    var sr = sc.getBoundingClientRect(), mr = mail.getBoundingClientRect();
    out.scroller_w = Math.round(sr.width);
    out.mail_w = Math.round(mr.width);
    out.scroller_fits = sr.width <= mr.width + 1;
    out.scroller_overflow = getComputedStyle(sc).overflow;
    out.scroller_min_width = getComputedStyle(sc).minWidth;
  }
  if (box) {
    var br = box.getBoundingClientRect();
    out.box_w = Math.round(br.width);
    out.box_h = Math.round(br.height);
    out.box_fits = out.mail_w === undefined ? null : br.width <= out.mail_w + 1;
  }
  out.doc_scroll_w = document.documentElement.scrollWidth;
  out.inner_w = window.innerWidth;
  out.no_h_overflow = out.doc_scroll_w <= out.inner_w + 1;

  // F5/F6（2026-10-08 新增）：跑馬燈必須被限制在自己的 grid 欄位內。
  // 背景：F2/F3 只驗「scroller <= .foooter-mail」，當 .foooter-mail 因 justify-self:start 走
  // shrink-to-fit、被 .scroller{max-width:2000px} 撐到 2000px 時，兩邊同時變大 → 舊檢查照樣 PASS
  // （實測：平板 1108 / 行動 2000，全靠 #bc-brand-stage{overflow:hidden} 裁掉 → 視覺越欄）。
  // 故改驗「所屬 grid 不溢出」＋「不寬於 viewport」，直接抓越欄這個症狀。
  if (mail) {
    var gp = mail.parentElement;
    if (gp) {
      out.parent_grid_tag = gp.tagName.toLowerCase() + '.' + String(gp.className).replace(/\s+/g, '.');
      out.parent_grid_scroll_w = gp.scrollWidth;
      out.parent_grid_client_w = gp.clientWidth;
      out.grid_no_overflow = gp.scrollWidth <= gp.clientWidth + 1;
    }
    out.mail_fits_win = Math.round(mail.getBoundingClientRect().width) <= window.innerWidth + 1;
  }

  // G. 相鄰文字
  if (mail) {
    var p1 = mail.querySelector('.p1');
    out.p1_text = p1 ? p1.textContent.replace(/\s+/g, ' ').trim() : null;
  }

  // H. base.html ftco 頁尾（/coffee_menu/ = 保真基準；about 的 E 項會在同 viewport 比對這裡的值）
  var ft = document.querySelector('.ftco-footer .scroller-box .scroller');
  if (ft) {
    var fin = ft.querySelector('.scroller__inner');
    out.ftco_found = true;
    out.ftco_data_animated = ft.getAttribute('data-animated');
    out.ftco_child_count = fin ? fin.children.length : 0;
    out.ftco_inner_pad_top = fin ? getComputedStyle(fin).paddingTop : null;
    out.ftco_inner_pad_bottom = fin ? getComputedStyle(fin).paddingBottom : null;
    out.ftco_overflow = getComputedStyle(ft).overflow;
    out.ftco_inner_flex_wrap = fin ? getComputedStyle(fin).flexWrap : null;
    if (fin) {
      var fics = getComputedStyle(fin);
      out.ftco_anim_name = fics.animationName;
      out.ftco_anim_duration = fics.animationDuration;
      out.ftco_anim_timing_function = fics.animationTimingFunction;
      out.ftco_anim_state = fics.animationPlayState;
    }
    var fli = fin ? fin.querySelector(':scope > li') : null;
    if (fli) {
      var flcs = getComputedStyle(fli);
      out.ftco_li_pad = flcs.padding;
      out.ftco_li_width_css = flcs.width;
      out.ftco_li_font_size = flcs.fontSize;
      out.ftco_li_text_align = flcs.textAlign;
    }
  }
  // J. 首頁 / 的 #bc-brand-stage 跑馬燈（2026-10-09：首頁頁尾改用共用 partial，保真度與 base.html 比對）
  var bg = document.querySelector('#bc-brand-stage .foooter-mail .scroller')
        || document.querySelector('#bc-brand-stage .scroller');
  out.bg_found = !!bg;
  out.index_ftco_count = document.querySelectorAll('.ftco-footer').length;
  if (bg) {
    var bin = bg.querySelector('.scroller__inner');
    out.bg_data_animated = bg.getAttribute('data-animated');
    out.bg_child_count = bin ? bin.children.length : 0;
    out.bg_overflow = getComputedStyle(bg).overflow;
    if (bin) {
      var bics = getComputedStyle(bin);
      out.bg_inner_pad_top = bics.paddingTop;
      out.bg_inner_pad_bottom = bics.paddingBottom;
      out.bg_inner_flex_wrap = bics.flexWrap;
      out.bg_anim_name = bics.animationName;
      out.bg_anim_duration = bics.animationDuration;
      out.bg_anim_timing_function = bics.animationTimingFunction;
    }
    var bli = bin ? bin.querySelector(':scope > li') : null;
    if (bli) {
      var blcs = getComputedStyle(bli);
      out.bg_li_pad = blcs.padding;
      out.bg_li_width_css = blcs.width;
      out.bg_li_font_size = blcs.fontSize;
      out.bg_li_text_align = blcs.textAlign;
    }
  }
  return out;
})()
"""

# 首頁 hero 順序／位置（2026-10-09 建立；2026-10-13 順序反轉；2026-10-18 改回品牌舞台第一屏）
# 2026-10-18（使用者指示）：品牌舞台（#bc-brand-stage）回到第一屏、GUNTE hero 加 hidden。
INDEX_HERO_JS = r"""
(function(){
  var out = {};
  var pc = document.querySelector('.bc-page-content');
  var secs = pc ? Array.prototype.slice.call(pc.querySelectorAll(':scope > section')) : [];
  function isVisible(el){
    var cs = getComputedStyle(el);
    return cs.display !== 'none' && cs.visibility !== 'hidden';
  }
  var vis = secs.filter(isVisible);
  out.section_count = secs.length;
  out.section_classes = secs.map(function(s){ return s.className || s.tagName.toLowerCase(); });
  out.first_visible_classes = vis.length ? vis[0].className : null;
  out.first_visible_is_stage = !!(vis.length && vis[0].classList.contains('bc-brand-stage-hero'));
  out.first_visible_is_gunte = !!(vis.length && vis[0].classList.contains('bc-gunte-hero'));
  out.first_dom_classes = secs.length
      ? (secs[0].className || secs[0].tagName.toLowerCase()) : null;
  out.first_dom_display = secs.length ? getComputedStyle(secs[0]).display : null;

  var gunte = document.querySelector('.bc-gunte-hero');
  var wrap = document.querySelector('.bc-brand-stage-hero');
  var root = document.getElementById('bc-brand-stage');
  out.gunte_found = !!gunte;
  out.bg_hero_found = !!wrap;
  out.hero_has_root = !!(root && wrap && wrap.contains(root));
  if (gunte && wrap) {
    // 2026-10-18：品牌舞台在 GUNTE 之前 → wrap.compareDocumentPosition(gunte) 會帶 FOLLOWING
    out.stage_before_gunte =
      (wrap.compareDocumentPosition(gunte) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
    // 舊欄位（2026-10-13 的順序）保留作診斷：GUNTE 在舞台之前時為 true
    out.gunte_before_wrap =
      (gunte.compareDocumentPosition(wrap) & Node.DOCUMENT_POSITION_FOLLOWING) !== 0;
  } else {
    out.stage_before_gunte = null;
    out.gunte_before_wrap = null;
  }
  out.gunte_display = gunte ? getComputedStyle(gunte).display : null;
  out.gunte_hidden_attr = gunte ? gunte.hasAttribute('hidden') : null;
  if (gunte) {
    var gr = gunte.getBoundingClientRect();
    out.gunte_top = Math.round(gr.top);
    out.gunte_h = Math.round(gr.height);
    out.gunte_margin_top = getComputedStyle(gunte).marginTop;
  }
  if (wrap) {
    var wr = wrap.getBoundingClientRect();
    out.hero_top = Math.round(wr.top);
    out.hero_h = Math.round(wr.height);
    out.hero_margin_top = getComputedStyle(wrap).marginTop;
  }
  if (root) out.footer_root_top = Math.round(root.getBoundingClientRect().top);
  out.inner_h = window.innerHeight;
  out.scroll_y = Math.round(window.scrollY);
  out.footer_tag_count = document.querySelectorAll('footer').length;

  // 2026-10-13：GUNTE hero 的環形字（曲線標題）—— markup 合法性與可見性。
  // 原 markup 把 6 張不顯示的環形字開啟標籤寫成不存在的 <hidden>（且以 </text> 收尾）→ 已改為
  // <text class="bc-ring-hide">，由 bc-gunte-hero.css 的 display:none 隱藏（只留 BUTTER KING）。
  out.hidden_tag_count = document.getElementsByTagName('hidden').length;
  var ttlSvgs = document.querySelectorAll('.bc-gunte-hero .hero_slide_item_ttl');
  var ttlTexts = document.querySelectorAll('.bc-gunte-hero .hero_slide_item_ttl text');
  out.ttl_svg_count = ttlSvgs.length;
  out.ttl_text_count = ttlTexts.length;
  out.ttl_ring_hide_count = document.querySelectorAll(
      '.bc-gunte-hero .hero_slide_item_ttl text.bc-ring-hide').length;
  out.ttl_hidden_by_css = 0;
  out.ttl_visible_texts = [];
  Array.prototype.forEach.call(ttlTexts, function(t){
    if (getComputedStyle(t).display === 'none') {
      out.ttl_hidden_by_css++;
    } else {
      out.ttl_visible_texts.push(t.textContent.trim());
    }
  });

  // 2026-10-13 稍後：環形字尺寸（K5／K6）——字級改由「432 參考寬的 24px」換算成 viewBox 單位。
  var ttlSvg0 = document.querySelector('.bc-gunte-hero .hero_slide_item_ttl');
  if (ttlSvg0 && ttlSvg0.querySelector('text')) {
    var tcs = getComputedStyle(ttlSvg0.querySelector('text'));
    out.ttl_font_size = tcs.fontSize;        // 期望 30px（＝calc(24px*540/432)）
    // ⚠ Chromium 對 SVG 幾何屬性（stroke-width）的 computed style 會「保留 calc() 字面」
    // （回傳 'calc(1.875px)'；font-size 這類則會解析成單一值 '30px'）→ 比對前先剝掉外層 calc()，
    // 原始字串另存 ttl_stroke_width_raw 一起印出（避免看起來像斷言把值「洗」過）。
    out.ttl_stroke_width_raw = tcs.strokeWidth;
    out.ttl_stroke_width = String(tcs.strokeWidth).replace(/^calc\((.*)\)$/, '$1');
    out.ttl_box_w = Math.round(ttlSvg0.getBoundingClientRect().width * 100) / 100;
    out.ttl_rendered_font = Math.round(parseFloat(tcs.fontSize) * out.ttl_box_w / 540 * 100) / 100;
    // 環形字框應與投影片圖片同寬（＝--bc-item-w；1280×800 屬短視窗層 → scale 0.55 → 297px）
    var ttlImg = document.querySelector('.bc-gunte-hero .hero_slide_item_img img.hide-sp');
    out.ttl_item_img_w = ttlImg
        ? Math.round(ttlImg.getBoundingClientRect().width * 100) / 100 : null;
  } else {
    out.ttl_font_size = null;
    out.ttl_stroke_width = null;
    out.ttl_stroke_width_raw = null;
    out.ttl_box_w = null;
    out.ttl_rendered_font = null;
    out.ttl_item_img_w = null;
  }

  // 2026-10-13 稍後：載入時置中那張的環形字（K7）——Splide start 3 → 1（start 為 0-based）。
  // ① 「載入時置中的是哪一張」由前置的 HERO_LOAD_JS 記到 window.__bcHeroLoadIndex
  //    （在 .state-active 一出現、尚未逼 frame 前就記錄 → 不受 autoplay 5s 後換張影響）；
  // ② 下面的 active_slide_* 則是「讀值當下」置中的那一張（autoplay 可能已前進），僅作診斷。
  var sliList = document.querySelectorAll('.bc-gunte-hero .splide__slide');
  var li = (typeof window.__bcHeroLoadIndex === 'number') ? window.__bcHeroLoadIndex : -1;
  var loadSlide = li >= 0 ? sliList[li] : null;
  var loadTtl = loadSlide ? loadSlide.querySelector('.hero_slide_item_ttl') : null;
  var loadTtlText = loadTtl ? loadTtl.querySelector('text') : null;
  out.active_slide_index_at_load = li >= 0 ? li : null;
  out.active_slide_is_butter_king_at_load = loadSlide
      ? loadSlide.textContent.indexOf('BUTTER KING') !== -1 : null;
  out.active_slide_aria_label_at_load = loadSlide ? loadSlide.getAttribute('aria-label') : null;
  out.active_ttl_opacity_at_load = loadTtl ? getComputedStyle(loadTtl).opacity : null;
  out.active_ttl_text_display_at_load = loadTtlText
      ? getComputedStyle(loadTtlText).display : null;

  var activeSlide = document.querySelector('.bc-gunte-hero .splide__slide.state-active');
  out.active_slide_is_butter_king = !!activeSlide
      && activeSlide.textContent.indexOf('BUTTER KING') !== -1;
  out.active_slide_index = activeSlide
      ? Array.prototype.indexOf.call(sliList, activeSlide)
      : null;
  out.active_slide_aria_label = activeSlide ? activeSlide.getAttribute('aria-label') : null;
  var activeTtl = activeSlide ? activeSlide.querySelector('.hero_slide_item_ttl') : null;
  out.active_ttl_opacity = activeTtl ? getComputedStyle(activeTtl).opacity : null;
  var activeTtlText = activeTtl ? activeTtl.querySelector('text') : null;
  out.active_ttl_text_display = activeTtlText
      ? getComputedStyle(activeTtlText).display : null;

  // 2026-10-09（使用者指示）：置頂 hero 去掉「頁尾感」——移除頂部 1px 分隔線與自帶黑底。
  // 這三組值由 index.html extra_css 的 .bc-brand-stage-hero #bc-brand-stage … 覆寫提供；
  // about 頁（真頁尾）不受影響，由下方 ABOUT_GUARD_JS 反向確認。
  if (root) {
    var grid = root.querySelector('.grid.is-footer');
    var fdiv = root.querySelector('.footer');
    out.grid_found = !!grid;
    if (grid) {
      var gs = getComputedStyle(grid);
      out.grid_border_top_w = gs.borderTopWidth;
      out.grid_border_top_style = gs.borderTopStyle;
      out.grid_border_top_color = gs.borderTopColor;
      out.grid_padding_top = gs.paddingTop;
    }
    out.root_bg = getComputedStyle(root).backgroundColor;
    out.footer_bg = fdiv ? getComputedStyle(fdiv).backgroundColor : null;
    out.root_parent_tag = root.parentElement ? root.parentElement.tagName : null;
    out.root_parent_classes = root.parentElement ? root.parentElement.className : null;
  }
  return out;
})()
"""

# 2026-10-13 稍後（K7 前置）：在「.state-active 一出現、尚未逼 frame」時記錄『載入時置中的那一張』，
# 並把 index 存到 window.__bcHeroLoadIndex 供 INDEX_HERO_JS 讀回（*_at_load 系列欄位）。
# [為什麼要分兩段] 逼 frame（Page.captureScreenshot，見下方 J11 段說明）會讓 CSS transition 前進、
# 但也會讓 Splide autoplay（interval 5000ms）真的走動 —— 讀值當下的 .state-active 可能已經不是
# 載入時那張，所以「載入時是哪一張」必須在逼 frame 之前先記下來。
HERO_LOAD_JS = r"""
(function(){
  var sli = document.querySelectorAll('.bc-gunte-hero .splide__slide');
  var idx = -1;
  for (var i = 0; i < sli.length; i++) {
    if (sli[i].classList.contains('state-active')) { idx = i; break; }
  }
  var s = idx >= 0 ? sli[idx] : null;
  var t = s ? s.querySelector('.hero_slide_item_ttl') : null;
  var tt = t ? t.querySelector('text') : null;
  if (idx >= 0) { window.__bcHeroLoadIndex = idx; }
  return {
    index: idx >= 0 ? idx : null,
    aria_label: s ? s.getAttribute('aria-label') : null,
    is_butter_king: s ? s.textContent.indexOf('BUTTER KING') !== -1 : null,
    ttl_opacity: t ? getComputedStyle(t).opacity : null,
    ttl_text_display: tt ? getComputedStyle(tt).display : null
  };
})()
"""

# /about/ 反向守門（2026-10-09）：本頁覆寫只加 .bc-brand-stage-hero 前綴 → about 的真頁尾必須「仍有」
# 1px 分隔線與 #0e0e0e 黑底；且其 #bc-brand-stage 的父層是 BODY（不是 SECTION.bc-brand-stage-hero），
# 證明作用域錨點正確、沒有誤傷 about。
ABOUT_GUARD_JS = r"""
(function(){
  var root = document.getElementById('bc-brand-stage');
  if (!root) return {found: false};
  var grid = root.querySelector('.grid.is-footer');
  var fdiv = root.querySelector('.footer');
  var gs = grid ? getComputedStyle(grid) : null;
  return {
    found: true,
    border_w: gs ? gs.borderTopWidth : null,
    border_style: gs ? gs.borderTopStyle : null,
    border_color: gs ? gs.borderTopColor : null,
    root_bg: getComputedStyle(root).backgroundColor,
    footer_bg: fdiv ? getComputedStyle(fdiv).backgroundColor : null,
    parent_tag: root.parentElement ? root.parentElement.tagName : null,
    parent_classes: root.parentElement ? root.parentElement.className : null
  };
})()
"""

# 動畫取樣：transform + 動畫時鐘（startTime / currentTime）
ANIM_SAMPLE_JS = r"""
(function(){
  var i = document.querySelector('.foooter-mail .scroller__inner');
  if (!i) return null;
  var a = (i.getAnimations ? i.getAnimations() : []);
  return {
    t: getComputedStyle(i).transform,
    count: a.length,
    start: a.length ? a[0].startTime : null,
    now: a.length ? a[0].currentTime : null
  };
})()
"""

# 動畫確定性驗證：pause + seek 到 50%（30s），讀 computed transform 與 keyframes，再復原播放
ANIM_SEEK_JS = r"""
(function(){
  var i = document.querySelector('.foooter-mail .scroller__inner');
  if (!i || !i.getAnimations) return null;
  var a = i.getAnimations()[0];
  if (!a) return null;
  var w = i.getBoundingClientRect().width;
  a.pause();
  a.currentTime = 30000;            // 60s 的 50%
  var t = getComputedStyle(i).transform;
  var kf = [];
  try { kf = a.effect.getKeyframes().map(function(k){ return k.transform || null; }); } catch (e) {}
  a.currentTime = 0;
  a.play();                          // 復原，後續截圖維持跑馬燈起點
  return { w: w, t: t, keyframes: kf };
})()
"""


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail != '' else ''}")
    return bool(ok)



async def main():
    req = urllib.request.Request(f"{CDP}/json/new?about:blank", method="PUT")
    tab = json.loads(urllib.request.urlopen(req).read())
    ws_url = tab["webSocketDebuggerUrl"]
    failures = []

    async with websockets.connect(ws_url, max_size=200 * 1024 * 1024) as ws:
        mid = 1

        def msg(m, p=None):
            nonlocal mid
            m = {"id": mid, "method": m, "params": p or {}}
            mid += 1
            return m

        async def send(m):
            await ws.send(json.dumps(m))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == m["id"]:
                    return r.get("result", {})

        await send(msg("Page.enable"))
        await send(msg("Runtime.enable"))
        # 避免讀到舊版 bc-brand-stage.css（本次改了補償規則，需確保量到的是最新 CSS）
        await send(msg("Network.enable"))
        await send(msg("Page.setCacheDisabled", {"cacheDisabled": True}))
        await send(msg("Network.setCacheDisabled", {"cacheDisabled": True}))

        async def evaljs(expr):
            r = await send(msg("Runtime.evaluate", {"expression": expr, "returnByValue": True}))
            res = r.get("result", {})
            if res.get("subtype") == "error":
                print("   JS error:", res.get("description"))
            return res.get("value")

        async def goto(url):
            await send(msg("Page.navigate", {"url": url}))
            for _ in range(60):
                await asyncio.sleep(0.25)
                # 2026-10-09：除 readyState 外必須同時確認 location.href 已切到目標 URL ——
                # Page.navigate 之後、新 document 尚未 commit 前，舊頁面的 readyState 仍然是
                # 'complete'，只驗 readyState 會提早跳出，並在「上一個頁面」上量測。
                # （實測：/about/ 390x844 迴圈裡的 /coffee_menu/ 基準量測偶發落在 about 頁，
                #   ftco_* 全為 None → E1–E4/E6 假 FAIL。加上 href 條件後即為確定性。）
                if await evaljs("document.readyState === 'complete' && location.href === "
                                + json.dumps(url)):
                    break
            await asyncio.sleep(1.2)  # 等 main.js 初始化 .scroller

        async def set_viewport(w, h):
            await send(msg("Emulation.setDeviceMetricsOverride",
                           {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False}))
            await asyncio.sleep(0.4)

        async def shot(name, sel=".foooter-mail"):
            rr = await evaljs(
                "(function(){var e=document.querySelector('" + sel + "');"
                "if(!e)return null;var r=e.getBoundingClientRect();"
                "return {x:r.left+window.scrollX,y:r.top+window.scrollY,w:r.width,h:r.height};})()")
            if not rr:
                print(f"   shot skipped (no {sel})")
                return
            res = await send(msg("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True,
                "clip": {"x": rr["x"], "y": rr["y"], "width": rr["w"], "height": rr["h"], "scale": 1}}))
            data = res.get("data")
            if data:
                path = f"{ROOT}/_verify_footer_scroller_{name}.png"
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                print(f"   shot -> {path}")


        async def force_frames(n=2):
            """強制 headless tab 產生 BeginFrame。

            本 CDP tab 沒有 frame producer，CSS animation 會停在 pending
            （startTime=null / currentTime=0、computed transform 為 identity），
            要先用 1×1 截圖逼出 frame，動畫才會取得 startTime 並隨時間前進。
            這是驗證環境（非 CSS）因素：標準 Chrome 視窗會正常播動畫。
            """
            for _ in range(n):
                await send(msg("Page.captureScreenshot", {
                    "format": "png",
                    "clip": {"x": 0, "y": 0, "width": 1, "height": 1, "scale": 1}}))


        # ================= /about/：各 viewport =================
        for w, h, name in ((1280, 800, "desktop"), (768, 1024, "tablet"), (390, 844, "mobile")):
            await set_viewport(w, h)
            await goto(f"{BASE}/about/")
            await evaljs("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.0)
            # 先逼出 frame，讓 CSS animation 從 pending 進入 running 後才量測
            await force_frames(2)
            m = await evaljs(MEASURE_JS) or {}

            print(f"\n=== /about/ {w}x{h} ({name}) ===")
            # A
            failures.append(check("A1 .footer-mail-inner 已移除", m.get("old_el_exists") is False,
                                  m.get("old_rule_refs")))
            failures.append(check("A2 footer 內無 mailto:hello@betweencoffee.hk",
                                  not any("hello@betweencoffee.hk" in (x or "")
                                          for x in (m.get("mailto_hrefs") or [])),
                                  m.get("mailto_hrefs")))
            # B
            failures.append(check("B1 .foooter-mail 存在", m.get("foooter_mail_found") is True))
            failures.append(check("B2 .scroller-box 存在", m.get("scroller_box_found") is True))
            failures.append(check("B3 ul.tag-list.scroller__inner 存在",
                                  m.get("inner_found") is True and m.get("inner_is_taglist") is True))
            failures.append(check("B4 原始（非複製）li = 2 且文字為 12 次 BETWEEN 串",
                                  m.get("li_orig_count") == 2
                                  and len(m.get("li_texts") or []) == 2
                                  and all(t.startswith("BETWEEN") and t.count("BETWEEN") == 12
                                          for t in (m.get("li_texts") or [])),
                                  f"原始 {m.get('li_orig_count')} / 全部 {m.get('li_raw_count')}"
                                  f"（文字 {[t.count('BETWEEN') for t in (m.get('li_texts') or [])]}）"))
            # C
            failures.append(check("C1 data-animated=true", m.get("data_animated") == "true",
                                  m.get("data_animated")))
            failures.append(check("C2 .scroller__inner 子節點 = 4（無縫循環）",
                                  m.get("inner_child_count") == 4, m.get("inner_child_count")))
            failures.append(check("C3 複製品 aria-hidden = 2", m.get("aria_hidden_count") == 2,
                                  m.get("aria_hidden_count")))
            # D
            failures.append(check("D1 animation-name = scroll", m.get("anim_name") == "scroll",
                                  m.get("anim_name")))
            failures.append(check("D2 animation-play-state = running", m.get("anim_state") == "running",
                                  m.get("anim_state")))
            failures.append(check("D2b animation 60s / linear / infinite（與 style-utilities.css 一致）",
                                  m.get("anim_duration") == "60s"
                                  and m.get("anim_timing_function") == "linear",
                                  f"{m.get('anim_duration')} {m.get('anim_timing_function')}"))
            t1 = m.get("transform_now")
            failures.append(check("D3 keyframes / 動畫時鐘存在（computed 有 animation）",
                                  (m.get("anim_count") or 0) >= 1
                                  and m.get("anim_start_time") is not None,
                                  f"animations={m.get('anim_count')} startTime={m.get('anim_start_time')}"
                                  f" currentTime={m.get('anim_current_time')}"))
            # 本 tab 無 frame producer → 取樣前先逼出 BeginFrame，動畫才會前進
            await force_frames(2)
            s1 = await evaljs(ANIM_SAMPLE_JS) or {}
            await asyncio.sleep(0.8)
            await force_frames(2)
            s2 = await evaljs(ANIM_SAMPLE_JS) or {}
            failures.append(check("D4 animation.currentTime 隨時間前進（動畫真的在跑）",
                                  s1.get("now") is not None and s2.get("now") is not None
                                  and s2.get("now") > s1.get("now"),
                                  f"currentTime {s1.get('now')} -> {s2.get('now')}"))
            failures.append(check("D5 transform 隨時間往左位移（負值，非 identity）",
                                  s1.get("t") not in (None, "none")
                                  and s2.get("t") not in (None, "none")
                                  and s1.get("t") != s2.get("t")
                                  and s2.get("t") != "matrix(1, 0, 0, 1, 0, 0)",
                                  f"量測時 {t1}；取樣 {s1.get('t')} -> {s2.get('t')}"))
            # D6 確定性驗證（與 frame 產生無關）：seek 到 50% 應為 -(inner寬/4 + 0.1rem/2)
            # 0.1rem 在不同斷點的 px 值不同（html font-size 會變），故直接由 keyframe 的
            # calc(-50% - Npx) 反推 N，不寫死 1.6px，讓三個 viewport 都是精確比對。
            seek = await evaljs(ANIM_SEEK_JS) or {}
            kf_list = seek.get("keyframes") or []
            kf_end = next((k for k in kf_list if k and "translate" in k), None)
            mm_end = re.search(r"calc\(-50% - ([\d.]+)px\)", kf_end or "")
            kf_px = float(mm_end.group(1)) if mm_end else None
            exp_tx = None
            got_tx = None
            try:
                w_inner = float(seek.get("w") or 0)
                exp_tx = -(w_inner / 4 + (kf_px if kf_px is not None else 0.8) / 2)
                mm = re.match(r"matrix\(1, 0, 0, 1, (-?[\d.]+), (-?[\d.]+)\)", seek.get("t") or "")
                got_tx = float(mm.group(1)) if mm else None
            except Exception:
                got_tx = None
            failures.append(check("D6 pause+seek 50% 位移量 = -(inner寬/4 + 0.1rem/2)（keyframes 有效）",
                                  got_tx is not None and exp_tx is not None and abs(got_tx - exp_tx) <= 2.0,
                                  f"got {got_tx} vs expected {None if exp_tx is None else round(exp_tx, 2)}"
                                  f"（inner 寬 {seek.get('w')}、0.1rem={kf_px}px）"))
            failures.append(check("D7 keyframes 解析出 translate 終點（to = translate calc(-50% - .1rem)）",
                                  kf_px is not None
                                  and re.fullmatch(r"translate\(calc\(-50% - [\d.]+px\)\)", kf_end or "")
                                  is not None,
                                  f"{kf_list} -> 0.1rem = {kf_px}px"))
            await shot(name)  # 先截 about 頁（下方 E 會切到 /coffee_menu/ 取基準）
            # E（保真基準法：同一 viewport 的 base.html ftco 頁尾計算值即為正解；不寫死單一斷點數值）
            await goto(f"{BASE}/coffee_menu/")
            mi = await evaljs(MEASURE_JS) or {}
            print(f"   [基準] base.html ftco 頁尾 @ {w}x{h}：inner {mi.get('ftco_inner_pad_top')}/"
                  f"{mi.get('ftco_inner_pad_bottom')}、li {mi.get('ftco_li_pad')} "
                  f"{mi.get('ftco_li_font_size')} {mi.get('ftco_li_width_css')} "
                  f"wrap={mi.get('ftco_inner_flex_wrap')}")
            failures.append(check("E1 .scroller__inner padding-block 與 /coffee_menu/ ftco 頁尾一致（補償生效）",
                                  m.get("inner_pad_top") == mi.get("ftco_inner_pad_top")
                                  and m.get("inner_pad_bottom") == mi.get("ftco_inner_pad_bottom")
                                  and m.get("inner_pad_top") not in (None, "0px"),
                                  f"about {m.get('inner_pad_top')}/{m.get('inner_pad_bottom')}"
                                  f" vs ftco {mi.get('ftco_inner_pad_top')}/{mi.get('ftco_inner_pad_bottom')}"))
            failures.append(check("E2 .tag-list li padding 與 /coffee_menu/ ftco 頁尾一致（補償生效）",
                                  m.get("li_pad") == mi.get("ftco_li_pad")
                                  and m.get("li_pad") not in (None, "0px"),
                                  f"about {m.get('li_pad')} vs ftco {mi.get('ftco_li_pad')}"))
            failures.append(check("E3 li font-size/width 與 /coffee_menu/ ftco 頁尾一致（未被 reset 影響）",
                                  m.get("li_font_size") == mi.get("ftco_li_font_size")
                                  and m.get("li_width_css") == mi.get("ftco_li_width_css"),
                                  f"about {m.get('li_font_size')}/{m.get('li_width_css')}"
                                  f" vs ftco {mi.get('ftco_li_font_size')}/{mi.get('ftco_li_width_css')}"))
            failures.append(check("E4 .scroller__inner flex-wrap 與 /coffee_menu/ ftco 頁尾一致（跑馬燈皆 nowrap）",
                                  m.get("inner_flex_wrap") is not None
                                  and m.get("inner_flex_wrap") == mi.get("ftco_inner_flex_wrap"),
                                  f"about {m.get('inner_flex_wrap')} vs ftco {mi.get('ftco_inner_flex_wrap')}"))
            failures.append(check("E6 animation 屬性與 /coffee_menu/ ftco 頁尾一致（name / duration / timing）",
                                  m.get("anim_name") is not None
                                  and m.get("anim_name") == mi.get("ftco_anim_name")
                                  and m.get("anim_duration") == mi.get("ftco_anim_duration")
                                  and m.get("anim_timing_function") == mi.get("ftco_anim_timing_function"),
                                  f"about {m.get('anim_name')}/{m.get('anim_duration')}/"
                                  f"{m.get('anim_timing_function')} vs ftco {mi.get('ftco_anim_name')}/"
                                  f"{mi.get('ftco_anim_duration')}/{mi.get('ftco_anim_timing_function')}"))
            if name == "desktop":
                # 桌面另驗絕對值，保留原本可追溯的硬性數值（2rem / .1rem / 桌面 li 尺寸）
                failures.append(check("E5 桌面絕對值 inner 32px / li 1.6px / 1108px / 22px",
                                      m.get("inner_pad_top") == "32px"
                                      and m.get("inner_pad_bottom") == "32px"
                                      and m.get("li_pad") == "1.6px"
                                      and m.get("li_width_css") == "1108px"
                                      and m.get("li_font_size") == "22px",
                                      f"{m.get('inner_pad_top')}/{m.get('inner_pad_bottom')}、"
                                      f"{m.get('li_pad')}、{m.get('li_width_css')}、{m.get('li_font_size')}"))
            # F
            failures.append(check("F1 .scroller overflow = hidden", m.get("scroller_overflow") == "hidden",
                                  m.get("scroller_overflow")))
            failures.append(check("F2 .scroller 寬 <= .foooter-mail 寬", m.get("scroller_fits") is True,
                                  f"{m.get('scroller_w')} <= {m.get('mail_w')}"))
            failures.append(check("F3 .scroller-box 不超出 .foooter-mail", m.get("box_fits") is True,
                                  f"{m.get('box_w')} / {m.get('mail_w')}"))
            failures.append(check("F4 無水平溢出", m.get("no_h_overflow") is True,
                                  f"scrollW {m.get('doc_scroll_w')} vs innerW {m.get('inner_w')}"))
            failures.append(check("F5 .foooter-mail 未撐破所屬 grid（跑馬燈不越欄）",
                                  m.get("grid_no_overflow") is True,
                                  f"grid scrollW {m.get('parent_grid_scroll_w')} vs clientW "
                                  f"{m.get('parent_grid_client_w')}（{m.get('parent_grid_tag')}）"))
            failures.append(check("F6 .foooter-mail 寬 <= viewport 寬（跑馬燈被欄位裁切、不橫貫全寬）",
                                  m.get("mail_fits_win") is True,
                                  f"{m.get('mail_w')} <= {m.get('inner_w')}"))
            # G
            failures.append(check("G1 \"Available for takeaway & Relaxing\" 仍在",
                                  "Available for" in (m.get("p1_text") or "")
                                  and "takeaway" in (m.get("p1_text") or ""),
                                  m.get("p1_text")))

        # ================= /coffee_menu/ ：base.html ftco 頁尾回歸（保真基準） =================
        await set_viewport(1280, 800)
        await goto(f"{BASE}/coffee_menu/")
        m2 = await evaljs(MEASURE_JS) or {}
        print("\n=== /coffee_menu/ (base.html ftco 頁尾回歸) 1280x800 ===")
        failures.append(check("H1 .ftco-footer .scroller 存在", m2.get("ftco_found") is True))
        failures.append(check("H2 data-animated=true", m2.get("ftco_data_animated") == "true",
                              m2.get("ftco_data_animated")))
        failures.append(check("H3 子節點 = 4", m2.get("ftco_child_count") == 4,
                              m2.get("ftco_child_count")))
        failures.append(check("H4 padding-block = 32px（未被本次 CSS 影響）",
                              m2.get("ftco_inner_pad_top") == "32px"
                              and m2.get("ftco_inner_pad_bottom") == "32px",
                              f"{m2.get('ftco_inner_pad_top')} / {m2.get('ftco_inner_pad_bottom')}"))
        failures.append(check("H5 overflow = hidden", m2.get("ftco_overflow") == "hidden",
                              m2.get("ftco_overflow")))
        failures.append(check("H6 li 桌面尺寸仍為 1108px / 22px（本斷點絕對值）",
                              m2.get("ftco_li_width_css") == "1108px"
                              and m2.get("ftco_li_font_size") == "22px",
                              f"{m2.get('ftco_li_width_css')} / {m2.get('ftco_li_font_size')}"))
        failures.append(check("H7 base.html ftco footer animation 仍為 scroll / 60s / linear（未受本次 CSS 影響）",
                              m2.get("ftco_anim_name") == "scroll"
                              and m2.get("ftco_anim_duration") == "60s"
                              and m2.get("ftco_anim_timing_function") == "linear",
                              f"{m2.get('ftco_anim_name')}/{m2.get('ftco_anim_duration')}/"
                              f"{m2.get('ftco_anim_timing_function')}"))
        await shot("coffee_menu_ftco_footer", ".ftco-footer .scroller-box")

        # ================= / ：#bc-brand-stage 保真（與上方 H 基準逐項比對） =================
        await set_viewport(1280, 800)
        # 2026-10-13 稍後（K7 用）：**不用 goto()** —— 它會等到 readyState complete 再 +1.2s，
        # 暖機狀態下（compositor 正在產 frame）Splide autoplay（interval 5000ms）可能已經換張，
        # 之後才記錄就會記到第 2 張之後（實測 shot 腳本固定 sleep 5s 曾記到 index 4）。
        # 改為 navigate 後立刻以 0.1s 間隔輪詢 .state-active，一出現就記錄（HERO_LOAD_JS）。
        # 前一頁是 /coffee_menu/（無 .bc-gunte-hero）→ 舊 document 階段輪詢必為 null，不會誤判。
        await send(msg("Page.navigate", {"url": f"{BASE}/"}))
        hero_load = {}
        for _ in range(150):
            hero_load = await evaljs(HERO_LOAD_JS) or {}
            if hero_load.get("index") is not None:
                break
            await asyncio.sleep(0.1)
        print("   [hero] 載入時置中: " + json.dumps(hero_load, ensure_ascii=False))
        mj = await evaljs(MEASURE_JS) or {}
        print("\n=== / (#bc-brand-stage 保真) 1280x800 ===")
        failures.append(check("J1 首頁 #bc-brand-stage .scroller 存在（已改用共用 partial）",
                              mj.get("bg_found") is True))
        failures.append(check("J2 首頁已無 .ftco-footer（頁尾只剩 #bc-brand-stage）",
                              mj.get("index_ftco_count") == 0, mj.get("index_ftco_count")))
        failures.append(check("J3 data-animated=true", mj.get("bg_data_animated") == "true",
                              mj.get("bg_data_animated")))
        failures.append(check("J4 子節點數與 /coffee_menu/ ftco 一致（4）",
                              mj.get("bg_child_count") == m2.get("ftco_child_count"),
                              f"{mj.get('bg_child_count')} vs {m2.get('ftco_child_count')}"))
        failures.append(check("J5 padding-block 與 /coffee_menu/ ftco 一致",
                              mj.get("bg_inner_pad_top") == m2.get("ftco_inner_pad_top")
                              and mj.get("bg_inner_pad_bottom") == m2.get("ftco_inner_pad_bottom")
                              and mj.get("bg_inner_pad_top") not in (None, "0px"),
                              f"{mj.get('bg_inner_pad_top')}/{mj.get('bg_inner_pad_bottom')}"
                              f" vs {m2.get('ftco_inner_pad_top')}/{m2.get('ftco_inner_pad_bottom')}"))
        failures.append(check("J6 overflow 與 /coffee_menu/ ftco 一致（皆 hidden）",
                              mj.get("bg_overflow") == m2.get("ftco_overflow")
                              and mj.get("bg_overflow") == "hidden",
                              f"{mj.get('bg_overflow')} vs {m2.get('ftco_overflow')}"))
        failures.append(check("J7 li 尺寸/字級 與 /coffee_menu/ ftco 一致（1108px / 22px）",
                              mj.get("bg_li_width_css") == m2.get("ftco_li_width_css")
                              and mj.get("bg_li_font_size") == m2.get("ftco_li_font_size"),
                              f"{mj.get('bg_li_width_css')}/{mj.get('bg_li_font_size')}"
                              f" vs {m2.get('ftco_li_width_css')}/{m2.get('ftco_li_font_size')}"))
        failures.append(check("J8 li padding-block 已補償（非 0px，與 ftco 一致）",
                              mj.get("bg_li_pad") == m2.get("ftco_li_pad")
                              and mj.get("bg_li_pad") not in (None, "0px"),
                              f"{mj.get('bg_li_pad')} vs {m2.get('ftco_li_pad')}"))
        failures.append(check("J9 .scroller__inner flex-wrap 與 ftco 一致（nowrap）",
                              mj.get("bg_inner_flex_wrap") == m2.get("ftco_inner_flex_wrap"),
                              f"{mj.get('bg_inner_flex_wrap')} vs {m2.get('ftco_inner_flex_wrap')}"))
        failures.append(check("J10 animation（name/duration/timing）與 ftco 一致",
                              mj.get("bg_anim_name") == m2.get("ftco_anim_name")
                              and mj.get("bg_anim_duration") == m2.get("ftco_anim_duration")
                              and mj.get("bg_anim_timing_function") == m2.get("ftco_anim_timing_function"),
                              f"{mj.get('bg_anim_name')}/{mj.get('bg_anim_duration')}/"
                              f"{mj.get('bg_anim_timing_function')} vs {m2.get('ftco_anim_name')}/"
                              f"{m2.get('ftco_anim_duration')}/{m2.get('ftco_anim_timing_function')}"))
        # ---- J11–J15：首頁 hero 順序（2026-10-13 反轉：GUNTE hero 第一屏、BC hero 下移） ----
        # 2026-10-13 稍後（K7 前置）：載入時置中的那張已在上方「navigate 後立刻輪詢」時記下
        # （window.__bcHeroLoadIndex，INDEX_HERO_JS 讀 *_at_load 欄位）→ 這裡只負責逼 frame：
        # 本機 CDP（headful，但 compositor 不一定產 frame）下 CSS transition 會停在 pending：
        # playState='running'、startTime=null、currentTime=0（el.getAnimations() 實測
        # CSSTransition opacity delay=1500 dur=500），computed opacity 一直停在過渡起點 0
        # （`.hero_slide` 與環形字都是），等 15 秒也不會動；逼 frame 後實測 0 → 0.30 → 1
        # （約 1 秒內完成）。等待條件只看「載入時記錄的那張」，autoplay 之後換張不影響斷言。
        if hero_load.get("index") is not None:
            op_ready = ("(function(){var s=document.querySelectorAll("
                        "'.bc-gunte-hero .splide__slide')[%d];if(!s)return false;"
                        "var t=s.querySelector('.hero_slide_item_ttl');"
                        "return !!t&&getComputedStyle(t).opacity==='1';})()"
                        % hero_load["index"])
            for _ in range(40):
                if await evaljs(op_ready):
                    break
                # ⚠ captureScreenshot 本身可能「等不到 frame 而卡死」（殘留多個背景分頁時遇到過）
                # → 包 3 秒逾時；逾時就當這輪沒逼到 frame，下一輪再試（不可讓整支腳本卡住）。
                try:
                    await asyncio.wait_for(
                        send(msg("Page.captureScreenshot",
                                 {"format": "jpeg", "quality": 10})), timeout=3)
                except asyncio.TimeoutError:
                    print("   [hero] captureScreenshot 逾時（3s）→ 續試")
                await asyncio.sleep(0.25)
        hero = await evaljs(INDEX_HERO_JS) or {}
        print("   [hero] " + json.dumps(
            {k: hero.get(k) for k in
             ("section_count", "first_dom_classes", "first_dom_display", "first_visible_classes",
              "first_visible_is_stage", "first_visible_is_gunte", "gunte_found", "bg_hero_found",
              "hero_has_root", "stage_before_gunte", "gunte_before_wrap",
              "gunte_display", "gunte_hidden_attr", "gunte_top", "gunte_h", "gunte_margin_top",
              "hero_top", "hero_h", "hero_margin_top", "footer_root_top",
              "inner_h", "scroll_y", "footer_tag_count",
              "hidden_tag_count", "ttl_svg_count", "ttl_text_count",
              "ttl_ring_hide_count", "ttl_hidden_by_css", "ttl_visible_texts",
              "ttl_font_size", "ttl_stroke_width", "ttl_stroke_width_raw",
              "ttl_box_w", "ttl_rendered_font",
              "ttl_item_img_w",
              "active_slide_is_butter_king_at_load", "active_slide_index_at_load",
              "active_slide_aria_label_at_load", "active_ttl_opacity_at_load",
              "active_ttl_text_display_at_load",
              "active_slide_is_butter_king", "active_slide_index",
              "active_slide_aria_label",
              "active_ttl_opacity",
              "active_ttl_text_display",
              "grid_found", "grid_border_top_w", "grid_border_top_style",
              "grid_border_top_color", "grid_padding_top",
              "root_bg", "footer_bg", "root_parent_tag", "root_parent_classes")},
            ensure_ascii=False))
        failures.append(check("J11 第一個「可見」section 是 .hero.bc-brand-stage-hero，"
                              "且 DOM 第一個 section 是 .bc-reviews-section（display:none）",
                              hero.get("first_visible_is_stage") is True
                              and hero.get("first_dom_display") == "none"
                              and "bc-reviews-section" in (hero.get("first_dom_classes") or ""),
                              f"firstVisible={hero.get('first_visible_classes')} / "
                              f"firstDom={hero.get('first_dom_classes')} "
                              f"display={hero.get('first_dom_display')}"))
        failures.append(check("J12 品牌舞台（.bc-brand-stage-hero）在文件順序上位於 GUNTE hero 之前、"
                              "內仍含 #bc-brand-stage，且 GUNTE hero 已 hidden（display:none）",
                              hero.get("stage_before_gunte") is True
                              and hero.get("bg_hero_found") is True
                              and hero.get("hero_has_root") is True
                              and hero.get("gunte_hidden_attr") is True
                              and hero.get("gunte_display") == "none",
                              f"stageBeforeGunte={hero.get('stage_before_gunte')} "
                              f"wrap={hero.get('bg_hero_found')} "
                              f"wrapHasRoot={hero.get('hero_has_root')} "
                              f"gunteHidden={hero.get('gunte_hidden_attr')} "
                              f"gunteDisplay={hero.get('gunte_display')}"))
        failures.append(check("J13 載入時（未捲動）品牌舞台由視口頂端開始（scrollY 0 且 0 <= top <= 8）"
                              "→ 與 navbar 間無 100px 空隙；#bc-brand-stage 位於舞台內（root.top >= hero.top）",
                              hero.get("scroll_y") == 0
                              and isinstance(hero.get("hero_top"), int)
                              and 0 <= hero.get("hero_top") <= 8
                              and isinstance(hero.get("footer_root_top"), int)
                              and hero.get("footer_root_top") >= hero.get("hero_top"),
                              f"heroTop={hero.get('hero_top')} "
                              f"scrollY={hero.get('scroll_y')} "
                              f"rootTop={hero.get('footer_root_top')} innerH={hero.get('inner_h')}"))
        failures.append(check("J14 兩塊 hero computed margin-top 皆 0px（GUNTE 由 bc-gunte-hero.css 的 "
                              "class 規則壓制；BC hero 已非 first-of-type → 100px 不再命中）",
                              hero.get("gunte_margin_top") == "0px"
                              and hero.get("hero_margin_top") == "0px",
                              f"gunte={hero.get('gunte_margin_top')} "
                              f"bcHero={hero.get('hero_margin_top')}"))
        failures.append(check("J15 / 已無 footer 元素（querySelector('footer') 為 null → yama 交會邏輯 no-op）",
                              hero.get("footer_tag_count") == 0, hero.get("footer_tag_count")))
        # ---- K1–K4：2026-10-13 環形字 markup 修正（非法的 <hidden text> → <text class="bc-ring-hide">） ----
        failures.append(check("K1 全頁已無非法 <hidden> 元素（getElementsByTagName('hidden') == 0）",
                              hero.get("hidden_tag_count") == 0, hero.get("hidden_tag_count")))
        failures.append(check("K2 7 張 slide 的環形字 SVG 各自 1 個 <text>（開／閉成對 ＝ 7）",
                              hero.get("ttl_svg_count") == 7 and hero.get("ttl_text_count") == 7,
                              f"svg={hero.get('ttl_svg_count')} text={hero.get('ttl_text_count')}"))
        failures.append(check("K3 6 個 text.bc-ring-hide 的 computed display ＝ none（CSS 隱藏生效）",
                              hero.get("ttl_ring_hide_count") == 6
                              and hero.get("ttl_hidden_by_css") == 6,
                              f"class={hero.get('ttl_ring_hide_count')} "
                              f"hidden={hero.get('ttl_hidden_by_css')}"))
        failures.append(check("K4 只有 1 個環形字可見且文案含 BUTTER KING",
                              len(hero.get("ttl_visible_texts") or []) == 1
                              and "BUTTER KING" in (hero.get("ttl_visible_texts") or [""])[0],
                              hero.get("ttl_visible_texts")))
        # ---- K5–K7：2026-10-13 稍後（環形字尺寸 ×1.25 ＋ Splide start 3 → 2） ----
        # 期望渲染字級 ＝ 24 × 框寬/432（＝設計值 24px 在 432px 參考圖寬下）；框寬由瀏覽器實測。
        exp_ttl_rendered = (round(24 * hero.get("ttl_box_w") / 432, 2)
                            if isinstance(hero.get("ttl_box_w"), (int, float)) else None)
        failures.append(check("K5 環形字 computed font-size ＝ 30px（＝calc(24px*540/432)："
                              "432 參考圖寬下的 24px 換算成 viewBox 單位、與 cap 14／en 12 同一套 "
                              "--bc-item-k 基準）且 stroke-width ＝ 1.875px（＝calc(1.5*540/432)；"
                              "Chromium 對 SVG 幾何屬性的 computed style 保留 calc() 字面 → "
                              "斷言比對剝除外層 calc() 後的值，原始字串另印 ttl_stroke_width_raw）",
                              hero.get("ttl_font_size") == "30px"
                              and hero.get("ttl_stroke_width") == "1.875px"
                              and hero.get("ttl_stroke_width_raw") in ("1.875px", "calc(1.875px)"),
                              f"font={hero.get('ttl_font_size')} "
                              f"stroke={hero.get('ttl_stroke_width')} "
                              f"raw={hero.get('ttl_stroke_width_raw')}"))
        failures.append(check("K6 環形字 SVG 框寬 ＝ 投影片圖片寬（＝--bc-item-w；1280×800 屬短視窗層 "
                              "scale 0.55 → 297px）→ 渲染字級 ＝ 24 × 框寬/432（改動前 ×1.25）",
                              hero.get("ttl_box_w") == hero.get("ttl_item_img_w")
                              and hero.get("ttl_box_w") not in (None, 0)
                              and hero.get("ttl_rendered_font") == exp_ttl_rendered,
                              f"box={hero.get('ttl_box_w')} "
                              f"img={hero.get('ttl_item_img_w')} "
                              f"rendered={hero.get('ttl_rendered_font')} "
                              f"期望={exp_ttl_rendered} "
                              f"（改動前＝{round(exp_ttl_rendered / 1.25, 2) if exp_ttl_rendered else None}）"))
        failures.append(check("K7 載入時（未捲動）置中的 slide 是 BUTTER KING（DOM 第 2 張："
                              "aria-label「2 of 7」、index 1）且其環形字 reveal 後 computed opacity ＝ 1、"
                              "computed display ≠ none（Splide start 3 → 1；start 為 0-based → 實測 "
                              "start 2 置中的是「3 of 7」＝果香浅煎、start 0 是 BLACK BLEND，"
                              "兩者的環形字皆 .bc-ring-hide），為 *_at_load 系列欄位（逼 frame 前記錄）",
                              hero.get("active_slide_is_butter_king_at_load") is True
                              and hero.get("active_slide_index_at_load") == 1
                              and hero.get("active_slide_aria_label_at_load") == "2 of 7"
                              and hero.get("active_ttl_opacity_at_load") == "1"
                              and hero.get("active_ttl_text_display_at_load") != "none",
                              f"atLoad[butter={hero.get('active_slide_is_butter_king_at_load')} "
                              f"index={hero.get('active_slide_index_at_load')} "
                              f"aria={hero.get('active_slide_aria_label_at_load')} "
                              f"opacity={hero.get('active_ttl_opacity_at_load')} "
                              f"textDisplay={hero.get('active_ttl_text_display_at_load')}] "
                              f"讀值當下[index={hero.get('active_slide_index')} "
                              f"aria={hero.get('active_slide_aria_label')} "
                              f"opacity={hero.get('active_ttl_opacity')}]"))
        failures.append(check("J16 置頂 hero 的頂部分隔線已移除（.grid.is-footer border-top 0px/none，"
                              "原本為 1px solid rgba(255,255,255,.08)）且 padding-top 非 0"
                              "（2026-10-18 起桌面為置中算式，≤991px 仍為 u-72）",
                              hero.get("grid_border_top_w") == "0px"
                              and hero.get("grid_border_top_style") == "none"
                              and hero.get("grid_padding_top") not in (None, "0px"),
                              f"border={hero.get('grid_border_top_w')}/{hero.get('grid_border_top_style')} "
                              f"padTop={hero.get('grid_padding_top')}"))
        failures.append(check("J17 自帶黑底已移除（#bc-brand-stage 與 .footer 皆 transparent → 由頁面底色穿透）",
                              hero.get("root_bg") == "rgba(0, 0, 0, 0)"
                              and hero.get("footer_bg") == "rgba(0, 0, 0, 0)",
                              f"root={hero.get('root_bg')} footer={hero.get('footer_bg')}"))
        failures.append(check("J18 覆寫作用域錨點正確（首頁 #bc-brand-stage 的父層是 SECTION.hero.bc-brand-stage-hero）",
                              hero.get("root_parent_tag") == "SECTION"
                              and "bc-brand-stage-hero" in (hero.get("root_parent_classes") or ""),
                              f"{hero.get('root_parent_tag')}.{hero.get('root_parent_classes')}"))
        # ---- J19：about 頁反向守門（同一腳本內以新分頁前的同頁面 goto 量測，1280x800） ----
        await goto(f"{BASE}/about/")
        ag = await evaljs(ABOUT_GUARD_JS) or {}
        print("   [about-guard] " + json.dumps(ag, ensure_ascii=False))
        failures.append(check("J19 首頁覆寫未波及 about 真頁尾（仍有 1px solid 分隔線 + #0e0e0e 黑底，父層為 BODY）",
                              ag.get("found") is True
                              and ag.get("border_w") == "1px"
                              and ag.get("border_style") == "solid"
                              and ag.get("footer_bg") == "rgb(14, 14, 14)"
                              and ag.get("root_bg") == "rgb(14, 14, 14)"
                              and ag.get("parent_tag") == "BODY",
                              f"border={ag.get('border_w')}/{ag.get('border_style')} "
                              f"footer_bg={ag.get('footer_bg')} parent={ag.get('parent_tag')}"))
        await goto(f"{BASE}/")  # 回到 / 續跑下方 index 截圖
        await shot("index_bg_footer", "#bc-brand-stage .scroller-box")

        # ================= prefers-reduced-motion: reduce =================
        await send(msg("Emulation.setEmulatedMedia", {
            "features": [{"name": "prefers-reduced-motion", "value": "reduce"}]}))
        await set_viewport(390, 844)
        await goto(f"{BASE}/about/")
        await asyncio.sleep(0.6)
        m3 = await evaljs(MEASURE_JS) or {}
        print("\n=== /about/ prefers-reduced-motion: reduce (390x844) ===")
        failures.append(check("I1 不設 data-animated",
                              m3.get("data_animated") in (None, "false"), m3.get("data_animated")))
        failures.append(check("I2 仍維持原始 2 個 li", m3.get("inner_child_count") == 2,
                              m3.get("inner_child_count")))
        failures.append(check("I3 無水平溢出（防護 overflow:hidden 生效）",
                              m3.get("no_h_overflow") is True,
                              f"scrollW {m3.get('doc_scroll_w')} vs innerW {m3.get('inner_w')}"))
        failures.append(check("I4 .scroller 仍被裁切",
                              m3.get("scroller_overflow") == "hidden", m3.get("scroller_overflow")))
        failures.append(check("I5（無動畫狀態也）未撐破所屬 grid",
                              m3.get("grid_no_overflow") is True,
                              f"grid scrollW {m3.get('parent_grid_scroll_w')} vs clientW "
                              f"{m3.get('parent_grid_client_w')}"))
        failures.append(check("I6（無動畫狀態也）.foooter-mail 寬 <= viewport 寬",
                              m3.get("mail_fits_win") is True,
                              f"{m3.get('mail_w')} <= {m3.get('inner_w')}"))
        await shot("mobile_reduced_motion")
        await send(msg("Emulation.setEmulatedMedia", {"features": []}))

        # 收尾：關掉本腳本開的分頁（原本沒有這行 → 每跑一次就留一個分頁；實測殘留 5 個頁面時
        # compositor 不再為本分頁產 frame，逼 frame 用的 Page.captureScreenshot 會卡住不回應）。
        await send(msg("Page.close"))

    total = len(failures)
    bad = sum(1 for f in failures if not f)
    print(f"\n===== 合計 {total} 項，PASS {total - bad}，FAIL {bad} =====")
    return bad


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

