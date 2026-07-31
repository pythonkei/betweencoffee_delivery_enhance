#!/usr/bin/env python
"""
Phase 3E Step 2: 測試覆蓋缺口分析
純分析，不修改任何程式碼
"""
import ast
import re
from datetime import datetime
from pathlib import Path

BASE = Path('/home/kei/Desktop/betweencoffee_delivery_enhance')

# 核心模組清單
CORE_MODULES = [
    'eshop/models/order.py',
    'eshop/models/queue_models.py',
    'eshop/models/base.py',
    'eshop/models/shop_items.py',
    'eshop/order_status/status_changer.py',
    'eshop/order_status/payment_handler.py',
    'eshop/order_status/order_type_analyzer.py',
    'eshop/order_status/status_display.py',
    'eshop/queue_manager_refactored.py',
    'eshop/serializers.py',
    'eshop/whatsapp_notifier.py',
    'eshop/audit_logger.py',
]

# 測試目錄
TEST_DIRS = [
    BASE / 'eshop/tests',
    BASE / 'tests/integration',
]


def get_definitions(filepath):
    """解析 Python 檔案中的函數/類別/方法定義"""
    try:
        tree = ast.parse(filepath.read_text(encoding='utf-8'))
    except Exception as e:
        return {'error': str(e), 'classes': [], 'functions': [], 'methods': []}

    classes = []
    functions = []
    methods = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(f"{node.name}.{item.name}")
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)

    return {'classes': classes, 'functions': functions, 'methods': methods}


def main():
    print("=" * 70)
    print("Between Coffee 測試覆蓋缺口分析 (Phase 3E Step 2)")
    print("=" * 70)

    # 讀取所有測試檔內容
    test_content = ""
    for td in TEST_DIRS:
        if td.exists():
            for f in td.glob('test_*.py'):
                try:
                    test_content += f.read_text(encoding='utf-8')
                except Exception:
                    pass

    # 分析各核心模組
    report = []
    for mod in CORE_MODULES:
        path = BASE / mod
        if not path.exists():
            report.append(f"\n❌ {mod}: 檔案不存在")
            continue

        defs = get_definitions(path)
        if 'error' in defs:
            report.append(f"\n⚠️ {mod}: 解析失敗 ({defs['error']})")
            continue

        covered = []
        uncovered = []
        for cls in defs['classes']:
            if cls.lower() in test_content.lower():
                covered.append(f"class {cls}")
            else:
                uncovered.append(f"class {cls}")

        for fn in defs['functions']:
            if re.search(rf'\b{fn}\b', test_content):
                covered.append(f"def {fn}()")
            else:
                uncovered.append(f"def {fn}()")

        for m in defs['methods']:
            short = m.split('.')[-1]
            if re.search(rf'\b{short}\b', test_content) or m.lower() in test_content.lower():
                covered.append(f"method {m}")
            else:
                uncovered.append(f"method {m}")

        total = len(covered) + len(uncovered)
        pct = (len(covered) / total * 100) if total else 0

        report.append(f"\n📄 {mod} ({total} 定義)")
        report.append(f"   覆蓋率: {len(covered)}/{total} ({pct:.0f}%)")
        if uncovered:
            report.append(f"   ❌ 未覆蓋 ({len(uncovered)}):")
            for u in uncovered[:15]:
                report.append(f"      - {u}")
            if len(uncovered) > 15:
                report.append(f"      ... 還有 {len(uncovered)-15} 個")

    output = "\n".join(report)
    print(output)

    # 儲存報告
    out_file = BASE / 'docs' / 'coverage-gap-report.md'
    out_file.parent.mkdir(exist_ok=True)
    md = [
        "# Phase 3E Step 2: 測試覆蓋缺口報告",
        "",
        f"> 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "> 純分析報告，不修改任何程式碼",
        "",
        "```",
        output,
        "```"
    ]
    out_file.write_text("\n".join(md), encoding='utf-8')
    print(f"\n📁 報告已儲存: {out_file}")


if __name__ == '__main__':
    main()