# 首頁 hero 背景照片視差（`.bc-photoarea`）

> 2026-11-07 建立。移植 **hicard.studio** 首頁的 `.fv__photoarea` ＋ GSAP「Sticky1」位移。
> 改這塊前必讀；檔案只有 3 個：`static/css/bc-photoarea.css`、`static/js/bc-photoarea.js`、
> markup 在 `templates/betweencoffee_delivery/partials/bc_brand_stage_hero.html`（`#bc-brand-stage` 第一個子節點）。
> 另外落點洗牌在 view：`betweencoffee_delivery/views.py` 的 `_photoarea_slots()`（見 §四之四）。

## 一、效果是什麼

首頁第一屏（品牌舞台 hero：時鐘 `{ 21 : 59 }` ＋環形咖啡照 ＋大字）的**背後**鋪 5 格照片，
往下捲時這 5 格比內容更快往上飄（多層視差），彼此錯位、依序離開畫面。
每格都壓了一層 **70% 黑蒙版**（2026-11-09 起，見 §四之三）⇒ 照片退成氛圍，不搶前面時鐘／環形照／大字。
**每次重新整理，5 格的落點都會重排**（2026-11-09 起，比照原站；見 §四之四）。

兩層位移（相加，皆 `scrub`、皆 `ease:'none'`）：

| 層 | 元素 | 位移量 | 來源 |
|---|---|---|---|
| 容器 | `.bc-photoarea` | `data-pa-shift`（vh，預設 `-10`）× factor | 原站 Sticky1 的容器位移 |
| 單張 | 每個 `[data-para]` 元素（4 個 `<img>` ＋ 1 個影片容器 `.bc-pa-video`） | `data-para`（vh，`-8 / -13 / -18 / -23 / -28`） | 原站 `data-para="-100…-500"` 等比換算 |

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
- 首頁 hero 的 `#bc-brand-stage` 與 `.footer` 底色已是 `transparent`
  （`bc-brand-stage.css` 檔尾「首頁專用覆寫」段）⇒ 照片直接透出，不必處理遮蓋。
- `pointer-events:none` ⇒ 環形照 hover 徽章／拖曳／連結、時鐘、nav 全不受影響
  （驗收方式：`document.elementFromPoint()` 取環形照與時鐘中心，`closest('.bc-photoarea')` 必為 null）。

## 三、素材（本站自存，2026-11-09 起）

- 位置：`static/images/photoarea/pa-1.webp` ~ `pa-5.webp`（`pa-n` 對應 DOM 的 `d_n`），皆 `768×1075`。
- **`pa-3.webp` 已不使用**：2026-11-09 15:27 使用者把它改名為 `pa-3__.webp`（只當備份，不參與畫面），
  第 3 格改由影片填滿（見 §四之二）。`<video>` **沒有** `poster` ⇒ 影片未播／不允許播時該格是空的
  （露出後面的深色底），好處是不會多一支 404 請求；缺點是 reduced-motion 使用者看不到靜態畫面。
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

### 四之二、第 3 格＝影片容器（2026-11-09 使用者指示）

第 3 格（`.yoko .d_3` ＋洗牌得來的 `.x_n／.y_n`）由 `<img>` 改成「容器＋影片」：

```html
<div class="x_{{ pa_slots.2.x|default:3 }} y_{{ pa_slots.2.y|default:5 }} d_3 yoko bc-pa-video" data-para="-18">
  <video class="bc-pa-video__el" muted loop playsinline preload="none" tabindex="-1">
    <source src="{% static 'media/hero_00.webm' %}?v=20261109a" type="video/webm">
  </video>
</div>
```

- **幾何沿用**：外層 `.bc-pa-video` 吃 `.bc-photoarea img` 同一組規則（`position:absolute`、
  `width:min(33.3vw,560px)`、`.yoko` 的 ×1.35（上限 760px）＋ `aspect-ratio:3/2`），只多補
  `overflow:hidden`；內層 `video{width:100%;height:100%;object-fit:cover}` ⇒ 換素材不必改任何尺寸。
- **位移掛外層**：JS 抓 `[data-para]`（img 與容器一視同仁），影片自己不掛 transform。
- **播放規則**（`setupVideos()`，刻意與 GSAP 解耦）：

  | 情況 | 行為 |
  |---|---|
  | 照片區在視窗內 | `play()`（`preload="none"` ⇒ 進畫面才抓檔） |
  | 捲離視窗 | `pause()`（不讓滾過去的 hero 繼續解碼／吃電） |
  | `prefers-reduced-motion:reduce` | 不播，停在第一幀之前（`readyState 0`）⇒ 該格空白（無 `poster`，見 §三） |
  | `play()` 被瀏覽器拒絕（iOS 省電／低電量） | 靜默失敗，該格空白，不報錯 |
  | 沒有 `IntersectionObserver` | 直接播 |

- **素材**：`static/media/hero_00.webm`（1280×720、6 秒、762KB），原本是 `/about/` 首屏 sticky MV 的第 1 支。
  換檔＝改 `<source>` 檔名＋升 `?v=`。本格位是 3:2＋`cover` ⇒ 16:9 影片會左右各裁約 8%。
- **快取**：這裡的 `?v=20261109a` 是手動升的（about 頁那條由 `views._mv_versioned_static()` 自動加 mtime）
  ⇒ **換掉 `hero_00.webm` 時，本行 `?v=` 要一起升**，否則瀏覽器可能續用舊檔。

### 四之三、每格黑蒙版 70%（2026-11-09 使用者指示，同日演進 40% → 50% → 60% → 70%）

```css
.bc-photoarea { --pa-dim: 0.3; }                     /* .3 ＝ 疊 black 70% */
.bc-photoarea img,
.bc-photoarea .bc-pa-video > video { filter: brightness(var(--pa-dim)); }
```

- **為什麼不是「遮罩層」**：`<img>` 是 replaced element，`::before`／`::after` 不會渲染 ⇒ 真遮罩層
  得為每一格加 wrapper（改 markup ＋全部幾何選擇器）。而 `rgba(0,0,0,.7)` 疊在圖上的結果是
  `C×.3 ＋ 0×.7 ＝ .3C`，`brightness(.3)` 同樣是逐通道乘 `.3` ⇒ **畫面完全等價**，一行 CSS 就够。
- **涵蓋範圍**：4 張 `<img>` ＋ 第 3 格的 `<video>`（影片會裁切、縮放顯示 ⇒ 影格同樣被壓暗；
  不會「先亮後暗」閃一下）。**不含** body 背景圖、也不含 stage 上的內容（時鐘／環形照／大字仍全亮）。
- **調濃淡**：只改 `--pa-dim`。`.3`＝70% 黑（現值）、`.4`＝60% 黑、`.5`＝50% 黑、`.6`＝40% 黑、
  `1`＝不壓暗；
  手機斷點共用同一個值（要分開就寫在 `≤768px` 的 `.bc-photoarea` 區塊）。
- **之後若要在蒙版「上」再疊東西**（漸層、文字、hover 提亮）：改 wrapper 結構
  `<div class="x_1 y_4 d_4 …" data-para="-23"><img …><span class="bc-pa-mask"></span></div>`，
  幾何 class／`data-para` 留在 wrapper、`img{width:100%;height:auto}`、`.bc-pa-mask{position:absolute;inset:0;background:rgba(0,0,0,.7)}`。
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

## 五、守衛與降級

| 情況 | 行為 |
|---|---|
| 找不到 `#bc-brand-stage`／`.bc-photoarea`／裡面沒有 `[data-para]` 元素 | `return`（不報錯） |
| GSAP／ScrollTrigger 沒載入（CDN 掛） | 視差 `return`（照片／影片容器停在 CSS 的 `translate3d(0,0,0)`＝靜態背景）；**影片播放不受影響** |
| `prefers-reduced-motion:reduce` | 視差 `return`（實測 `ScrollTrigger.getAll()` 相關 trigger = 0）；影片不播、`readyState 0`（連檔案都不抓）⇒ 該格空白 |
| 影片檔案 404／格式不支援 | 該格空白（無 `poster`），版面不壞；其餘 4 格照常 |
| `/about/` | 不載入本檔、也不含 `.bc-photoarea`；`isolation` 規則只在 `.bc-brand-stage-hero` 之下生效 |

## 六、驗收清單（改完照這串跑）

1. `python3 manage.py check` → 0 issue；`python3 scripts/docs_size_check.py` → 無超標。
2. 首頁載入後：
   - `.bc-photoarea` 的 computed `z-index:-1`、`pointer-events:none`；`#bc-brand-stage` 的 `isolation:isolate`。
   - 5 張 `naturalWidth=768`（圖真的有載到）。
   - `document.documentElement.scrollWidth === window.innerWidth`（不會橫向溢出）。
3. 影片格位（第 3 格）：
   - `video.videoWidth === 1280`、`videoHeight === 720`、`paused === false`（在首屏時）。
   - 容器寬＝`min(41.6vw/33.3vw ×1.35, 760px)`、高＝寬×2/3（3:2），`overflow:hidden`。
   - 往下捲過 hero（如 `y=2000`）→ `video.paused === true`；捲回 → 又 `false`。
   - DevTools 開 `prefers-reduced-motion: reduce` 重新載入 → `video.paused === true`、`currentTime === 0`、
     `readyState === 0`（影片檔沒被抓）⇒ 該格空白、4 張照片仍在、視差 transform 全為 `none`。
4. 逐段捲動（0 / 300 / 700 / 1300）讀 `getComputedStyle(tile).transform`（4 張 img ＋ 1 個影片容器）：
   位移量必須與 `data-para × vh × factor × 進度` 成比例（比例＝para 的比值）。
5. `elementFromPoint()` 打在環形照與時鐘上 → 不可以命中 `.bc-photoarea` 內的 `img`／`.bc-pa-video`。
6. 模擬 `prefers-reduced-motion: reduce` → 所有 transform 為 0。
7. 手機 390×844：照片寬 162px（41.6vw）、位移為桌面的一半、沒有橫向溢出。
8. `/about/` 回應內 `grep -c bc-photoarea` = 0。
9. 蒙版：`getComputedStyle(el).filter === 'brightness(0.3)'` —— 4 張 `img` 與第 3 格 `video` 都要有；
   容器 `.bc-photoarea` 本身**不該**有 filter（否則會多壓一次）。
10. 落點洗牌：連跑 5 次 `curl -s http://127.0.0.1:8081/ | grep -o 'class="x_[0-9] y_[0-9] d_[0-9][^"]*"'`
    —— 每次都不同，且同一次載入內 5 個 `x_n` 互不重複、5 個 `y_n` 互不重複（各自是 1–5 的排列），
    `.d_n`、`data-para`、照片檔順序固定不變；`yoko` 永遠在 `.bc-pa-video` 那格。
