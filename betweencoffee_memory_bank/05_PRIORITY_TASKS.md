# 05_PRIORITY_TASKS

> **最後更新**: 2026-09-14

## 近期優先
1. **咖啡詳情頁 staff-comment 氣泡**（✅ 完成 2026-09-13，2026-09-14 微調）：`/coffee/10/` 氣泡已由「壓在咖啡杯照片上」改為對齊去背 PNG 留白（p-1 右緣 = 9.30% − 0.5fs、p-3 左緣 = 89.53% + 0.5fs）；2026-09-14 再微調 5%（p-1 往左、p-3 向上右，5% ＝ 氣泡自身尺寸）；8 斷點實測距咖啡杯 9~12px、無水平溢出；bc-coffee-comment.css ?v=20260914a
2. **氣泡文字垂直置中**（✅ 完成 2026-09-14）：使用者回報 `blowing-pattern02a.svg` 未與文字中心對齊 → 診斷為 SVG 本身水平已精確置中，真因是兩顆氣泡文字都偏高（pattern-1 高 3.49px、pattern-5 高 2.32px）；只重新分配 `.text` 上下內距（合計不變）修正，最終 4 斷點實測偏差 ≤ 0.92px
3. **全部咖啡詳情頁套用氣泡**（待做）：目前僅 `{% if coffee.id == 10 %}` 輸出；各商品照片比例與去背邊界不同（如 Black Blend 1200×840 橫圖），需逐張量 alpha bbox，並把 9.30% / 89.53% 由硬編碼改為可依圖設定的 CSS 變數
4. **sake-mv 資源集中**（✅ 完成 2026-09-14）：`static/images/sake-mv/*` 11 檔搬至 `static/images/*`、資料夾刪除、CSS/模板路徑同步（bc-sake-mv.css ?v=20260914a）
5. **首頁 yama tax-nav 收尾**（進行中）：welcome 面板已隱藏、圓球主題色 #774f18 / hover #1a1919、deco 白色、tagline 兩態文字完成；最後 → index/about/bean_menu 375–1280 響應式全面檢查 + CSS 版號 + git push
6. **行動端 `.bc-reviews-section` 縮放**（待做）：加入 ≤768 media 縮小
7. **bean_menu REAL 模組整合驗收**：模組已插入頁面、背景圖隱藏；需最後響應式與 push
8. **記憶庫瘦身收尾**：驗證 auto_load 正常、更新所有引用 `.clinerules/uiux-principles.md` 的路徑為 `docs/uiux-full-reference.md`
9. **安全（依 docs/security/git-history-cleanup.md）**：確認支付寶金鑰 8/1 已於後台輪換；git filter-repo 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private
