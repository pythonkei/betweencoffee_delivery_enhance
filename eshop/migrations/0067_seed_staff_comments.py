"""種入咖啡詳情頁氣泡文字（2026-09-14）

原為 coffee.html 內 hardcode 的兩句文案 → 改為 CoffeeItem 欄位後在此種入：
  id=10（Butter King）：staff_comment_1 = 原 p-1 文案、staff_comment_3 = 原 p-3 文案
  staff_comment_2（新增的右下氣泡）＝ 佔位文案，待 Admin 逐款調整
僅寫入「目前為空」的欄位，不覆蓋 Admin 之後的編輯（可重複執行）。
"""

from django.db import migrations

SEED = {
    10: {
        "staff_comment_1": "配牛油香最對味",
        "staff_comment_2": "熱飲更顯層次",
        "staff_comment_3": "冰飲也很清爽",
    },
}


def seed_staff_comments(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, values in SEED.items():
        item = CoffeeItem.objects.filter(pk=pk).first()
        if not item:
            continue
        changed = [f for f in values if not getattr(item, f)]
        if changed:
            for f in changed:
                setattr(item, f, values[f])
            item.save(update_fields=changed)


def unseed_staff_comments(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, values in SEED.items():
        CoffeeItem.objects.filter(pk=pk).update(**{f: "" for f in values})


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0066_coffeeitem_staff_comment_1_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_staff_comments, unseed_staff_comments),
    ]
