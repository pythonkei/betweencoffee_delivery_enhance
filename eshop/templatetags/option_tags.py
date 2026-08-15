# eshop/templatetags/option_tags.py
"""自訂選項組模板 filter（2026-08-15）"""
from django import template

from eshop.models.option_definitions import (
    OPTION_GROUPS,
    get_option_label,
    get_option_value_label,
)

register = template.Library()


@register.filter
def option_label(key):
    """選項組 key → 中文標籤（奶類/焦糖/黃油/…）"""
    return get_option_label(key)


@register.filter
def option_icon(key):
    """選項組 key → material-symbols 圖示名"""
    for g in OPTION_GROUPS:
        if g["key"] == key:
            return g["icon"]
    return "add_circle"


@register.filter
def option_value(value, key):
    """選項值（raw）→ 中文（需傳選項組 key）
    用法：{{ opt_val|option_value:opt_key }} → oat|milk → 燕麥奶
    """
    return get_option_value_label(key, value)
