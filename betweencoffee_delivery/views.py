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

from django.db.models import Q

# betweencoffee_delivery/views.py
from django.shortcuts import get_object_or_404, render
from django.views import View

from cart.cart import Cart  # Import the Cart class
from eshop.models import BeanItem, CoffeeItem


# 處理index, about HTTP 請求所發生的情況
# 當使用者向伺服器發送 GET 請求時渲染 HTML template模板
class Index(View):
    def get(self, request, *args, **kwargs):
        shop_hot_coffees = CoffeeItem.objects.filter(
            is_shop_hot_item=True, is_published=True
        )[:4]

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
    )[:4]
    all_coffees = CoffeeItem.objects.filter(is_published=True)[:9]
    beans = BeanItem.objects.filter(is_published=True)[:3]

    context = {
        "shop_hot_coffees": hot_coffees,
        "hot_coffees": hot_coffees,
        "all_coffees": all_coffees,
        "beans": beans,
        "is_authenticated": request.user.is_authenticated,
        "user_avatar": "",
        "last_order_image": "",
        "last_order_link": "",
    }

    if request.user.is_authenticated:
        context["user_avatar"] = _get_user_avatar(request.user)
        context["last_order_image"] = _get_last_order_image(request.user)
        context["last_order_link"] = _get_last_order_link(request.user)

    return context


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
                else:
                    for key in ("cup_level", "milk_level", "strength_level"):
                        val = item.get(key)
                        if val:
                            opts.append(f"{key}={val}")
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
        coffee_menu = CoffeeItem.objects.all()
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

        context = {
            "coffee": coffee,
            "cart": cart,  # Add the cart to the context
        }
        return render(request, "betweencoffee_delivery/coffee.html", context)


# List out bean item
class BeanMenu(View):
    def get(self, request, *args, **kwargs):
        bean_items = BeanItem.objects.all()
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

        context = {
            "bean": bean,
            "cart": cart,  # keep cart count fn
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
        )

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
        )

        context = {"search_items": search_items}
        return render(request, "betweencoffee_delivery/bean_menu.html", context)


class About(View):
    def get(self, request, *args, **kwargs):
        cart = Cart(request)  # Initialize the cart

        context = {
            "cart": cart,  # keep cart count fn
        }
        return render(request, "betweencoffee_delivery/about.html", context)


# ItemInCart 已移除（未使用，無路由引用）
