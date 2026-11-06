# 封存：navbar 天氣模組手機／平板位移修正（2026-11-05）

> 由 `task_progress.md` 抽出（該檔有 11.7K 預算）。只在追查天氣對齊細節時讀。

**navbar 天氣模組（`.weather -font_en -color_white`）手機／平板位移 — 2026-11-05 修復完成**

| 項目 | 內容 |
|---|---|
| 症狀 | about 頁 navbar 右上角天氣（溫度＋日期）在手機／平板與右側浮動列（購物袋／Order 長條）不成一直線 |
| 根因①（位置主因） | `bc-components.css:2975-2978` 在 ≤767.98px 把 `.ftco_navbar .container` 設為 `justify-content: initial`（原意是 logo 與漢堡水平對齊），但漢堡自 2026-09-21 起全站 `display:none`（`bc-attract.css:52-54`）→ 只剩 [logo][weather] 兩項，失去 space-between ⇒ weather 緊貼 logo 右緣（實測 390px：`x=166.9／right=204.9`） |
| 根因②（對齊基準錯） | v1 以「weather 右緣 ＝ Order 長條右緣」推 `translateX`（`-11／+3／+5px`）：平板因 weather 盒寬 67.4px 剛好等於軸線而看起來正確，但手機盒寬只有 38px，右緣齊平會讓**中心點**落在浮動購物車軸心右側 8px（≤767.98）／6px（≤575.98）→ 使用者複驗仍覺位移 |
| 修法（v2 定案） | `bc-weather.css`：位移改「中心點 ＝ 浮動購物車垂直軸心」，`translateX = 15px − var(--bc-weather-axis) + 50%`（50% ＝ 元素自身寬度一半 ⇒ 溫度位數、日期字串變長變短仍自動置中）；`--bc-weather-axis` 逐斷點 ＝ `--bc-fc-right` ＋ 22px（購物車 44px 點擊盒的一半）：≥992 `66`／768–991.98 `60`／≤767.98 `39`／≤575.98 `35`；≤767.98px 對 `.weather--visible` 保留 `margin-left:auto` 推回 container 右緣；`base.html` 版號 `?v=20261105a → ?v=20261105b` |
| 驗證 | `manage.py check` 0 issue；headless 實測「weather 中心距右緣 − 購物袋中心距右緣」＝ **0.00px**（1440／1024／991／768／767／576／575／390／360／320；購物袋軸心 66／66／60／60／39／39／35／35／35／35）；改前同值為 67.2／67.2／59.7／59.7／31.0／—／29.0／29.0／—／—（平板差 0.3px、手機差 8／6px）；`scrollWidth==clientWidth`（320）、console 0 error；首頁 navbar 那顆仍 `visibility:hidden`＋`margin-left:0`、hero 那顆 `transform:none`（皆未受影響） |
