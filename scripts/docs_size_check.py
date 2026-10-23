#!/usr/bin/env python3
"""檢查「會被 AI 讀取」的文件大小，避免再次長成巨型檔案（爆 token / 拖慢回應）。

背景：2026-10-23 發現 `.clinerules/.clinerules` 209KB、`task_progress.md` 290KB、
`04_SYSTEM_STATE.md` 181KB、`05_PRIORITY_TASKS.md` 100KB，導致每次載入上下文都要
分頁多次，回應明顯變慢。此腳本用固定上限守住，超過就提示封存到 `docs/archive/`。

用法：
    python3 scripts/check_docs_size.py          # 檢查（超標則 exit 1）
    python3 scripts/check_docs_size.py --quiet  # 只印超標項目
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# (glob, 上限 bytes, 說明)
WATCHED = [
    (".clinerules/*.md", 12_000, "自動注入規則，越小越好"),
    ("task_progress.md", 12_000, "只留現況；歷史封存"),
    ("betweencoffee_memory_bank/0[045]*.md", 12_000, "只留摘要；歷史封存"),
    ("betweencoffee_memory_bank/0[13]*.md", 40_000, "架構／規範，可稍大"),
    ("docs/INDEX.md", 8_000, "索引要短"),
    ("docs/uiux-full-reference.md", 45_000, "只在做新 UI 元件時讀"),
    ("docs/guides/*.md", 40_000, "操作指南"),
    ("docs/verify/CDP_SETUP.md", 45_000, "驗證環境說明"),
]

# 永遠不檢查（歷史封存／一次性報告，只用 grep）
SKIPPED_PARTS = {"archive", "reports", "node_modules", ".git", "media"}


def human(n: int) -> str:
    return f"{n / 1024:.1f}K"


def collect() -> list[tuple[Path, int, str]]:
    rows: list[tuple[Path, int, str]] = []
    seen: set[Path] = set()
    for pattern, limit, note in WATCHED:
        for path in sorted(PROJECT_ROOT.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            if SKIPPED_PARTS & set(path.relative_to(PROJECT_ROOT).parts):
                continue
            seen.add(path)
            rows.append((path, limit, note))
    return rows


def main() -> int:
    quiet = "--quiet" in sys.argv
    rows = collect()
    if not rows:
        print("⚠️  找不到要檢查的文件（請確認在專案根目錄執行）")
        return 0

    failures = []
    if not quiet:
        print(f"{'檔案':<62}{'大小':>8}{'上限':>8}  狀態")
        print("-" * 92)

    for path, limit, note in rows:
        size = path.stat().st_size
        rel = path.relative_to(PROJECT_ROOT)
        ok = size <= limit
        if not ok:
            failures.append((rel, size, limit, note))
        if not quiet or not ok:
            status = "OK" if ok else "❌ 超過"
            print(f"{str(rel):<62}{human(size):>8}{human(limit):>8}  {status}")

    total = sum(p.stat().st_size for p, _, _ in rows)
    if not quiet:
        print("-" * 92)
        print(f"{'合計':<62}{human(total):>8}")

    if failures:
        print("\n超標文件（請把歷史段移到 docs/archive/ 後再精簡）：")
        for rel, size, limit, note in failures:
            print(f"  • {rel}：{human(size)} > {human(limit)}（{note}）")
        return 1

    print("\n✅ 全部在預算內")
    return 0


if __name__ == "__main__":
    sys.exit(main())
