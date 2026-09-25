"""咖啡詳情頁圖修正：Flat White／Black Blend（2026-09-25）

使用者回報「coffee 詳情頁顯示錯誤，顯示了首頁的圖片（/coffee/3/、/coffee/4/），
參考 /coffee/2/」＝這兩款的 `image`（詳情頁／購物車／訂單快照用）指向的檔案
其實與首頁圖（`image_index`）是同一張畫（像素比對差 4.9~5.3，肉眼相同）：

  #3 Flat White  image = coffee_images/flat_white.png          （840×1200，與 index/flat_white_4.png 同畫）
  #4 Black Blend image = coffee_images/black_blend_fRQ6OTF.png （1200×840，與 index/black_blend_4.png 同畫）

改為舊站滿版照片（860×1100，與 #2 Sunshine 的 coffee_08_B0g2qHs.png 同類、同畫風）：

  #3 Flat White  → coffee_images/coffee_03_1.png（紅杯紫底滿版；與本款首頁圖同設計）
  #4 Black Blend → coffee_images/coffee_02_1.png（黑杯滿版；與本款首頁圖同設計）

範圍：只改 `image`（詳情頁／購物車／訂單快照）；`image_index`（首頁圖）不動。
舊檔保留在 media/（既有訂單 items JSON 仍指向舊檔名，不會 404）。
比對方式：先以 (pk, name) 精準比對，找不到再以 name 比對。可重入、已被改成其他圖則不覆寫。
"""

from django.db import migrations

# (pk, name, 原 image, 新 image)
TARGETS = [
    (3, "Flat White", "coffee_images/flat_white.png", "coffee_images/coffee_03_1.png"),
    (4, "Black Blend", "coffee_images/black_blend_fRQ6OTF.png", "coffee_images/coffee_02_1.png"),
]


def _find(CoffeeItem, pk, name):
    return CoffeeItem.objects.filter(pk=pk, name=name).first() or CoffeeItem.objects.filter(
        name=name
    ).first()


def _current(item):
    """目前 image 的路徑字串（ImageFieldFile → .name；空值 → ""）"""
    field = item.image
    return (getattr(field, "name", "") or "") if field else ""


def update_detail_images(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in TARGETS:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        current = _current(item)
        if current == new:
            continue  # 已套用（可重入）
        if current not in ("", old):
            continue  # 已被改成其他圖 → 不覆寫
        item.image = new
        item.save(update_fields=["image"])


def restore_detail_images(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in TARGETS:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        if _current(item) == new:
            item.image = old
            item.save(update_fields=["image"])


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0075_coffee_index_image_sunshine_v2"),
    ]

    operations = [
        migrations.RunPython(update_detail_images, restore_detail_images),
    ]
