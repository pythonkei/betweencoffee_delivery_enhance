# 首頁推薦雙卡（標題字體／大小）＋ 手機平板三項間距修正 — 2026-11-14 完成（本地驗證）

（封存自 `task_progress.md`；同日晚間又做了「手機 who 內文縮小＋左上 logo 貼左緣＋hero 影片 3→6 支」，
那筆仍留在 `task_progress.md` 的現況段。）

- 標題：HTML 仍 `Coffee` / `Beans`（無括號）→ CSS `text-transform:uppercase`＋Mogra 400＋`letter-spacing:-0.04167em`
  ⇒ 顯示 `COFFEE` / `BEANS`（字距等比例：@1440 -2.17px、@375 -1.02px）；font-size `#spacing` 28→**26**、56→**52**。
- 卡片間隙（使用者：手機／平板兩卡太擠）：<64rem 直向堆疊改 `--gap-stack: clamp(20px,24×spacing,36px)`
  ⇒ @375 **7.5→22.5px**、@768/820 **15.4→36px**；≥64rem 橫向 `--gap: max(12px,8×spacing)` ⇒ @1024 **5.7→12px**。
- yama 圓球右緣（使用者：太近）：`.tax-nav` `right` ≤768 **10→20px**、744–1199.98 **20→28px**（`.header-bot` 同步）；
  ORDER NOW 環墨跡右緣留白 **@320 9.4／@375 7.6／@768 8.2px**（原本 @375 只剩 0.25px、字被切）。
- `wwa-visual-03`（使用者：沒隨螢幕縮小）：`--who-visual03-w: 62px → clamp(48px,14vw,62px)`
  ⇒ @320 48、@375 52.5、@430 60.2、≥443 62px；gif 改「底緣定位」`bottom:-8.8px`（寬度縮小時底緣不浮動）；
  `bc-who.js` `getVar()` 改用隱藏探針解析 clamp（`parseFloat("clamp…")` 會 NaN），resize 清快取。
- 版號：`bc-recommended-pages.css`／`bc-who.css`／`bc-who.js` `?v=20261114b`、`bc-yama-header.css ?v=20261114a`
  （index.html:1012／1016／1035／1165）。
- 驗證（CDP headless @320/360/375/768/820/1024/1440，`/tmp/cdp_m3.py`、`/tmp/cdp_fix_shots.py`）：間隙
  20／22.5／36／12px、`docOverflowX=0`、0 exception；截圖 `_shot/bc-fix-{cards,who,yama}-*.jpeg`。
  已知（既有、非本次改動）：≤375 段落 `scrollWidth` 大於盒寬，body `overflow-x:clip` 會把超出的字形裁掉
  → 2026-11-14 晚間（who 內文改 clamp 縮小）已解。
