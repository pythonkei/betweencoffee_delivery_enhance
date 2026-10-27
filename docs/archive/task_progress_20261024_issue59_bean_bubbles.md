# #59 咖啡豆（BeanItem）詳情頁氣泡文字 — 完整記錄（封存）

> 2026-10-25 從 `task_progress.md` 移出（該檔超出 11.7K 上限）。此任務已完成並 push `edf3e87c`，
> 只有要追查細節（欄位、migration、實測數據）時才讀。

**#59 咖啡豆（BeanItem）詳情頁氣泡文字 — ✅ 完成並驗證（已 push `edf3e87c`）**

| 項目 | 內容 |
|---|---|
| 需求 | 咖啡豆詳情頁也要有咖啡頁那套「店員氣泡」：同一套渲染邏輯、6 個落點可選、Admin 逐款設定 |
| 改動檔案 | `eshop/models/shop_items.py`（BeanItem 新增 10 欄位＋`BUBBLE_POS_CHOICES`＋`measure_bubble_geometry()`＋`save()` 自動量測）、`eshop/admin.py`（加 2 個 fieldset）、`templates/.../bean.html`（氣泡 markup＋`extra_css`/`extra_scripts`，含 `block.super`）、`templates/.../coffee.html`（加 `bc-photo-comment` 類別、版號 `?v=20261024a`）、`static/css/bc-coffee-comment.css`＋`static/js/bc-coffee-comment.js`（宿主 selector 由 `.bc-coffee-photo` 改中性 `.bc-photo-comment`，51+2 處，邏輯未改） |
| 遷移 | `0081` AddField（10 欄位）、`0082` 量測填入幾何（Pillow，只填空值）、`0083` 依品名預填氣泡文字（只填空值，reverse 只清自己寫的句子） |
| 幾何實測 | 6 款豆圖皆 1263×1263、alpha bbox 18.61%／80.21%、ratio 1.0、scale 1.0 |
| 驗證 | `check` 0 issue、`makemigrations --check` clean；`/bean/1/`、`/bean/8/`、`/coffee/10/` 皆 200 且各 3 顆氣泡；6 落點 × 8 斷點（375/480/576/768/992/1200/1400/1920）量測：無水平溢出、氣泡最外緣 19.7~994.9px 皆在視窗內、與照片內容 bbox 間距 ≥ -2.2px（768 的 p3:tr 為 −2.2px，落在去背透明區，視覺無重疊）；桌機／手機截圖確認氣泡、頭像、動畫正常；console 0 error |
| 文案 | 預填 6 款 × 3 句為**草稿**（依各款 flavor 擬），員工可直接在 Admin 改寫；改寫後 seed migration 不會覆蓋 |
