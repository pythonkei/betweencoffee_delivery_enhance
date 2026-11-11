# 品牌舞台 `bc-brand-stage` 的 `footer*` class 改名為 `bc-stage-*`（2026-11-10 完成）

> 由 `task_progress.md` 於 2026-11-11 封存（`task_progress.md` 只留摘要，細節在此）。

- 指示：`#bc-brand-stage` 在首頁是第一屏 hero（不是真頁尾），class 卻叫 `footer*` → 改成語意正確的 `bc-stage-*`；**外觀必須完全不變**。
- 改名 16 組（對照表見 `static/css/bc-brand-stage.css:2-75`）：`.footer`→`.bc-stage-content`、`.footer-inner`→`.bc-stage-content-inner`、
  `.grid.is-footer`→`.grid.is-stage`、`.footer-time(-inner)`→`.bc-stage-time(-inner)`、`.footer-logo-{item,list,list-wrap,cell,caption,link}`→`.bc-stage-photo-*`、
  `.footer-socials`→`.bc-stage-socials`、`.footer-mail-inner`→`.bc-stage-mail-inner`、`.m-footer-*`→`.bc-stage-m-*`、
  `.foooter-mail`（Webflow 拼字錯誤）→`.bc-stage-marquee`（與既有 id `#bc-stage-marquee` 同名）。
- 同步 8 檔：兩個 partial＋`bc-brand-stage.css`＋`bc-brand-stage.js`（`_footerLogoClick`→`_stagePhotoClick`）＋`index.html`／`about.html`
  （`?v=20261110b`）＋`docs/verify/` 六支 `cdp_*.py` 的 selector（不改會讓驗證全紅）。
- **刻意不動**：`<footer>` 標籤（index 用 `<div>`、about 才用 `<footer>`；`bc-yama-header.js` 靠 `querySelector('footer')`）、
  所有 `id`／`data-*`（`#bc-stage-clock`／`#bc-stage-photo-ring`／`#bc-stage-marquee`… 10-12 已是語意名）、
  `#bc-sticky-mv .foooter-mail`（另一模組的 Webflow class）。
- 驗證（dev 8081＋headless Chromium@9222）：
  ① **靜態等價證明**：`bc-brand-stage.css` 套用對照表後與改名前**逐字元相同**（245 條規則、宣告 0 變動）；兩個 partial 的
     標籤／id／屬性結構相同，175 個 `class` 屬性只換值（1:1 對應 16 組、零不一致）。
  ② **實測基準比對** `/` 390×844（同量法、隱藏捲軸）：`docH 3394`、stage `[0,0,390,730]`、clock `[16,143,358,279]`、
     ring `[139,143,111,279]`、marquee `[16,574,173,85]`、`overflowX 0` —— 六項與改名前**完全相同**。
  ③ `cdp_verify_bg_footer.py` **41/41 PASS**（1280／768／390＋點擊輪播 0→1→2→3→4→0）；兩頁渲染後 `#bc-brand-stage` 內已無任何
     `footer*`／`foooter*` class（只剩無關的 `.bc-cart-footer`、`#bc-sticky-mv .foooter-mail`、`.c-real-title-footer`）。
  ④ console 0 error、`manage.py check` 0 issue（`/about/` 的 4 個 404 是工作區已刪的 `static/images/staff0[1-4].png`，與改名無關）。
- 已知殘留（**非本次造成**）：`cdp_verify_footer_scroller.py` 121/127，6 個 FAIL 全在 J11／K3–K7（GUNTE hero 環形字與首頁 section 順序；
  該模組 10-18 起 `hidden`、selector 鏈與 `bc-stage-*` 無關，10-16 曾記錄 127/127）。
