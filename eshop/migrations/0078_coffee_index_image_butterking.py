"""首頁 Butter King 圓圈圖補上（#10 image_index）＋ 4 張 index 圖更新（2026-09-30）

承 0077（咖啡商品圖全面換新）留下的 TODO_INDEX：

1. #10 Butter King 的 image_index 由 "" 補為 `coffee_images/butterking_index.png`
   —— 0077 當時該檔不存在（newimg/ 與專案內皆無），首頁 hero 手套圓圈第 2 格
   （sort_order 2）只能 fallback 到 `image`＝butterking_detail.png。
   現使用者已補檔：840×1200 RGBA，與其他 `*_index.png` 同規格。

2. 使用者同日（2026-09-30 17:26）重新匯出 4 張**同檔名**既有 index 圖：
   blackblend_index.png / friuty_index.png / matchamix_index.png / sunshine_index.png
   → DB 路徑不變，故**不需 migration**，僅圖檔內容更新（已一併入版控）。
   此處僅記錄，未做任何欄位變更。

範圍：僅 #10 的 `image_index`（首頁 hero 圓圈／商品卡）。`image`（詳情頁）不動。
比對方式：先以 (pk, name) 精準比對，找不到再以 name 比對。
可重入：值已是新值即跳過；若已被人為改成其他圖則不覆寫。
回滾：還原為 ""（＝回到 0077 後的 fallback 行為）。
"""

from django.db import migrations

# (pk, name, 原 image_index, 新 image_index)
INDEX_TARGETS = [
    (10, "Butter King", "", "coffee_images/butterking_index.png"),
]


def _find(CoffeeItem, pk, name):
    return CoffeeItem.objects.filter(pk=pk, name=name).first() or CoffeeItem.objects.filter(
        name=name
    ).first()


def _current(item, field_name):
    """目前欄位的路徑字串（ImageFieldFile → .name；空值 → ""）"""
    field = getattr(item, field_name)
    return (getattr(field, "name", "") or "") if field else ""


def _apply(apps, field_name, targets):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in targets:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        current = _current(item, field_name)
        if current == new:
            continue  # 已套用（可重入）
        if current not in ("", old):
            continue  # 已被改成其他圖 → 不覆寫
        setattr(item, field_name, new)
        item.save(update_fields=[field_name])


def _restore(apps, field_name, targets):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in targets:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        if _current(item, field_name) == new:
            setattr(item, field_name, old)
            item.save(update_fields=[field_name])


def update_images(apps, schema_editor):
    _apply(apps, "image_index", INDEX_TARGETS)


def restore_images(apps, schema_editor):
    _restore(apps, "image_index", INDEX_TARGETS)


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0077_coffee_detail_images_and_hero_index_images"),
    ]

    operations = [
        migrations.RunPython(update_images, restore_images),
    ]
