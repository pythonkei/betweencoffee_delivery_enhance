# 封存：浮動購物車圖示「10 種造型 × 線條／實心」（2026-11-09 完成並已 push）

> 2026-11-10 由 `task_progress.md` 移出（該檔超過 11.7K 上限）。內容逐字保留。

**浮動購物車圖示改為「10 種造型 × 線條／實心」可選（使用者指示）— 2026-11-09 完成並已 push**

- 指示：「修改 bc-floating-cart-btn 購物車圖標，提供 10 種選擇，線條及實心形狀」。
- **最終選定：`04 手提包（線條）`**（使用者 2026-11-09 從 20 個候選中挑出）：梯形包身＋短提把＋中央金屬扣；
  `base.html:190` 為三個 `<path class="bc-fc-line">`，上方註解同步「目前使用：04 手提包（線條）」。
- 為什麼用 inline SVG：原 `icon-shopping-bag` 是 icomoon 字型（單一造型，且首頁 2026-10-19 起不載 Material 字型）
  → SVG 才能同時提供線條／實心兩態、免字型、免 FOUT。
- `base.html:190` → `<svg class="bc-fc-icon" viewBox="0 0 24 24">`（**04 手提包（線條）**，見上方選定）；
  元素只分兩種 class：`.bc-fc-line`（`fill:none;stroke:currentColor`）／`.bc-fc-solid`（`fill:currentColor`）。
- `bc-components.css:1622` 新增 `svg.bc-fc-icon{width:1.05em;height:1.05em;transform:translateY(.1em)}`
  （墨跡 ≈0.79em ＝原字形象大小；下移 0.1em 讓數字圓點不壓袋口）。
- badge 定位 `top/right:-4px` → `0/0` ＋ `translate(35%,-35%)`（`.bc-floating-cart-badge` 為浮動鈕專屬）：
  SVG 墨跡滿版、無字形留白，舊值 22px 圓點會蓋掉提把；新值外溢 3.3px（< 原 4px）⇒ 與 `.bc-attract-buy`
  軸心對齊、浮動鈕定位（量 `--bc-fc-size`＋44px 盒）完全不變。
- 10 種造型：購物袋／紙袋／帆布袋／手提包／提籃／購物推車／外帶咖啡杯／紙箱／禮物盒／店面；
  預覽頁 `static/preview/bc-floating-cart-icons-v2.html`（載入正式 CSS、37/34/31 三尺寸、可試 hover 金色）。
- 版號：`bc-components.css` → **`20261109a`**、`bc-slideout-cart.js` → **`20261109a`**（字型預載段加註：SVG 會自動跳過）。
- 驗證（dev 8081＋Playwright）：首頁／`/cart/`／`/about/` 皆 `svg.bc-fc-icon` 38.8px＝37×1.05、hover
  `rgb(196,155,99)`、圖示不被 badge 遮；390×844 `--bc-fc-size:31px`／SVG 32.5px／badge 右緣距視窗 5.3px／
  `overflowX=0`；預覽頁 10 卡 × 6 SVG 全渲染、console 0 error（僅預覽頁 favicon 404）；`manage.py check` 0 issue。
- 文件：新預覽頁 v2；舊 `bc-floating-cart-icons.html` 加「已由 v2 取代」提示；
  `docs/verify/cdp_verify_floating_cart.py` selector 支援 `svg.bc-fc-icon`（並修 SVG 的 `className` 序列化）。
- 預覽頁 v2 二次強化（`b08292ea`）：① 新增「放大對照 96px」區（20 格，仍走正式 `.bc-floating-cart-btn`
  結構、只放大 `--bc-fc-size`，不在預覽頁重刻樣式）；② 實心態 02/05/07/08/09 改 `fill-rule="evenodd"` 真鏤空
  （折口線＋打孔、垂直格線、杯蓋分界＋杯套、紙箱頂面 V＋中線、緞帶），10 店面移除硬寫 `fill="#0e0e0e"`
  黑門改挖洞；③ 04 卡片標「★ 使用中」。
- 換成 04 後重驗（dev 8081＋Playwright，1440×900）：`/`、`/cart/`、`/about/`、`/coffee/4/`、`/bean/1/`、
  `/coffee_menu/` 六頁皆 `svg.bc-fc-icon` 38.8px（37×1.05）、3 個 path、`button` 44×44 且 x=1352／y=48
  （`/about/` y=118 因 navbar 較高，與其他頁基準一致）；hover `rgb(196,155,99)`；墨跡 27.9×25.6px、
  badge 22px 與墨跡僅邊角接觸（視覺無遮擋）；390×844 SVG 32.5px、`overflowX=0`、badge 右緣距視窗 5.3px；
  console 0 error。

