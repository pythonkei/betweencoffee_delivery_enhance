# 首頁「咖啡豆製程」捲動模組（bc-home-service）開發紀錄

> 2026-11-02 自 `task_progress.md` 移出（檔案預算），原樣保留。

**首頁「咖啡豆製程」捲動模組（移植 union-tec.jp `homeService`）— 2026-10-30 完成，未 commit**
位置：首頁 `[2b-2]`，`aside.bc-recommended-pages` 之後、`.bc-capabilities` 之前。

| 項目 | 內容 |
|---|---|
| 新檔 | `templates/betweencoffee_delivery/partials/bc_home_service.html`、`static/css/bc-home-service.css`（`?v=20261030a`）、`static/js/bc-home-service.js`（`?v=20261030a`）、`scripts/make_hs_images.py` |
| 素材 | `static/images/home-service/hs-{1..4}{,-sp,-blur,-clip}.webp` 共 16 檔 1.4MB（全幅 1600×900 ≤340KB、SP 900×1200、blur 480×270 ≤2KB、clip 640×444）；原始 4 張 JPG 留在 `static/images/` 未刪 |
| 結構 | header（Beans／咖啡豆＋說明）→ 錨點／`-120px` 手機上拉 → `sticky` bg（`clip-path` 膠囊 463×320）→ `sticky` stage（`-mt-100svh`：4 標籤＋CTA＋網格層）→ `leave` 100svh。總高 1907px @1440×900（原站 1897） |
| 幾何 | `enterScaleP += (easeInCirc(clamp01(invLerp(.5,1,bgScrollP))) - enterScaleP) × 0.15`；`clipScale = lerp(minScale, maxCoverScale, p)`；minScale PC `463/1440`／SP `217/400`；maxCover 用 64 次二分＋`isPointInFill`（實測 1440×900＝1.2644、390×844＝3.207） |
| 其他數值 | 影像輪播 3000ms／交接 800ms、Ken Burns 6s `scale 1.04→1`、模糊＋50% 暗幕 = `clamp01(invLerp(.75,1,p))`、收尾 `translateY ≤30%`＋`scale→1.25`、標籤內縮 25／51px、圓點 9／19px、字 24／64px、網格格點 24vw／12.222vw（8.18 欄） |
| 驗證 | `manage.py check` 0 issue、`node --check` OK、flake8／black OK、console 0 error、16 張圖全 200；實測 1440×900 五段＋390×844 兩段，數值與公式逐項對上（例：leave p=0.677 → `translateY 10.647%`、`scale 1.2186`，理論 10.6%／1.2185）；反向捲動可完整回捲 |
| 踩雷 | **Django `{# #}` 不支援跨行**（regex 無 DOTALL）→ 多行註解會被原樣輸出成頁面文字（會多出 25.2px 行盒）；本模組改用 `{% comment %}`／HTML 註解 |
