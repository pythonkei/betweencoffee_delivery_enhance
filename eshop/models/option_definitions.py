# eshop/models/option_definitions.py
"""咖啡自訂選項組定義（2026-08-15）

每種咖啡在 Admin 勾選啟用哪些選項組；組內選項值全域固定。
詳情頁 / 購物車 / 訂單顯示共用此定義（key / label / icon / choices）。
"""

OPTION_GROUPS = [
    {
        "key": "cup_level",
        "label": "杯量",
        "icon": "water_full",
        "default": "Medium",
        "choices": [
            ("Small", "少", "12oz"),
            ("Medium", "正常", "16oz"),
            ("Large", "追加", "20oz"),
        ],
    },
    {
        "key": "strength_level",
        "label": "濃度",
        "icon": "bolt",
        "default": "Normal",
        "choices": [("Normal", "預設"), ("Extra", "特濃")],
    },
    {
        "key": "milk_level",
        "label": "奶量",
        "icon": "humidity_mid",
        "default": "Medium",
        "choices": [
            ("Light", "少"),
            ("Medium", "正常"),
            ("Extra", "追加"),
        ],
    },
    {
        "key": "milk",
        "label": "奶類",
        "icon": "local_drink",
        "default": "pure",
        "choices": [
            ("pure", "純牛奶"),
            ("oat", "燕麥奶"),
            ("almond", "杏仁奶"),
            ("skim", "無糖脫脂奶"),
        ],
    },
    {
        "key": "caramel",
        "label": "焦糖",
        "icon": "icecream",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "butter",
        "label": "黃油",
        "icon": "egg_alt",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "coconut",
        "label": "椰奶",
        "icon": "water_drop",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "vanilla",
        "label": "香草",
        "icon": "grass",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "special",
        "label": "特調",
        "icon": "eco",
        "default": "grapefruit",
        "choices": [
            ("grapefruit", "西柚"),
            ("lemon", "檸檬"),
            ("citrus", "柑橘"),
        ],
    },
    {
        "key": "oolong",
        "label": "烏龍茶",
        "icon": "emoji_food_beverage",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "jasmine",
        "label": "茉莉花茶",
        "icon": "emoji_food_beverage",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "matcha",
        "label": "抹茶",
        "icon": "emoji_food_beverage",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "green",
        "label": "綠茶",
        "icon": "emoji_food_beverage",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "hojicha",
        "label": "焙茶",
        "icon": "emoji_food_beverage",
        "default": "default",
        "choices": [("default", "默認"), ("double", "加倍")],
    },
    {
        "key": "topping",
        "label": "面層配料",
        "icon": "grain",
        "default": "choco",
        "choices": [
            ("choco", "碎朱古力"),
            ("osmanthus", "碎桂花"),
            ("rose", "碎玫瑰"),
            ("nuts", "碎堅果"),
        ],
    },
    {
        "key": "bean_blend",
        "label": "配豆",
        "icon": "local_cafe",
        "default": "espresso",
        "choices": [
            ("espresso", "意式拼配"),
            ("dark", "深烘拼配"),
            ("brand", "品牌配豆"),
        ],
    },
]

OPTION_KEYS = [g["key"] for g in OPTION_GROUPS]


def get_option_label(key):
    """取得選項組的中文標籤"""
    for g in OPTION_GROUPS:
        if g["key"] == key:
            return g["label"]
    return key


def get_option_value_label(key, value):
    """取得選項值的中文標籤（choices 支援 (value, label) 或 (value, label, meta)）"""
    for g in OPTION_GROUPS:
        if g["key"] == key:
            for v, label, *_ in g["choices"]:
                if v == value:
                    return label
    return value


def sort_option_keys_for_coffee(coffee, keys):
    """依咖啡的 option_order_<key> 數字排序（數字小在前、0=預設順序）

    用於顯示端（訂單確認/訂單歷史/購物車/員工端）統一選項顯示順序，
    不受 add_to_cart 收集順序或 PostgreSQL jsonb 重排影響。
    coffee 為 None 或找不到時維持傳入順序。
    """
    if not coffee or not keys:
        return list(keys)
    pos = {g["key"]: i for i, g in enumerate(OPTION_GROUPS)}

    def _key(k):
        n = getattr(coffee, "option_order_" + k, 0) or 0
        return (n if n > 0 else 10 ** 9, pos.get(k, 999))

    return sorted(keys, key=_key)
