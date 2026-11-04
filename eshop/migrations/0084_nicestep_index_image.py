"""補上 #7 Nice Step 的 `image_index`（about 首屏產品列用圖一致化，2026-11-04）

背景（0077 的 TODO_INDEX 已註記）：
  0077 只把「首頁 hero 手套圓圈」那 7 格（sort_order 1~7）的 `image_index`
  換成 `*_index.png`；#7 Nice Step 是 sort_order 8（不在 hero 7 格內），
  因此 `image_index` 一直是 ""，`get_index_image()` 會 fallback 到
  `image`＝coffee_images/nicestep_detail.png。

問題（使用者回報「about 首屏 page-top__mv__product 這組間距跟別組不一樣」）：
  about 首屏產品列的 series_coffees 是 id__in=[1,2,3,4,7,8]（含 #7），
  卡片用 `get_index_image()`：
    · 其他 5 款 = `*_index.png`（840×1200，杯身約佔畫布寬 62~87%）
    · Nice Step  = `nicestep_detail.png`（860×1100，杯身佔畫布寬 80%，比例 0.782）
  兩者都放在同一個 3:4 的 `.p-image` 盒子裡 `object-fit: contain` →
  detail 版被放大約 4.6%（270→仍 270 寬但有效杯身寬 217px），
  其他 index 版杯身只有 154~218px（抹茉 154、Flat White 162、Nice Step index 156）。
  結果：Nice Step 那張的杯身比其他組大近 40%、上下留白也變少
  → 視覺上「這一組比較擠／間距跟別組不同」。

修法：把 #7 的 `image_index` 設成專為列表用的
  coffee_images/nicestep_index.png（840×1200，與其他 5 款同尺寸同畫布），
  杯身渲染寬度 156px，與抹茉（154）／Flat White（162）一致。

可重入：值已是新值即跳過；若已被人為改成其他圖則不覆寫。
回滾：reverse 把 image_index 還原成 ""（恢復 fallback 到 detail 的舊行為）。
"""

from django.db import migrations

# (pk, name, 原 image_index, 新 image_index)
INDEX_TARGETS = [
    (7, "Nice Step", "", "coffee_images/nicestep_index.png"),
]


def _find(CoffeeItem, pk, name):
    return (
        CoffeeItem.objects.filter(pk=pk, name=name).first()
        or CoffeeItem.objects.filter(name=name).first()
    )


def _current(item):
    """目前 image_index 的路徑字串（ImageFieldFile → .name；空值 → ""）"""
    field = getattr(item, "image_index")
    return (getattr(field, "name", "") or "") if field else ""


def apply_index(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in INDEX_TARGETS:
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


def restore_index(apps, schema_editor):
    CoffeeItem = apps.get_model("eshop", "CoffeeItem")
    for pk, name, old, new in INDEX_TARGETS:
        item = _find(CoffeeItem, pk, name)
        if not item:
            continue
        if _current(item) == new:
            item.image_index = old
            item.save(update_fields=["image_index"])


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0083_seed_bean_bubble_texts"),
    ]

    operations = [
        migrations.RunPython(apply_index, restore_index),
    ]
