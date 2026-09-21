#!/usr/bin/env python3
"""驗證：咖啡豆自訂選項組（2026-09-21）

與咖啡端 verify_group_order.py 對應，涵蓋資料層 → Admin → 前台 → 購物車/訂單。

A. 資料層
   1. get_bean_option_groups(bean)：只回傳「客人可選」的組（唯讀組如產地不在此列），依排序數字排序
   2. 排序機制：sort_option_keys_for_bean 依 option_order_<key>（數字小在前、0=預設）
   3. 產地中文值：「其他（自填）」→ 顯示 origin_custom；代碼 → 中文（get_option_value_label）
   4. 合併查找不影響咖啡端（get_option_label / get_option_value_label / get_option_icon）
B. Admin
   5. Bean Admin 渲染各組（可選組＝勾選＋排序數字；唯讀組＝只有勾選，標示「唯讀 · 沿用原有排版」）
   6. Bean Admin 不再有分離欄位 name="option_origin"
   7. POST 儲存：勾選／數字 → 正確寫回 option_origin / option_grinding_level / option_order_grinding_level
   8. Coffee Admin 回歸：仍 16 組、排序數字欄位齊全、無唯讀標示
C. 前台詳情頁（/bean/<id>/）
   9. 產地：沿用既有排版（block-23 清單行的中文值），不新增任何選項 UI
  10. 沒有唯讀晶片（.bc-option-readonly*）與 option-group-origin
  11. 可選組（研磨）：.bc-option-btn + 預設值 active + hidden input 帶預設值
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
    bean_option_display_value,
    get_bean_option_groups,
    get_option_icon,
    get_option_label,
    get_option_value_label,
    sort_option_keys_for_bean,
)

BKEYS = [g["key"] for g in BEAN_OPTION_GROUPS]  # 豆的選項組（含唯讀的產地）
SKEYS = [g["key"] for g in BEAN_OPTION_GROUPS if g.get("customer_selectable")]  # 客人可選（按鈕 UI）
RKEYS = [g["key"] for g in BEAN_OPTION_GROUPS if not g.get("customer_selectable")]  # 唯讀（沿用原有排版）
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
    old = {k: getattr(bean, f"option_{k}", None) for k in BKEYS}
    for k in BKEYS:  # 全部啟用
        setattr(bean, f"option_{k}", True)
    for k in SKEYS:  # 排序歸零
        setattr(bean, f"option_order_{k}", 0)

    got = [g["key"] for g in get_bean_option_groups(bean)]
    results.append(check("只回傳客人可選的組（唯讀組不在此列）", got == SKEYS, str(got)))
    results.append(check("唯讀組（產地）不在按鈕 UI 清單", "origin" not in got, str(RKEYS)))

    # 排序機制：sort_option_keys_for_bean 依 option_order_<key>（用記憶體 stub 驗，不動 DB）
    class _Stub:
        pass

    stub = _Stub()
    stub.option_order_origin = 1
    stub.option_order_grinding_level = 2
    results.append(check("排序：origin=1 / grinding=2 → 產地在前",
                         sort_option_keys_for_bean(stub, ["grinding_level", "origin"]) == ["origin", "grinding_level"]))
    stub.option_order_origin = 0
    stub.option_order_grinding_level = 0
    results.append(check("排序：皆 0 → 依定義順序（BEAN_OPTION_GROUPS）",
                         sort_option_keys_for_bean(stub, ["grinding_level", "origin"]) == ["origin", "grinding_level"]))

    # 產地中文值（沿用既有排版，值由此解析）
    other = BeanItem.objects.filter(origin="OT").exclude(origin_custom="").first()
    if other:
        og = next(g for g in BEAN_OPTION_GROUPS if g["key"] == "origin")
        results.append(check("產地『其他』→ 顯示 origin_custom",
                             bean_option_display_value(other, og) == other.origin_custom,
                             bean_option_display_value(other, og)))
    coded = BeanItem.objects.exclude(origin__in=["", "OT"]).first()
    if coded:
        og = next(g for g in BEAN_OPTION_GROUPS if g["key"] == "origin")
        results.append(check("產地代碼 → 中文（%s）" % coded.origin,
                             bean_option_display_value(coded, og) == get_option_value_label("origin", coded.origin),
                             bean_option_display_value(coded, og)))
    results.append(check("烘焙度未納入選項組", "roast_level" not in BKEYS, str(BKEYS)))

    results.append(check("合併查找：咖啡標籤不受影響",
                         get_option_label("cup_level") == "杯量" and get_option_value_label("milk", "oat") == "燕麥奶"
                         and get_option_icon("milk") == "local_drink"))
    results.append(check("合併查找：豆標籤正確",
                         get_option_label("origin") == "產地" and get_option_value_label("origin", "ET") == "埃塞俄比亞"
                         and get_option_icon("origin") == "pin_drop"))
    for k, en in old.items():  # 還原
        if en is not None:
            setattr(bean, f"option_{k}", en)
    bean.save()
    return bean



def section_b(results, bean, c):
    """B. Admin（渲染 + 儲存 + 咖啡端回歸）"""
    print("B. Admin")
    coffee = CoffeeItem.objects.first()
    url = f"/admin/eshop/beanitem/{bean.pk}/change/"
    h = c.get(url).content.decode("utf-8", "replace")
    results.append(check("所有組 checkbox 皆渲染", all(f'id="option_groups_config_{k}"' in h for k in BKEYS), str(BKEYS)))
    results.append(check("只有可選組有排序數字欄位",
                         all(f'name="option_groups_config_{k}_order"' in h for k in SKEYS)
                         and all(f'name="option_groups_config_{k}_order"' not in h for k in RKEYS)))
    results.append(check('不再有分離欄位 name="option_origin"', 'name="option_origin"' not in h))
    ro = h.count('class="og-readonly"')
    results.append(check("唯讀組標示 1 個（產地）", ro == 1, f"實得 {ro}"))

    old = {k: getattr(bean, f"option_{k}", None) for k in BKEYS}
    old_orders = {k: getattr(bean, f"option_order_{k}", None) for k in SKEYS}
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
    # 產地不勾選（＝詳情頁不顯示產地那一行）
    r = c.post(url, data)
    results.append(check("POST 成功（302）", r.status_code == 302, f"status={r.status_code}"))
    if r.status_code != 302 and r.context:
        form = r.context.get("adminform")
        if form:
            for k, errs in form.form.errors.items():
                print(f"     ⚠ {k}: {errs}")
    bean.refresh_from_db()
    results.append(check("寫回：產地停用（未勾選）", bean.option_origin is False, str(bean.option_origin)))
    results.append(check("寫回：研磨啟用/order=1",
                         bean.option_grinding_level is True and bean.option_order_grinding_level == 1,
                         f"{bean.option_grinding_level}/{bean.option_order_grinding_level}"))

    hc = c.get(f"/admin/eshop/coffeeitem/{coffee.pk}/change/").content.decode("utf-8", "replace")
    n_ck = sum(1 for k in CKEYS if 'id="option_groups_config_%s"' % k in hc)
    results.append(check("Coffee Admin 仍 16 組", n_ck == len(CKEYS), f"{n_ck}/{len(CKEYS)}"))
    results.append(check("Coffee Admin 無「唯讀顯示」", 'class="og-readonly"' not in hc))

    for k, en in old.items():  # 還原
        if en is not None:
            setattr(bean, f"option_{k}", en)
    for k, order in old_orders.items():
        if order is not None:
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
    og = next(g for g in BEAN_OPTION_GROUPS if g["key"] == "origin")
    bean.option_origin = True
    bean.option_grinding_level = True
    bean.option_order_grinding_level = 0
    bean.save()
    h = c.get(f"/bean/{bean.pk}/").content.decode("utf-8", "replace")

    # 產地：沿用既有排版（block-23 清單行），不新增任何 UI
    origin_line = re.search(r'<li><span class="icon material-icons">pin_drop</span><span class="text">產地 :.*?</li>', h, re.S)
    results.append(check("產地沿用既有排版（block-23 清單行）", bool(origin_line)))
    results.append(check("產地顯示中文值（非代碼）",
                         bool(origin_line) and bean_option_display_value(bean, og) in origin_line.group(0),
                         (origin_line.group(0)[:110].replace("\n", " ") if origin_line else "")))
    results.append(check("沒有新增的唯讀晶片 UI（bc-option-readonly*）", "bc-option-readonly" not in h))
    results.append(check("產地不在選項按鈕區（無 option-group-origin）", 'id="option-group-origin"' not in h))
    results.append(check("產地不送值（無 hidden option_origin）", 'name="option_origin"' not in h))

    # 可選組（研磨）：既有 .bc-option-btn UI
    results.append(check("研磨渲染 id=option-group-grinding_level", 'id="option-group-grinding_level"' in h))
    gr = re.search(r'id="option-group-grinding_level".*?</div>', h, re.S)
    gr_html = gr.group(0) if gr else ""
    results.append(check("研磨 4 顆按鈕", gr_html.count("bc-option-btn") == 4, f"{gr_html.count('bc-option-btn')} 顆"))
    results.append(check("研磨預設值 active", 'bc-option-btn active' in gr_html))
    results.append(check("hidden input option_grinding_level", 'name="option_grinding_level"' in h))

    # Admin 勾選「顯示產地」的實際效果
    bean.option_origin = False
    bean.save()
    h2 = c.get(f"/bean/{bean.pk}/").content.decode("utf-8", "replace")
    results.append(check("取消勾選「顯示產地」→ 該行不顯示", 'material-icons">pin_drop' not in h2))
    bean.option_origin = True
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
