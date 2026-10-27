# #60 品牌舞台環形照片列「第一張咖啡」進場動畫（2026-10-24，已 push `7a073263`）

**#60 品牌舞台環形照片列「第一張咖啡」進場動畫 — ✅ 完成並驗證（已 push `7a073263`）**

| 項目 | 內容 |
|---|---|
| 需求 | `#bc-stage-photo-ring-list` 的第一張咖啡原本是 scale 0.5 → 1（從小放大），改成與 `#bc-stage-headline-fresh-beans`「Follow Your Rhythm」文字相同的動畫 |
| 原因 | `register()` → `go()` 第一次定位時 `.is-ready` 已加上 ⇒ `img` 從預設 `scale: 0.5` 過渡到 `-current` 的 `scale: 1`（rAF 取樣確認：0.5 → 1，約 1.2s） |
| 改動檔案 | `static/js/bc-hand-ring.js`（第一次定位加 `.is-snap`＋`releaseSnap()`（兩個 frame 後移除）＋`revealPhoto()`；第一次定位不跑 `revealCaption()`，避免字型未就緒的 SplitText 警告）、`static/css/bc-hand-ring.css`（`.hero_hand.is-ready.is-snap` 關掉圓盤與 img 過渡）、`static/js/bc-brand-stage.js`（新增 `window.BC_MEDIA_REVEAL`：沿用 goo 文字揭示的同一組 STD/AMP/OFF 濾鏡與 1.2s `Out` 時間軸；`boot()` 改為 `initGsap` → `initClockHandRing`，讓 API 先就位）、`templates/.../index.html`＋`about.html`（版號 `?v=20261024a`） |
| 行為 | 第 1 張直接以 `scale 1` 就位（不再放大）→ 由 `filter: url(#goo-…)` 的 `stdDeviation 50 → 0` 收斂成清晰照片（＝文字揭示同一套）；`is-snap` 於 2 frame 後移除，之後換張仍是圓盤旋轉＋`scale 0.5 ⇄ 1` |
| 驗證 | 首屏 rAF 取樣：`scale` 全程 `1`、`filter` `url(#goo-…)`→`none`、`stdDeviation` 50→0（約 1.2s）；換張（`goAll(1)`）`scale` 0.5→1 正常；1440／375 皆無水平溢出；index／about console 僅剩既有 payment reminder 警告（原本的 SplitText 警告已消失）；`check` 0 issue、`makemigrations --check` clean、`node --check` OK |
| 備註 | 顏色對比濾鏡（alpha ×20 −8）在照片上只在揭示前段把輪廓「goo」成一團色塊（STD 50 實測＝只剩剪影），與標題文字一致；GSAP 未載入時照片直接以最終尺寸出現 |
