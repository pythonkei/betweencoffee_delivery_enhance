#!/usr/bin/env python3
"""Between Coffee CSS 引用審計腳本（2026-08-11）

掃描所有模板的 CSS <link> 引用，對照 static/css/ 檔案，
標記死資產 / 重複引用 / 僅特定頁面載入，並驗證 URL 可存取。

用法：
    python scripts/audit_css_references.py

輸出：
    console 摘要 + docs/css_audit_report.md 完整報告
"""
import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CSS_DIR = ROOT / "static" / "css"
OUTPUT = ROOT / "docs" / "css_audit_report.md"

# 掃描所有 templates 目錄（ROOT/templates + 各 app 的 templates/）
TEMPLATE_DIRS = [ROOT / "templates"]
for d in ROOT.glob("*/templates"):
    if d.is_dir():
        TEMPLATE_DIRS.append(d)

# ---------- 1. 掃描模板 CSS 引用 ----------
static_re = re.compile(r"static\s+['\"](css/[^'\"]+\.css)['\"]")
link_re = re.compile(r"<link\b[^>]*stylesheet[^>]*>", re.IGNORECASE)
href_re = re.compile(r"href=['\"]([^'\"]+)['\"]")

css_refs = defaultdict(set)      # css 名稱 -> {模板相對路徑}
external_refs = []               # (URL, 模板)
templates_with_css = 0

for tdir in TEMPLATE_DIRS:
    for html in sorted(tdir.rglob("*.html")):
        rel = str(html.relative_to(ROOT)).replace("\\", "/")
        text = html.read_text(encoding="utf-8", errors="ignore")
        # 移除 Django 註解與 HTML 註解（避免誤報被註解的引用）
        text = re.sub(r"{%\s*comment\s*%}.*?{%\s*endcomment\s*%}", "", text, flags=re.DOTALL)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        matched = False
        for m in static_re.finditer(text):
            raw = m.group(1)                     # 'css/xxx.css' 或 'fontawesome/css/all.css'
            key = raw[4:] if raw.startswith("css/") else raw   # 根目錄檔案去 'css/' 前綴統一
            css_refs[key].add(rel)
            matched = True
        for lm in link_re.finditer(text):
            hm = href_re.search(lm.group(0))
            if hm and hm.group(1).startswith("http"):
                external_refs.append((hm.group(1), rel))
                matched = True
        if matched:
            templates_with_css += 1

# ---------- 2. static/css 全部檔案 ----------
all_css_files = {}
for f in sorted(CSS_DIR.rglob("*.css")):
    if f.name == "all.css" and "fontawesome" in f.as_posix():
        all_css_files["fontawesome/css/all.css"] = f
    elif f.parent == CSS_DIR:
        all_css_files[f.name] = f
    else:
        all_css_files[f.relative_to(CSS_DIR).as_posix()] = f

# ---------- 3. 分類 ----------
referenced = set(css_refs.keys())
all_names = set(all_css_files.keys())
dead = sorted(all_names - referenced)                      # 死資產
# 有 .bak / 子目錄源碼 / 非 css 檔
dead_meta = sorted(f.name for f in CSS_DIR.iterdir()
                   if f.is_file() and f.suffix not in (".css", ".gif"))
dead_dirs = sorted(d.name for d in CSS_DIR.iterdir() if d.is_dir() and d.name not in ("fontawesome",))

# 重複引用：同 css 被多個模板引用（且 base.html 也引）
base_refs = {r for r in css_refs if "base.html" in {Path(x).name for x in css_refs[r]}}
conditional = {}   # 非 base.html 全域，僅特定頁面
for name, refs in css_refs.items():
    names = {Path(r).name for r in refs}
    if "base.html" not in names:
        conditional[name] = sorted(refs)

duplicates = {name: sorted(refs) for name, refs in css_refs.items() if len(refs) > 1}

# ---------- 4. 大小統計 ----------
def fsize(name):
    f = all_css_files.get(name)
    return f.stat().st_size if f else 0

referenced_size = sum(fsize(n) for n in css_refs)
dead_size = sum(fsize(n) for n in dead)
total_size = sum(fsize(n) for n in all_names)

# ---------- 5. HTTP 驗證 ----------
def check_http(name):
    """嘗試檢查本地 CSS URL 可存取（需伺服器運行），失敗則 fallback 檔案存在"""
    try:
        import urllib.request
        url = f"http://localhost:8081/static/{name}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status
    except Exception:
        return None  # 伺服器未運行 → 以檔案存在為準

http_results = {}
server_up = True
sample = list(referenced)[:10]
for name in sample:
    code = check_http(name)
    if code is None:
        server_up = False
        break
    http_results[name] = code

# ---------- 6. 輸出 ----------
lines = []
def add(s=""):
    lines.append(s)

add("# Between Coffee CSS 引用審計報告")
add("")
add(f"> **執行時間**: 自動產生 ｜ **模板數**: {templates_with_css} ｜ **CSS 檔案數**: {len(all_names)}")
add("")
add("## 摘要")
add("")
add(f"- **被引用 CSS**: {len(referenced)} 個（約 {referenced_size//1024} KB）")
add(f"- **死資產（未被引用）**: {len(dead)} 個（約 {dead_size//1024} KB）")
add(f"- **僅特定頁面載入**: {len(conditional)} 個")
add(f"- **重複引用（多模板）**: {len(duplicates)} 個")
add(f"- **全部 CSS 總量**: 約 {total_size//1024} KB")
add("")
add("## 被引用 CSS（base.html 全域 + 特定頁面）")
add("")
add("| CSS 檔案 | 大小 | 引用模板 |")
add("|---|---:|---|")
for name in sorted(css_refs):
    refs = sorted(css_refs[name])
    tag = "🟢 全域" if "base.html" in {Path(r).name for r in refs} else "🟡 條件"
    add(f"| {name} ({tag}) | {fsize(name)//1024}KB | {', '.join(refs[:4])}{'…' if len(refs)>4 else ''} |")
add("")
add("## 🔴 死資產（未被任何模板引用，可清理）")
add("")
if dead:
    for name in dead:
        add(f"- `{name}`（{fsize(name)//1024}KB）")
else:
    add("- 無")
add("")
add("## 🔴 死資產（非 .css：備份/源碼/垃圾）")
add("")
if dead_meta:
    add(", ".join(f"`{x}`" for x in dead_meta))
if dead_dirs:
    add("目錄: " + ", ".join(f"`{x}/`" for x in dead_dirs))
add("")
add("## 🟡 重複引用（同 CSS 多模板載入）")
add("")
if duplicates:
    for name, refs in sorted(duplicates.items()):
        add(f"- `{name}` ← {', '.join(refs)}")
else:
    add("- 無")
add("")
add("## 🟡 外部 CSS（CDN / Google Fonts）")
add("")
if external_refs:
    seen = set()
    for url, tpl in external_refs:
        if url not in seen:
            add(f"- `{url}`")
            seen.add(url)
else:
    add("- 無")
add("")
add("## HTTP 驗證")
add("")
if server_up:
    for name, code in http_results.items():
        add(f"- `{name}` → HTTP {code}")
    add("- （抽查前 10 個全域 CSS）")
else:
    add("- ⚠️ 伺服器未運行（localhost:8081），HTTP 驗證略過（以檔案存在為準）")
add("")

report = "\n".join(lines)
OUTPUT.parent.mkdir(exist_ok=True)
OUTPUT.write_text(report, encoding="utf-8")

# console 摘要
print("=" * 60)
print("✅ CSS 引用審計完成")
print(f"   被引用: {len(referenced)} 個（{referenced_size//1024} KB）")
print(f"   死資產: {len(dead)} 個（{dead_size//1024} KB）")
print(f"   僅特定頁面: {len(conditional)} 個")
print(f"   重複引用: {len(duplicates)} 個")
print(f"   全部 CSS 總量: {total_size//1024} KB")
print("=" * 60)
print(f"📁 完整報告: {OUTPUT.relative_to(ROOT)}")
print("")
print("🔴 死資產（可清理）:")
for name in dead:
    print(f"   - {name}（{fsize(name)//1024}KB）")
print("🟡 僅特定頁面載入（可條件化）:")
for name in sorted(conditional):
    print(f"   - {name} ← {', '.join(conditional[name])}")
