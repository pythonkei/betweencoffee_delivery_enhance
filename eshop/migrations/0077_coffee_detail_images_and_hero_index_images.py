"""咖啡商品圖全面換新：詳情頁 `image` + 首頁 hero 圓圈 `image_index`（2026-09-29）

使用者指示（新圖來源 ~/Downloads/newimg/，2026-09-29 15:00）：

1. 詳情頁（coffee.html，依商品 id）改用 `*_detail.png`：
     #4 Black Blend  → coffee_images/blackblend_detail.png
     #10 Butter King → coffee_images/butterking_detail.png
     #3 Flat White   → coffee_images/flatwhite_detail.png
     #9 果香浅煎      → coffee_images/friuty_detail.png
     #8 抹茉          → coffee_images/matchamix_detail.png
     #7 Nice Step    → coffee_images/nicestep_detail.png
     #2 Sunshine     → coffee_images/sunshine_detail.png
     #1 WakeMeUp     → coffee_images/wakemeup_detail.png

2. 首頁 index.html 的 hero 手套圓圈（`hero_coffees` = is_published 依
   `sort_order, id` 取前 7 筆 → .hero_hand_item 0~6，使用 get_index_image）
   的 7 張商品圖改用 `*_index.png`，排序即使用者指定：
     Black Blend(#4) → butterking(#10) → friuty(#9) → matchamix(#8)
     → flatwhite(#3) → sunshine(#2) → wakemeup(#1)
   （與目前 sort_order 1~7 完全一致，故不動 sort_order。）

檔案尺寸：`*_detail.png` = 860×1100（詳情頁滿版照片）、`*_index.png` = 840×1200
（首頁圓圈方圖），尺寸與既有同類圖一致。

檔名慣例：新圖沿用使用者放置位置＝media/coffee_images/ 下的扁平命名
（`<name>_detail.png` / `<name>_index.png`），與既有 `coffee_images/index/`
（舊 v2/v4 圖）並存；舊檔一律保留（既有訂單 items JSON 仍指向舊檔名，不會 404）。

**Butter King 首頁圖（#10 image_index）本次未設定**：`butterking_index.png`
在使用者提供的 newimg/ 與整個專案內都不存在（只有 butterking_detail.png）。
因此 #10 保持 image_index="" → `get_index_image()` 會自動 fallback 到剛更新的
`image`＝coffee_images/butterking_detail.png（仍是新版畫風，僅比例略異）。
待使用者補檔後另開一支 migration 補上即可（清單見下方 TODO_INDEX 註解）。

範圍：`image`（詳情頁／購物車／訂單快照）＋ `image_index`（首頁／商品卡）。
比對方式：先以 (pk, name) 精準比對，找不到再以 name 比對。
可重入：值已是新值即跳過；若已被人為改成其他圖則不覆寫。
"""

from django.db import migrations

# (pk, name, 原 image, 新 image)
DETAIL_TARGETS = [
    (4, "Black Blend", "coffee_images/coffee_02_1.png", "coffee_images/blackblend_detail.png"),
    (10, "Butter King", "coffee_images/coffee_09.png", "coffee_images/butterking_detail.png"),
    (9, "果香浅煎", "coffee_images/coffee_07_1_ywGMC7S.png", "coffee_images/friuty_detail.png"),
    (8, "抹茉", "coffee_images/coffee_06_1_zlHhb48.png", "coffee_images/matchamix_detail.png"),
    (3, "Flat White", "coffee_images/coffee_03_1.png", "coffee_images/flatwhite_detail.png"),
    (2, "Sunshine", "coffee_images/coffee_08_B0g2qHs.png", "coffee_images/sunshine_detail.png"),
    (1, "WakeMeup", "coffee_images/coffee_01_2.png", "coffee_images/wakemeup_detail.png"),
    (7, "Nice Step", "coffee_images/coffee_05_1_bcHDwCS.png", "coffee_images/nicestep_detail.png"),
]

# (pk, name, 原 image_index, 新 image_index)  ← 首頁 hero 圓圈 7 格（缺 #10，見 docstring）
INDEX_TARGETS = [
    (4, "Black Blend", "coffee_images/index/black_blend_v4.png", "coffee_images/blackblend_index.png"),
    (9, "果香浅煎", "coffee_images/index/friuty.png", "coffee_images/friuty_index.png"),
    (8, "抹茉", "", "coffee_images/matchamix_index.png"),
    (3, "Flat White", "coffee_images/index/flat_white_4.png", "coffee_images/flatwhite_index.png"),
    (2, "Sunshine", "coffee_images/index/sunshine_v2.png", "coffee_images/sunshine_index.png"),
    (1, "WakeMeup", "coffee_images/index/wakemeup_v2_2.png", "coffee_images/wakemeup_index.png"),
]

# TODO_INDEX：待 butterking_index.png 補上後新增 migration 套用
#   (10, "Butter King", "", "coffee_images/butterking_index.png")
# 另：nicestep_index.png 亦已提供，但 #7 Nice Step 為 sort_order 8（不在首頁 7 格內），
#      使用者未列入，故不動其 image_index（商品卡目前 fallback 到 image）。


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
    _apply(apps, "image", DETAIL_TARGETS)
    _apply(apps, "image_index", INDEX_TARGETS)


def restore_images(apps, schema_editor):
    _restore(apps, "image_index", INDEX_TARGETS)
    _restore(apps, "image", DETAIL_TARGETS)


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0076_coffee_detail_images_flatwhite_blackblend"),
    ]

    operations = [
        migrations.RunPython(update_images, restore_images),
    ]
