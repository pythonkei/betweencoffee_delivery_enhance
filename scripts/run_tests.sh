#!/bin/bash
# run_tests.sh — Between Coffee 一鍵測試腳本
# 用法: bash scripts/run_tests.sh [--coverage]

set -e
cd "$(dirname "$0")/.."

echo "============================================"
echo "🚀 Between Coffee 測試執行器"
echo "============================================"

# 執行 Django 測試
echo ""
echo "▶️  執行 Django 測試..."
python manage.py test eshop.tests --verbosity 1 --keepdb --noinput 2>&1 | tail -30

# 選擇性執行覆蓋率分析
if [ "$1" == "--coverage" ]; then
    echo ""
    echo "▶️  執行測試覆蓋缺口分析..."
    python scripts/analyze_test_coverage.py
fi

echo ""
echo "============================================"
echo "✅ 測試完成"
echo "============================================"