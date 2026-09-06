"""全域 context processors（betweencoffee_delivery）

2026-09-06：提供 user_avatar 給所有模板（含全站 nav.html 的
.bc-attract-profile 圓鈕 → 登入後顯示 FB/Google 用戶頭像）。
頭像取法與 index view 相同（_get_user_avatar：socialaccount
picture/avatar/avatar_url，Facebook 補 Graph API URL），避免 views
模組頂層載入副作用，採函式內 lazy import。
"""


def user_avatar(request):
    ctx = {}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        try:
            from .views import _get_user_avatar

            ctx["user_avatar"] = _get_user_avatar(user)
        except Exception:
            ctx["user_avatar"] = ""
    return ctx
