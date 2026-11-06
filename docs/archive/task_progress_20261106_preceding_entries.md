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
