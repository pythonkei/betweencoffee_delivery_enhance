# 05_PRIORITY_TASKS

> 2026-10-23 精簡版（原檔 100KB 已封存：`docs/archive/memory_bank_05_full_20261017.md`）。
> 本檔**只放未完成**與**最近完成一行式**；已完成項目的完整說明不在此，必要時 grep 封存檔。

## 當前版本控制狀態

- ⚠ **本機有多個未 push commit**：#55 `aaf7c2aa`、#57 `28b1c322`、10-14 hero `aedcf859`…（`bf495475` 之後全部）
- ⚠ **#58（bc-steps Rive 圖示列）尚未 commit**：`static/js/bc-steps-rive.js`、`static/css/bc-steps.css`、`static/animations/rive/`、`static/library/rive-canvas-2.35.2/` 為 untracked；`templates/betweencoffee_delivery/index.html` 已修改（`?v=20261022c`）
- ⚠ 正式站仍為 `ec8fcadb`（autoDeploy 關閉，需手動 deploy）

## 近期優先（未完成）

| # | 任務 | 類型 | 備註 |
|---|---|---|---|
| 1 | **提交 #58 bc-steps** | 版控 | `git add` 上述 4 個路徑 + `index.html` |
| 2 | **push 累積 commit** | 版控 | 推 `origin/main` 後再決定是否手動部署 |
| 3 | 逐款咖啡填入詳情頁氣泡文字 | 內容（Admin） | `CoffeeItem.staff_comment_1/2/3`，留空＝不顯示；目前僅 Butter King 有第 1、3 句 |
| 4 | 行動端 `.bc-reviews-section` 縮放 | 前端 | 新增 ≤768 媒體查詢；純 CSS、可逆 |
| 5 | `bean_menu` REAL 模組驗收 | 前端 | 響應式檢查後收尾 |
| 6 | yama `tax-nav` 收尾 | 前端 | welcome 面板已隱藏、圓球配色（`#774f18` / hover `#1a1919`）已完成，剩平板層確認 |
| 7 | 安全性收尾 | 維運 | 確認支付寶金鑰已輪換（2026-08-01）；`git filter-repo` 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private。見 `docs/security/git-history-cleanup.md` |

## 最近完成（一行式）

- **2026-10-22~23｜#58 首頁四步旅程 Rive 圖示列**：自架 Rive 2.35.2 ＋ IntersectionObserver 延遲載入；intro/hover/rest 行為修正（不再 `stop`/`scrub`）；桌機 4 欄、手機 2×2、reduced-motion 全數驗證通過。
- **2026-10-17｜#57 移除 hero／導覽列時鐘**：`bc-weather.js` `ORDER`＝`['icon','temperature']`，刪 `updateClock()`。（`28b1c322`）
- **2026-10-16｜#56 首頁照片格桌機字級再加大**：名稱／highlight 24/18px、`--bc-hero-caption-h` 68.38。（本機）
- **2026-10-15｜#55 首頁照片格桌機照片縮小**：1440 時 280×400、字級 20/16px。（`aaf7c2aa`）
- **2026-10-14｜#51 首頁順序反轉**：GUNTE hero 回第一屏＋環形字 markup／尺寸／載入可見性修正。（`bf495475` 已 push）
- **2026-10-14｜生產版本複驗**：Render live＝`dep-db6btj0473hc73du80hg`／`ec8fcadb`（manual trigger）。
- **2026-10-12｜hero 時鐘手機 `{ }`**：9 欄顯示＋`#bc-bg-footer` 的 `w-node-*` id 語意化。（`6e29b447`，已部署）
- **2026-10-08｜10 月批次收尾**：migration 0079（烘焙）/0080（茶種）、about 頁 BC 動態 footer、首頁 `.top_art`、滑出購物車 API 驅動。（`18a14070` 已 push）
- **2026-10-06｜CDP 驗證基礎建設**：`docs/verify/CDP_SETUP.md` ＋ `cdp_verify_*` 腳本群。
- **2026-09-15｜正式庫落差回補**：訂單 643 筆／帳號 13／佇列 354 補入（單 transaction＋PK 去重＋sequence 修正）。
