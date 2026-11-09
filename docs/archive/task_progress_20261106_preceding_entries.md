# task_progress 封存（2026-11-06 前段）

> 自 `task_progress.md` 移出以符合 11.7K 預算；內容為 2026-11-05／11-06 兩筆紀錄（push 記錄、詳情頁欄距放寬）。

**已 commit ＋ push 到 `origin/main`（`8799454e`）— 2026-11-06**

- 4 筆功能/修正已入庫：`00698fcd` 首頁環形列改名＋徽章、`b6140421` baker 頭像、`89a9f052` navbar 天氣、`f30cbe4b` 詳情頁容器加寬（另 2 筆 `.clinerules` 版本狀態／預算）。
- ⚠ 推送時發現本機 `.git` 有 **23 個 0-byte 物件**（IDE／磁碟中斷造成，含 `52d17b3…`）⇒ `git push`／`format-patch` 直接失敗。修法：乾淨 clone 重建同內容 4 筆 → push → 把該 clone 的 pack 補回本機 + 刪空物件 + `reset --hard origin/main`。日後見 `bad tree object`／`object file … is empty` 先跑 `find .git/objects -type f -size 0`。
- 殘留：`git fsck` 僅剩 `refs/cline/checkpoints/**`（Cline 快照）內的 broken link，不在 main 歷史中、不影響 fetch／push。

**coffee／bean 詳情頁「左右欄間距」加寬（放寬容器）— 2026-11-05 完成（未 commit）**

| 項目 | 內容 |
|---|---|
| 指示 | 「`/coffee/x/`、`/bean/x/` 左邊商品圖與右邊內容欄位距離太近」（尤其氣泡幾乎貼到右欄文字） |
| 改前實測 | 1440px（容器 1140）：咖啡 照片右緣→文字 142 / 右側氣泡右緣→文字 52；豆 63 / 28。1100px（容器 960）：咖啡 97 / **7**（最擠）；豆 63 / 25 |
| 改動 | `static/css/bc-components.css` 檔尾新增（不依賴 `:root` 變數、可整段刪除回滾）：`@media (min-width:1200px){ .ftco-subpage-section.ftco-section-single-product > .container{max-width:1320px} }`、`@media (min-width:992px) and (max-width:1199.98px){ … max-width:1140px }` |
| 為何不必動照片／氣泡 | 照片尺寸由 `style-custom.css` 的 `max-width`／`max-height` 決定（咖啡 88.825% ＋限高 458、豆 100% ＋限高 516）⇒ 容器變寬只是左右黑留白變多；氣泡層以 `aspect-ratio` ＋ `translate(-50%,-50%)` 貼齊「照片」⇒ 自動跟隨，`bubble_safe_left/right` 不需重測 |
| 影響範圍 | `ftco-section-single-product` 全站只有 `coffee.html:39`、`bean.html:38` 使用；實測 `/`、`/about/` 的 `.container` 仍 `1140px`；<992px 上下堆疊不套用（991px 實測容器仍 720） |
| 版號 | `base.html:44` `bc-components.css?v=20261028a → 20261105a` |
| 改後驗證 | 照片寬度全程不變（咖啡 358.3、豆 516）。1440：咖啡 142→**186.8**／氣泡 52→**97.2**、豆 63→**108**／28→**73.5**；1200：咖啡 156.8／67.2、豆 78／43.5；1199（容器 1140）：咖啡 141.8／52.2、豆 63／28.5；1100：咖啡 131.8／**42.2**（原 7.2）、豆 63／30.9；1024：咖啡 161.8／79.5、豆 63／30.9；992：咖啡 158.4／75.5。`overflowX=0`、選項鈕不換行（≥1100 單行）、標題不溢出、console 0 error；截圖 `/home/kei/bc-detail-{coffee,bean}-{1440,1024}-after.png` |
| 已知未解（非本次造成） | ① 豆頁在 992–1199 之間方形圖會隨欄寬等比撐滿 ⇒ 間距固定 63px（要更寬需另給該頁 `.img-4` 加 `max-width`）；② ≤1024 時「研磨」按鈕文字折兩行（`padding:14px 20px` ＋ 3 字 ×16px＝48px > 內容寬 45px），改前即如此 |

## `/about/` 首屏影片追加 3 支（片單 6 支）— 2026-11-06（已 push `4f9fa76c`）


- 影片：`static/media/` 新增 `index_hero_bg.mp4`（1920×1080／8.6s／3.8MB）、`bean_bg.webm`（1280×720／10s／2.3MB）、`13687671-hd_720_1280_60fps.mp4`（**720×1280 直式**／7.5s／1.6MB；滿版 `object-fit:cover` 只露中間橫條，屬預期）。
- `views.py`：`MV_MAX` 5 → **6**（層數＝min(片單長度, MV_MAX)，不調的話第 6 支永遠輪不到）；`MV_VIDEOS` 依指示順序追加 3 筆（第 0 層仍是 `hero_bg_v2.webm`）。
- `bc-sticky-mv.js`（`?v=20261106b`）：① 換片判斷改 `isReady()`＝`readyState >= 3` 即時看，不再只信 `canplaythrough`（省流量時它不一定會發 → 會卡在沒載好的層）；② 找不到就緒層時補呼叫 `loadNextUnloaded()`（原本只在成功換片後才補載，載入鏈可能停住）；③ `clone.preload` `none → auto`（沒被 `loadLayer()` 點到的層仍不會下載）。
- 實測（Playwright 8000）：6 層全建立、強制快轉 30s 得到 `4→5→0→1→2→3→4…` 完整循環 38 次（6 支全輪到、全程 1 個 `.is-on`＋淡入中 2 個）、初次載入只抓 2 支（5.4MB）、390 無水平溢出、reduced-motion 只 1 層 paused、console 0 error、`manage.py check` 0 issue、flake8 無新增問題。
- 注意：片單總量約 22MB（原 3 支 14.4MB＋新 7.7MB），仍是「用到才載」。


**`/about/` 重新顯示 `bc-popeye50` 字輪，位置改到 `#bc-sticky-mv` 正下方 — 2026-11-06 完成（已 push `f88da5de`）**

| 項目 | 內容 |
|---|---|
| 指示 | 「修改 about.html：重新顯示 section bc-popeye50，並移動到 bc-sticky-mv 下方」 |
| 改動 | 只改 `templates/betweencoffee_delivery/about.html`（+53 行）：① extra_css 加 `bc-popeye50.css?v=20261102f`；② markup 插在 `#bc-sticky-mv` 收尾 `</section>` 之後（DOM 順序＝`#bc-sticky-mv` → `.bc-popeye50` → `.bc-series-hero.bc-series-bracket`）；③ extra_scripts 加 `bc-popeye50.js?v=20261102c`（`defer`，緊接 `bc-sticky-mv.js`）。CSS／JS 檔本身未改 ⇒ 沿用原版號 |
| 免改後端 | `views.About` 的 `wheel_items`（`betweencoffee_delivery/views.py:475-491`）與 `series_coffees` 移除期間一直留在 context |
| 驗證（Playwright，8081） | gap 0、模組 1440×900／390×844、字輪自動旋轉、中心連結實點導頁 `/coffee/2/`、無水平溢出、上方 sticky 影片正常播放（currentTime 前進）、console 0 error、`manage.py check` 0 issue |
| 已知行為 | 開場 loader 約 7s 進終態（載入即開始跑，模組在第二屏看不到）；要「進視窗才播」需改 `bc-popeye50.js` 的 `runIntro()` |
| 截圖 | `/home/kei/bc-about-popeye50-below-mv-{1280,390}.png` |
