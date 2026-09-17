#!/usr/bin/env python3
"""整包移除 #borders（全屏左右垂直虛線裝飾）2026-09-16

背景：兩側虛線皆已隱藏（左 2026-08-10、右 2026-09-16），#borders 實質已無作用，
      使用者確認「OK, 清理」→ 連 markup 與 CSS 一起移除。
涵蓋：
  1. templates/betweencoffee_delivery/base.html：<div id="borders"> … </div> markup
     （保留其後 .bc-page-content 的 position: relative——它是通用 wrapper 樣式）
  2. static/css/bc-attract.css：header 註解提及、#borders 區塊、
     #borders .bc-borders__inner / __right / __left 規則與 3 個 media 覆寫、
     以及 .bc-attract-buy 段落中提及 #borders 的註解
  3. templates/layouts/nav.html、static/css/bc-weather.css：提及 #borders 的註解加註歷史
  4. templates/admin/staff_order_management.html：selector 清單移除 #borders
用法：python3 scripts/remove_borders_20260916.py          # dry-run
      python3 scripts/remove_borders_20260916.py --apply  # 寫入
"""
import re
import sys

BASE = "/home/kei/Desktop/betweencoffee_delivery_enhance/"
APPLY = "--apply" in sys.argv
report = []


def edit(path, fn, label):
    p = BASE + path
    s = open(p, encoding="utf-8").read()
    new = fn(s)
    before, after = s.count("borders"), new.count("borders")
    report.append("%-46s %-34s borders 出現：%d → %d" % (path.split("/")[-1], label, before, after))
    if APPLY:
        open(p, "w", encoding="utf-8").write(new)


# ---- 1. base.html：移除 markup（保留 .bc-page-content）----
def base_fn(s):
    s = re.sub(r'\n<!-- 2026-08-10: 全屏虛線邊框[^\n]*-->\n<div id="borders">.*?</div>\n</div>\n', "\n", s, count=1, flags=re.S)
    s = s.replace(
        "<!-- 2026-08-10: 內容 wrapper 提升層級（z-index:1），確保在 #borders 虛線之上 -->",
        "<!-- 2026-08-10 內容 wrapper 提升層級；2026-09-16 已移除 #borders 虛線（position: relative 保留） -->",
    )
    return s


edit("templates/betweencoffee_delivery/base.html", base_fn, "移除 markup")


# ---- 2. bc-attract.css：移除所有 #borders 規則與相關註解 ----
def css_fn(s):
    # a. header 註解那行
    s = re.sub(r'\n\s*- #borders：全屏 fixed 左右垂直虛線（dots mask），左線對齊 Buy 按鈕', "", s, count=1)
    # b. #borders 主區塊（到 .bc-page-content 之前）
    s = re.sub(r'/\* ===== #borders 全屏虛線邊框.*?(?=/\* 內容 wrapper)', "", s, count=1, flags=re.S)
    # c. .bc-page-content 註解更新
    s = s.replace(
        "/* 內容 wrapper：恢復自然層級（虛線為裝飾引導線，位於內容之上但細線不遮擋） */",
        "/* 內容 wrapper（原為 #borders 虛線的層級安排；2026-09-16 #borders 已移除，保留 position: relative） */",
    )
    # d. inner / right / left 規則＋media（到 c-attract 段落之前）
    s = re.sub(r'#borders \.bc-borders__inner \{.*?(?=/\* ===== c-attract 通用容器)', "", s, count=1, flags=re.S)
    # e. 兩個 media 內的 .bc-borders__right 覆寫（含其註解行）
    s = re.sub(r'\n[ \t]*/\* 右虛線（按鈕中心點對齊此虛線中心） \*/\n[ \t]*#borders \.bc-borders__right \{[^}]*\}\n', "\n", s)
    # f. .bc-attract-buy 註解中提及 #borders 者
    s = s.replace("（高於右側虛線 #borders z-index:9999）。", "（2026-09-16 前為高於右側虛線 #borders）。")
    s = s.replace("低於 #borders(9999) 而被虛線蓋住。 */", "原會低於當時的右側虛線（#borders 9999，已於 2026-09-16 移除）。 */")
    return s


edit("static/css/bc-attract.css", css_fn, "移除 #borders 規則/註解")


# ---- 3. 註解加註歷史 ----
def nav_fn(s):
    s = s.replace(
        "按鈕若在 nav 內 z-index:99999 會被鎖在層級 3，低於 #borders(9999) 而被虛線蓋住。",
        "按鈕若在 nav 內 z-index:99999 會被鎖在層級 3，原會低於 #borders 虛線(9999) 而被蓋住（#borders 已於 2026-09-16 移除，說明保留）。",
    )
    s = s.replace(
        "移出後與 #borders 同層比較 → 99999 > 9999 → 按鈕在最頂、右側虛線在下。 -->",
        "移出後與 #borders 同層比較 → 99999 > 9999 → 按鈕在最頂。 -->",
    )
    return s


edit("templates/layouts/nav.html", nav_fn, "註解加註歷史")


def weather_fn(s):
    return s.replace(
        "weather 水平中心對齊 #borders 右側虛線中心（= Order 按鈕視覺中心）。",
        "weather 水平中心對齊 Order 按鈕視覺中心（2026-09-16 前同位置為 #borders 右側虛線）。",
    )


edit("static/css/bc-weather.css", weather_fn, "註解加註歷史")


def admin_fn(s):
    return s.replace(
        ".bc-attract-nav,\n.bc-floating-cart,\n#borders {\n  display: none !important;\n}",
        ".bc-attract-nav,\n.bc-floating-cart {\n  display: none !important;\n}",
    ).replace(
        "/* 員工訂單管理頁：隱藏全站懸浮按鈕（右側 Buy & Order + 浮動購物車）與右側虛線——管理介面不需顯示 */",
        "/* 員工訂單管理頁：隱藏全站懸浮按鈕（右側 Buy & Order + 浮動購物車）——管理介面不需顯示\n   （右側虛線 #borders 已於 2026-09-16 全站移除） */",
    )


edit("templates/admin/staff_order_management.html", admin_fn, "selector 移除 #borders")

print("\n".join(report))
print("\n%s" % ("已寫入" if APPLY else "dry-run（加 --apply 才寫入）"))
