# 05_PRIORITY_TASKS

> **最後更新**: 2026-09-13

## 近期優先
1. **咖啡詳情頁 staff-comment 氣泡**（✅ 本次完成 2026-09-13）：`/coffee/10/` 氣泡已由「壓在咖啡杯照片上」改為對齊去背 PNG 留白（p-1 右緣 = 9.30% − 0.5fs、p-3 左緣 = 89.53% + 0.5fs；單一 calc 算式通吃 375→1920 全斷點，實測零重疊／無水平溢出；bc-coffee-comment.css ?v=20260913a）
2. **全部咖啡詳情頁套用氣泡**（待做）：目前僅 `{% if coffee.id == 10 %}` 輸出；各商品照片比例與去背邊界不同（如 Black Blend 1200×840 橫圖），需逐張量 alpha bbox，並把 9.30% / 89.53% 由硬編碼改為可依圖設定的 CSS 變數
3. **首頁 yama tax-nav 收尾**（進行中）：welcome 面板已隱藏、圓球主題色 #774f18 / hover #1a1919、deco 白色、tagline 兩態文字完成；最後 → index/about/bean_menu 375–1280 響應式全面檢查 + CSS 版號 + git push
4. **行動端 `.bc-reviews-section` 縮放**（待做）：加入 ≤768 media 縮小
5. **bean_menu REAL 模組整合驗收**：模組已插入頁面、背景圖隱藏；需最後響應式與 push
6. **記憶庫瘦身收尾**：驗證 auto_load 正常、更新所有引用 `.clinerules/uiux-principles.md` 的路徑為 `docs/uiux-full-reference.md`
7. **安全（依 docs/security/git-history-cleanup.md）**：確認支付寶金鑰 8/1 已於後台輪換；git filter-repo 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private
