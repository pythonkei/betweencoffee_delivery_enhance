# 05_PRIORITY_TASKS

> **最後更新**: 2026-09-14

## 近期優先
1. **咖啡詳情頁 staff-comment 氣泡**（✅ 完成 2026-09-13，2026-09-14 微調＋DB 化＋幾何可設定）：三顆氣泡文字由 `CoffeeItem.staff_comment_1/2/3` 驅動（Admin 逐款改字、留空不顯示）＋ 第三顆（pattern-2 / `blowing-pattern03a.svg` / p-2 右側下半）＋ **定位幾何每款可設定**（`bubble_safe_left/right`、`bubble_photo_ratio`、`bubble_scale`；留空時存檔以 Pillow 自動量測去背 PNG，換圖後清空再存即重新量測）→ 直式、橫式（Black Blend 1200×840）與其他比例（Flat White 840×1200）皆可用；內距依字數 `--bc-cb-n` 自動置中；版號 bc-coffee-comment.css ?v=20260914d、bc-coffee-comment.js ?v=20260914a
2. **逐款咖啡填入氣泡文字**（待做，Admin 操作）：在 CoffeeItem 的「詳情頁氣泡文字（留空=不顯示）」為每款填入 1~3 句（建議 5~7 字）。目前只有 Butter King 有第 1、3 句（第 2 句為空），其餘 7 款皆待填（照片幾何已自動備好，填字即生效）
3. **Black Blend / Flat White 氣泡定位**（✅ 完成 2026-09-14）：不再受限於 860×1100 寫死的留白；已量測填入 Black Blend（15.08/80.25、比例 1.429、倍率 0.70）與 Flat White（18.1/80.71、比例 0.7、倍率 1.0），CDP 12 組驗證氣泡皆在 `.img-box` 內、距照片內容 6~16px
4. **sake-mv 資源集中**（✅ 完成 2026-09-14）：`static/images/sake-mv/*` 11 檔搬至 `static/images/*`、資料夾刪除、CSS/模板路徑同步（bc-sake-mv.css ?v=20260914a）
5. **首頁 yama tax-nav 收尾**（進行中）：welcome 面板已隱藏、圓球主題色 #774f18 / hover #1a1919、deco 白色、tagline 兩態文字完成；最後 → index/about/bean_menu 375–1280 響應式全面檢查 + CSS 版號 + git push
6. **行動端 `.bc-reviews-section` 縮放**（待做）：加入 ≤768 media 縮小
7. **bean_menu REAL 模組整合驗收**：模組已插入頁面、背景圖隱藏；需最後響應式與 push
8. **記憶庫瘦身收尾**：驗證 auto_load 正常、更新所有引用 `.clinerules/uiux-principles.md` 的路徑為 `docs/uiux-full-reference.md`
9. **安全（依 docs/security/git-history-cleanup.md）**：確認支付寶金鑰 8/1 已於後台輪換；git filter-repo 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private
