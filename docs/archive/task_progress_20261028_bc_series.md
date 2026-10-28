# 封存：/bean/<id>/ 咖啡豆 SERIES 括號滑桿（2026-10-28）

> 自 `task_progress.md` 移出（該檔超過 11.7K 預算）。內容＝模組自 about 搬到 bean 詳情頁、
> 箭頭方向修正、每組間隔加大（兩次）。現況摘要見 `task_progress.md`。

**`/bean/<id>/` 咖啡豆 SERIES 括號滑桿（2026-10-28，使用者指示：「about 的咖啡豆輪播整個模組移至咖啡豆詳情頁，位置在商品主區下方」）**：`about.html` 的 `<section class="bc-series-hero bc-series-bracket">`（BEANS 組，原 2026-08-27 加入）整組搬到 `bean.html`（約 253–312 行），插在 `.ftco-subpage-section.ftco-section-single-product`（商品主區）之後、`#cart-popup` 之前；`about.html` 只留上方咖啡 SERIES 滑桿（原地留 4 行說明註解）。連帶：`bean.html` extra_css 加 `bc-series.css?v=20260828q`、extra_scripts 加 `bc-series.js?v=20260824d`；`views.Bean` 補 `series_beans`（`BeanItem.objects.all().order_by("id")`，與原本 About 的 id 1,2,3,6,7,8 同 6 支）、`views.About` 移除 `series_beans`。迴圈變數改 `item`（避免覆蓋詳情頁的 `bean`）。實測 1440＝100vh（900）／slide 420／括號框 600、375＝365 高／6 張卡；標題模糊觸發正常、無水平溢出、console 0 error、`check` 0 issue。
**箭頭方向修正（同日追加）**：`bc-series.js` 原本把 `data-direction="left"` 對應 `--js-x -1`（內容左推＝其實是下一張），與模板的 `aria-label="Prev"` 語意相反 → 改成 **左＝上一張（`--js-x` 往 0 增加）／右＝下一張（往負值減少）**，拖曳方向不動；版號 `bc-series.js?v=20260824d → 20261028a`（`about.html:1361`、`bean.html:648` 同步）。Playwright 實測 bean：RIGHT → −420／−840（末張夾在 −2100）、LEFT → 回 0（首張夾在 0）、`data-blurred` 同步翻轉；about：RIGHT −420／LEFT 0；pager 幾何 1440（640／750）、375（108／218）＝Prev 確實在左，console 0 error（上述 x 值為間隔加大前；加大後步進見下段）。

**每組咖啡豆間隔加大（同日追加，使用者指示「bc-series 每組咖啡豆之間間隔加大」，之後再追加「再次稍微加大」）**：`bc-series.css` 三段落點 —— 桌機（≥1200）`.bc-series-slide:not(:last-child)` 寬 420 → 480 → **520**（照片 280 不變、間隔 140 → 200 → **240**）、平板（768–1199）300 → 320 → **340**（照片 200 不變、間隔 80 → 120 → **140**）、行動（<768）`margin-right` 48 → 60 → **70**（照片 32vw 不變）。
⚠️ 此模組的「間距」是做在 slide 的 `padding-right`（桌機／平板）與 `margin-right`（行動）上，**只加大 padding 會把照片壓小**（實測 280→220），必須同時把 `width` 一起加寬。
JS `stepSize()` 讀 `offsetWidth + marginRight`，故翻頁步進自動連動：桌機 480 → 520、平板 320 → 340、375＝180 → 190。版號 `bc-series.css?v=20260828q → 20261028a → 20261028b`（`about.html:10`、`bean.html:640`）。
實測（第二次加大後）：1920／1440 → slide 520／photo 280／gap 240／步進 520；1199／768 → 340／200／140（步進 340）；375 → photo 120／gap 70（步進 190）；首張與翻頁後照片居中偏移皆 0、`overflowX` 0、console 0 error。about 頁咖啡 SERIES 共用同一支 CSS ⇒ 間距同步變大（1440 驗證 gap 240／步進 520）。
