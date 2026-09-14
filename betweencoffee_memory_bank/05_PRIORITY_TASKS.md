# 05_PRIORITY_TASKS

> **最後更新**: 2026-09-14

## 近期優先
1. **咖啡詳情頁 staff-comment 氣泡**（✅ 完成 2026-09-13，2026-09-14 微調＋DB 化）：`/coffee/x/` 三顆氣泡文字改由 `CoffeeItem.staff_comment_1/2/3` 驅動（Admin 可逐款改字、留空=不顯示、三顆全空則不出現）＋ 新增第三顆（pattern-2 / `blowing-pattern03a.svg` / p-2 右側下半）；內距依字數 `--bc-cb-n` 自動置中（4 斷點實測 ≤0.43px）；氣泡位置對齊 860×1100 去背照片留白（9.3% / 89.53%）；bc-coffee-comment.css ?v=20260914c、bc-coffee-comment.js ?v=20260914a
2. **逐款咖啡填入氣泡文字**（待做，Admin 操作）：在 CoffeeItem 的「詳情頁氣泡文字（留空=不顯示）」為每款填入 1~3 句（建議 5~7 字）。目前只有 Butter King（原兩句＋第 2 顆佔位「熱飲更顯層次」待改）
3. **Black Blend / Flat White 的氣泡位置**（待做）：氣泡位置以「860×1100 直式去背照片、左右留白 9.3% / 89.53%」設計；其餘 6 款 860×1100 已實測留白幾乎一致（9.07~9.42% / 89.65~89.88%）可通用，但 Black Blend（1200×840 橫式）與 Flat White（840×1200、留白 18.1/80.7%）需改成每款可設定的 CSS 變數（或由 ImageField 自動量測 alpha bbox）
4. **sake-mv 資源集中**（✅ 完成 2026-09-14）：`static/images/sake-mv/*` 11 檔搬至 `static/images/*`、資料夾刪除、CSS/模板路徑同步（bc-sake-mv.css ?v=20260914a）
5. **首頁 yama tax-nav 收尾**（進行中）：welcome 面板已隱藏、圓球主題色 #774f18 / hover #1a1919、deco 白色、tagline 兩態文字完成；最後 → index/about/bean_menu 375–1280 響應式全面檢查 + CSS 版號 + git push
6. **行動端 `.bc-reviews-section` 縮放**（待做）：加入 ≤768 media 縮小
7. **bean_menu REAL 模組整合驗收**：模組已插入頁面、背景圖隱藏；需最後響應式與 push
8. **記憶庫瘦身收尾**：驗證 auto_load 正常、更新所有引用 `.clinerules/uiux-principles.md` 的路徑為 `docs/uiux-full-reference.md`
9. **安全（依 docs/security/git-history-cleanup.md）**：確認支付寶金鑰 8/1 已於後台輪換；git filter-repo 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private
