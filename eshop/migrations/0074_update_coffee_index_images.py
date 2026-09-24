"""首頁商品圖更名（2026-09-24）

使用者指示（首頁 index 內、bc-yama／hero 圓圈顯示的商品圖）：
  black_blend_4.png       → black_blend_v4.png（新圖，840×1200）
  coffee_07_1_ywGMC7S.png → friuty.png（新圖，840×1200）
  shunshine_kFPsy3b.png   → sunshine.png（與原圖同內容，840×1200）

範圍：
  - 只改 CoffeeItem.image_index（首頁專用圖）→ 不動 image（詳情頁／訂單快照用）。
  - #9 果香浅煎原本 image_index 留空 → 首頁 fallback 到 image（coffee_07_1_ywGMC7S.png），
    本遷移補上 image_index，首頁改顯示新的 840×1200 直式首頁圖。
  - 舊檔保留在 media/（既有訂單 items JSON 仍指向舊檔名，不會 404）。

對應檔案（須存在於 media/coffee_images/index/，已一併入版控）：
  black_blend_v4.png / friuty.png / sunshine.png

比對方式：先以 (pk, name) 精準比對，找不到再以 name 比對（生產環境 id／命名不同也能套用）。
可重入：值已是新值即跳過；若已被人為改成其他圖則不覆寫。
"""

from django.db import migrations

# (pk, name, 原 image_index, 新 image_index)
TARGETS = [
    (2, "Sunshine", "coffee_images/index/shunshine_kFPsy3b.png", "coffee_images/index/sunshine.png"),
    (4, "Black Blend", "coffee_images/index/black_blend_4.png", "coffee_images/index/black_blend_v4.png"),
    (9, "果香浅煎", "", "coffee_images/index/friuty.png"),
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
        ("eshop", "0073_beanitem_remove_unused_option_fields"),
    ]

    operations = [
        migrations.RunPython(update_index_images, restore_index_images),
    ]
