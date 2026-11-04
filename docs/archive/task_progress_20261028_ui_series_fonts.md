# 2026-10-27 ~ 10-28 UI／字型調整（封存檔）

> 2026-10-30 自 `task_progress.md` 移出（該檔超過 11.7K 上限，只留現況摘要）。
> 內容：首頁 sukima capabilities 搬家＋放大置中、`/bean/<id>/` `.bc-staff` 字級、
> 全站 `trade-gothic` 英文字型、咖啡豆詳情頁 SERIES 標題兩行與行距／字級調整。
> 需要細節時 grep 本檔即可，不要整份讀。

**首頁 sukima capabilities（`[2c]`，2026-10-27 自 about 移入＋加大置中）**：`bc-capabilities.css?v=20261027a`／`bc-capabilities.js?v=20260825k`（原生 scroll＋rAF）。單一變數 `--cap-scale`：1（<834）／1.30（≥834）／1.40（≥1280）／1.60（≥1920），`max-width`·`gap`·`padding`·閃電 SVG 全部 `calc(基準 × var)`；gallery `align-self:center` 置中。實測寬度 1920＝970、1440／1280＝848、1024／834＝788、768＝606、375＝375，左右對稱、無水平溢出、動畫參數未動。

**`/bean/<id>/` `.bc-staff` 文字放大（2026-10-28，使用者指示）**：`bc-components.css`（約 2719–2840 行）。`title-sub` 13→17px、姓名（`h3 strong`）13→16px、內文 14→16px（行高 1.7→1.75）；行動端（≤575.98）15／14／14px（行高 1.7）。容器 483px、頭像 96／64px、虛線與內距皆未動。版號 `bc-components.css?v=20261019a → 20261028a`（`base.html:39`）。實測 1280／900／768／600／576／414／375：字級如上、姓名不裁切、無水平溢出、console 0 error、`check` 0 issue。

**全站英文字型 family「trade-gothic」（同日追加，使用者指示「新增一個英文 web font family 'trade-gothic' 供 global 使用，bc-series-heading 改用此字體」）**：

- 新增 `static/fonts/trade-gothic/`（自架）：`LeagueGothic-latin.woff2`（10.4K）、`LeagueGothic-latin-ext.woff2`（6.8K）、`OFL.txt`、`SOURCE.txt`（來源／授權說明）。

- 新增 `static/css/bc-fonts.css`（`?v=20261028a`，`base.html:19-21` 全站載入，僅 2 個 `@font-face` ＋ `:root` 變數）：family 名 **`trade-gothic`**，`font-weight: 100 900`（單一字重 400，宣告範圍避免瀏覽器合成 fake bold）、`font-display: swap`、latin／latin-ext 兩個 `unicode-range`；`:root { --bc-font-trade-gothic: "trade-gothic", "Arial Narrow", "Helvetica Neue", "Noto Sans TC", sans-serif }`。

- 為何不是真的 Trade Gothic：Trade Gothic 是 Monotype 商業字型、Google Fonts 沒有（已實測 fonts.google.com metadata 1951 個 family 內無此字型）；依使用者選擇改用 **League Gothic（SIL OFL 1.1，可自架可商用）**，CSS family 名仍沿用 `trade-gothic`，日後換授權檔只需換 `src`。

- 套用：`bc-series.css` 的 `.bc-series-heading` 改 `font-family: var(--bc-font-trade-gothic)`、`font-weight: 400`、`letter-spacing: -0.02em → -0.01em`；`.bc-series-heading-sub`（中文副標／綠色手繪圈）維持 `"Noto Sans TC"` 不受影響。版號 `bc-series.css?v=20261028b → 20261028c`。

- 實測（8099）：字型檔 200、`document.fonts.check` 通過；1440 標題盒 558×229 → **323×229**（about SERIES 552×201 → 334×201，140px 未動）、1024＝151×137、375＝375×84；副標字型仍 Noto Sans TC、`overflowX` 0、console 0 error（無關的 `row-animation.mp4` 404 為既有問題）；首頁等其他頁面只載 CSS、不載字型檔（未使用就不下載）。

**咖啡豆詳情頁滑桿標題改兩行＋縮小（同日追加，使用者指示「bc-series-heading 文字縮小／改兩行 Recommend・Roastery」）**：`bean.html:262-264` —— section 加 `bc-series-beans`（原本與 `about.html` 的 SERIES 共用 `.bc-series-hero.bc-series-bracket`，無法用既有 class 區分），標題文字 `BEANS`／`Roasted` → `Recommend<br />Roastery`。`bc-series.css` 檔尾新增 `.bc-series-beans .bc-series-heading` 覆寫：行動 26px（原 30）／平板 ≥768 40px（原 52）／桌面 ≥1200 80px（原 140，`line-height:1.05` 讓兩行更緊湊）；about 的 SERIES 維持 140px 不受影響。實測字級 80／40／26px、標題盒 558×229（1440）右緣 558 未壓到首張照片（左緣 580）、375 兩行 84 高不溢出、console 0 error、`check` 0 issue。

**標題行距縮小＋字級加大（同日追加，使用者指示「更改 .bc-series-heading，1 行距縮小、2 文字加大」）**：`bc-series.css` 四段落點同步調整 —— 基礎 `.bc-series-heading` `line-height 1.2 → 0.95`、`font-size 50 → 60px`；平板（768–1199）`52 → 62px`＋`line-height: 0.95`；行動（≤767.98）`30 → 36px`＋`line-height: 0.95`；桌面（≥1200）`140 → 160px`＋`line-height: 1 → 0.9`；bean 覆寫 `26/40/80 → 32/48/96px`（`line-height` 0.9／0.9／0.85）。因 `line-height < 1` 讓字母下伸部（y/g）溢出該行 box，`.bc-series-heading-sub` 間距一併放大 `14 → 52px`（桌機）、平板 `36px`、行動 `8 → 22px`，bean 桌機另覆寫 `44px`（字級較小）→ 綠色手繪圈（`.hero-title-svg` inset -24px）與字母間留 4–5px 不再壓字。版號 `bc-series.css?v=20261028c → 20261028d`（`about.html:10`、`bean.html:640`）。Playwright 實測 1440／1199／768／375 兩頁：字級 160/62/62/36（about）、96/48/48/32（bean）、圈與字母間距 +4～+5px、`overflowX 0`、console 0 error、`check` 0 issue。
