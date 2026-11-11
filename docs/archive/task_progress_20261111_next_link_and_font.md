# 2026-11-11 完成紀錄（封存）

> 由 `task_progress.md` 移出（該檔超標，只留現況與未完成項）。內容為當日各任務的完整紀錄，只在追查細節時 grep。

## 咖啡詳情頁頁尾新增「前往咖啡豆選單」next-link 面板（移植 daisheng `.c-footer__section`）— 2026-11-11 完成

- 指示：把 https://daisheng.com.tw/business/ 的 `.c-footer__section` **互動效果**移植到 `/coffee/<id>/`，面板連到 `/bean_menu/`。
- 新增 `static/css/bc-next-link.css`（`?v=20261111f`，當日 e→f：`( NEXT )` 字型／字級）、`static/js/bc-next-link.js`（`?v=20261111d`）、
  `partials/bc_next_link.html`；`coffee.html` 覆寫 **`bcc_footer`**（`block.super` 之後 include）→ 面板接在 `</footer>` 之後，
  extra_css／extra_scripts 各加一行。（原站 `.c-footer__section` 是 `.l-footer__body` 最後一個子元素、在版權列之下
  ⇒ 面板＝整份文件最底；2026-11-11 修正，原本誤放在 footer 之前。）
- 4 互動：① 進場 opacity 0→1／scale 1.3→1（IO 加 `.is-active`；**每次捲回面板都重播**：完全離開視口時以 `transition:none` 歸位後移除 class）② hover `scale(1.1)`
  ③ 背景視差（媒體高 160%／top -30%，rAF 寫 `--bc-nl-y` `-14%→0%`，不露黑邊）④ `( NEXT )` 無限上捲（純 CSS）。
- 尺寸 37.5vw（手機 72vw，上下限 280/540、260/460）；文案 `( NEXT )`／`咖啡豆`／`COFFEE BEANS`；
  背景**照片** `static/images/bean_menu.jpg`（1920×1280、`loading="lazy"`＋`object-fit:cover`；2026-11-11 使用者指示取代 `bean_bg.webm`，影片邏輯已從 JS 移除）。
- 雷：Django **`{# #}` 不可跨行、內文不可再出現 `{#`／`#}`** → 一律用 `{% comment %}`（曾造成 500 遞迴／文字外漏）；
  `runserver --noreload` 會快取舊模板，改檔後須重啟。
- 驗證（8081，1440／390）：順序 `footer.ftco-footer` → `section.bc-next-link`、間距 0、面板下緣＝文件底、
  進場 opacity 1／stage 540（390：281）、**捲離→捲回連續 3 次都重播**（中途量到 scale 1.22／opacity 0.26）、
  照片 1920×1280 已載入（img 高＝stage×1.6）、hover 1.1、視差 −10.89%／0.00%、`overflowX=0`、
  reduced-motion 直接 opacity 1／transform none、console 0 error、`manage.py check` 0 issue。
  截圖 `_shot/nextlink_after_footer_{1440,390}.png`、`_shot/nextlink_photo_{1280,390}.png`。
- 同日追加（使用者指示）：`( Next )` → **`( NEXT )`**、字級 `.9375rem`→`clamp(1.25rem, .95rem + 1vw, 1.75rem)`、
  字型改 **Akzidenz Grotesk Pro**（品牌舞台「Follow Your Rhythm」同一支；`--bc-font-akzidenz` 定義在
  `static/css/bc-fonts.css`，因為 `/coffee/<id>/` 沒載 `bc-brand-stage.css`）。

## 左上 logo 字級 +6px→再 +2px、浮動購物車數量文字 +1px→再 +1px — 2026-11-11 完成

- 指示：① `bc-attract-buy` 數量文字加大 1px（後再 +1px）；② `.bc-navbar-brand-fixed` 的 `｛ Between ｝` 加大 6px（後再 +2px）。
- 做法（都在 `bc-components.css`）：
  - `.bc-floating-cart-badge`（浮動購物車袋內數量＝長條 ORDER 正上方那組）`font-size` 0.79→0.85→**0.91rem**（12.64→**14.56px**，累計 +1.92px）；
    定位 `translate(-50%,-50%-6px)` 不動 ⇒ 仍對齊袋子中心、上提 6px。
  - `.bc-navbar-brand-fixed` 全斷點字級（+6px 再 +2px）：40→**48**／34→**42**（≤991.98）／28→**36**（≤767.98）／26→**34**（≤575.98）；top／left 不動。
  - 版號：`bc-components.css` `20261111d`→`20261111e`→**`20261111f`**（`base.html:46` 含註解紀錄）。
- 驗證（CDP 1920/1440/1200/1000/800/700/500/380）：logo 48/48/48/48/42/36/34/34px、badge 14.56px（移動端隨 root 等比略小＝既有機制）、
  badge 對袋子 dx 0／dy −6、logo 與 navbar **0 重疊**、各寬度 `overflowX=0`、console 0 error、`manage.py check` 0 issue。commit `fe17a2d0`＋`5896aa96`。

## 首頁 who 模組：素材換裝（svg／gif）＋整組放大 ×1.3 — 2026-11-11 完成

- ① 素材：`wwa.mp4`→`wwa-03.gif`、`wwa-01.png`→`wwa-01.svg`；`index.html` video→img、`bc-who.css` 選擇器改 `img`、
  `bc-who.js` gif 走 `type:"img"` scale scrub。commit `702570e3`。
- ② 放大：`bc-who.css` 全部長度值 **×1.3**（section 外距 96/80 不動；對照表在該檔檔頭）、`--label-width:150px`；
  版號 `20261111b`。commit `a49fd5a9`。驗證 1440／390／1920 全 ≈×1.3、label 未截字、`overflowX=0`。
- ③ 同日追加（使用者指示）：`.section-title__text` 字型 Josefin Sans → **Akzidenz Grotesk Pro**
  （`var(--bc-font-akzidenz)`）；字級／字距／字重不動。版號 `20261111c`。同次提交 index.html 的文案
  `Set Your Rhythm`→`Hmm....Coffee is always better hot not matter`、kicker `About Between`→`Between Say:`。
- ⚠ `index.html` 仍有使用者 WIP（hero webm）⇒ 只 stage 我方 hunk；live 仍 `c3f7509c` ⇒ 待手動 Deploy。

## 右側整組微調：購物車↔ORDER −2px、ORDER↔個人圓鈕 +6px、長條文字改 `ORDER` — 2026-11-11 完成

- `bc-components.css` `--bc-fc-gap` 20→**18px**（≤767.98px 12→10）、各斷點 `--bc-fc-top` 同步 −2px；
  `bc-attract.css` `--bc-buy-profile-gap` 8→**14px**；`nav.html:140` `Order`→`ORDER`。
- 量測基準：可見長條／圓鈕是 `.bc-attract-buy__link`／`.bc-attract-profile__link`（外盒含 `margin:-24px` 位移層，會多算）。
- 版號 `bc-components.css 20261111d`／`bc-attract.css`＋`bc-attract-place.js 20261111a`；`cdp_verify_floating_cart.py` 5 斷點×5 頁全通過。

## 浮動購物車圖示改用 `onlineshop-cart.svg`（縮小 30%），數量＝無圓圈白字、上移 6px — 2026-11-11 完成

- **外部 SVG ＋ CSS mask**（`base.html:196` 空 `<span class="bc-fc-icon">`；`bc-components.css` 以
  `background-color:currentColor` ＋ `mask-image` 取檔）⇒ 檔案即唯一來源、hover 轉金照舊；
  尺寸 0.735em×1.225em 吃 `--bc-fc-size`、`margin-inline` 讓佔位恆為 44×44（JS 不動）。
- 數量：無底色／無圓角／`#fff`、`dy=-6`（袋型視覺重心高於幾何中心）。回退：保留 `svg.bc-fc-icon` 可回 11-09 inline SVG。
- `static/images/onlineshop-cart.svg` 須與 `base.html`／`bc-components.css` 同 commit，否則正式站缺圖（已於 11-11 一併提交）。
