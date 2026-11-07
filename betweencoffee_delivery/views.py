"""
*args, **kwargs 語法使用 :

可以在同一個函數定義中同時使用兩者，但*args必須在之前出現**kwargs。
您也可以在呼叫函數時使用*和語法。**例如：
>>> def print_three_things(a, b, c):
...     print( 'a = {0}, b = {1}, c = {2}'.format(a,b,c))
...
>>> mylist = ['aardvark', 'baboon', 'cat']
>>> print_three_things(*mylist)
a = aardvark, b = baboon, c = cat

正如您在這種情況下看到的，它會獲取項目清單（或元組）並將其解包。透過這種方式
它將它們與函數中的參數進行匹配。當然，您可以*在函數定義和函數呼叫中同時擁有它們。
"""

import os

from django.contrib.staticfiles import finders
from django.db.models import Q

# betweencoffee_delivery/views.py
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import reverse
from django.views import View

from cart.cart import Cart  # Import the Cart class
from eshop.models import BeanItem, CoffeeItem

# /about/ 首屏產品列（page-top__mv__product）要排除的咖啡 id。
# 2026-11-04（使用者指示）：可在此增減；只影響首屏輪播，不影響下方 SERIES 滑桿／字輪。
MV_EXCLUDE_IDS = {7}  # #7 Nice Step

# /about/ 首屏背景影片（.sticky-bg__bg）多層輪播設定。
# 2026-11-06（使用者指示）：改成「可載入多支影片、依序輪播」→ 機制移植
# weekday.co.jp 首頁 .p-hero__videos（多層 <video> + 提前 0.75s 交叉淡入，
# 細節見 static/js/bc-sticky-mv.js 的 initVideo）。
# · 第一筆＝模板預先渲染的第 0 層；第 1 層之後由 bc-sticky-mv.js 建立。
#   2026-11-06（使用者指示第二輪）：播放順序改為「依清單順序」
#   （hero_00 → hero_01 → … → hero_06 → 回到 hero_00），不再每次載入洗牌。
# · 每筆可含 webm / mp4 / poster，缺少的鍵就不輸出對應 <source>（單 mp4 也能用）。
# · MV_MAX＝同時最多幾層（原站寫死 t < 5）。層數 = min(片單長度, MV_MAX)
#   ⇒ 片單變長時要一起調，否則多出來的片永遠輪不到。
# · 快取：WHITENOISE_MAX_AGE＝1 年 ⇒ 同名檔換內容，瀏覽器不會來問就沿用舊快取。
#   2026-11-07（使用者回報「hero_00~06 換了影片內容還顯示舊版」）：改由下方
#   _mv_versioned_static() 在 URL 後自動加 ?v=<檔案 mtime>，換檔即換網址，
#   不必再改檔名、也不必手動升版號（舊做法：換片要改名）。
MV_MAX = 7
MV_VIDEOS = [
    # 2026-11-06（使用者指示）：整組換成 hero_00 ~ hero_06 七支 webm，依檔名順序播放。
    # 第 0 層沒有另附 poster —— 舊版 poster（images/hero_bg_v2-poster.jpg）是舊影片的
    # 截圖，內容不符；影片解碼前顯示的是品牌黑底（#0e0e0e），不會閃到別的畫面。
    {"webm": "media/hero_00.webm"},
    {"webm": "media/hero_01.webm"},
    {"webm": "media/hero_02.webm"},
    {"webm": "media/hero_03.webm"},
    {"webm": "media/hero_04.webm"},
    {"webm": "media/hero_05.webm"},
    {"webm": "media/hero_06.webm"},
]


def _mv_versioned_static(rel_path):
    """把 static() 的 URL 加上 ?v=<檔案 mtime>，用來破 WhiteNoise 的 1 年長快取。

    2026-11-07（使用者回報）：`hero_00~06.webm` 換了內容但檔名不變，瀏覽器直接
    用快取（WHITENOISE_MAX_AGE＝31536000）→ 看起來「還顯示舊版本」。
    以檔案最後修改時間當版號：換檔 → mtime 變 → 網址變 → 一定重新下載；
    平時（沒換檔）網址穩定，長快取照樣有效。找不到檔案時退回原始 URL。
    """
    url = static(rel_path)
    abs_path = finders.find(rel_path)
    if not abs_path:
        return url
    try:
        return f"{url}?v={int(os.path.getmtime(abs_path))}"
    except OSError:
        return url


# 處理index, about HTTP 請求所發生的情況
# 當使用者向伺服器發送 GET 請求時渲染 HTML template模板
class Index(View):
    def get(self, request, *args, **kwargs):
        shop_hot_coffees = CoffeeItem.objects.filter(
            is_shop_hot_item=True, is_published=True
        ).order_by("hot_item_order", "id")[:4]

        # 简化：上下文处理器已经处理了cart，这里不需要重复
        context = _build_landing_context(request)
        return render(request, "betweencoffee_delivery/index.html", context)


# 新 Landing 頁面：讀取實際咖啡/咖啡豆資料（原型 B）
class LandingNew(View):
    def get(self, request, *args, **kwargs):
        context = _build_landing_context(request)
        return render(request, "betweencoffee_delivery/landing_v3.html", context)


def _build_landing_context(request):
    """共用：首頁 / landing 的商品 + 登入狀態 + 社交頭像 context"""
    hot_coffees = CoffeeItem.objects.filter(
        is_shop_hot_item=True, is_published=True
    ).order_by("hot_item_order", "id")[:4]
    all_coffees = CoffeeItem.objects.filter(is_published=True)[:9]
    # 2026-09-07：GUNTE hero 手套圓 → coffee menu 照片（排序同 coffee_menu 頁）
    hero_coffees = CoffeeItem.objects.filter(is_published=True).order_by("sort_order", "id")[:7]
    # 2026-09-07：bc-search 背景浮動圖改用 BeanItem（id7 / id6）
    search_bean_01 = BeanItem.objects.filter(pk=7).first()
    search_bean_02 = BeanItem.objects.filter(pk=6).first()
    beans = BeanItem.objects.filter(is_published=True)[:3]

    context = {
        "shop_hot_coffees": hot_coffees,
        "hot_coffees": hot_coffees,
        "all_coffees": all_coffees,
        "hero_coffees": hero_coffees,
        "search_bean_01": search_bean_01,
        "search_bean_02": search_bean_02,
        "beans": beans,
        "is_authenticated": request.user.is_authenticated,
        "user_avatar": "",
        "last_order_image": "",
        "last_order_link": "",
        # 2026-10-04：首頁 .top_art sticky 堆疊卡片（loogg.jp 模組移植）
        # 2026-10-08：模組已依指示移至 About 頁（見 About.get → 同一 builder）；
        #            index.html 不再輸出此區塊，landing context 保留供其他 landing 模板沿用。
        "top_art_cards": _build_top_art_cards(),
    }

    if request.user.is_authenticated:
        context["user_avatar"] = _get_user_avatar(request.user)
        context["last_order_image"] = _get_last_order_image(request.user)
        context["last_order_link"] = _get_last_order_link(request.user)

    return context


def _build_top_art_cards():
    """About 頁 .top_art（loogg.jp sticky 堆疊卡片模組移植）11 張卡內容。

    2026-10-04 建立（當時位於首頁）；2026-10-08 依指示自 index.html 移至 About 頁
    （.bc-fujiya-photo 區塊正下方），內容與動畫參數不變，素材全部取自站上既有圖（非新圖）：
      · 7 張 hero 素材（PC 方圖 + SP 510x680；與 GUNTE hero 同一組、同一 PC/SP 配對）
      · 3 張 fujiya-photo（PC 取 _b 半尺寸 1360x600 省頻寬；SP 取 photoN_sp 750x1040）
      · 1 張 bc_machine.jpg（門市烘豆機；站上無 SP 版本 → PC/SP 共用，
        由 CSS object-fit:cover 置中裁切）
    文案沿用站上既有商品名與 hero 文案語氣；三個 atmosphere 卡的文案為品牌語氣的
    氛圍字（非商品描述），如需調整只改這個 list。

    數量固定 11：bc-top-art.css 的 :nth-child 陰影、bc-top-art.js 的
    「最後一張不縮放」皆以 11 張為準。
    """
    return [
        {
            "name_label": "Coffee Vol.01: ",
            "name_strong": "Black Blend",
            "title_pc": "專屬配豆驅動您最佳狀態，",
            "title_sp": "釋放能量。",
            "img_pc": "images/01_1080.webp",
            "img_sp": "images/01_sp_510x680.webp",
            "alt": "Black Blend 咖啡",
            "href": reverse("coffee", args=[4]),
        },
        {
            "name_label": "Coffee Vol.02: ",
            "name_strong": "Butter King",
            "title_pc": "極致豐厚焦糖黃油定番，",
            "title_sp": "餘味完全覆蓋在味蕾上。",
            "img_pc": "images/02_1080.webp",
            "img_sp": "images/02_sp_510x680.webp",
            "alt": "Butter King 咖啡",
            "href": reverse("coffee", args=[10]),
        },
        {
            "name_label": "Coffee Vol.03: ",
            "name_strong": "果香浅煎",
            "title_pc": "果香先行，",
            "title_sp": "淺焙明亮、甜感收尾。",
            "img_pc": "images/03_1080.webp",
            "img_sp": "images/03_sp_510x680.webp",
            "alt": "果香浅煎 咖啡",
            "href": reverse("coffee", args=[9]),
        },
        {
            "name_label": "Coffee Vol.04: ",
            "name_strong": "抹茉",
            "title_pc": "静岡縣產抹茶，",
            "title_sp": "在牛奶裡慢慢散開。",
            "img_pc": "images/04_660.webp",
            "img_sp": "images/04_sp_510x680.webp",
            "alt": "抹茉 抹茶咖啡",
            "href": reverse("coffee", args=[8]),
        },
        {
            "name_label": "Coffee Vol.05: ",
            "name_strong": "Flat White",
            "title_pc": "濃縮與牛奶的黃金比例，",
            "title_sp": "只留剛剛好的那一口。",
            "img_pc": "images/05_630.webp",
            "img_sp": "images/05_sp_510x680.webp",
            "alt": "Flat White 咖啡",
            "href": reverse("coffee", args=[3]),
        },
        {
            "name_label": "Coffee Vol.06: ",
            "name_strong": "Sunshine",
            "title_pc": "連接專屬於您的味蕾，",
            "title_sp": "從一天的第一口開始。",
            "img_pc": "images/06_720.jpg",
            "img_sp": "images/06_sp_510x680.webp",
            "alt": "Sunshine 咖啡",
            "href": reverse("coffee", args=[2]),
        },
        {
            "name_label": "Coffee Vol.07: ",
            "name_strong": "WakeMeup",
            "title_pc": "醒來的那一口，",
            "title_sp": "由這裡開始。",
            "img_pc": "images/07_1080.jpg",
            "img_sp": "images/07_sp_510x680.webp",
            "alt": "WakeMeup 咖啡",
            "href": reverse("coffee", args=[1]),
        },
        {
            "name_label": "Atmosphere Vol.01: ",
            "name_strong": "Strawberry",
            "title_pc": "季節的果物，",
            "title_sp": "先替甜點預告了顏色。",
            "img_pc": "images/fujiya-photo/photo1_b.jpg",
            "img_sp": "images/fujiya-photo/photo1_sp.jpg",
            "alt": "季節果物",
            "href": reverse("about"),
        },
        {
            "name_label": "Atmosphere Vol.02: ",
            "name_strong": "Shortcake",
            "title_pc": "一層一層夾起來的，",
            "title_sp": "是剛剛好的甜。",
            "img_pc": "images/fujiya-photo/photo2_b.jpg",
            "img_sp": "images/fujiya-photo/photo2_sp.jpg",
            "alt": "手作蛋糕",
            "href": reverse("about"),
        },
        {
            "name_label": "Atmosphere Vol.03: ",
            "name_strong": "Baked",
            "title_pc": "出爐的那一刻，",
            "title_sp": "整間店都醒了。",
            "img_pc": "images/fujiya-photo/photo3_b.jpg",
            "img_sp": "images/fujiya-photo/photo3_sp.jpg",
            "alt": "出爐甜點",
            "href": reverse("about"),
        },
        {
            "name_label": "Bean Vol.01: ",
            "name_strong": "Kingsman",
            "title_pc": "機器裡養著今天的豆子，",
            "title_sp": "磨豆聲，就是開店的信號。",
            "img_pc": "images/bc_machine.jpg",
            "img_sp": "images/bc_machine.jpg",
            "alt": "門市烘豆機裡的咖啡豆",
            "href": reverse("bean", args=[3]),
        },
    ]


def _get_last_order_image(user):
    """取得用戶最後一筆訂單的第一個商品圖片"""
    try:
        last_order = user.orders.order_by("-id").first()
        if last_order:
            items = last_order.get_items()
            if items:
                return items[0].get("image") or ""
    except Exception:
        pass
    return ""


def _get_last_order_link(user):
    """產生最後訂單商品詳細頁連結（含預先選取上次選項的 query string）

    - 咖啡（coffee）: cup_level / milk_level / strength_level
    - 咖啡豆（bean）: weight / grinding_level
    """
    try:
        last_order = user.orders.order_by("-id").first()
        if last_order:
            items = last_order.get_items()
            if items:
                item = items[0]
                pid = item.get("id")
                ptype = item.get("type")
                if not pid or ptype not in ("coffee", "bean"):
                    return ""
                opts = []
                if ptype == "bean":
                    for key in ("weight", "grinding_level"):
                        val = item.get(key)
                        if val:
                            opts.append(f"{key}={val}")
                    # 自訂選項組（2026-09-21）：客人可選的組另帶 option_<key>=<value> 供詳情頁預選
                    for key, val in (item.get("extra_options") or {}).items():
                        if val:
                            opts.append(f"option_{key}={val}")
                else:
                    for key in ("cup_level", "milk_level", "strength_level"):
                        val = item.get(key)
                        if val:
                            opts.append(f"{key}={val}")
                    # 自訂選項組（2026-08-15）：extra_options → option_<key>=<value>（詳情頁 preselect 支援）
                    for key, val in (item.get("extra_options") or {}).items():
                        if val:
                            opts.append(f"option_{key}={val}")
                qs = "?" + "&".join(opts) if opts else ""
                base = "/coffee/" if ptype == "coffee" else "/bean/"
                return f"{base}{pid}/{qs}"
    except Exception:
        pass
    return ""


def _get_user_avatar(user):
    """優先取社交頭像（Facebook/Google），否則用 Profile 頭像"""
    try:
        for account in user.socialaccount_set.all():
            extra = account.extra_data or {}
            picture = (
                extra.get("picture")
                or extra.get("avatar")
                or extra.get("avatar_url")
            )
            if picture:
                # 直接字串 URL（Google picture / avatar_url）
                if isinstance(picture, str) and picture.startswith("http"):
                    return picture
                # Facebook 巢狀 dict 格式: {"data": {"url": "..."}}
                if isinstance(picture, dict):
                    data = picture.get("data") or {}
                    url = data.get("url") if isinstance(data, dict) else None
                    if url:
                        return url

            # Facebook：extra_data 無 picture 時用 Graph API 標準頭像 URL
            # 需附帶 access token，否則 Facebook 只回傳預設/模糊頭像
            if account.provider == "facebook":
                uid = extra.get("id") or account.uid
                if uid:
                    token = (
                        account.socialtoken_set.first()
                        if hasattr(account, "socialtoken_set")
                        else None
                    )
                    token_str = token.token if token else ""
                    if token_str:
                        return (
                            "https://graph.facebook.com/v3.0/"
                            f"{uid}/picture?type=square&height=96&width=96"
                            f"&access_token={token_str}"
                        )
                    return (
                        "https://graph.facebook.com/v3.0/"
                        f"{uid}/picture?type=square&height=96&width=96"
                    )
    except Exception:
        pass

    # Profile 頭像（本地上傳或預設 avatar.svg）
    try:
        profile = getattr(user, "profile", None)
        if profile:
            return profile.avatar
    except Exception:
        pass
    return ""
# List out coffee item
class CoffeeMenu(View):
    def get(self, request, *args, **kwargs):
        coffee_menu = CoffeeItem.objects.all().order_by("sort_order", "id")
        cart = Cart(request)  # Initialize the cart

        context = {
            "coffee_menu": coffee_menu,
            "cart": cart,  # keep cart count fn
        }
        return render(request, "betweencoffee_delivery/coffee_menu.html", context)


class Coffee(View):
    def get(self, request, product_id, *args, **kwargs):
        coffee = get_object_or_404(CoffeeItem, id=product_id)
        cart = Cart(request)  # Initialize the cart

        # 自訂選項組（2026-08-15）：依該咖啡啟用的選項組，提供給詳情頁渲染
        from eshop.models.option_definitions import OPTION_GROUPS

        # 以 (預設索引, group) 成對處理；排序用索引當 secondary key，避免在 sort 期間查 list
        enabled = [
            (i, g)
            for i, g in enumerate(OPTION_GROUPS)
            if getattr(coffee, f"option_{g['key']}", False)
        ]

        # 依 Admin 數字排序（option_order_<key>：數字越小越靠前，0=預設順序）
        def _order_key(item):
            i, g = item
            n = getattr(coffee, f"option_order_{g['key']}", 0) or 0
            return (n if n > 0 else 10 ** 9, i)

        enabled.sort(key=_order_key)
        enabled_groups = [g for _, g in enabled]

        context = {
            "coffee": coffee,
            "cart": cart,  # Add the cart to the context
            "option_groups": enabled_groups,
        }
        return render(request, "betweencoffee_delivery/coffee.html", context)


# List out bean item
class BeanMenu(View):
    def get(self, request, *args, **kwargs):
        bean_items = BeanItem.objects.all().order_by("sort_order", "id")
        cart = Cart(request)  # Initialize the cart

        context = {
            "bean_items": bean_items,
            "cart": cart,  # keep cart count fn
        }
        return render(request, "betweencoffee_delivery/bean_menu.html", context)


class Bean(View):
    def get(self, request, product_id, *args, **kwargs):
        bean = get_object_or_404(BeanItem, id=product_id)
        cart = Cart(request)  # Initialize the cart

        # 自訂選項組（2026-09-21）：與咖啡同一套機制。
        # - option_groups ＝前台用「按鈕 UI」渲染的組（＝客人可選的組，目前為研磨），
        #   依 Admin 排序數字排序。
        # - 產地為唯讀組，**不新增 UI** → 沿用詳情頁原有排版，只需解析中文值（含「其他（自填）」）。
        from eshop.models.option_definitions import (
            BEAN_OPTION_GROUPS,
            bean_option_display_value,
            get_bean_option_groups,
        )

        origin_group = next((g for g in BEAN_OPTION_GROUPS if g["key"] == "origin"), None)
        # 2026-10-28（使用者指示）：about.html 的「咖啡豆 SERIES 括號滑桿」移入本頁
        # （位置＝商品主區 .ftco-subpage-section.ftco-section-single-product 正下方）
        # → 需要同一組咖啡豆清單。原本 About 用固定 id 1,2,3,6,7,8（＝目前全部 6 支），
        #   此處改為全部 BeanItem 依 id 排序，結果相同但新增咖啡豆時會自動納入。
        series_beans = list(BeanItem.objects.all().order_by("id"))

        context = {
            "bean": bean,
            "cart": cart,  # keep cart count fn
            "option_groups": get_bean_option_groups(bean),
            # 產地沿用既有排版顯示；中文值在此解析（「其他（自填）」→ origin_custom）
            "origin_display": bean_option_display_value(bean, origin_group) if origin_group else "",
            # 咖啡豆 SERIES 括號滑桿（頁面底部）
            "series_beans": series_beans,
        }
        return render(request, "betweencoffee_delivery/bean.html", context)


# Keeping NOT use
class CoffeeMenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("q")
        # # 提供Search 搜尋特定的項目, 使用below過濾任何部分匹配結果
        search_items = CoffeeItem.objects.filter(
            Q(name__icontains=query)
            | Q(price__icontains=query)
            | Q(description__icontains=query)
        ).order_by("sort_order", "id")

        context = {"search_items": search_items}
        return render(request, "betweencoffee_delivery/coffee_menu.html", context)


class BeanMenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("q")
        # 使用below過濾任何部分匹配結果
        search_items = BeanItem.objects.filter(
            Q(name__icontains=query)
            | Q(price__icontains=query)
            | Q(description__icontains=query)
        ).order_by("sort_order", "id")

        context = {"search_items": search_items}
        return render(request, "betweencoffee_delivery/bean_menu.html", context)


class About(View):
    def get(self, request, *args, **kwargs):
        cart = Cart(request)  # Initialize the cart

        # 2026-08-27：SERIES 滑桿改資料庫驅動——取目前顯示的 6 種咖啡
        # （資料庫 id 1-4、7、8；id 5、6 已刪除不存在）
        series_coffees = list(
            CoffeeItem.objects.filter(id__in=[1, 2, 3, 4, 7, 8]).order_by("id")
        )
        # 2026-11-04（使用者指示）：首屏產品列（page-top__mv__product）只放 5 張，
        # 移除 #7 Nice Step（使用者：「page-top__mv__product 減少 Nice Step 該咖啡組」）。
        # 只影響首屏輪播；下方「咖啡 SERIES 括號滑桿」與字輪仍用完整 6 筆 series_coffees。
        # 註：Nice Step 原本 image_index 空著 → fallback 到詳情圖，杯身渲染比其他組大，
        # 已由 migration 0084 補上 nicestep_index.png（其他列表／商品卡一併受益）。
        mv_coffees = [
            coffee for coffee in series_coffees if coffee.id not in MV_EXCLUDE_IDS
        ]
        # 2026-10-28（使用者指示）：咖啡豆 SERIES 括號滑桿已移至咖啡豆詳情頁
        # （bean.html，商品主區下方）→ 本頁不再需要 series_beans。

        # 2026-11-02（使用者指示）：首屏移植 popeyemagazine.jp/50interviews/ 旋轉字輪
        # → 字輪字（英文品名）／中心圖文（中文亮點＋去背圖）都改由本店咖啡提供。
        # 品項不足 10 筆時前端會自動重複排列補滿圓周（只影響密度，不改資料）。
        # 2026-11-02（使用者指示第二輪）：首屏字輪中心圖文加上連結 → 該咖啡的詳情頁
        # （url 於前端換品項時同步換 href，見 static/js/bc-popeye50.js 的 updateCenterLink）
        wheel_items = [
            {
                "word": coffee.name,
                "name": coffee.highlight or coffee.name,
                "image": coffee.get_index_image(),
                "url": reverse("coffee", kwargs={"product_id": coffee.id}),
            }
            for coffee in series_coffees
        ]

        # 2026-11-06（使用者指示）：首屏背景影片改「多支輪播」（見檔頭 MV_VIDEOS 說明）。
        # json_script 產出的 JSON 內無法執行 {% static %} → 在此先解析成絕對 URL；
        # 模板的第 0 層 <video> 與 JSON 共用同一份清單，避免兩處各寫一次檔名。
        mv_videos = [
            {
                key: _mv_versioned_static(item[key])
                for key in ("webm", "mp4", "poster")
                if item.get(key)
            }
            for item in MV_VIDEOS
        ]

        context = {
            "cart": cart,  # keep cart count fn
            "series_coffees": series_coffees,
            # 2026-11-04（使用者指示）：首屏產品列只放 5 張（排除 MV_EXCLUDE_IDS）；
            # 下方 SERIES 括號滑桿與字輪仍用 series_coffees 的完整 6 筆。
            "mv_coffees": mv_coffees,
            "wheel_items": wheel_items,
            # 2026-10-08：loogg.jp「.top_art」sticky 堆疊卡片模組自 index.html 移至本頁
            # （置於 .bc-fujiya-photo 區塊正下方）。內容與動畫參數不變，
            # 與 landing context 共用同一個 builder。
            "top_art_cards": _build_top_art_cards(),
            # 2026-10-25（使用者指示）：.bc-search 大區塊自 index.html 移至本頁
            # （插在兩段 SERIES 滑桿之後）。背景浮動圖沿用首頁同一組咖啡豆
            # （BeanItem id 7／6，見 _build_landing_context），取不到時模板會
            # fallback 成 static/images/search_img01/02.png。
            "search_bean_01": BeanItem.objects.filter(pk=7).first(),
            "search_bean_02": BeanItem.objects.filter(pk=6).first(),
            # 2026-11-06：首屏背景影片多層輪播（第 0 層由模板渲染，其餘由 JS 依洗牌補上）
            "mv_videos": mv_videos,
            "mv_max": MV_MAX,
        }
        return render(request, "betweencoffee_delivery/about.html", context)


# ItemInCart 已移除（未使用，無路由引用）
