"""預填各咖啡豆詳情頁的 3 顆氣泡文字（2026-10-24）

咖啡豆詳情頁氣泡上線時的初始文案（6 款 × 3 顆）。以「品名」比對而非 id：
本地與正式站曾發生 id 不一致，用品名較安全。
只寫入目前為空的欄位 → 員工之後在 Admin 改寫的內容不會被覆蓋；
reverse 也只清掉「本遷移寫入的那幾句」，不會誤刪人工文案。

字數：氣泡 1／2 建議 5~7 字、氣泡 3 建議 5~6 字（pattern 圖形固定寬度）。
"""

from django.db import migrations

# 品名（正規化後）→ (氣泡 1 左側, 氣泡 2 右下, 氣泡 3 右上)
SEED_COMMENTS = {
    "kenya": ("柑橘與花香", "蜂蜜般甜感", "香氣清爽明亮"),
    "rwanda nyarusiza": ("酸甜恰到平衡", "口感乾淨純淨", "日日新鮮烘焙"),
    "kingsman": ("香甜又多汁", "成熟櫻桃香", "果香濃郁迷人"),
    "brazil fazenda": ("品質與創意", "沉醉咖啡香", "處處是驚喜"),
    "sumatra kerinci": ("草本微苦回甘", "圓潤甜味綿長", "香氣如香水"),
    "colombia los": ("花香與果香", "蜂蜜葡萄乾", "柑橘檸檬香"),
}


def _key(name):
    return " ".join((name or "").split()).strip().lower()


def seed_bubble_texts(apps, schema_editor):
    BeanItem = apps.get_model("eshop", "BeanItem")
    for item in BeanItem.objects.all():
        seed = SEED_COMMENTS.get(_key(item.name))
        if not seed:
            continue
        changed = []
        for idx, text in enumerate(seed, start=1):
            field = f"staff_comment_{idx}"
            if not (getattr(item, field) or "").strip():
                setattr(item, field, text)
                changed.append(field)
        if changed:
            item.save(update_fields=changed)


def clear_bubble_texts(apps, schema_editor):
    BeanItem = apps.get_model("eshop", "BeanItem")
    for item in BeanItem.objects.all():
        seed = SEED_COMMENTS.get(_key(item.name))
        if not seed:
            continue
        changed = []
        for idx, text in enumerate(seed, start=1):
            field = f"staff_comment_{idx}"
            if (getattr(item, field) or "") == text:
                setattr(item, field, "")
                changed.append(field)
        if changed:
            item.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0082_fill_bean_bubble_geometry"),
    ]

    operations = [
        migrations.RunPython(seed_bubble_texts, clear_bubble_texts),
    ]
