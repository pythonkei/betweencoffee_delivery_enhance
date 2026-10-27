# docs/ 索引（先讀這頁，再決定要讀哪個檔）

> 目的：**避免 AI 亂翻 2MB 文件**。規則：只讀「活文件」；`[ARCHIVE]` 只能用 `grep` 找關鍵字，不要整檔讀。

## 一、活文件（會持續更新，值得讀）

| 檔案 | 內容 | 大小 |
|---|---|---|
| `.clinerules/uiux-core.md` | UI/UX 規範精簡版（**已自動注入**，通常不需再讀） | 3.6K |
| `.clinerules/project-core.md` | 專案核心規則（**已自動注入**） | 8.5K |
| `docs/uiux-full-reference.md` | UI/UX 完整參考（設計流程、四角色分析、審查清單、SVG 範例）→ 只在做新 UI 元件時讀 | 34K |
| `betweencoffee_memory_bank/04_SYSTEM_STATE.md` | 系統現況、DB 現況、部署版本 | 5.4K |
| `betweencoffee_memory_bank/05_PRIORITY_TASKS.md` | 未完成事項與優先序 | 4.5K |
| `task_progress.md` | 當前任務進度（只留現況；歷史已封存） | 10.4K |
| `docs/guides/RENDER_DEPLOY_GUIDE.md` | Render 部署步驟（Docker、env、migration） | 11K |
| `docs/guides/WEBSOCKET_MIGRATION_GUIDE.md` | WebSocket 三層架構與遷移 | 8K |
| `docs/security/git-history-cleanup.md` | 金鑰清除與 repo 安全待辦 | — |
| `docs/verify/CDP_SETUP.md` | CDP 驗證環境啟動方式（port 9222、snap chromium 注意事項）→ 跑驗證腳本前讀一次 | 35K（只讀前 80 行即可） |

## 二、驗證腳本（`docs/verify/`，改前端後挑一支跑）

命名慣例：`cdp_verify_<主題>.py`（斷言式，輸出 PASS/FAIL）、`cdp_measure_*`／`cdp_diag_*`（量測診斷）、`cdp_shot_*`（截圖）。

- 首頁：`cdp_verify_feed_animation.py`、`cdp_verify_hero_coffee_photos.py`、`cdp_verify_hero_weather.py`、`cdp_verify_clock_braces.py`、`cdp_verify_clock_clash.py`、`cdp_verify_bg_footer.py`、`cdp_verify_footer_scroller.py`、`cdp_verify_top_art.py`
- 商品/選項：`cdp_verify_roast_active.py`、`cdp_verify_oz_label.py`、`verify_coffee_roast_option.py`、`verify_coffee_tea_type_option.py`、`verify_cup_strength_option.py`、`verify_bean_group_order.py`
- 購物車/結帳：`cdp_verify_floating_cart.py`、`cdp_verify_payment_item_style.py`
- 其他：`cdp_verify_welcome_mobile.py`、`cdp_verify_leader.py`、`cdp_verify_login_deco.py`

> 執行方式與前置（dev server + chromium `--remote-debugging-port=9222`）見 `docs/verify/CDP_SETUP.md`。

## 三、`[ARCHIVE]` 歸檔區（不要主動讀）

| 路徑 | 內容 | 何時才查 |
|---|---|---|
| `docs/archive/clinerules_history_20261014.md` | 舊 `.clinerules` 全文（209K，含 2026-08~10 任務日誌、Phase 3 規劃） | 要追查舊決策／舊 commit 時 `grep` |
| `docs/archive/task_progress_202608-20261015_full.md` | 舊 `task_progress.md` 全文（290K，**本機留存、未入庫**：根層 `/*.md` 被 `.gitignore` 排除） | 追查舊任務細節 |
| `docs/archive/memory_bank_04_full_20261017.md` | 舊 `04_SYSTEM_STATE.md` 全文（181K，逐筆變更日誌） | 追查某次變更內容 |
| `docs/archive/memory_bank_05_full_20261017.md` | 舊 `05_PRIORITY_TASKS.md` 全文（100K，已完成項目明細） | 追查舊任務 |
| `docs/archive/04_SYSTEM_STATE_history_202607-202609.md` | 2026-07~09 系統狀態歷史（195K） | 同上 |
| `docs/archive/task_progress_20261024_issue59_bean_bubbles.md` | #59 咖啡豆詳情頁氣泡文字完整記錄（2026-10-25 從 `task_progress.md` 移出） | 追查氣泡欄位／migration `0081`–`0083` 細節 |
| `docs/reports/**`（47 份） | 2026 年一次性「完成報告／遷移報告／優化方案」 | 只 `grep` 關鍵字 |
| `docs/*.md`（頂層 20+ 份：`*完成報告`、`*修復報告`、`*清理總結`、`MCP-*`、`Memory-Bank-*`） | 一次性報告與 MCP 安裝紀錄 | 只 `grep` 關鍵字 |

## 四、查詢建議

```bash
# 找哪份文件提過某主題（不開檔）
grep -rl "關鍵字" docs --include='*.md' | head

# 只要上下文兩行
grep -rn -C2 "關鍵字" docs/reports | head -40

# 文件防爆檢查（活文件超過上限就 exit 1）
python3 scripts/docs_size_check.py
```

- 不要用「列出所有 md 再逐一讀」的方式探索；先看本頁 → 直接開對應活文件。
