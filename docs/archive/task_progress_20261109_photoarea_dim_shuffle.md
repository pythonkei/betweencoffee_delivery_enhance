# 封存：2026-11-09 首頁 hero 照片（黑蒙版 75%／每次載入重排落點）與「咖啡豆製程」模組移頁

> 2026-11-10 由 `task_progress.md` 移出（該檔超過 11.7K 上限）。內容逐字保留。

**首頁 hero 照片黑蒙版 70% → 75%（使用者指示）— 2026-11-09 完成（未 push）**

- 只改一個值：`bc-photoarea.css:37` `--pa-dim: 0.3` → **`0.25`**（`.25` ＝ 疊 `rgba(0,0,0,.75)`，`brightness(.25)` 等價）；`:36`／`:89-96` 註解同步（演進 40%→50%→60%→70%→**75%**）。
- 版號：`index.html:973` `?v=20261109f` → **`g`**；驗證：4 張 `img` ＋ 第 3 格 `video` 的 `filter` 全為 `brightness(0.25)`、
  容器無 filter；1440／390 無溢出、console 0 error；`/about/` 不含 `bc-photoarea`。
- 文件：`docs/home-photoarea.md`（§四之三、§六第 9 條）、`.clinerules/project-core.md:49`、`04_SYSTEM_STATE.md` 11-09 ①。

**首頁 hero 照片「每次載入重排落點」（比照 hicard 原站）— 2026-11-09 完成（未 push）**

- 指示：「原站每次刷新網站時，每張照片的顯示位置都不同，可以按照修改」。
- 做法（**伺服器端洗牌**，不是在 JS 裡）：`betweencoffee_delivery/views.py` 新增 `PHOTOAREA_TILES`＋
  `_photoarea_slots()`（x、y 各自 `random.sample` 取 1–5 的排列）→ `Index.get` 塞 `context["pa_slots"]`；
  `partials/bc_brand_stage_hero.html` 5 格改寫成 `x_{{ pa_slots.N.x|default:舊值 }}`／`y_{{ … }}`
  （`.d_n` 層序、`data-para` 視差量、`.yoko` 影片格固定不動）。
- 為什麼不放 JS：`bc-photoarea.js` 是 `defer`，執行時機晚於首次繪製 → 會「先排在原位、載入後才跳位」；
  view 端決定 ⇒ HTML 到瀏覽器時已是隨機落點，關 JS／GSAP 掛掉也有效（原站本身也是 SSR 洗牌）。
- 沒動任何 `static/**` ⇒ 不必升 `?v=`；驗證：連 5 次 `curl /` 的 `x_n y_n d_n` 都不同、單次內 x/y 各自不重複。
- 文件：`docs/home-photoarea.md` §四之四（含「要固定落點」的回復方法）＋§六第 10 條；`04_SYSTEM_STATE.md` 11-09 ③。

**首頁 hero 黑蒙版 70%＋「咖啡豆製程」模組移至 about 頁 — 2026-11-09 完成（細節併入上面 75% 條目）**

- ① 黑蒙版同日 40% → 50% → 60% → 70%（`--pa-dim` `.6→.5→.4→.3`、`?v=` `c→d→e→f`；最終 75% 見上）。
- ② `.bc-home-service` 自首頁 `[2b-2]` 移到 `/about/` 的 `aside.bc-search` 之後（三處掛載點對調；
  版號 `20261030a`→`20261109a`，只改檔頭註解；原生 scroll ⇒ 不依賴 GSAP／Lenis）。
