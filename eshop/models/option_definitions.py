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


# ============================================================
#  咖啡豆自訂選項組（2026-09-18）
#  與咖啡同一套機制：Admin 勾選啟用 + 排序數字；詳情頁依排序渲染。
#
#  設計重點（使用者定案）：
#  - 產地不是讓客人選 → 資料組的 customer_selectable=False：詳情頁只「唯讀顯示」該豆的值，
#    不渲染按鈕、不送 hidden input、不寫入購物車（故購物車 dedupe 與 orders 結構不受影響）。
#  - grinding_level 為客人可選（沿用既有購物車欄位與舊訂單顯示，零相容成本）。
#  - 「值 / 預設值」來源＝BeanItem 的同名欄位（key 與欄位同名）→ 不需額外欄位。
# ============================================================

# 產地選項（既有自由文字值由 migration 0072 正規化；選單含「其他（自填）」）
ORIGIN_CHOICES = [
    ("ET", "埃塞俄比亞"),
    ("JP", "日本"),
    ("CO", "哥倫比亞"),
    ("BR", "巴西"),
    ("GT", "危地馬拉"),
    ("CR", "哥斯大黎加"),
    ("KE", "肯亞"),
    ("ID", "印尼"),
    ("PE", "秘魯"),
    ("PA", "巴拿馬"),
    ("RW", "盧安達"),
    ("HN", "宏都拉斯"),
    ("TW", "台灣"),
    ("CN-YN", "雲南"),
    ("OT", "其他（自填）"),
]

BEAN_OPTION_GROUPS = [
    {
        # 產地（唯讀；客人不能選）：值＝同名的 BeanItem.origin 欄位。
        # ⚠ 前台「不」由選項組渲染 → 沿用詳情頁原有的產地排版（block-23 清單行：圖示＋中文值），
        #   不新增任何 UI。Admin 的勾選 option_origin＝該行是否顯示；
        #   中文標籤仍由 option_value 過濾器解析（get_option_value_label / bean_option_display_value）。
        "key": "origin",
        "label": "產地",
        "icon": "pin_drop",
        "customer_selectable": False,
        "choices": ORIGIN_CHOICES,
    },
    {
        "key": "grinding_level",  # 同 BeanItem.grinding_level（預設值來源）
        "label": "研磨",
        "icon": "roller_shades",
        "customer_selectable": True,  # 客人可選；沿用既有購物車欄位與舊訂單顯示
        "default": "Non",
        "choices": [
            ("Non", "免研磨"),
            ("Light", "細研磨"),
            ("Medium", "中研磨"),
            ("Deep", "粗研磨"),
        ],
    },
    # 註：烘焙度不納入選項組 —— 詳情頁已有專屬的「烘焙水平」視覺刻度（roastrange），
    #     再開一組會重複顯示；如未來需要，比照上方格式補一組即可。
]

BEAN_OPTION_KEYS = [g["key"] for g in BEAN_OPTION_GROUPS]

# 顯示端合併查找用（咖啡 16 組 + 豆 3 組；key 不重疊）
ALL_OPTION_GROUPS = OPTION_GROUPS + BEAN_OPTION_GROUPS


def get_option_label(key):
    """取得選項組的中文標籤（咖啡 + 咖啡豆合併查找）"""
    for g in ALL_OPTION_GROUPS:
        if g["key"] == key:
            return g["label"]
    return key


def get_option_value_label(key, value):
    """取得選項值的中文標籤（choices 支援 (value, label) 或 (value, label, meta)）"""
    for g in ALL_OPTION_GROUPS:
        if g["key"] == key:
            for v, label, *_ in g["choices"]:
                if v == value:
                    return label
    return value


def get_option_icon(key):
    """取得選項組的 material-symbols 圖示名（咖啡 + 咖啡豆合併查找）"""
    for g in ALL_OPTION_GROUPS:
        if g["key"] == key:
            return g["icon"]
    return "add_circle"


def get_bean_option_groups(bean):
    """前台「選項按鈕 UI」要渲染的組（＝客人可選的組），依 Admin 排序數字排好（0=預設順序）。

    唯讀組（customer_selectable=False，例如產地）**不在此列** —— 它們沿用詳情頁既有排版，
    由模板直接讀 bean 欄位顯示（中文標籤用 bean_option_display_value）。
    回傳 list[dict]：原定義 + default（原始值＝客人可選時預設選中的值）。
    """
    enabled = []
    for i, g in enumerate(BEAN_OPTION_GROUPS):
        if not g.get("customer_selectable"):
            continue
        if not getattr(bean, "option_" + g["key"], False):
            continue
        g = dict(g)  # 複製，避免污染全域定義
        g["default"] = getattr(bean, g["key"], "") or ""
        enabled.append((i, g))

    def _order_key(item):
        i, g = item
        n = getattr(bean, "option_order_" + g["key"], 0) or 0
        return (n if n > 0 else 10 ** 9, i)

    enabled.sort(key=_order_key)
    return [g for _, g in enabled]


def bean_option_display_value(bean, group):
    """唯讀選項組要顯示的值；產地選「其他（自填）」時改用 origin_custom"""
    key = group["key"]
    raw = getattr(bean, key, "") or ""
    if key == "origin" and raw == "OT":
        return (getattr(bean, "origin_custom", "") or "").strip()
    return get_option_value_label(key, raw) if raw else ""


def sort_option_keys_for_bean(bean, keys):
    """依該咖啡豆的 option_order_<key> 數字排序（數字小在前、0=預設順序）

    對齊 sort_option_keys_for_coffee：用於購物車/訂單等顯示端統一選項順序。
    """
    if not bean or not keys:
        return list(keys)
    pos = {g["key"]: i for i, g in enumerate(BEAN_OPTION_GROUPS)}

    def _key(k):
        n = getattr(bean, "option_order_" + k, 0) or 0
        return (n if n > 0 else 10 ** 9, pos.get(k, 999))

    return sorted(keys, key=_key)


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
