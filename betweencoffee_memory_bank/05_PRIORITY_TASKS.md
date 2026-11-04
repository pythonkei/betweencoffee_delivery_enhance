# 05_PRIORITY_TASKS

> 2026-11-04 複驗版（2026-10-25 版之後累積 10-28 ~ 11-04；原檔 100KB 已封存：`docs/archive/memory_bank_05_full_20261017.md`）。
> 本檔**只放未完成**與**最近完成一行式**；已完成項目的完整說明不在此，必要時 grep 封存檔。

## 當前版本控制狀態（2026-11-04 複驗）

- ✅ `origin/main`＝`0c4189fe`（本輪 4 筆：`0bd7172d` 三段 grid 修正、`e9bdefdb` 補齊 10-28 起累積前端、`7251018f`／`0c4189fe` docs 記憶文件同步與收尾），本機 `main`＝`origin/main`、工作區乾淨（不寫死文件 hash，複驗用 `git log -1`）
- ℹ️ 2026-11-04 之前的 `e2a5d747`／`ef98d37e`／`fc7b7cb3`／`e49ac4d9` 均已在遠端
- ℹ️ `.gitignore` 排除的本機暫存素材（`static/images/hero_bg.mp4` 81MB 未引用、`recommended-pages/` 底線開頭 webm／png 變體）不入庫
- ⚠ 正式站 live＝`c3f7509c`（`dep-dbkpv7tg1s2s73df3leg`，2026-11-03 08:47Z 手動部署成功）⇒ **待部署 `c3f7509c..origin/main`（4 筆 code／feature＋docs）**；autoDeploy＝off → push 不會上線

## 近期優先（未完成）

| # | 任務 | 類型 | 備註 |
|---|---|---|---|
| 1 | **手動部署 `c3f7509c..e9bdefdb`** | 維運 | 到 Render dashboard 按 Manual Deploy（DB 已可連）；上線後複驗：`/about/` 首屏 sticky 影片＋三段位置（與 about 頁尾同格位）、字體輪播有樣式（`bc-catch.css` 本輪才入庫，先前 404）、首頁製程模組 `[2b-2]`、品牌舞台天氣在 `{` 左側、環形照片列 hover 徽章／拖曳、`/bean/<id>/` 氣泡與 `.bc-staff` 字級、migration `0081`–`0083` 已套用 |
| 2 | 咖啡／咖啡豆氣泡文案校稿 | 內容（Admin） | 咖啡：`CoffeeItem.staff_comment_1/2/3`（留空＝不顯示，目前僅 Butter King 有第 1、3 句）；咖啡豆：`0083` 已預填 6 款草稿待改寫 |
| 3 | 行動端 `.bc-reviews-section` 縮放 | 前端 | 新增 ≤768 媒體查詢；純 CSS、可逆 |
| 4 | `bean_menu` REAL 模組驗收 | 前端 | 響應式檢查後收尾 |
| 5 | yama `tax-nav` 收尾 | 前端 | welcome 面板已隱藏、圓球配色（`#774f18` / hover `#1a1919`）已完成，剩平板層確認 |
| 6 | 安全性收尾 | 維運 | 確認支付寶金鑰已輪換（2026-08-01）；`git filter-repo` 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private。見 `docs/security/git-history-cleanup.md` |

## 最近完成（一行式）

- **2026-11-04｜about 首屏三段改回品牌舞台 7 欄 grid 格位**：`.mv-stage` 由 flex 堆疊改 grid（fresh `1/3/2/6`、roasted `2/4/3/7`＋8px、marquee `2/3/3/5` 同列靠左；≤991px 6 欄），字級改原站流體公式（h1 `90vw/14.4`／p1 `14vw/14.4`）、`.scroller-box` 補 `line-height:1`；1440／1280／992／834／480／390 位置與原站同值、0 溢出。（`0bd7172d`，`bc-sticky-mv.css?v=20261104c`）
- **2026-11-04｜補齊 10-28 起累積未提交前端**：首頁製程模組（`bc-home-service.{css,js}`＋partial＋`make_hs_images.py`＋16 張 webp）、`bc-catch.css` **入庫**（先前只有 about.html 引用 ⇒ 正式站 404）、品牌舞台 `.footer-time` 8→10 欄（天氣移到 `{` 左側＋鏡像留白）＋天氣 `z-index:3`、capabilities `--cap-scale`、環形照片列拖曳、`.bc-staff` 字級、`.gitignore` 排除 81MB `hero_bg.mp4` 等暫存檔。（`e9bdefdb`）
- **2026-11-03｜about 首屏改 sticky 影片＋產品照弧形輪播**（移植 yurumaru.life，`bc-sticky-mv.{css,js}`＋`hk_topshot-720p.mp4`），取代 popeye50 字輪；同日修 loop 歸位抖動＋原生 `dragstart` 中斷＋產品列下方加品牌舞台三段。（`e2a5d747`／`ef98d37e`）
- **2026-11-03｜首頁環形咖啡照列 hover 徽章**：`bc-hand-hover.js` 跟隨游標圓形徽章＋`bc-hand-ring.css` 照片 hover 放大（僅 `(hover:hover) and (pointer:fine)`，觸控不啟動）。（`c3f7509c`＝**現行 live**）
- **2026-11-02｜about 首屏字輪微調＋popeye50 去黑底**：直徑係數 0.86、中心品名 13.5／13.2px、中心與 SERIES 連結詳情頁。（`87d66040`／`33a4c06a`；已由 11-03 sticky mv 取代）
- **2026-10-31｜about 新增「字體輪播」**：移植 eightdesign.co.jp `.PZL1xq_catch`，3 行 × 4 種字體、`.74s` step-end 硬切、純 CSS＋reduced-motion 靜止。（`bc-catch.css`）
- **2026-10-30｜首頁「咖啡豆製程」捲動模組**：移植 union-tec `homeService`（clip-path 膠囊→滿版、4 段輪播、標籤＋網格字母），原生 JS 不依賴 Alpine／Lenis／three.js／GSAP。（`bc-home-service.*`、`bc_home_service.html`）
- **2026-10-28｜capabilities 搬家 ＋ 字型／字級調整**：about→首頁＋`--cap-scale` 等比放大置中；`/bean/<id>/` `.bc-staff` 17／16／16px；自架 trade-gothic；bean SERIES 滑桿搬到商品主區下方。（`29eb67d1`／`f57eb768`／`f730abab`）
- **2026-10-24｜#61 首頁推薦雙卡**：移植 union-tec `recommendedPages`（`bc-recommended-pages.css/js`，vanilla 切 `is-hover-active`）；同日搬到品牌舞台正下方、隱藏首頁 `#bc-stage-socials`。（`d27f7c90` 已 push）
- **2026-10-24｜#60 環形照片列第一張咖啡改 goo 揭示**：不再 scale 0.5→1，改用與標題文字同一套 `stdDeviation 50→0` 濾鏡時間軸（`window.BC_MEDIA_REVEAL`）；index／about `?v=20261024a`；rAF 取樣與換張行為驗證通過。（`7a073263` 已 push）
- **2026-10-24｜#59 咖啡豆詳情頁店員氣泡**：`BeanItem` 10 欄位＋自動幾何量測、Admin 2 fieldset、`0081`–`0083`；`.bc-coffee-comment` 宿主 selector 改中性 `.bc-photo-comment`；6 落點 × 8 斷點量測無溢出、console 0 error。（`edf3e87c` 已 push）
- **2026-10-22~23｜#58／#58b 首頁四步旅程 Rive 圖示列**：自架 Rive 2.35.2 ＋ IntersectionObserver 延遲載入；intro/hover/rest 修正（不再 `stop`/`scrub`）＋靜止 4s 自動循環＋圖示純白；桌機 4 欄、手機 2×2、reduced-motion 全數驗證通過。（已 push `a732cc28`）
- **2026-10-17｜#57 移除 hero／導覽列時鐘**：`bc-weather.js` `ORDER`＝`['icon','temperature']`，刪 `updateClock()`。（`28b1c322` 已 push）
- **2026-10-16｜#56 首頁照片格桌機字級再加大**：名稱／highlight 24/18px、`--bc-hero-caption-h` 68.38。（`71018e97` 已 push）
- **2026-10-15｜#55 首頁照片格桌機照片縮小**：1440 時 280×400、字級 20/16px。（`aaf7c2aa` 已 push）
- **2026-10-14｜#51 首頁順序反轉**：GUNTE hero 回第一屏＋環形字 markup／尺寸／載入可見性修正。（`bf495475` 已 push）
