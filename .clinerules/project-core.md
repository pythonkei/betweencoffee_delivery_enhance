# Between Coffee — 專案核心（自動注入精簡版）

> 2026-10-23 由 209KB 的 `.clinerules/.clinerules` 重整。**本檔＝現行規則**；歷史任務日誌已移至
> `docs/archive/clinerules_history_20261014.md`（**不要讀**，除非要追查舊決策，且只 grep 關鍵字）。
> 文件導覽見 `docs/INDEX.md`。

## 0. AI 工作守則（省 token / 加速，優先遵守）

1. **先搜後讀**：先 `grep -n` 或 search 取得「檔案:行號」，再 `read_files(start_line, end_line)` 只讀該段。**不要整檔讀 > 500 行的檔案**。
2. **預設不讀**：`docs/archive/**`、`docs/reports/**`（一次性報告）、`task_progress.md` 歷史段、`node_modules/**`、`media/**`、`*.log`、`_herocmp/**`、`js_analysis_report/**`。
3. **讀文件順序**：`docs/INDEX.md` → 對應「活文件」→ 原始碼。Memory Bank 只在需要系統全貌時讀 `04` / `05`（各 ≤3KB）。
4. **單次驗證迴圈**：改完 → `python3 manage.py check` → 前端才加跑一支 CDP 腳本 + 看 console error。**不要重跑整套驗證**，除非使用者要求回歸。
5. **併發工具**：獨立的讀取／搜尋／指令放在同一輪呼叫，不要一問一答。
6. **回報格式**：結論 + `檔案:行號`；不貼大段程式碼、不重述已完成事項。
7. **改檔前**：先 grep 同類命名／既有 class，沿用 `.bc-*` 命名與既有元件，不新增樣式體系。
8. **改文件後**：跑 `python3 scripts/docs_size_check.py`；超標就把歷史段移到 `docs/archive/`，只留現況摘要。

## 1. 專案與部署

- **專案**：Between Coffee 咖啡店外帶網站＋訂單製作管理系統（單店、輕量）。
- **技術棧**：Django 4.x + PostgreSQL + Django Channels（InMemoryChannelLayer，無 Redis）+ DRF + Bootstrap 5 + Vanilla JS ES6；Celery 以 **MockCelery** 同步降級。
- **模組**：`eshop/`（商品/訂單/支付/隊列）、`cart/`、`socialuser/`、`restaurant/`、`core/`。
- **Live**：https://betweencoffee-delivery-enhance-v1.onrender.com/ ｜ GitHub：`pythonkei/betweencoffee_delivery_enhance`
- **部署**：Render Docker（service `srv-d8jce6rtqb8s73897t4g`、singapore、free）。
  ⚠ **autoDeploy 已關閉（2026-10-06 起）→ 必須在 dashboard 按 Manual Deploy**。
- **版本狀態（2026-10-28 複驗）**：`origin/main` 尖端＝`b29ff324`（當日推 4 筆 code/docs：`29eb67d1` bean SERIES 滑桿、`f57eb768` trade-gothic 字型、`f730abab` bc-series 標題行距／字級、`b29ff324` docs 封存），本機 `main`＝`origin/main`。正式站 live＝`cc99a3a4`（`dep-dbermb1srm7s73d4s13g`，2026-10-25 08:20Z 手動部署成功；10-23 的 Supabase `ENOTFOUND` 已排除）⇒ **待手動部署**（autoDeploy＝off，push 不會觸發）。即時複驗：`git log --oneline -3`＋Render API。

## 2. 核心業務

- **狀態機**：`pending → payment_pending (FPS/現金) → paid → waiting → preparing → ready → completed`
- **支付**：PayPal（全自動，`process_payment_success()`）／Alipay（全自動，`alipay_callback()`）／FPS、現金（半自動，`confirm_fps_payment()` / `confirm_cash_payment()`）。
- **模型關係**：`OrderModel → CoffeeItem/BeanItem (M2M) + CoffeeQueue (1:1)`；`CoffeeQueue → Barista`；`CustomerLoyalty → user`。
- **營運參數**：2 台咖啡機、2 名員工、同時最多 4 杯。

## 3. 關鍵檔案

| 檔案 | 用途 |
|---|---|
| `betweencoffee_delivery/settings.py` | 全站設定（含 WhiteNoise、CHANNEL_LAYERS） |
| `eshop/models/order.py`、`eshop/models/base.py` | 訂單／商品模型 |
| `eshop/order_status_manager.py`、`eshop/queue_manager_refactored.py` | 狀態流轉／隊列 |
| `eshop/serializers.py` | 訂單序列化（選項顯示的第一層） |
| `eshop/views/payment_views.py`、`eshop/consumers.py` | 支付／WebSocket |
| `static/js/websocket-core.js` | 前端 WS 三層架構底層 |
| `static/js/staff-order-management/base-order-renderer-v2.js` | 員工端渲染器基底 |
| `static/css/bc-components.css` | 品牌元件庫（`.bc-btn` / `.bc-input` / `.bc-card` / `.bc-order-collapse`） |
| `static/css/bc-recommended-pages.css`、`static/js/bc-recommended-pages.js` | 首頁「推薦頁面」雙卡（緊接品牌舞台 `[2b]`） |
| `eshop/models/shop_items.py`、`static/js/bc-coffee-comment.js` | 咖啡／咖啡豆詳情頁氣泡（`measure_bubble_geometry()`＋6 落點） |

## 4. 開發規範

- Python：flake8 + black + isort（`pyproject.toml`）；JS：ES6 class；CSS：`bc-` 前綴、BEM-ish。
- Commit：`feat|fix|docs|style|refactor|test|chore`；分支 `main`（生產）/ `develop` / `feature/*` / `bugfix/*`。
- **前端版號**：WhiteNoise 快取 1 年 → **改任何 `static/js/*.js`、`static/css/*.css` 必須同步升 `?v=`**（格式 `YYYYMMDDx`，同檔同日多次改就換字母）。
- 前端改動完成定義：`manage.py check` 0 issue + 實際載入頁面無 console error + 目標尺寸/狀態實測。

## 5. 常見任務速查

- **新增商品選項顯示**（如濃度／烘焙／茶種）：① `eshop/serializers.py` 的 `serialize_order()` items mapping → ② `base-order-renderer-v2.js` 的 `_renderItemOptions()` → ③ 子渲染器若硬編碼選項 HTML 也要改 → ④ `common-utils.js` 的 `renderOrderItems()`（若有）。
- **選項行樣式**：`.bc-options-row`（flex/wrap/gap 8、`--bc-text-muted`）+ `.option-item`（nowrap）+ `.ov`（白字）。
- **自訂選項組**：資料驅動（Admin 勾選啟用＋排序），新增選項只需 3 檔＋一支 migration。
- **首頁區塊順序**：看 `templates/betweencoffee_delivery/index.html` 檔頭註解 `[1]…[2b]`（＝實際 DOM 順序）。`[2b]` 推薦雙卡必須**緊接** `<section class="hero bc-brand-stage-hero">`，中間不插留白 section（模組自帶 `#0e0e0e` 底）。
- **首頁隱藏品牌舞台社群列**：只靠 extra_css 的 `.bc-brand-stage-hero #bc-stage-socials{display:none}`；不要改 `partials/bc_brand_stage_hero.html`（about 頁真頁尾要保留社群列）。
- **詳情頁氣泡（咖啡／咖啡豆）**：資料在 `CoffeeItem` / `BeanItem` 的 `staff_comment_1~3`＋`bubble_pos_1~3`（`tl/ml/bl/tr/mr/br`）；幾何 `bubble_safe_left/right`、`bubble_photo_ratio`、`bubble_scale` 存檔時由 `measure_bubble_geometry()` 自動量測，換照片會重算。

## 6. 除錯速查

- **WebSocket**：`asgi.py` → `settings.CHANNEL_LAYERS` → `eshop/consumers.py` → `eshop/routing.py` → `static/js/websocket-core.js`。
- **支付**：環境變數（`PAYPAL_CLIENT_ID` / `ALIPAY_APP_ID`…）→ `payment_views.py` → `paypal_utils.py` / `alipay_utils.py` → `order_status_manager.py`。
- **選項不顯示**：serializer 是否 mapping `strength_level_cn`；子渲染器是否硬編碼；欄位名（API 給 `strength_level`，渲染器讀 `strength_level_cn || strength_level`）。

## 7. 已知地雷（踩過）

- **Rive 圖示（首頁四步）**：`intro` 是唯一會走到「完整圖示」的 timeline；`hover` 播完停在起始姿勢、`off` 是空白線稿。**不可 `stop()`/`scrub()`**，只能 `play()`；one-shot 播完會自動 dispose，再 `play()` 會從 frame 0 重來。
- **浮動購物車** z-index 必須 ≥ 100000（`.bc-attract-buy` 為 99999 且熱區有負 margin）。
- **`.bc-attract` 負 margin** 會讓「外層盒」與「可見長條」差 24px，量測一律量可見元素。
- **Render free plan** 無 Redis：不要引入需要 Redis 的功能；Celery 任務同步執行。
- **Migration 編號**：`python3 manage.py makemigrations --check` 必須乾淨；資料搬移用 data migration，不在 view 裡寫死。
- **`hidden` 屬性在品牌舞台無效**：`static/css/bc-brand-stage.css:207` `#bc-brand-stage .footer-socials{display:flex}`（特異度 1,1,0）壓過 UA `[hidden]`（0,1,0）→ 要隱藏必須寫作者 CSS。
- **`#bc-brand-stage` 是明確 `grid-area` 版面**：藏掉一列（社群列 `grid-area:6/3/7/7`，≤991px 為 `grid-column:1/7`）整列連 `padding-top` 一起消失，下方內容自動整齊上移，不要再補留白。
- **大型原始素材不進版控**：`static/images/ani_{coffee,bean}_apng.png`（12.8MB，僅供重新產圖）已列 `.gitignore`；頁面用的是 `static/images/recommended-pages/title-*.png`（176×176 APNG）。

## 8. 文件導覽

| 想做什麼 | 讀哪個 |
|---|---|
| UI/UX 規範 | `.clinerules/uiux-core.md`（已注入）／細節 `docs/uiux-full-reference.md` |
| 系統現況 | `betweencoffee_memory_bank/04_SYSTEM_STATE.md` |
| 待辦／優先序 | `betweencoffee_memory_bank/05_PRIORITY_TASKS.md` |
| 當前任務進度 | `task_progress.md`（只留現況，歷史已封存） |
| 目錄索引 | `docs/INDEX.md` |
| 歷史決策／舊任務 | `docs/archive/**`（僅 grep） |
