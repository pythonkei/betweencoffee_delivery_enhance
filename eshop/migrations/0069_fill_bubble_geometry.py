"""量測並填入各咖啡的氣泡定位幾何（2026-09-14）

新增 bubble_safe_left / bubble_safe_right / bubble_photo_ratio / bubble_scale 後，
既有資料需要初值（否則所有咖啡都用 CSS 預設的 860×1100 幾何）。
此遷移直接以 Pillow 量測每款咖啡的詳情照片：
  左右緣 = 去背 PNG 不透明區邊界（占照片寬 %）
  寬高比 = 寬 ÷ 高
  倍率   = min(1, 1/寬高比)（橫式照片自動縮小，避免氣泡相對照片過大）
只寫入目前為空的欄位（不覆蓋人工設定）；模型 save() 之後也會做同樣的事。
"""

from django.db import migrations


def fill_bubble_geometry(apps, schema_editor):
    from PIL import Image

    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for item in CoffeeItem.objects.all():
        if (
            item.bubble_safe_left is not None
            and item.bubble_safe_right is not None
            and item.bubble_photo_ratio is not None
            and item.bubble_scale is not None
        ):
            continue
        try:
            field_file = item.image
            if not (field_file and getattr(field_file, "name", "")):
                continue
            with Image.open(field_file.path) as im:
                width, height = im.size
                if not (width and height):
                    continue
                ratio = round(width / height, 3)
                left = right = None
                if im.mode in ("RGBA", "LA") or "transparency" in im.info:
                    box = im.convert("RGBA").getchannel("A").getbbox()
                    if box:
                        left = round(box[0] / width * 100, 2)
                        right = round(box[2] / width * 100, 2)
                scale = round(1 / ratio, 2) if ratio > 1 else 1.0
        except Exception:
            continue
        changed = []
        if item.bubble_photo_ratio is None:
            item.bubble_photo_ratio = ratio
            changed.append("bubble_photo_ratio")
        if item.bubble_scale is None:
            item.bubble_scale = scale
            changed.append("bubble_scale")
        if item.bubble_safe_left is None and left is not None:
            item.bubble_safe_left = left
            changed.append("bubble_safe_left")
        if item.bubble_safe_right is None and right is not None:
            item.bubble_safe_right = right
            changed.append("bubble_safe_right")
        if changed:
            item.save(update_fields=changed)


def clear_bubble_geometry(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    CoffeeItem.objects.all().update(
        bubble_safe_left=None,
        bubble_safe_right=None,
        bubble_photo_ratio=None,
        bubble_scale=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0068_coffeeitem_bubble_photo_ratio_and_more"),
    ]

    operations = [
        migrations.RunPython(fill_bubble_geometry, clear_bubble_geometry),
    ]
