"""咖啡豆自訂選項組：產地正規化（2026-09-18）

BeanItem.origin 由自由文字改為自訂選項組「產地」的 preset 值
（定義見 eshop/models/option_definitions.py 的 ORIGIN_CHOICES）。

既有資料為自由文字，若不轉成代碼：
  - Admin 的下拉會選不中（顯示空白）
  - 詳情頁選項組取不到中文標籤（只會原樣輸出）

規則：
  1. 空白 → 不動
  2. 已是代碼（ET/JP/CO/...）→ 不動（可重入）
  3. 已知國名（含常見別名）→ 對應代碼
  4. 其他（例如拼配描述「埃塞俄比亞 拼配 巴西」）→ "OT"，原文保留到 origin_custom（零資料損失）

新選項組欄位（option_origin / option_grinding_level / option_roast_level 與其排序）由
模型 default 帶入，不需在此處理：產地與研磨預設啟用、烘焙度預設關閉。
"""

from django.db import migrations

# 自由文字 → 代碼（含常見別名／簡繁差異）
ORIGIN_TEXT_TO_CODE = {
    "埃塞俄比亞": "ET",
    "衣索比亞": "ET",
    "埃塞俄比亚": "ET",
    "日本": "JP",
    "哥倫比亞": "CO",
    "哥伦比亚": "CO",
    "巴西": "BR",
    "危地馬拉": "GT",
    "瓜地馬拉": "GT",
    "哥斯大黎加": "CR",
    "哥斯達黎加": "CR",
    "肯亞": "KE",
    "肯尼亞": "KE",
    "印尼": "ID",
    "印度尼西亞": "ID",
    "秘魯": "PE",
    "秘鲁": "PE",
    "巴拿馬": "PA",
    "巴拿马": "PA",
    "盧安達": "RW",
    "卢旺达": "RW",
    "宏都拉斯": "HN",
    "洪都拉斯": "HN",
    "台灣": "TW",
    "台湾": "TW",
    "雲南": "CN-YN",
    "云南": "CN-YN",
}

# 已是代碼者（避免重複轉換）
ORIGIN_CODES = {
    "ET", "JP", "CO", "BR", "GT", "CR", "KE", "ID", "PE", "PA", "RW", "HN", "TW", "CN-YN", "OT",
}


def normalize_origin(apps, schema_editor):
    BeanItem = apps.get_model("eshop", "BeanItem")
    for bean in BeanItem.objects.all():
        raw = (bean.origin or "").strip()
        if not raw:
            continue
        if raw in ORIGIN_CODES:
            continue  # 已是代碼（可重入）
        code = ORIGIN_TEXT_TO_CODE.get(raw)
        if code:
            bean.origin = code
            bean.origin_custom = ""
        else:
            # 拼配描述等無法對應單一產國 → 其他（自填），原文保留
            bean.origin = "OT"
            bean.origin_custom = raw[:50]
        bean.save(update_fields=["origin", "origin_custom"])


def restore_origin_text(apps, schema_editor):
    """回滾：把「其他（自填）」的原文寫回 origin（僅還原此遷移造成的改動）"""
    BeanItem = apps.get_model("eshop", "BeanItem")
    for bean in BeanItem.objects.filter(origin="OT").exclude(origin_custom=""):
        bean.origin = bean.origin_custom
        bean.origin_custom = ""
        bean.save(update_fields=["origin", "origin_custom"])


class Migration(migrations.Migration):

    dependencies = [
        ("eshop", "0071_beanitem_option_groups"),
    ]

    operations = [
        migrations.RunPython(normalize_origin, restore_origin_text),
    ]
