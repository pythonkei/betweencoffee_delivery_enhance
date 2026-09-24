"""首頁商品圖更新：Sunshine 首頁圖改為 v2（2026-09-24）

使用者指示（bc-yama／首頁 index 內商品圖）：sunshine.png → sunshine+v2.png
＝實際檔案 static/images/sunshine_v2.png（同日 12:14 上傳，已複製到
media/coffee_images/index/sunshine_v2.png）。

範圍：
  - 只改 CoffeeItem.image_index（首頁專用圖）→ 不動 image（詳情頁／訂單快照用）。
  - 舊檔 coffee_images/index/sunshine.png 保留（既有訂單 items JSON 仍指向舊檔名，不會 404）。

比對方式：先以 (pk, name) 精準比對，找不到再以 name 比對（生產環境 id／命名不同也能套用）。
可重入：值已是新值即跳過；若已被人為改成其他圖則不覆寫。
"""

from django.db import migrations

# (pk, name, 原 image_index, 新 image_index)
TARGETS = [
    (2, "Sunshine", "coffee_images/index/sunshine.png", "coffee_images/index/sunshine_v2.png"),
]


def _find(CoffeeItem, pk, name):
    return CoffeeItem.objects.filter(pk=pk, name=name).first() or CoffeeItem.objects.filter(
        name=name
    ).first()


def _current(item):
    """目前 image_index 的路徑字串（ImageFieldFile → .name；空值 → ""）"""
    field = item.image_index
    return (getattr(field, "name", "") or "") if field else ""


def update_index_images(apps, schema_editor):
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
        item.image_index = new
        item.save(update_fields=["image_index"])


def restore_index_images(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in TARGETS:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        if _current(item) == new:
            item.image_index = old
            item.save(update_fields=["image_index"])


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0074_update_coffee_index_images"),
    ]

    operations = [
        migrations.RunPython(update_index_images, restore_index_images),
    ]
