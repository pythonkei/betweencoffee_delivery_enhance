#!/usr/bin/env python3
"""驗證：咖啡豆自訂選項組（2026-09-21）

與咖啡端 verify_group_order.py 對應，涵蓋資料層 → Admin → 前台 → 購物車/訂單。

A. 資料層
   1. get_bean_option_groups(bean)：啟用組 + 依 option_order_<key> 排序（0=預設順序）
   2. 唯讀組無值時不渲染（空產地不顯示空殼）
   3. 產地「其他（自填）」→ 顯示 origin_custom
   4. 合併查找不影響咖啡端（get_option_label / get_option_value_label / get_option_icon）
B. Admin
   5. Bean Admin 渲染 3 組「勾選 + 排序數字」；唯讀組標示「唯讀顯示」
   6. Bean Admin 不再有分離欄位 name="option_origin"
   7. POST 儲存：勾選 + 數字 → 正確寫回 6 個 option_* / option_order_* 欄位
   8. Coffee Admin 回歸：仍 16 組、無「唯讀顯示」標示
C. 前台詳情頁（/bean/<id>/）
   9. 每組渲染 id="option-group-<key>"（與咖啡同一組 class/標記）
  10. 唯讀組：顯示值、不渲染 .bc-option-btn、不送 hidden input
  11. 可選組：渲染 .bc-option-btn、預設值 active、hidden input 帶預設值
D. 購物車 / 訂單
  12. add_to_cart：只收「客人可選」的組進 extra_options（唯讀組不入庫）
  13. CartItem.options_json / grinding_level 同步寫入
  14. 訂單顯示：extra_options_cn + options_display（bean 中文標籤正確）
  15. 舊訂單相容：只有 grinding_level 的 bean item 仍顯示「研磨: ...」

用法：python3 docs/verify/verify_bean_group_order.py
"""
import os
import sys

import django

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "betweencoffee_delivery.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import models
from django.test import Client

from eshop.models import BeanItem, CoffeeItem
from eshop.models.option_definitions import (
    BEAN_OPTION_GROUPS,
    OPTION_GROUPS,
    get_bean_option_groups,
    get_option_icon,
    get_option_label,
    get_option_value_label,
)

BKEYS = [g["key"] for g in BEAN_OPTION_GROUPS]
CKEYS = [g["key"] for g in OPTION_GROUPS]


def check(label, ok, detail=""):
    print(f"  {'✓' if ok else '✗'} {label}" + (f"  ({detail})" if detail else ""))
    return ok


def admin_user():
    U = get_user_model()
    user = U.objects.filter(is_superuser=True).first()
    if not user:
        user = U.objects.create_superuser("verify_tmp", "verify@example.com", "verify-tmp-pass")
    return user


def section_a(results):
    """A. 資料層"""
    print("A. 資料層")
    bean = BeanItem.objects.filter(origin__in=["CO", "ET", "JP"]).order_by("id").first() or BeanItem.objects.order_by("id").first()
    old = {k: (getattr(bean, f"option_{k}"), getattr(bean, f"option_order_{k}")) for k in BKEYS}
    for k in BKEYS:  # 全部啟用、順序歸零
        setattr(bean, f"option_{k}", True)
        setattr(bean, f"option_order_{k}", 0)
    default_order = [g["key"] for g in BEAN_OPTION_GROUPS]
    got = [g["key"] for g in get_bean_option_groups(bean)]
    results.append(check("全 0 → BEAN_OPTION_GROUPS 順序", got == default_order, str(got)))

    bean.option_order_grinding_level = 1
    got2 = [g["key"] for g in get_bean_option_groups(bean)]
    results.append(check("研磨 order=1 → 排到最前", got2[0] == "grinding_level", str(got2)))
    bean.option_order_grinding_level = 0

    empty_bean = BeanItem.objects.filter(origin="").first()
    if empty_bean:
        keys = [g["key"] for g in get_bean_option_groups(empty_bean)]
        results.append(check("唯讀無值組不渲染（空產地）", "origin" not in keys, str(keys)))
    other = BeanItem.objects.filter(origin="OT").exclude(origin_custom="").first()
    if other:
        g = [x for x in get_bean_option_groups(other) if x["key"] == "origin"]
        results.append(check("產地『其他』→ 顯示 origin_custom", bool(g) and g[0]["display_value"] == other.origin_custom,
                             f"{g[0]['display_value'] if g else '-'}"))

    results.append(check("合併查找：咖啡標籤不受影響",
                         get_option_label("cup_level") == "杯量" and get_option_value_label("milk", "oat") == "燕麥奶"
                         and get_option_icon("milk") == "local_drink"))
    results.append(check("合併查找：豆標籤正確",
                         get_option_label("origin") == "產地" and get_option_value_label("origin", "ET") == "埃塞俄比亞"
                         and get_option_icon("origin") == "pin_drop"))
    for k, (en, order) in old.items():  # 還原
        setattr(bean, f"option_{k}", en)
        setattr(bean, f"option_order_{k}", order)
    bean.save()
    return bean



def section_b(results, bean, c):
    """B. Admin（渲染 + 儲存 + 咖啡端回歸）"""
    print("B. Admin")
    coffee = CoffeeItem.objects.first()
    url = f"/admin/eshop/beanitem/{bean.pk}/change/"
    h = c.get(url).content.decode("utf-8", "replace")
    results.append(check("3 組 checkbox 皆渲染", all(f'id="option_groups_config_{k}"' in h for k in BKEYS), str(BKEYS)))
    results.append(check("3 組排序數字欄位皆渲染", all(f'name="option_groups_config_{k}_order"' in h for k in BKEYS)))
    results.append(check('不再有分離欄位 name="option_origin"', 'name="option_origin"' not in h))
    ro = h.count('class="og-readonly"')
    results.append(check("唯讀標示數 = 2（產地/烘焙度）", ro == 2, f"實得 {ro}"))

    old = {k: (getattr(bean, f"option_{k}"), getattr(bean, f"option_order_{k}")) for k in BKEYS}
    data = {}
    for f in BeanItem._meta.fields:
        if not f.editable or f.name == "id":
            continue
        # 檔案欄位不可用字串帶入（admin 的 ClearableFileInput 未上傳時沿用實例檔案）
        if isinstance(f, models.FileField) or isinstance(f, models.DateTimeField):
            continue
        if isinstance(f, models.ForeignKey):
            fid = getattr(bean, f.attname)
            if fid in (None, ""):
                continue
            data[f.name] = str(fid)
            continue
        v = getattr(bean, f.name)
        if v in (None, ""):
            continue
        data[f.name] = str(v)
    data["option_groups_config_grinding_level"] = "on"
    data["option_groups_config_grinding_level_order"] = "1"
    data["option_groups_config_roast_level"] = "on"
    data["option_groups_config_roast_level_order"] = "0"
    data["option_groups_config_origin_order"] = "3"
    r = c.post(url, data)
    results.append(check("POST 成功（302）", r.status_code == 302, f"status={r.status_code}"))
    if r.status_code != 302 and r.context:
        form = r.context.get("adminform")
        if form:
            for k, errs in form.form.errors.items():
                print(f"     ⚠ {k}: {errs}")
    bean.refresh_from_db()
    results.append(check("寫回：產地停用/order=3", bean.option_origin is False and bean.option_order_origin == 3,
                         f"{bean.option_origin}/{bean.option_order_origin}"))
    results.append(check("寫回：研磨啟用/order=1",
                         bean.option_grinding_level is True and bean.option_order_grinding_level == 1,
                         f"{bean.option_grinding_level}/{bean.option_order_grinding_level}"))
    results.append(check("寫回：烘焙度啟用/order=0",
                         bean.option_roast_level is True and bean.option_order_roast_level == 0,
                         f"{bean.option_roast_level}/{bean.option_order_roast_level}"))

    hc = c.get(f"/admin/eshop/coffeeitem/{coffee.pk}/change/").content.decode("utf-8", "replace")
    n_ck = sum(1 for k in CKEYS if 'id="option_groups_config_%s"' % k in hc)
    results.append(check("Coffee Admin 仍 16 組", n_ck == len(CKEYS), f"{n_ck}/{len(CKEYS)}"))
    results.append(check("Coffee Admin 無「唯讀顯示」", 'class="og-readonly"' not in hc))

    for k, (en, order) in old.items():  # 還原
        setattr(bean, f"option_{k}", en)
        setattr(bean, f"option_order_{k}", order)
    bean.save()
    bean.refresh_from_db()
    return bean


def section_cd(results, bean, c):
    """C. 前台詳情頁 + D. 購物車/訂單"""
    import re

    from django.urls import reverse

    from eshop.models import OrderModel

    print("C. 前台詳情頁 /bean/%s/" % bean.pk)
    bean.option_origin, bean.option_grinding_level, bean.option_roast_level = True, True, False
    bean.option_order_origin = bean.option_order_grinding_level = 0
    bean.save()
    h = c.get(f"/bean/{bean.pk}/").content.decode("utf-8", "replace")
    results.append(check("唯讀組渲染 id=option-group-origin", 'id="option-group-origin"' in h))
    results.append(check("可選組渲染 id=option-group-grinding_level", 'id="option-group-grinding_level"' in h))
    results.append(check("未啟用組（烘焙度）不渲染", 'id="option-group-roast_level"' not in h))
    ro = re.search(r'id="option-group-origin".*?</div>', h, re.S)
    ro_html = ro.group(0) if ro else ""
    results.append(check("唯讀組標記 bc-option-readonly-value", "bc-option-readonly-value" in ro_html))
    results.append(check("唯讀組不含按鈕（客人不能選）", "bc-option-btn" not in ro_html))
    results.append(check("唯讀組不送值", 'name="option_origin"' not in h))
    results.append(check("唯讀組顯示中文值", "哥倫比亞" in ro_html or "埃塞俄比亞" in ro_html))
    gr = re.search(r'id="option-group-grinding_level".*?</div>', h, re.S)
    gr_html = gr.group(0) if gr else ""
    results.append(check("可選組 4 顆按鈕", gr_html.count("bc-option-btn") == 4, f"{gr_html.count('bc-option-btn')} 顆"))
    results.append(check("研磨預設值 active", 'bc-option-btn active' in gr_html))
    results.append(check("hidden input option_grinding_level", 'name="option_grinding_level"' in h))

    bean.option_order_grinding_level = 1
    bean.save()
    order = re.findall(r'id="option-group-([a-z_]+)"', c.get(f"/bean/{bean.pk}/").content.decode("utf-8", "replace"))
    results.append(check("排序：研磨 order=1 → 排最前", order == ["grinding_level", "origin"], str(order)))
    bean.option_order_grinding_level = 0
    bean.save()

    print("D. 購物車 / 訂單")
    r = c.post(reverse("cart:add_to_cart", args=[bean.pk, "bean"]),
               {"option_grinding_level": "Deep", "weight": "500g", "quantity": "2"})
    cart = c.session.get("cart") or {}
    item = list(cart.values())[0] if cart else {}
    results.append(check("加入購物車成功", r.status_code == 200 and bool(item), f"status={r.status_code}"))
    results.append(check("extra_options 只含可選組", item.get("extra_options") == {"grinding_level": "Deep"},
                         str(item.get("extra_options"))))
    results.append(check("唯讀組（產地）未進購物車", "origin" not in (item.get("extra_options") or {})))
    results.append(check("舊欄位同步 grinding_level", item.get("grinding_level") == "Deep"))

    j = c.get(reverse("cart:cart_count")).json()
    it = (j.get("items") or [{}])[0]
    results.append(check("cart_count extra_options_cn 研磨=粗研磨",
                         (it.get("extra_options_cn") or {}).get("grinding_level") == "粗研磨",
                         str(it.get("extra_options_cn"))))
    results.append(check("cart_count 附 icons/labels",
                         (it.get("extra_options_icons") or {}).get("grinding_level") == "roller_shades"
                         and (it.get("extra_options_labels") or {}).get("grinding_level") == "研磨"))

    results.append(check("translate_option 標籤統一（Deep→粗研磨）",
                         OrderModel.translate_option("grinding_level", "Deep") == "粗研磨"))
    new_order = OrderModel(items=[{"type": "bean", "id": bean.pk, "name": bean.name, "price": 100,
                                   "quantity": 1, "weight": "500g", "grinding_level": "Deep",
                                   "extra_options": {"grinding_level": "Deep"}}])
    d_new = new_order.get_order_display_items()[0]
    results.append(check("新訂單：extra_options_cn 研磨=粗研磨",
                         (d_new.get("extra_options_cn") or {}).get("grinding_level") == "粗研磨"))
    results.append(check("新訂單：不再另存 grinding_level_cn（不重複）", "grinding_level_cn" not in d_new))
    od = d_new.get("options_display", "")
    chips = od.count('class="option-item"')
    results.append(check("新訂單：options_display 為 bc-options-row", 'class="bc-options-row"' in od))
    results.append(check("新訂單：晶片數=2（研磨+重量）", chips == 2, f"{chips} 個"))
    old_order = OrderModel(items=[{"type": "bean", "id": bean.pk, "name": bean.name, "price": 100,
                                   "quantity": 1, "weight": "200g", "grinding_level": "Medium"}])
    d_old = old_order.get_order_display_items()[0]
    results.append(check("舊訂單相容：grinding_level_cn=中研磨", d_old.get("grinding_level_cn") == "中研磨"))
    results.append(check("舊訂單相容：options_display 含研磨", "研磨" in d_old.get("options_display", "")))

    print("E. 觸及的模板編譯")
    from django.template.loader import get_template

    for tpl in [
        "eshop/order_confirm.html", "eshop/fps_payment.html", "eshop/cash_payment.html",
        "eshop/order_payment_confirmation.html", "socialuser/order_history.html",
        "cart/checkout.html", "betweencoffee_delivery/bean.html", "betweencoffee_delivery/coffee.html",
    ]:
        try:
            get_template(tpl)
            results.append(check(f"編譯 {tpl}", True))
        except Exception as e:  # noqa: BLE001
            results.append(check(f"編譯 {tpl}", False, str(e)[:80]))


def main():
    results = []
    c = Client(HTTP_HOST="localhost:8081")
    c.force_login(admin_user())
    bean = section_a(results)
    section_b(results, bean, c)
    section_cd(results, bean, c)
    print(f"\n結果：{sum(1 for r in results if r)}/{len(results)} 通過")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
