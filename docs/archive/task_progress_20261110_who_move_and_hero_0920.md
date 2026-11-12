# 封存：品牌舞台改名／who section 搬頁／浮動購物車圖示／11-09 hero 移頁

> 2026-11-12 由 `task_progress.md` 移出（該檔只留現況；`docs_size_check.py` 超標）。
> 原文逐字保留，內容皆已 push（部分待部署）。

**品牌舞台 `bc-brand-stage` 的 `footer*` class 改名為 `bc-stage-*` — 2026-11-10 完成**

- 16 組改名（`.footer*`→`.bc-stage-content*` 等，對照表在 `static/css/bc-brand-stage.css:2-75`），同步 10 檔；`<footer>` 標籤與 `id`／`data-*` 不動。
- 靜態等價驗證（245 條規則逐字元相同）＋ `cdp_verify_bg_footer.py` 41/41 PASS；全文 → `docs/archive/task_progress_20261110_brand_stage_rename.md`。

**sukima who section 由 about.html 搬到首頁（使用者指示）— 2026-11-10 完成**

- 指示：把 `.section.who.bc-who-section` 區塊從 about.html 移到 index.html、放在 `bc-recommended-pages` 正下方。
- 搬移：about.html 原 700–725 行（25 行 markup）整段原封搬入 `index.html`，插在 `<aside class="bc-recommended-pages">`
  之後、`.capabilities` 之前（現 index.html:261 起，含檔頭註解說明來源與素材）。
- 依賴一併搬：`bc-who.css`（about 移除 → index extra_css 載入）、`bc-who.js`（about 移除 → index extra_scripts 載入）；
  兩檔皆**完全 scoped 於 `.bc-who-section`**、JS 只用原生 scroll + rAF（無 GSAP→不依賴載入順序），故搬頁不需改邏輯。
- 素材不動：`static/animations/wwa.mp4`、`static/images/wwa-01.png`／`wwa-02.png` 路徑不變。
- 版號：`bc-who.css` `20260825e`→**`20261110a`**、`bc-who.js` `20260825k`→**`20261110a`**（僅檔頭註解改記「index 頁」）；
  `bc-hero-description.css` →**`20261110a`**（檔頭「放置位置」改為 `.bc-product-real` 正下方）。
- 驗證（dev 8081，1440／390）：`previousElementSibling`＝`ASIDE.bc-recommended-pages`、`nextElementSibling`＝`.capabilities`、間距 0；
  93 幀＋圓圈／箭頭齊備、spacer 0→90px（390：75px）、opacity .5→1、circle dash 377；about 端 `bc-who.*` 不再請求、gap 0、console 0 error。

**浮動購物車圖示改為「10 種造型 × 線條／實心」可選（使用者指示）— 2026-11-09 完成並已 push**

- 最終選定 **`04 手提包（線條）`**；`base.html:190` 為 inline SVG（`.bc-fc-line`／`.bc-fc-solid` 雙態），
  `bc-components.css:1622` 的 `svg.bc-fc-icon` 定尺寸；版號 `20261109a`。
- 造型清單與預覽頁 `static/preview/bc-floating-cart-icons-v2.html`；量測／驗證數據全文 →
  `docs/archive/task_progress_20261109_floating_cart_icons.md`。

**11-09 首頁 hero 照片與「咖啡豆製程」移頁（已 push，待部署）** — 四則細節已封存：

- 黑蒙版 70%→**75%**（`bc-photoarea.css` `--pa-dim .25`；演進 40→50→60→70 記在該檔頭）。
- hero 照片**每次載入重排落點**（`views._photoarea_slots()` → `pa_slots`；關 JS 也有效）。
- 「咖啡豆製程」`bc-home-service` 自首頁 `[2b-2]` 移到 `/about/` `.bc-search` 下方。
- 第 3 格影片改**可輪播容器**（`views.PA_VIDEOS`、0.75s 換片／0.6s 淡入、離開視窗 pause）
  → `docs/archive/task_progress_20261109_hero_pa_video_carousel.md`。
- 全文 → `docs/archive/task_progress_20261109_photoarea_dim_shuffle.md`；模組細節 `docs/home-photoarea.md`。
