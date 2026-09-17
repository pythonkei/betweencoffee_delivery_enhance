#!/usr/bin/env python3
"""移除 .feed__triangle 死碼 + 移除影片 poster（2026-09-16）

需求：
 1. 修正 .feed--video 初始顯示：原本有 poster="index_feed_image.png"，
    進視口前會先顯示那張靜態照片、之後才播影片（使用者回報「初始顯示異常」）
    → 移除 poster，未播放時改用容器底色 rgba(17,16,19,1)（與蒙版同色）。
 2. 移除 .feed 與 .feed--video 內的 <div hidden class="feed__triangle">（含外部
    wondercrecue.com 圖片的死碼）→ 連同 landing.css 中已無用的 .feed__triangle 規則。

用法：python3 scripts/cleanup_feed_20260916.py           # dry-run
      python3 scripts/cleanup_feed_20260916.py --apply   # 寫入
"""
import re
import sys

BASE = "/home/kei/Desktop/betweencoffee_delivery_enhance"
APPLY = "--apply" in sys.argv

TEMPLATES = [
    BASE + "/templates/betweencoffee_delivery/index.html",
    BASE + "/templates/betweencoffee_delivery/landing_v3.html",
]
CSS = BASE + "/static/css/landing.css"

DIV_RE = re.compile(r'\n[ \t]*<div hidden class="feed__triangle">.*?</div>', re.S)
POSTER_RE = re.compile(r'\n?[ \t]*poster="\{% static \'images/index_feed_image\.png\' %\}"')
TRI_CSS_RE = re.compile(r'\n[ \t]*\.feed__triangle \{[^}]*\}\n', re.S)

total = {"div": 0, "poster": 0, "css": 0}
for p in TEMPLATES:
    s = open(p, encoding="utf-8").read()
    s, n1 = DIV_RE.subn("", s)
    s, n2 = POSTER_RE.subn("", s)
    total["div"] += n1
    total["poster"] += n2
    print("%-58s 移除 div=%d  poster=%d  殘留 feed__triangle=%d" % (p.split("/")[-1], n1, n2, s.count("feed__triangle")))
    if APPLY:
        open(p, "w", encoding="utf-8").write(s)

c = open(CSS, encoding="utf-8").read()
c, n3 = TRI_CSS_RE.subn("\n", c)
total["css"] += n3
print("%-58s 移除 .feed__triangle 規則=%d  殘留=%d" % ("landing.css", n3, c.count(".feed__triangle")))
if APPLY:
    open(CSS, "w", encoding="utf-8").write(c)

print("\n合計：div %d、poster %d、css %d；%s" % (total["div"], total["poster"], total["css"], "已寫入" if APPLY else "dry-run（加 --apply 才寫入）"))
