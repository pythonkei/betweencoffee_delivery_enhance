# 封存：首頁 hero 第 3 格影片改為「可輪播容器」（2026-11-09 完成，未 push）

> 2026-11-11 由 `task_progress.md` 移出（該檔超過 11.7K 上限，加入 11-11 浮動購物車項目後超標）。
> 內容逐字保留。

**首頁 hero 第 3 格影片改為「可輪播容器」（使用者指示）— 2026-11-09 完成（未 push）**

- 指示：影片改成可載入多支的輪播容器；順序＝① 現用的 `hero_00` ② `hero_04` ③ `hero_05`。
- 片單＝單一來源 `views.PA_VIDEOS`（依序、不洗牌）→ `Index.get` 塞 `context["pa_videos"]`
  （URL 由 `_mv_versioned_static()` 自動加 `?v=<mtime>`）⇒ **日後加片／換序只改這個常數**。
- 模板 `partials/bc_brand_stage_hero.html`：`{% for pa_video in pa_videos %}` 長出多支 `<video>`（第一支帶 `is-on`）；
  外層 `.bc-pa-video` 幾何／`data-para` 不動。CSS：內層 `position:absolute;inset:0` 疊同框＋`opacity:0`、
  `.is-on{opacity:1;z-index:1}`、`transition:opacity .6s`（z-index 只給 `.is-on` ⇒ 繞回第 1 支不會被蓋）。
- JS：`setupVideos()` → `setupVideoCarousel()`：依 DOM 順序循環、距結束 **0.75s** 換片、**0.6s** 交叉淡入後
  才暫停舊支並歸零（沿用 `bc-sticky-mv.js` 參數）；播滿 1s 才預載下一支（3 支 2.2MB，不開場全抓）；
  下一支未 ready ⇒ 這輪不換並補載（buffer 被回收會重新 `load()`）；`timeupdate` 漏窗用「位置倒退」兜底；
  捲離視窗／分頁切背景全 pause。
- 版號：`index.html` CSS `?v=20261109g` → **`h`**、JS `?v=20261109b` → **`c`**。
- 驗證（8093 dev＋Playwright 1440／390）：3 支 `<video>`、永遠只有 1 支 `.is-on`；自然順序 `0→1`（5.82s 淡入、
  6.44s 淡完暫停）→ `1→2`（10.31s）→ `2→0` 繞回；seek 逼換片三次順序全對（淡入中兩支 opacity 同時 >0）；
  捲到 `y=3000` 三支全 `paused`、回頂部續播；三支 `filter=brightness(0.25)`；`overflowX=0`、console 0 error；
  `manage.py check` 0 issue。文件：`docs/home-photoarea.md` §四之二重寫（＋§一／§三／§五／§六第 3、9 條）、
  `.clinerules/project-core.md:49`、`04_SYSTEM_STATE.md` 11-09 ④。
