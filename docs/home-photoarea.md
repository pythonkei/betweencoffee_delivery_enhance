# 首頁 hero 背景照片視差（`.bc-photoarea`）

> 2026-11-07 建立。移植 **hicard.studio** 首頁的 `.fv__photoarea` ＋ GSAP「Sticky1」位移。
> 改這塊前必讀；檔案只有 3 個：`static/css/bc-photoarea.css`、`static/js/bc-photoarea.js`、
> markup 在 `templates/betweencoffee_delivery/partials/bc_brand_stage_hero.html`（`#bc-brand-stage` 第一個子節點）。
> 另外落點洗牌在 view：`betweencoffee_delivery/views.py` 的 `_photoarea_slots()`（見 §四之四）。

## 一、效果是什麼

首頁第一屏（品牌舞台 hero：時鐘 `{ 21 : 59 }` ＋環形咖啡照 ＋大字）的**背後**鋪 5 格
（4 張照片 ＋ 第 3 格是**影片輪播**，內含 3 支依序播放，見 §四之二），
往下捲時這 5 格比內容更快往上飄（多層視差），彼此錯位、依序離開畫面。
每格都壓了一層 **75% 黑蒙版**（2026-11-09 起，見 §四之三）⇒ 照片退成氛圍，不搶前面時鐘／環形照／大字。
**每次重新整理，5 格的落點都會重排**（2026-11-09 起，比照原站；見 §四之四）。

兩層位移（相加，皆 `scrub`、皆 `ease:'none'`）：

| 層 | 元素 | 位移量 | 來源 |
|---|---|---|---|
| 容器 | `.bc-photoarea` | `data-pa-shift`（vh，預設 `-10`）× factor | 原站 Sticky1 的容器位移 |
| 單張 | 每個 `[data-para]` 元素（4 個 `<img>` ＋ 1 個影片容器 `.bc-pa-video`） | `data-para`（vh，`-8 / -13 / -18 / -23 / -28`） | 原站 `data-para="-100…-500"` 等比換算 |

> 第 5 個 `[data-para]` 是影片容器（內含 3 支依序輪播的 `<video>`，見 §四之二）；位移／視差
> 一律掛在**外層容器**，內層影片只做 `object-fit:cover`。

- ScrollTrigger 兩層都是 `trigger:#bc-brand-stage`、`start:'top top'`、`end:'bottom top'`、
  `scrub:1`、`invalidateOnRefresh:true`（`vh` 用 `window.innerHeight` 現算 ⇒ 換視窗高度會重算）。
- **factor**：`innerWidth ≤ 768 → 0.5`，其餘 `1`（沿用原站「手機位移減半」）。
- 實測（1600×1000，hero 高 1332）：滾到 1300px 時容器 `-97.6px`、5 張分別
  `-78.1 / -126.9 / -175.7 / -224.5 / -273.2`（＝值 × 100vh/100 × 進度 0.976，逐值吻合）。

## 二、圖層與版面

```css
.bc-photoarea{position:absolute;inset:0;z-index:-1;overflow:hidden;pointer-events:none}
.bc-brand-stage-hero #bc-brand-stage{isolation:isolate}   /* 讓負層留在 stage 內 */
```
- `#bc-brand-stage` 本身已是 `position:relative;overflow:hidden`，所以**不需要**動 hero 高度、
  也不會多出可捲動空間（原站是 `height:120vh` ＋ `margin-bottom:-120vh`，本地直接吃 stage 的高度）。
- 首頁 hero 的 `#bc-brand-stage` 與 `.bc-stage-content`（原 `.footer`，2026-11-10 改名）底色已是 `transparent`
  （`bc-brand-stage.css` 檔尾「首頁專用覆寫」段）⇒ 照片直接透出，不必處理遮蓋。
- `pointer-events:none` ⇒ 環形照 hover 徽章／拖曳／連結、時鐘、nav 全不受影響
  （驗收方式：`document.elementFromPoint()` 取環形照與時鐘中心，`closest('.bc-photoarea')` 必為 null）。

## 三、素材（本站自存，2026-11-09 起）

- 位置：`static/images/photoarea/pa-1.webp` ~ `pa-5.webp`（`pa-n` 對應 DOM 的 `d_n`），皆 `768×1075`。
- **`pa-3.webp` 已不使用**：2026-11-09 15:27 使用者把它改名為 `pa-3__.webp`（只當備份，不參與畫面），
  第 3 格改由影片輪播填滿（3 支依序，見 §四之二）。`<video>` **沒有** `poster` ⇒ 影片未播／
  不允許播時該格是空的（露出後面的深色底），好處是不會多一支 404 請求；缺點是 reduced-motion
  使用者看不到靜態畫面。
- 由來：原站 hicard.studio 的 5 支 `768×1075` jpg（合計 758KB），2026-11-09 下載後
  以 Pillow 轉 `webp q=82, method=6`（不帶 metadata）→ 合計 **524KB（省 31%）**，jpg 原檔已刪、
  不留重複素材。原始 URL（要重新下載時用）：

  | 檔名 | 來源 URL（前綴 `https://hicard-wp.prm-test.com/wp-content/uploads/2025/03/`） |
  |---|---|
  | `pa-1.webp` | `f894401c86664c5c3629ae5d0bcaf257-768x1075.jpg` |
  | `pa-2.webp` | `986e5d2b8018444b24321cea495a72ec-768x1075.jpg` |
  | `pa-3.webp` | `614848684b1b78d0e9e551e56aa73070-768x1075.jpg` |
  | `pa-4.webp` | `967eaf9ebd251e683f6775c8005bc05f-768x1075.jpg` |
  | `pa-5.webp` | `79918f724b505be173f2877b1aa06644-768x1075.jpg` |

- 版號：改圖＝**直接覆蓋同名檔**＋升模板上的 `?v=YYYYMMDDx`（目前 `20261109b`，2026-11-09 15:27 換圖那批升的）。
- **目前實際尺寸（2026-11-09 換圖後實測）**：全部是 768×1075 比例（0.7143）的直式，只有解析度混用：

  | 檔名 | 尺寸 | 大小 | 格位 |
  |---|---|---|---|
  | `pa-1.webp` | 768×1075 | 79 KB | `.x_4 .y_2 .d_1` |
  | `pa-2.webp` | **640×896** | 93 KB | `.x_2 .y_3 .d_2` |
  | `pa-3__.webp` | 768×1075 | 92 KB | （不使用・備份） |
  | `pa-4.webp` | **767×1074** | **448 KB** | `.x_1 .y_4 .d_4` |
  | `pa-5.webp` | 768×1075 | 100 KB | `.x_5 .y_1 .d_5` |

  比例完全相同 ⇒ 5 格節奏一致，不會有「某格特別胖／瘦」的問題；模板的 `width/height` 已同步成各檔實際值
  （`pa-2` 改 640×896、`pa-4` 改 767×1074），載入前的預留盒比例也對得上。
  兩個小瑕疵（不影響版面）：`pa-2` 解析度較低，桌面上會被放大約 1.2×（近看略軟）；
  `pa-4` 448KB 偏大（同尺寸 q82 應在 100KB 上下 ⇒ 值得重壓）。
- `width/height="768" "1075"` 寫死：照片絕對定位不撐版面，但先宣告尺寸可避免解碼跳動。
- 檔案不存在／404 時：圖層是空的海綿層，版面不會壞、背景回到純黑（不會出現破圖框）。

## 四、落點與尺寸（CSS 逐值對照原站）

- 照片寬：`min(33.3vw, 560px)`（原站 `480rem`／上限 576px）；`≤768px` → `min(41.6vw, 300px)`。
- 寬版那張（原站 `.yoko`，本專案給第 3 張）：寬 ×1.35（上限 760px）＋ `aspect-ratio:3/2; object-fit:cover`；
  `≤768px` 回到與其他張同寬。
- 落點：`.x_1 left:0`／`.x_2 left:10%`／`.x_3 right:10%`／`.x_4 right:0`／`.x_5 left:20%`；
  `.y_1 top:0`／`.y_2 top:20%`／`.y_3 bottom:20%`／`.y_4 bottom:0`／`.y_5 bottom:30%`。
  `≤768px` 改成一路往下排：`top 0 / 10% / 30% / 60% / 85%`（`y_3`、`y_4` 需 `bottom:auto`）。
  上表只是「座標 → 位置」的定義；**哪一格拿到哪個 x/y 每次載入都不同**（§四之四）。
- `.d_1~.d_5` → `z-index 1~5`（重疊時號碼大的在上；不依賴 DOM 順序）。

### 四之二、第 3 格＝可輪播的影片容器（2026-11-09 使用者指示）

第 3 格（`.yoko .d_3` ＋洗牌得來的 `.x_n／.y_n`）由 `<img>` 改成「容器＋多支影片」：

```html
<div class="x_{{ pa_slots.2.x|default:3 }} y_{{ pa_slots.2.y|default:5 }} d_3 yoko bc-pa-video" data-para="-18">
  {% for pa_video in pa_videos %}
  <video class="bc-pa-video__el{% if forloop.first %} is-on{% endif %}" muted loop playsinline preload="none" tabindex="-1">
    <source src="{{ pa_video }}" type="video/webm">
  </video>
  {% endfor %}
</div>
```

- **片單＝單一來源**：`betweencoffee_delivery/views.py` 的 `PA_VIDEOS`，**依序播放、不洗牌**：
  ① `media/hero_00.webm`（原本那一支）② `media/hero_04.webm` ③ `media/hero_05.webm`
  ④ `media/hero_03.webm` ⑤ `media/hero_02.webm` ⑥ `media/hero_06.webm`（2026-11-14 追加後 3 支）。
  `Index.get` 把它轉成 `context["pa_videos"]` 給模板 ⇒ **加片／減片／換順序只改 `PA_VIDEOS`**，
  模板、CSS、JS 都不用動。
- **堆疊與交叉淡入**：多支影片全部 `position:absolute; inset:0` 疊在同一個框（`object-fit:cover`），
  預設 `opacity:0`；只有帶 `.is-on` 的那支 `opacity:1` ＋ `z-index:1`。換片＝下一支加 `.is-on`
  疊上來（`transition:opacity .6s` 交叉淡入），淡完 JS 才把舊支的 `.is-on` 拿掉並暫停歸零。
  `z-index` 只給 `.is-on`（不是靠 DOM 順序）⇒ 輪播繞回第 1 支時也一定壓在最上層。
- **幾何沿用**：外層 `.bc-pa-video` 吃 `.bc-photoarea img` 同一組規則（`position:absolute`、
  `width:min(33.3vw,560px)`、`.yoko` 的 ×1.35（上限 760px）＋ `aspect-ratio:3/2`），只多補
  `overflow:hidden`；內層 `video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}`
  ⇒ 換素材不必改任何尺寸。
- **位移掛外層**：JS 抓 `[data-para]`（img 與容器一視同仁），影片自己不掛 transform。
- **播放／換片規則**（`setupVideoCarousel()`，刻意與 GSAP 解耦；換片參數沿用 `bc-sticky-mv.js`）：

  | 情況 | 行為 |
  |---|---|
  | 照片區在視窗內 | 播當前那一支（`preload="none"` ⇒ 進畫面才抓檔） |
  | 當前支播滿 1 秒 | 預載下一支（`preload="auto"` ＋ `load()`）——不在開場一次抓完（6 支合計約 3.9MB） |
  | 距當前支結束 **0.75s** | 換片：下一支加 `.is-on` 淡入 **0.6s** → 淡完暫停舊支並歸零 |
  | 下一支還沒 ready | 這輪先不換（當前支有 `loop`，畫面不會凍住）並補載；buffer 被瀏覽器回收過就重新 `load()` |
  | `timeupdate` 漏掉換片窗口（掉幀／seek） | 兜底：播放位置明顯倒退＝`loop` 已繞回開頭 ⇒ 立刻換片，不會同一支多播一輪 |
  | 捲離視窗／分頁切到背景 | `pause()`（不讓滾過去的 hero 繼續解碼／吃電）；回來從原位置續播 |
  | `prefers-reduced-motion:reduce` | 不播、`readyState 0`（連檔案都不抓）⇒ 該格空白（無 `poster`，見 §三） |
  | `play()` 被瀏覽器拒絕（iOS 省電／低電量） | 靜默失敗，該格空白，不報錯 |
  | 片單只有 1 支 | 等同舊行為：`loop` 自己循環，不進換片流程 |
  | 沒有 `IntersectionObserver` | 直接播 |

- **實測（1440×900、`?v=20261109c`）**：`0 → 1` 在 5.82s 交叉淡入、6.44s 淡完暫停舊支；
  `1 → 2` 10.31s；`2 → 0` 繞回正常（淡入那支 `z-index:1`）。捲到 `y=3000` 三支全 `paused`、
  回頂部續播；console 0 error。
- **素材（實測尺寸）**：`hero_00.webm` 1280×720／5.97s／762KB、`hero_04.webm` **1080×718**／5.0s／718KB、
  `hero_05.webm` 1280×720／5.0s／705KB —— 都是 `/about/` 首屏 sticky MV 用的同一批檔案。
  2026-11-14 追加的三支同樣取自該批：`hero_03.webm` 905KB、`hero_02.webm` 548KB、`hero_06.webm` 438KB
  （清單 6 支合計約 3.9MB，但 `preload="none"`＋逐支預載 ⇒ 首屏只抓 1～2 支）。
  本格位是 3:2＋`cover` ⇒ 16:9 的片會左右各裁約 8%，`hero_04`（1.50）幾乎不裁。
- **快取**：URL 由 `views._mv_versioned_static()` 自動加 `?v=<檔案 mtime>`（與 about 頁同一套）
  ⇒ **換同名檔直接覆蓋即可**，不必手動升 `?v=`（圖片那 4 格仍要手動升）。

### 四之三、每格黑蒙版 75%（2026-11-09 使用者指示，同日演進 40% → 50% → 60% → 70% → 75%）

```css
.bc-photoarea { --pa-dim: 0.25; }                    /* .25 ＝ 疊 black 75% */
.bc-photoarea img,
.bc-photoarea .bc-pa-video > video { filter: brightness(var(--pa-dim)); }
```

- **為什麼不是「遮罩層」**：`<img>` 是 replaced element，`::before`／`::after` 不會渲染 ⇒ 真遮罩層
  得為每一格加 wrapper（改 markup ＋全部幾何選擇器）。而 `rgba(0,0,0,.75)` 疊在圖上的結果是
  `C×.25 ＋ 0×.75 ＝ .25C`，`brightness(.25)` 同樣是逐通道乘 `.25` ⇒ **畫面完全等價**，一行 CSS 就够。
- **涵蓋範圍**：4 張 `<img>` ＋ 第 3 格的 `<video>`（影片會裁切、縮放顯示 ⇒ 影格同樣被壓暗；
  不會「先亮後暗」閃一下）。**不含** body 背景圖、也不含 stage 上的內容（時鐘／環形照／大字仍全亮）。
- **調濃淡**：只改 `--pa-dim`。`.25`＝75% 黑（現值）、`.3`＝70% 黑、`.4`＝60% 黑、`.5`＝50% 黑、
  `.6`＝40% 黑、`1`＝不壓暗；
  手機斷點共用同一個值（要分開就寫在 `≤768px` 的 `.bc-photoarea` 區塊）。
- **之後若要在蒙版「上」再疊東西**（漸層、文字、hover 提亮）：改 wrapper 結構
  `<div class="x_1 y_4 d_4 …" data-para="-23"><img …><span class="bc-pa-mask"></span></div>`，
  幾何 class／`data-para` 留在 wrapper、`img{width:100%;height:auto}`、`.bc-pa-mask{position:absolute;inset:0;background:rgba(0,0,0,.75)}`。
- **效能（2026-11-09 實測，headless Chromium 軟體渲染、1440×900、一邊捲動一邊播影片；
  當時 `--pa-dim:.6`，純乘算 filter 的成本與乘數無關）**：
  有蒙版 69.8ms/幀（14.3fps）vs 無蒙版 57.3ms/幀（17.5fps）⇒ 約 **+20% 每幀時間**。
  這是**沒有 GPU**的最壞情況；實機 filter 走合成層、成本遠低於此。若日後在真機上仍覺得捲動變鈍，
  可改成「單一覆蓋層」省掉 5 個 filter：`.bc-photoarea::after{content:'';position:absolute;inset:0;z-index:6;background:rgba(0,0,0,.7)}`
  —— 差別是重疊處只壓一次（每格各自壓 ⇒ 重疊處會壓兩次、更暗），視覺取捨自行決定。

### 四之四、每次載入重排落點（2026-11-09 使用者指示）

原站（hicard.studio/ja）每次請求都由**伺服器**重新分配每張照片的 `.x_n`／`.y_n`：照片本體、
`data-para`、`.d_n` 固定不動，只有「擺在哪個落點」每次不同 ⇒ 重新整理就換一種構圖。
本專案照同一個做法，在 **view 端**洗牌（不是丟給 JS）：

```python
# betweencoffee_delivery/views.py
PHOTOAREA_TILES = 5

def _photoarea_slots(count=PHOTOAREA_TILES):
    xs = random.sample(range(1, count + 1), count)   # x 自己排一次
    ys = random.sample(range(1, count + 1), count)   # y 自己排一次
    return [{"x": x, "y": y} for x, y in zip(xs, ys)]

class Index(View):
    def get(self, request, *args, **kwargs):
        context["pa_slots"] = _photoarea_slots()     # 只有首頁要
```

模板（`partials/bc_brand_stage_hero.html`）逐格寫 `x_{{ pa_slots.N.x|default:<原值> }}`，
`N` = 0–4 依序對應 `.d_1`～`.d_5`。

- **為什麼在 server 做**：HTML 送到瀏覽器時落點已經是隨機值 ⇒ 不會出現「先排在原位、載入後才跳位」
  的閃動；關掉 JS／GSAP 掛掉／`prefers-reduced-motion` 時也一樣有效（原站本身也是 SSR 端洗牌）。
- **x 與 y 各自獨立排列**（比照原站實測結果）：同一次載入不會有兩張撞同一個 x 或同一個 y，
  但 x 與 y 之間沒有固定配對 ⇒ 組合數 `5! × 5! = 14,400`。
- **固定不動的**：照片檔（`pa-1~5`／影片）、`data-para`（視差量）、`.d_n`（層序）、
  `.yoko`（只有影片那格是寬版，不能跟著洗牌——來源是 16:9）。
- **`|default:` 是保險**：別的模板 include 本檔卻沒給 `pa_slots` 時，會退回原本的固定落點
  （`x_4 y_2` / `x_2 y_3` / `x_3 y_5` / `x_1 y_4` / `x_5 y_1`），不會 5 張疊在左上角。
- **不用升 `?v=`**：這個改動只碰 view ＋ 模板，沒有動任何 `static/**`。
- **要固定落點**：把 `context["pa_slots"]` 那行拿掉（自動走 fallback），或改 `_photoarea_slots()`
  回傳固定清單。

### 四之五、階梯式圖片揭露（2026-11-14 使用者指示：逐值移殖 global-tree.jp `.layeredImage`）

來源＝global-tree.jp 首頁 `.layeredImage | -home-mv`。數值直接取自該站 build 檔
（`build/index-wua8aVMQ.css` 與 `build/index-CEEWSRgo.js` 的 Alpine 元件 `layeredImage`），不是憑截圖推的：

```html
<div class="layeredImage -home-mv" x-data="layeredImage({ debug:false, useIntersectionObserver:false })">
  <div class="layeredImage__image-wrapper | overflow-hidden flex shrink-0">
    <div class="layeredImage__image -index-1 [--w-mobile:31] [--w-desktop:49] w-[calc(var(--w-desktop)/1440*100vw)]">
      <img class="w-full h-full object-cover">
    <div class="layeredImage__image -index-2 ml-[-1px] [--w-desktop:97] …>
    <div class="layeredImage__image -index-3 ml-[-1px] isolate [--w-desktop:293] aspect-[293/380]">
```

原站 JS（`show()`）：wrapper 與 root 加 `.is-show` → GSAP `{value:0→1, duration:.9, ease:'expo.out'}`
每幀寫 `--tr = value²`、`--br = value`、`--tl = 0`、`--bl = 1`；切片位移與第 3 層 `img` 寬度
則是 CSS `transition … 1s cubic-bezier(.16,1,.3,1)`，`--delay` 原站是 `0s`（多個實例各自進場、不級聯）。

| 項目 | 原站值 | 本地對應 |
|---|---|---|
| 結構 | `.layeredImage > __image-wrapper > __image ×3` | `.bc-pa-stair > .bc-pa-stair__track > .bc-pa-stair__slice ×3` |
| 切片寬 | 49 / 97 / 293px @1440（後兩層 `margin-left:-1px`） | `flex: 49 1 0` / `97 1 0` / `293 1 0`（比例一字不差，隨本站格寬縮放）。原站那兩條 `margin-left:-1px` 本站抄了但**一直是無效宣告**：hero 內被 `bc-brand-stage.css` 的 reset `#bc-brand-stage span{margin:0}`（ID 選擇器）蓋掉 ⇒ 三條本來就是無縫相接 |
| 起始 | `translateX(-100%)` / `(-151%)` / `(-50%)`；第 3 層 `img{width:0}` | 同（`--pa-x` ＋ `@keyframes bc-pa-slice` / `bc-pa-image`） |
| 進場 | `1s cubic-bezier(.16,1,.3,1)`、無延遲 | 同（`animation: … 1s cubic-bezier(.16,1,.3,1) backwards`） |
| 擦除 | `clip-path` 四角：`.9s expo.out`，`--tr=v²`、`--br=v`、`--tl=0`、`--bl=1` | `@keyframes bc-pa-wipe 0.9s linear`，101 格（每 1%）直接寫出 `tr=v²`、`br=v` ⇒ 與原站逐幀等值 |

- **版面零變化**：格位仍是 `min(33.3vw, 560px)` 寬（走原本的 `--pa-w`），高度用
  `aspect-ratio: var(--pa-ratio)`（模板給該檔實際比例 768/1075、640/896、767/1074）；
  1440 實測 479.52 × 671.19 / 671.31 / 671.44、390 為 162.23 × 227.08，`ovfX = 0`。
  三層在格位內橫排（總寬 = 格寬），每層寬度 = 11.1% / 22.0% / 66.9% 格寬。
- **2026-11-16（使用者指示「移除錯位疊印」）**：改動前三層 `<img>` 都各自把「整張圖」
  `object-fit:cover` 進自己的窄條 ⇒ 同一張照片在格子裡重複出現 3 次（接縫處內容錯位，
  看起來像套印沒對準）。現在三層的 `<img>` 一律放大成 **整個 track 寬**、各自
  `left: 0` / `-(49/97)%` / `-(146/293)%` ⇒ 每層只露出自己那一段，拼起來就是原本那一張
  完整照片。三層結構、`--pa-x` 位移、wipe／slice／image 三條 keyframes 全部不動。
- **純 CSS 三條 `@keyframes`**（`bc-pa-wipe` / `bc-pa-slice` / `bc-pa-image`），沒有新 JS：
  收合狀態只存在於 `0%` 影格 ⇒ 第一繪製前就生效（原站 GSAP 版要等 `loadingDone` 才跑，
  自己會先閃一張完整照片）。`fill-mode` 一律 `backwards`（不是 `both`）：延遲期間吃 `0%` 影格、
  播完回基底樣式（＝終態）⇒ 動畫被中斷／被瀏覽器丟棄都不會停在「收合」。
- **為什麼不是 JS**：第一版用 `deferred` 腳本加 `.is-armed` 收合，實測第一帧仍是完整照片
  （會先閃一下再收合）；純 CSS 沒有這個問題，而且基底樣式＝終態 ⇒ `prefers-reduced-motion`、
  舊瀏覽器、`animation:none` 都是「靜態照片」而不是空白 hero。
- **手機保留三層**（與原站一致）：390×844 實測三層 18.11 / 35.84 / 108.28px，仍可辨識為直紋。
- **第 3 格（`.bc-pa-video` 影片輪播）不做階梯**：複製 3 份 `<video>` 太重，只吃原本的 0.6s 交叉淡入。

**調參**：切片寬度比＝`.bc-pa-stair__slice.-index-1/2/3` 的 `flex` 值（現值 49 / 97 / 293）；
時間與曲線＝`@keyframes` 的宣告（`bc-pa-wipe 0.9s`、切片 1s `cubic-bezier(.16,1,.3,1)`）；
擦除曲線要改就重算 `bc-pa-wipe` 的百分比表（`v = t===1 ? 1 : 1−2^(−10t)`，`tr = v²`、`br = v`，
每 1% 一格；目前 101 格，取樣誤差 < 0.05% 格寬）。

**回退**：`git checkout -- static/css/bc-photoarea.css templates/betweencoffee_delivery/partials/bc_brand_stage_hero.html`
（外加把 `index.html` 的 `bc-photoarea.css?v=` 降回 `20261109h`）。

### 四之六、「圖片 ＋ 文字」主視覺整塊移植（2026-11-14 使用者指示）

四之五是「照片格」單獨吃 `.layeredImage`；這一節是把原站**圖片與文字一起**的那個區塊
整塊搬過來 —— 也就是使用者指定的
`<div class="sm:flex flex-row-reverse justify-end items-center">`：

```html
<div class="sm:flex flex-row-reverse justify-end items-center">
  <div class="layeredText -home-mv _text-ja-heading-mxl">      <!-- 大字 3 份疊在同一格 -->
    <div class="layeredText__text-wrapper-wrapper | grid">      <!-- scale(1.5) → 1 -->
      <div class="layeredText__text-wrapper -index-1"><div class="layeredText__text">…</div>
      <div class="layeredText__text-wrapper -index-2">…
      <div class="layeredText__text-wrapper -index-3">…
  <div class="sm:mr-fluid-20 mt-2 sm:-mt-fluid-20 sm:w-[20.8%]">
    <div class="splide"><ul><li>… <div class="layeredImage -home-mv">…</div></li> ×3
```

**檔案**：`static/css/bc-gt-mv.css`（全部版面＋文字動畫）、`static/js/bc-gt-mv.js`（只負責換片）、
`templates/betweencoffee_delivery/partials/bc_gt_mv.html`（markup，結構與原站一對一）。

**放置位置**：首頁 who section 的 `.section-title__text`（2026-11-14 使用者指示「替換此內容
到 .section-title__text」）—— 原本放「Hmm...........」分層文字（`.who-title-layers`）的位置，
該組樣式已移除。外框由 `h2` 改 `div`（模組內是 div／img 等區塊層級內容），無障礙標題由
模組內的 `.visually-hidden h2` 提供。

- 模組自帶的左右 padding（原站 `._l-container` 的 `2.9166vw`／`1.25rem`）在 who section 內
  歸零，讓照片左緣對齊 kicker「(About)」；小螢幕幾 px 的溢出用 `overflow-x: clip` 收掉
  （都寫在 `bc-gt-mv.css` 檔尾 [6]）。
- 進場動畫改由 `IntersectionObserver`（25% 可見）起播：模組落在第二屏之後，若照原站在載入時
  就播，捲到那裡只會看到靜態照片。起播時 JS 在根節點加 `.is-live`（文字 zoom／切片）＋第一片
  `.is-on`（照片擦除／切片／縮放），之後每 5s 只搬 `.is-on`（文字不重播，與原站一致）。
  沒有 JS／`prefers-reduced-motion: reduce` 時停在 CSS 終態，第一片可見度由
  `.bc-gtmv__item.-index-1{opacity:1}` 保證（JS 起播後改由 `.is-live` ＋ `.is-on` 控制）。
- 舊的 `?mv=gt` 對照模式（`.bc-gtmv--preview` 鋪滿視窗 `position:fixed`）已移除。
- **2026-11-14 使用者後續指示**：① 模組底色清除（`background: transparent`，原本鋪 `--bc-bg`
  `#0e0e0e`，在 body 的 `bg_4.jpg` 上是一塊純黑方塊）② 大字文案改成單行 `Hm.......`
  （原站是 3 行；行高 94% 與所有位移比例不變，照片欄仍由 293:380 決定高度 ⇒ 版面高度不變）。
- **2026-11-16 使用者指示「文字 Hm..... 移到圖片頂部對齊」**：≥640px 的 `align-items`
  由 `center`（原站 `items-center`）改 `flex-start`，文字元素補
  `margin-top: calc(-0.10361em - 20px)`：
  - `0.12861em` ＝ 行盒（line-height 94%）內大寫字母墨跡頂點落在行盒頂點下方的量
    （半 leading −23.35px ＋ 字身 145px − `H` 帽高 103px ⇒ @1440 18.65px）；
  - 減 `0.025em` 是因為 `.bc-gtmv__scale > *` 本來就有 `-0.025em`，切片已先上移 3.63px；
  - 再減 `20px` 是照片欄的 `margin-top:-20px`（flex-start 的起點在照片上緣之上）。
  ⇒ 大字墨跡上緣與照片上緣齊平（@1440 實測 ink 249.79 / photo 249.78，差 0.01px；
  1024 / 834 / 640 分別差 0.23 / 0.69 / 0.51px）。**照片欄位置、區塊總高（360px）、
  下方內容位置都不變**（照片仍吃 −20px，文字多吃一份）。
  <640px 是區塊堆疊（文字本來就在照片上方，`margin-top:0`），不受影響；
  `overflow-x: clip` 只管水平，字往上的溢出不會被裁掉。
- **2026-11-16 使用者指示（同日第二批）**：「錯位疊印圖片效果」三片照片依序改成
  `who_01.jpg` / `who_02.jpg` / `who_01.jpg`（原 `photoarea/pa-1`、`pa-2`、`pa-4.webp`），
  `?v=20261116a`。新素材是直幅（1280×1920、1920×2880），`.bc-gtmv__px > img` 是
  `object-fit: cover` ⇒ 每條切片只是取同一張圖的不同裁切，版面／動畫參數都不用改
  （實測 1440：row 1280×360、照片欄 437×380、三條 283.6 寬的照片區完全同前）。
- **2026-11-16 使用者指示（同日第四批）**：第三片 `who_01.jpg` → **`who_03.jpg?v=20261116b`**
  （`bc_gt_mv.html`），片單定為 `who_01` / `who_02` / `who_03`（每片仍是同一張圖的 3 條重複切片）。
  `who_03.jpg` 是 1080×1080 方形，`object-fit: cover` 自動裁成 293/380 ⇒ 參數不動；
  實測三條切片 box 49 / 97 / 293×380、`naturalWidth` 1080、換片輪播正常。
- **2026-11-16 使用者指示（同日第五批）「who-section 文案 `Hm.......` → `Hmmm...`，and 文字縮小」**：
  ① `bc_gt_mv.html` 三份切片與螢幕閱讀器用的 `.visually-hidden` 都改成 `Hmmm...`。
  ② `bc-gt-mv.css` 字級改 `calc(var(--gt-fs-scale) * clamp(1.25rem, 10.0694444vw, 24.1666667rem))`，
     `--gt-fs-scale: 0.8` ⇒ @1440 **145 → 116px**（行高仍 94%）。要再調只改這一個變數：
     檔內其餘比例值（`0.25/0.36em` 裁切、`0.1em` 位移、`-0.10361em` 對齊補正）都是 em ⇒ 自動等比。
  ③ 實測 @1440：單行寬 444 → 461.5（`m` 比 `.` 寬得多，縮 0.8 倍後仍略寬）、高 136.3 → 109、
     墨跡上緣與照片上緣 **172 / 172px 仍齊平**（比例不變）；@834 font 67.18、墨跡差 0.03px；
     @390 font 31.42、文字盒 350×28.8、`ovfX=0`、0 console error。版號 `bc-gt-mv.css ?v=20261116a → 20261116b`。

| 項目 | 原站值 | 本地對應（`bc-gt-mv.css`） |
|---|---|---|
| 外框 | `._l-container`：content-box、`padding-inline:2.9166vw`（≥768px） | `.bc-gtmv__row` 同值（@1440 ⇒ 左右 42px） |
| 排列 | `sm:flex flex-row-reverse justify-end items-center` | `display:flex; flex-direction:row-reverse; justify-content:flex-end`（DOM 先文字後照片 ⇒ 視覺上照片在左、文字在右、整組靠左）；`align-items` 2026-11-16 由 `center` 改 `flex-start`（見上方「文字移到圖片頂部對齊」） |
| 照片欄寬 | 49+97+293−2 ＝ 437px @1440 | `30.3472vw`（內部再用 `flex: 49/97/293` 切一次；手機 `74.1333vw`＝31/62/185） |
| 照片高度 | 第 3 條 `aspect-[293/380]` ⇒ 380px | `.bc-gtmv__px.-index-3{aspect-ratio:293/380}` |
| 照片間距 | `sm:mr-fluid-20` ＝ clamp(…) 恆 20px；`sm:-mt-fluid-20` ＝ −20px | `.bc-gtmv__media{margin-right:20px; margin-top:-20px}`（2026-11-16 起文字改為與照片上緣對齊，−20px 保留 ⇒ 照片位置不變；文字在 `.bc-gtmv__text` 再多吃一份 −20px） |
| 字級 | `_text-ja-heading-mxl` ＝ clamp(1.25rem, 145/1440·100vw, 24.1667rem) | 同值再乘 `--gt-fs-scale`（2026-11-16 第五批＝**0.8**）；`line-height:94%`；原站 3 行，本站 2026-11-14 起改單行、2026-11-16 起文案 `Hmmm...`（@1440 = **116px** / 109px） |
| 文字變數 | `-home-mv`：`--firstLetterVisibleArea:.25em`、`--second:.36em`、`--margin:.1em`、`--bottomLetterVisibleArea:94%`、`--startLinetranslateX:-12%` | `--gt-a/--gt-b/--gt-m/--gt-bottom/--gt-start` 同值 |
| 文字裁切 | `-index-1` 露到 `.25em`、`-index-2` 到 `.36em`、`-index-3` 到 `110%`，下緣 94% | 同（`clip-path: polygon(-10% -10%, … , -10% 94%)`；@1440 實測 36.25px / 52.2px / 110%） |
| 文字位移 | 三份都從 `translateX(-12%)` 歸位：`0` / `calc(.25em+.1em)` / `calc(.25em+.36em+.2em)` | 同（`--gt-end`；@1440 實測 0 / 50.75px / 117.45px，起始 −60.54px ＝ 12% 字寬） |
| 文字進場 | 外層 `scale(1.5)→1`、`transition 1s cubic-bezier(.16,1,.3,1)` | `@keyframes bc-gtmv-zoom` / `bc-gtmv-line`，同曲線同時長、`fill:backwards`（收合只存在於 from 影格，不會先閃） |
| 圖片動畫 | 同四之五 | 直接沿用 `bc-pa-wipe` / `bc-pa-slice` / `bc-pa-image`（**本檔必須在 `bc-photoarea.css` 之後載入**） |
| 換片 | Splide 自動輪播，每片重播 `.layeredImage` | `bc-gt-mv.js` 進視口（25% 可見）先加 `.is-on` 起播，之後每 5s 把它搬到下一片（搬 class ⇒ 動畫重新開始）；`prefers-reduced-motion` 只起播不換片 |

**實測（首頁 who section，Chromium）**

| 檢查 | 1440×900 | 390×844 |
|---|---|---|
| 照片欄 | x=80（＝section padding 80）、437×380、三條 49 / 97 / 293 | x=20、289.1×251.2、三條 32.5 / 64.9 / 193.7（＝31/62/185 ÷ 375） |
| 文字 | x=537（＝80+437+20）、寬 461.5（單行 `Hmmm...`，高 106.2）、font 116px、line-height 109 | x=20、寬 350（超出部分由 `overflow-x: clip` 收掉）、font 31.42px、高 28.8 |
| 文字裁切／位移 | 36.25px / 52.2px / 110%，終態 0 / 50.75 / 117.45，下緣 94% | 同比例（第 3 片終態 `translateX` 31.8px ＝ 0.81em） |
| 起播 | 進視口前 0 個 `.is-on`、0 個 animation；捲入後同時 9 個（`bc-gtmv-zoom` ＋ 3 × `bc-gtmv-line` ＋ `bc-pa-wipe` ＋ 3 × `bc-pa-slice` ＋ `bc-pa-image`） | 同 |
| `prefers-reduced-motion: reduce` | animation 0 個、`.is-on` 停在第一片、照片可見（opacity 1） | 同 |
| 沒有 JS（手動移除 JS 加的 class） | 第一片 opacity 1、`clip-path` 全開、`img.naturalWidth` 768 ⇒ 靜態完成態 | 同 |
| 橫向溢出 `scrollWidth-clientWidth` | 0 | 0 |
| console error | 0 | 0 |

**已知差異（刻意）**：① 文案／照片換成本站的（2026-11-16 起 `Hmmm...`、字級 ×0.8；
`who_01/who_02/who_03.jpg`）
② 原站字距 `-.11em` 是日文全角字的視覺修正，本站用拉丁字 ⇒ `letter-spacing:0`
③ 原站是白底＋藍色重點字，本站不畫底色（吃 body 的 `bg_4.jpg`）＋白字（`.bc-gtmv__line.-accent`
   金色行 2026-11-14 隨單行化移除）
④ 原站的 3 份文字帶 `aria-hidden` ＋ 另給 `sr-only` 一段，本站同（`.visually-hidden` 由本檔自帶，
因為首頁沒有載入 Bootstrap 那一類）。

**回退**：`git checkout -- templates/betweencoffee_delivery/index.html` 後刪
`static/css/bc-gt-mv.css`、`static/js/bc-gt-mv.js`、`templates/betweencoffee_delivery/partials/bc_gt_mv.html`。


## 五、守衛與降級

| 情況 | 行為 |
|---|---|
| 找不到 `#bc-brand-stage`／`.bc-photoarea`／裡面沒有 `[data-para]` 元素 | `return`（不報錯） |
| GSAP／ScrollTrigger 沒載入（CDN 掛） | 視差 `return`（照片／影片容器停在 CSS 的 `translate3d(0,0,0)`＝靜態背景）；**影片播放不受影響** |
| `prefers-reduced-motion:reduce` | 視差 `return`（實測 `ScrollTrigger.getAll()` 相關 trigger = 0）；影片全部不播、`readyState 0`（連檔案都不抓）⇒ 該格空白；階梯圖三條 animation 由 `@media (prefers-reduced-motion: no-preference)` 包住 ⇒ reduce 時完全沒有 animation（實測 `getAnimations()` 相關 = 0），照片靜態全顯（基底樣式＝終態） |
| 舊瀏覽器不支援 `clip-path`／`aspect-ratio`，或使用者關掉 CSS 動畫 | 同上：照片照常顯示（只是沒有階梯／擦除動畫），不會空白 |
| 片單中某一支 404／格式不支援 | 那支永遠不 ready ⇒ 換片時跳過（留在當前支繼續 loop），版面不壞；若第 1 支就壞 ⇒ 該格空白 |
| `/about/` | 不載入本檔、也不含 `.bc-photoarea`；`isolation` 規則只在 `.bc-brand-stage-hero` 之下生效 |

## 六、驗收清單（改完照這串跑）

1. `python3 manage.py check` → 0 issue；`python3 scripts/docs_size_check.py` → 無超標。
2. 首頁載入後：
   - `.bc-photoarea` 的 computed `z-index:-1`、`pointer-events:none`；`#bc-brand-stage` 的 `isolation:isolate`。
   - 4 格 × 3 層 = 12 個 `.bc-pa-stair__slice > img`（`naturalWidth` 768／640／767；三份共用
     同一個 `src`，實際只抓一次）；第 3 格是影片容器（沒有 img）。
   - `document.documentElement.scrollWidth === window.innerWidth`（不會橫向溢出）。
3. 影片格位（第 3 格，輪播容器）：
   - `document.querySelectorAll('.bc-pa-video > video').length === 6`（＝`views.PA_VIDEOS` 長度），
     載入後**只有 1 支**帶 `.is-on`（`opacity:1`、`z-index:1`），其餘 `opacity:0`。
   - 當前那支 `paused === false`、`videoWidth > 0`；換片順序必須是
     `hero_00 → hero_04 → hero_05 → hero_03 → hero_02 → hero_06 → 回 hero_00`。
   - 觀察 6～11 秒：換片瞬間**兩支同時 `opacity` 介於 0–1**（交叉淡入），淡完（0.6s 後）舊支
     `paused === true` 且 `currentTime === 0`。
   - 容器寬＝`min(41.6vw/33.3vw ×1.35, 760px)`、高＝寬×2/3（3:2），`overflow:hidden`。
   - 往下捲過 hero（如 `y=2000`）→ 六支全部 `paused === true`；捲回 → 當前那支 `false`。
   - DevTools 開 `prefers-reduced-motion: reduce` 重新載入 → 六支全 `paused === true`、`readyState === 0`
     （影片檔沒被抓）⇒ 該格空白、4 張照片仍在、視差 transform 全為 `none`。
4. 逐段捲動（0 / 300 / 700 / 1300）讀 `getComputedStyle(tile).transform`（4 張 img ＋ 1 個影片容器）：
   位移量必須與 `data-para × vh × factor × 進度` 成比例（比例＝para 的比值）。
5. `elementFromPoint()` 打在環形照與時鐘上 → 不可以命中 `.bc-photoarea` 內的 `img`／`.bc-pa-video`。
6. 模擬 `prefers-reduced-motion: reduce` → 所有 transform 為 0。
7. 手機 390×844：照片寬 162px（41.6vw）、位移為桌面的一半、沒有橫向溢出。
8. `/about/` 回應內 `grep -c bc-photoarea` = 0。
9. 蒙版：`getComputedStyle(el).filter === 'brightness(0.25)'` —— 12 個內層 `img`（`.bc-pa-stair__slice > img`）
   與第 3 格的 **6 支 `video`** 都要有；容器 `.bc-photoarea` 本身**不該**有 filter（否則會多壓一次）。
10. 落點洗牌：連跑 5 次 `curl -s http://127.0.0.1:8081/ | grep -o 'class="bc-pa-stair x_[0-9] y_[0-9] d_[0-9][^"]*"'`
    —— 每次都不同，且同一次載入內 4 個 `x_n` 互不重複（1–5 取 4 個）、`y_n` 同理，
    `.d_n`、`data-para`、照片檔順序固定不變；`yoko` 永遠在 `.bc-pa-video` 那格。
11. 階梯揭露（2026-11-14 新增，`docs/home-photoarea.md` 四之五）：
    - 4 個 `.bc-pa-stair` 寬 = `min(33.3vw,560px)`、高 = 寬 × 該檔比例（1440 實測 479.52×671.19／
      671.31／671.44；390 為 162.23×227.08）；三層寬 53.52 / 105.95 / 320.05（依 49:97:293 分掉格寬）。
    - 擦除在 `.bc-pa-stair__track`：載入第一帧 `clipPath` 應為 `polygon(0% 0%, 0% 0%, 0% 100%, 0% 100%)`
      （收合，**不能**是 100%——那代表會先閃一張完整照片），約 0.9s 後變全開；過程中
      上緣百分比 = 下緣百分比²（例：t=45ms → tr 8.58%、br 29.29%；t=180ms → 56.25% / 75%）。
      驗法：`document.getAnimations().forEach(a=>a.pause())` 後把 `currentTime` 設 0/45/90/180/450/900
      逐點讀 `getComputedStyle(track).clipPath`。
    - 三層與第 3 層 `img` 皆無延遲級聯（`animationDelay` 全 `0s`，與原站 `--delay: 0s` 一致）；
      1s 後 `transform === 'none'`、第 3 層 `img` 寬 = **track 寬**（＝切片寬 × 439/293 ＝ 149.83%）、
      `clipPath` 全開。
    - 拼回一張照片（2026-11-16 起）：三層 `img` 的 `getBoundingClientRect().x` 都等於 track 左緣、
      寬高都等於 track（1440 實測左緣偏移 0 / 0 / 0、寬 479.45 / 479.52 / 479.52）；若偏移是
      1px／2px 代表 `left` 的百分比算錯。
    - 390×844：三層都在（`display:block`）、`ovfX = 0`。
    - `prefers-reduced-motion: reduce`：`getAnimations()` 內 `bc-pa-*` = 0、`clipPath` 全開、第 3 層
      `img` 寬 = 切片寬（＝照片靜態全顯）。
    - 模擬 `prefers-reduced-motion: reduce`：三條 `animationName === 'none'`、照片立刻全顯（無裁切）。
