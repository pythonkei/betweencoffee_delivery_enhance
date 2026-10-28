# 05_PRIORITY_TASKS

> 2026-10-25 複驗版（2026-10-23 精簡版；原檔 100KB 已封存：`docs/archive/memory_bank_05_full_20261017.md`）。
> 本檔**只放未完成**與**最近完成一行式**；已完成項目的完整說明不在此，必要時 grep 封存檔。

## 當前版本控制狀態（2026-10-25 複驗）

- ✅ `origin/main`＝`b29ff324`（2026-10-28 推 `29eb67d1`／`f57eb768`／`f730abab`／`b29ff324`），本機 `main`＝`origin/main`（不寫死文件 hash，複驗用 `git log -1`）
- ℹ️ `#55 aaf7c2aa`／`#56 71018e97`／`#57 28b1c322`／`#58 a732cc28`／`#51 bf495475` 均已在遠端
- ℹ️ 原始 APNG 素材 `static/images/ani_{coffee,bean}_apng.png`（12.8MB，僅供重新產圖）列入 `.gitignore`，頁面用的是 `static/images/recommended-pages/title-*.png`
- ⚠ 正式站 live＝`a732cc28`（`dep-dbed2vm7bikc73825md0`，2026-10-24 15:43Z 手動部署成功；10-23 的 Supabase ENOTFOUND 已排除）⇒ **待部署 `#59`／`#60`／`#61` 三個 code commit**；autoDeploy＝off → push 不會上線

## 近期優先（未完成）

| # | 任務 | 類型 | 備註 |
|---|---|---|---|
| 1 | **手動部署 #59／#60／#61** | 維運 | 到 Render dashboard 按 Manual Deploy（DB 已可連）；上線後複驗首頁推薦雙卡位置、首頁社群列隱藏、`/about/` 頁尾社群列、`/bean/<id>/` 氣泡、migration `0081`–`0083` 已套用 |
| 2 | 咖啡／咖啡豆氣泡文案校稿 | 內容（Admin） | 咖啡：`CoffeeItem.staff_comment_1/2/3`（留空＝不顯示，目前僅 Butter King 有第 1、3 句）；咖啡豆：`0083` 已預填 6 款草稿待改寫 |
| 3 | 行動端 `.bc-reviews-section` 縮放 | 前端 | 新增 ≤768 媒體查詢；純 CSS、可逆 |
| 4 | `bean_menu` REAL 模組驗收 | 前端 | 響應式檢查後收尾 |
| 5 | yama `tax-nav` 收尾 | 前端 | welcome 面板已隱藏、圓球配色（`#774f18` / hover `#1a1919`）已完成，剩平板層確認 |
| 6 | 安全性收尾 | 維運 | 確認支付寶金鑰已輪換（2026-08-01）；`git filter-repo` 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private。見 `docs/security/git-history-cleanup.md` |

## 最近完成（一行式）

- **2026-10-24｜#61 首頁推薦雙卡**：移植 union-tec `recommendedPages`（`bc-recommended-pages.css/js`，vanilla 切 `is-hover-active`）；同日搬到品牌舞台正下方、隱藏首頁 `#bc-stage-socials`。（`d27f7c90` 已 push）
- **2026-10-24｜#60 環形照片列第一張咖啡改 goo 揭示**：不再 scale 0.5→1，改用與標題文字同一套 `stdDeviation 50→0` 濾鏡時間軸（`window.BC_MEDIA_REVEAL`）；index／about `?v=20261024a`；rAF 取樣與換張行為驗證通過。（`7a073263` 已 push）
- **2026-10-24｜#59 咖啡豆詳情頁店員氣泡**：`BeanItem` 10 欄位＋自動幾何量測、Admin 2 fieldset、`0081`–`0083`；`.bc-coffee-comment` 宿主 selector 改中性 `.bc-photo-comment`；6 落點 × 8 斷點量測無溢出、console 0 error。（`edf3e87c` 已 push）
- **2026-10-22~23｜#58／#58b 首頁四步旅程 Rive 圖示列**：自架 Rive 2.35.2 ＋ IntersectionObserver 延遲載入；intro/hover/rest 修正（不再 `stop`/`scrub`）＋靜止 4s 自動循環＋圖示純白；桌機 4 欄、手機 2×2、reduced-motion 全數驗證通過。（已 push `a732cc28`）
- **2026-10-17｜#57 移除 hero／導覽列時鐘**：`bc-weather.js` `ORDER`＝`['icon','temperature']`，刪 `updateClock()`。（`28b1c322` 已 push）
- **2026-10-16｜#56 首頁照片格桌機字級再加大**：名稱／highlight 24/18px、`--bc-hero-caption-h` 68.38。（`71018e97` 已 push）
- **2026-10-15｜#55 首頁照片格桌機照片縮小**：1440 時 280×400、字級 20/16px。（`aaf7c2aa` 已 push）
- **2026-10-14｜#51 首頁順序反轉**：GUNTE hero 回第一屏＋環形字 markup／尺寸／載入可見性修正。（`bf495475` 已 push）
- **2026-10-14｜生產版本複驗**：Render live＝`dep-db6btj0473hc73du80hg`／`ec8fcadb`（manual trigger）。
- **2026-10-12｜hero 時鐘手機 `{ }`**：9 欄顯示＋`#bc-bg-footer` 的 `w-node-*` id 語意化。（`6e29b447`，已部署）
- **2026-10-08｜10 月批次收尾**：migration 0079（烘焙）/0080（茶種）、about 頁 BC 動態 footer、首頁 `.top_art`、滑出購物車 API 驅動。（`18a14070` 已 push）
- **2026-10-06｜CDP 驗證基礎建設**：`docs/verify/CDP_SETUP.md` ＋ `cdp_verify_*` 腳本群。
- **2026-09-15｜正式庫落差回補**：訂單 643 筆／帳號 13／佇列 354 補入（單 transaction＋PK 去重＋sequence 修正）。
