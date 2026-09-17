#!/usr/bin/env python3
"""移除 .feed__clock（懸浮時鐘）死碼（2026-09-16）

背景：模板中已不存在 .feed__clock 元素（grep templates/ → 0），landing.css 內的
      規則（基礎 / :hover / span / ≤768 與 ≤576 兩個 media）全是死碼。
      使用者要求一併清掉。
用法：python3 scripts/cleanup_feed_clock_20260916.py           # dry-run
      python3 scripts/cleanup_feed_clock_20260916.py --apply   # 寫入
"""
import sys

CSS = "/home/kei/Desktop/betweencoffee_delivery_enhance/static/css/landing.css"
APPLY = "--apply" in sys.argv

s = open(CSS, encoding="utf-8").read()
START = "/* 懸浮時鐘樣式"
END = "@media screen and (max-width: 1200px) {"

i = s.find(START)
j = s.find(END, i)
if i < 0 or j < 0:
    print("✗ 找不到標記：START=%s END=%s" % (i >= 0, j >= 0))
    sys.exit(1)

removed = s[i:j]
lines = [l for l in removed.split("\n") if l.strip()]
print("將移除 %d 字元 / %d 行（自 '%s' 起、至 '%s' 前）" % (len(removed), len(lines), START, END))
print("  首行：%s" % lines[0])
print("  末行：%s" % lines[-1])
print("  含 .feed__clock 次數：%d" % removed.count(".feed__clock"))

new = s[:i] + s[j:]
print("移除後 landing.css 內 .feed__clock 次數：%d（應為 0）" % new.count(".feed__clock"))
print("大括號：{ %d  } %d  %s" % (new.count("{"), new.count("}"), "OK" if new.count("{") == new.count("}") else "BAD"))

if APPLY:
    open(CSS, "w", encoding="utf-8").write(new)
    print("已寫入")
else:
    print("dry-run（加 --apply 才寫入）")
