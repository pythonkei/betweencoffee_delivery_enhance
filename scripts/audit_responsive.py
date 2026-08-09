#!/usr/bin/env python3
"""
verify_responsive.py — 全站響應式設計驗證腳本（2026-08-09）

功能：
  1. 遍歷指定頁面 × 斷點，測量關鍵元素 font-size（headless + 同源 iframe）
  2. 檢查頁面橫向溢出（scrollWidth vs innerWidth）
  3. 標記「未響應式縮放」異常（同一元素在不同斷點 font-size 相同）
  4. 輸出表格

前置條件：
  - 本地開發伺服器運行在 localhost:8081
  - settings.py 需臨時 X_FRAME_OPTIONS = "SAMEORIGIN"（診斷 iframe 用，用完恢復）
  - static/diag_fs.html 存在（診斷載入頁）

用法：
  python3 scripts/verify_responsive.py                # 全站 × 375/768/1200
  python3 scripts/verify_responsive.py --page /coffee_menu/
  python3 scripts/verify_responsive.py --widths 375 768
"""

import argparse
import re
import subprocess
import sys
import time

BASE = "http://localhost:8081"
DIAG = f"{BASE}/static/diag_fs.html"
PAGES = ["/", "/coffee_menu/", "/bean_menu/", "/coffee/4/", "/bean/8/",
         "/checkout/", "/cart/", "/about/", "/accounts/login/"]
DEFAULT_WIDTHS = [375, 768, 1200]
KEYS = ["headingH2", "subheading", "menuTitle", "price", "desc", "beanDesc", "btn", "h1", "coffeeTitle", "beanTitle", "prodPrice", "descClamp"]

CHROME = "/snap/bin/chromium"


def fetch_fonts(page, width, timeout=12):
    """用 headless dump-dom 讀取診斷頁，解析 font-size 字典。"""
    url = f"{DIAG}?w={width}&t={page}"
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--window-size=1300,900", f"--virtual-time-budget={timeout * 1000}",
             "--dump-dom", url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        html = r.stdout
    except Exception as e:
        return {"error": str(e)}
    data = {}
    for key in KEYS:
        m = re.search(rf"\b{key}=([\d.]+)px", html)
        data[key] = m.group(1) if m else "NA"
    m = re.search(r"overflow=(true|false)", html, re.IGNORECASE)
    data["overflow"] = m.group(1) if m else "NA"
    return data


def audit(page, widths):
    print(f"\n{'='*60}\n頁面: {page}\n{'='*60}")
    print(f"{'元素':<14}" + "".join(f"{w:>10}" for w in widths) + f"{'狀態':>12}")
    print("-" * 60)
    # 每個斷點只 fetch 一次，取得全部 keys + overflow
    results = {}
    for w in widths:
        results[w] = fetch_fonts(page, w)
    for key in KEYS:
        vals = [results[w].get(key, "NA") for w in widths]
        distinct = set(v for v in vals if v != "NA")
        status = "✅ 縮放" if len(distinct) > 1 else ("⚠️ 未縮放" if vals[0] != "NA" else "—")
        print(f"{key:<14}" + "".join(f"{v:>10}" for v in vals) + f"{status:>12}")
    over = [results[w].get("overflow", "NA") for w in widths]
    print(f"{'overflow':<14}" + "".join(f"{v:>10}" for v in over))
    print()


def main():
    ap = argparse.ArgumentParser(description="全站響應式設計驗證")
    ap.add_argument("--page", help="指定單一頁面（預設全部）")
    ap.add_argument("--widths", nargs="+", type=int, default=DEFAULT_WIDTHS,
                    help="斷點寬度列表（預設 375 768 1200）")
    args = ap.parse_args()

    pages = [args.page] if args.page else PAGES
    for p in pages:
        audit(p, args.widths)
    print("✅ 驗證完成（未縮放項目需檢查 responsive-system.css 覆蓋）")


if __name__ == "__main__":
    main()
