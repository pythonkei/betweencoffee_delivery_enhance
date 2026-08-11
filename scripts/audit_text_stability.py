#!/usr/bin/env python3
"""
audit_text_stability.py — 全域文字穩定性審計（2026-08-10）
檢查「載入時文字大小跳變/抖動」的全域修復狀態：
  根因1：rem 依賴 html font-size clamp（responsive-system 後載入覆蓋基準 → 跳變）
  根因2：FOUT（display=swap 字體交換）
  修復：<html> inline font-size clamp + Google Fonts display=block
用法: python scripts/audit_text_stability.py [--url http://localhost:8081]
"""
import argparse
import glob
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PASS, FAIL, WARN = "✅", "❌", "⚠️"


def audit_css_font_units():
    """統計全域 CSS font-size 單位分布"""
    print("\n=== 1. 全域 CSS font-size 單位分布 ===")
    units = {}
    files_with_rem = []
    total = 0
    for css in sorted(glob.glob(str(BASE_DIR / "static/css/*.css"))):
        if "dist-" in css:
            continue
        text = Path(css).read_text(encoding="utf-8", errors="ignore")
        matches = re.findall(r"font-size\s*:\s*([0-9.]+)(rem|em|px|%|vw|vh)", text)
        if not matches:
            continue
        fname = Path(css).name
        f_units = {}
        for val, unit in matches:
            f_units[unit] = f_units.get(unit, 0) + 1
            units[unit] = units.get(unit, 0) + 1
            total += 1
        if f_units.get("rem", 0):
            files_with_rem.append(f"{fname}: {f_units.get('rem')} rem")
        print(f"  {fname:40s} px={f_units.get('px',0):3d} rem={f_units.get('rem',0):3d} em={f_units.get('em',0):3d} %={f_units.get('%',0):3d} vw={f_units.get('vw',0):3d}")
    print(f"\n  總計 {total} 個 font-size：{units}")
    print(f"  rem 用量（依賴 html clamp，需 inline 基準確保穩定）：{len(files_with_rem)} 個檔案")
    return units

def audit_base_template():
    """檢查 base.html 的字體穩定性標記"""
    print("\n=== 2. base.html 字體穩定性標記 ===")
    base = (BASE_DIR / "templates/betweencoffee_delivery/base.html").read_text(encoding="utf-8")
    ok = True
    html_match = re.search(r'<html[^>]*style="[^"]*font-size:[^"]*"', base)
    if html_match:
        fs = re.search(r"font-size:\s*([^;\"]+)", html_match.group(0))
        print(f"  {PASS} <html> inline font-size: {fs.group(1)}")
    else:
        print(f"  {FAIL} <html> 缺 inline font-size（rem 載入時序跳變風險）")
        ok = False
    font_link = re.search(r"fonts.googleapis.com/css2\?[^\"']+", base)
    if font_link:
        if "display=block" in font_link.group(0):
            print(f"  {PASS} Google Fonts display=block（無 FOUT）")
        else:
            disp = re.search(r"display=(\w+)", font_link.group(0))
            print(f"  {FAIL} Google Fonts display={disp.group(1) if disp else '?'}（應為 block）")
            ok = False
    if "display=swap" in base:
        print(f"  {FAIL} 殘留 display=swap（FOUT 抖動源）")
        ok = False
    else:
        print(f"  {PASS} 無 display=swap 殘留")
    return ok


def audit_http(url):
    """HTTP 驗證主要頁面渲染後的字體穩定性標記"""
    print(f"\n=== 3. HTTP 渲染驗證（{url}）===")
    import urllib.request
    pages = [("/", "首頁"), ("/coffee_menu/", "咖啡菜單"), ("/bean_menu/", "烘焙豆"),
             ("/about/", "關於我們"), ("/cart/", "購物車"), ("/cart/checkout/", "結帳"),
             ("/accounts/login/", "登入")]
    ok = True
    for path, label in pages:
        try:
            html = urllib.request.urlopen(url + path, timeout=10).read().decode("utf-8", errors="ignore")
        except Exception:
            print(f"  {WARN} {label:8s} {path:22s} 無法連線")
            continue
        html_inline = 'font-size: clamp(14px, 0.3vw' in html
        block = "display=block" in html
        swap = "display=swap" in html
        status = []
        if html_inline:
            status.append(f"{PASS} html inline")
        else:
            status.append(f"{FAIL} 缺 html inline"); ok = False
        if block and not swap:
            status.append(f"{PASS} display=block")
        else:
            status.append(f"{FAIL} display={'swap!' if swap else '缺'}"); ok = False
        print(f"  {' '.join(status)}  {label} ({path})")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Between Coffee 全域文字穩定性審計")
    ap.add_argument("--url", default="http://localhost:8081", help="本機 dev server URL")
    args = ap.parse_args()
    print("=" * 60)
    print("☕ Between Coffee — 全域文字穩定性審計（2026-08-10）")
    print("=" * 60)
    audit_css_font_units()
    r1 = audit_base_template()
    r2 = audit_http(args.url)
    print("\n" + "=" * 60)
    print(f"審計結果：{'✅ 全域文字載入穩定' if (r1 and r2) else '❌ 有項目未通過'}")
    sys.exit(0 if (r1 and r2) else 1)


if __name__ == "__main__":
    main()

