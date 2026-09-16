# 05_PRIORITY_TASKS

> **最後更新**: 2026-09-15

> ⚠️ **待部署**：本批改動（氣泡 6 落點／退場動畫／Admin 精簡／留白與照片尺寸／migration 0070）尚未上正式站 —— Render `autoDeploy=no`，需在 dashboard 按 **Manual Deploy**（部署時自動套用 migration 0070），或提供 `RENDER_API_KEY` 以 API 觸發。

## 近期優先
1. **咖啡詳情頁 staff-comment 氣泡**（✅ 完成 2026-09-13，2026-09-14 微調＋DB 化＋幾何可設定）：三顆氣泡文字由 `CoffeeItem.staff_comment_1/2/3` 驅動（Admin 逐款改字、留空不顯示）＋ 第三顆（pattern-2 / `blowing-pattern03a.svg` / p-2 右側下半）＋ **定位幾何每款可設定**（`bubble_safe_left/right`、`bubble_photo_ratio`、`bubble_scale`；留空時存檔以 Pillow 自動量測去背 PNG，換圖後清空再存即重新量測）→ 直式、橫式（Black Blend 1200×840）與其他比例（Flat White 840×1200）皆可用；內距依字數 `--bc-cb-n` 自動置中＋ **氣泡位置 6 選 1**（✅ 2026-09-15：每顆氣泡可在 Admin 選左上／左中間／左下／右上／右中間／右下，欄位 `bubble_pos_1/2/3`（migration 0070）；6 個落點都自動貼在咖啡杯外圍、所有斷點自動縮放；動畫效果與原站相同；CDP 實測預設值與改動前逐項相同）＋ **Admin 精簡**（同日移除「氣泡定位」欄位組：幾何值仍自動量測，只是不再顯示）＋ 三列整體上移（上−2%／中−7%／下−10%）＋ **退場動畫修正**（同日：原會瞬間跳回入場起點往上 40px 才縮小 → 改 `.is-hiding` ＋ 收縮原點 center center，原地縮小消失）＋ **6 落點逐點微調**（`--cb-out` 水平錯開）＋ **Admin 精簡**（移除「氣泡定位」欄位組）；版號 bc-coffee-comment.css ?v=20260915p、bc-coffee-comment.js ?v=20260915a
2. **版面留白與咖啡照片尺寸**（✅ 完成 2026-09-15）：`.ftco-section-blank-small` 累計縮減（桌機 224→112.9px、平板 80.6→65.3px、行動 53.8→22.9px）——樣式綁 class（改標籤無效），改在 `bc-components.css` 覆蓋；平板端咖啡照片 ×0.64（`style-custom.css` 768–1079.98 區塊）；**最後由使用者手動定案**：留白基礎 `2em 0` / `10vh`、≤991 與 ≤768 `2vh`、≤480 `1vh`；`.bc-page-content` 首個 section 上緣 100 / 72 / 60 / 60px；＋ **GUNTE hero slide 等比縮小 10%**（✅ 同日：單一旋鈕 `--bc-gunte-scale`（定案 **0.8**） 驅動容器寬／圖片／圈圈字／hero 高／手套圓，手機不動；版號 bc-gunte-hero.css ?v=20260915a）；版號 bc-components.css ?v=20260915e、style-custom.css ?v=20260915b
2. **逐款咖啡填入氣泡文字**（待做，Admin 操作）：在 CoffeeItem 的「詳情頁氣泡文字（留空=不顯示）」為每款填入 1~3 句（建議 5~7 字）。目前只有 Butter King 有第 1、3 句（第 2 句為空），其餘 7 款皆待填（照片幾何已自動備好，填字即生效）
3. **正式庫資料落差回補 + 資料統一**（✅ 完成 2026-09-15）：訂單 643 筆、帳號 13 個、咖啡佇列 354 筆補入正式庫（單一 transaction + PK 去重 + sequence 修正；腳本 `scripts/backfill_orders_to_prod_20260915.py --apply`、log `scripts/backfill_orders_to_prod_20260915.log`）；`fb_kei` 因正式庫已有同 username/email 帳號，本地 id 58 的訂單改掛正式 id 62（不重複建帳號）；13 個腳本測試帳號一律降權停用（`is_superuser/is_staff/is_active=False`）避免密碼與權限上正式站；5 個 varchar 欄位以 Django 模型為權威對齊（本地庫才是偏離者）；unique 撞號自動改派（order_number 29 筆 → `BC-YYYYMMDD-9NNN`、pickup_code 3 筆 → 9000+）。**後續資料統一**（`scripts/unify_prod_data_20260915.py --apply`）：發現本地 id 62（`test_customer`）與正式 id 62（`fb_kei`）是不同人的 **id 碰撞** → 以 username 為橋樑重新對齊全部 2661 筆訂單歸屬（更新 36 筆：31 筆無主→fb_kei、5 筆→test_customer）、補建 `test_customer`（降權+停用）、覆蓋咖啡名稱 8/9/10（→ 抹茉 / 果香浅煎 / Butter King）。驗證：帳號 40/40、訂單 2661/2661、佇列 1036/1036、訂單歸屬依 username 完全一致、咖啡名稱 0 差異（本地 dump 備份 `/tmp/betweencoffee_now.backup`，1.98MB 仍保留）
4. **Black Blend / Flat White 氣泡定位**（✅ 完成 2026-09-14）：不再受限於 860×1100 寫死的留白；已量測填入 Black Blend（15.08/80.25、比例 1.429、倍率 0.70）與 Flat White（18.1/80.71、比例 0.7、倍率 1.0），CDP 12 組驗證氣泡皆在 `.img-box` 內、距照片內容 6~16px。※ 註：正式庫這兩款其實是 860×1100 的其他照片（`coffee_03_1.png` / `coffee_02_1.png`），量測結果自動為預設值
4. **sake-mv 資源集中**（✅ 完成 2026-09-14）：`static/images/sake-mv/*` 11 檔搬至 `static/images/*`、資料夾刪除、CSS/模板路徑同步（bc-sake-mv.css ?v=20260914a）
5. **首頁 yama tax-nav 收尾**（進行中）：welcome 面板已隱藏、圓球主題色 #774f18 / hover #1a1919、deco 白色、tagline 兩態文字完成；最後 → index/about/bean_menu 375–1280 響應式全面檢查 + CSS 版號 + git push
6. **行動端 `.bc-reviews-section` 縮放**（待做）：加入 ≤768 media 縮小
7. **bean_menu REAL 模組整合驗收**：模組已插入頁面、背景圖隱藏；需最後響應式與 push
8. **記憶庫瘦身收尾**：驗證 auto_load 正常、更新所有引用 `.clinerules/uiux-principles.md` 的路徑為 `docs/uiux-full-reference.md`
9. **安全（依 docs/security/git-history-cleanup.md）**：確認支付寶金鑰 8/1 已於後台輪換；git filter-repo 清除歷史金鑰（init commit 曾含 alipay pem）；repo 建議改 private
