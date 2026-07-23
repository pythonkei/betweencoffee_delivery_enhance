#!/usr/bin/env python3
"""
隊列渲染器系統分析腳本
分析 3 個基礎類 + 4 個具體渲染器的重複情況
"""

import os
import re

RENDERER_DIR = "static/js/staff-order-management"

FILES = {
    "base-order-renderer.js": "BaseOrderRenderer",
    "optimized-base-renderer.js": "OptimizedBaseRenderer",
    "renderers/base-renderer.js": "BaseRenderer",
    "payment-pending-renderer.js": "PaymentPendingRenderer",
    "preparing-orders-renderer-enhanced.js": "EnhancedPreparingOrdersRenderer",
    "ready-orders-renderer.js": "DynamicReadyOrdersRenderer",
    "completed-orders-renderer.js": "DynamicCompletedOrdersRenderer",
}


def count_lines(filepath):
    with open(filepath, "r") as f:
        return len(f.readlines())


def extract_methods(filepath):
    """提取類中的方法名"""
    with open(filepath, "r") as f:
        content = f.read()

    # 匹配方法定義
    methods = re.findall(r"^\s+(async\s+)?(\w+)\(", content, re.MULTILINE)
    return [m[1] for m in methods]


def find_duplicate_patterns():
    """找出重複的程式碼模式"""
    results = {}

    # 要檢查的重複模式
    patterns = {
        "renderOrderItems": r"function renderOrderItems|renderOrderItems\(items\)",
        "getDefaultImage": r"function getDefaultImage|getDefaultImage\(itemType\)",
        "orderTypeBadges": r"order-type-badge.*快速訂單|order-type-badge.*混合訂單|order-type-badge.*普通訂單",
        "registerToUnifiedManager": r"registerToUnifiedManager\(\)",
        "bindEvents": r"bindEvents\(\)",
        "showToast": r"showToast\(message",
        "showEmpty": r"showEmpty\(\)",
        "forceRefresh": r"forceRefresh\(\)",
        "checkAndLoadData": r"checkAndLoadData\(\)",
        "onTabActivated": r"onTabActivated\(\)",
        "isActiveTab": r"isActiveTab\(\)",
        "cacheOrders": r"cacheOrders\(orders\)",
        "cleanup": r"cleanup\(\)",
        "updateLastUpdateTime": r"updateLastUpdateTime\(\)",
        "handleOrdersData": r"handleOrdersData\(orders\)",
        "requestOrdersData": r"requestOrdersData\(\)",
        "itemsDisplayHTML": r"items_count.*項商品.*order-product-badge",
        "paymentMethodBadge": r"payment_method.*badge-success",
        "baristaHTML": r"barista.*badge-barista",
        "combinedBadge": r"combinedBadge.*d-flex.*align-items-center.*mt-2",
        "orderDiv_setAttribute": r"setAttribute\(.*data-order-id",
        "orderDiv_className": r"className = 'order-item mb-5 p-5 rounded selectable'",
        "pickupCode_badge": r"取餐碼.*badge badge-dark",
        "customer_phone": r"客戶:.*電話:.*formatPhoneNumber",
        "order_number": r"訂單編號:.*#",
        "order_time": r"訂單時間:.*formatOrderTime",
        "total_price": r"total_price.*toFixed",
    }

    for filename, classname in FILES.items():
        filepath = os.path.join(RENDERER_DIR, filename)
        if not os.path.exists(filepath):
            results[filename] = {"exists": False, "patterns": {}}
            continue

        with open(filepath, "r") as f:
            content = f.read()

        file_results = {"exists": True, "lines": count_lines(filepath), "patterns": {}}
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            file_results["patterns"][pattern_name] = len(matches) > 0

        results[filename] = file_results

    return results


def print_analysis():
    print("=" * 80)
    print("  隊列渲染器系統 - 重複程式碼分析報告")
    print("=" * 80)

    # 1. 檔案大小
    print("\n📊 1. 檔案大小統計")
    print("-" * 60)
    total = 0
    for filename, classname in FILES.items():
        filepath = os.path.join(RENDERER_DIR, filename)
        if os.path.exists(filepath):
            lines = count_lines(filepath)
            total += lines
            print(f"  {filename:45s} {lines:4d} 行")
    print(f"  {'─' * 50}")
    print(f"  {'總計':45s} {total:4d} 行")

    # 2. 繼承關係
    print("\n📊 2. 繼承關係")
    print("-" * 60)
    print(
        """
  基礎類（3個）：
    BaseRenderer (renderers/base-renderer.js) ─── 358 行 ─── 被 PaymentPendingRenderer 使用（但未繼承）
    BaseOrderRenderer (base-order-renderer.js) ── 503 行 ─── ❌ 未被任何渲染器繼承
    OptimizedBaseRenderer (optimized-base-renderer.js) ─ 491 行 ─── ❌ 未被任何渲染器繼承（孤兒代碼）

  具體渲染器（4個）：
    PaymentPendingRenderer ─── 358 行 ─── 獨立類，未繼承任何基礎類
    EnhancedPreparingOrdersRenderer ─── 1241 行 ─── 獨立類，未繼承任何基礎類
    DynamicReadyOrdersRenderer ─── 810 行 ─── 獨立類，未繼承任何基礎類
    DynamicCompletedOrdersRenderer ─── 605 行 ─── 獨立類，未繼承任何基礎類
    """
    )

    # 3. 重複模式分析
    print("\n📊 3. 重複模式分析")
    print("-" * 60)

    results = find_duplicate_patterns()

    # 只分析具體渲染器
    concrete_renderers = [
        "payment-pending-renderer.js",
        "preparing-orders-renderer-enhanced.js",
        "ready-orders-renderer.js",
        "completed-orders-renderer.js",
    ]

    pattern_summary = {}
    for filename in concrete_renderers:
        if filename not in results:
            continue
        for pattern_name, found in results[filename]["patterns"].items():
            if pattern_name not in pattern_summary:
                pattern_summary[pattern_name] = []
            if found:
                pattern_summary[pattern_name].append(filename)

    print(f"\n  {'重複模式':30s} {'出現次數':10s} {'渲染器':30s}")
    print(f"  {'─' * 70}")

    for pattern_name, files in sorted(pattern_summary.items()):
        count = len(files)
        file_names = ", ".join([f.split(".")[0] for f in files])
        bar = "█" * count + "░" * (4 - count)
        print(f"  {pattern_name:30s} {bar:10s} {count}/4 ({file_names})")

    # 4. 具體重複項目
    print("\n\n📊 4. 具體重複項目詳情")
    print("-" * 60)

    duplicates = [
        ("renderOrderItems() 方法", "每個渲染器都有幾乎一樣的商品項目渲染邏輯", 4),
        ("getDefaultImage() 方法", "每個渲染器都有相同的默認圖片邏輯", 4),
        ("訂單類型徽章邏輯", "orderTypeBadges 判斷散落在各處", 4),
        ("registerToUnifiedManager()", "每個渲染器都有幾乎一樣的註冊邏輯", 4),
        ("bindEvents() 方法", "每個渲染器都有幾乎一樣的事件綁定邏輯", 4),
        ("showToast() 方法", "每個渲染器都有幾乎一樣的 Toast 邏輯", 4),
        ("showEmpty() 方法", "每個渲染器都有幾乎一樣的空狀態邏輯", 4),
        ("forceRefresh() 方法", "每個渲染器都有幾乎一樣的刷新邏輯", 4),
        ("checkAndLoadData() 方法", "3 個渲染器有幾乎一樣的數據檢查邏輯", 3),
        ("onTabActivated() 方法", "3 個渲染器有幾乎一樣的標籤頁激活邏輯", 3),
        ("isActiveTab() 方法", "3 個渲染器有幾乎一樣的活動標籤檢查邏輯", 3),
        ("cacheOrders() 方法", "3 個渲染器有幾乎一樣的緩存邏輯", 3),
        ("cleanup() 方法", "3 個渲染器有幾乎一樣的清理邏輯", 3),
        ("updateLastUpdateTime() 方法", "3 個渲染器有幾乎一樣的時間更新邏輯", 3),
        ("handleOrdersData() 方法", "3 個渲染器有幾乎一樣的數據處理邏輯", 3),
        ("requestOrdersData() 方法", "3 個渲染器有幾乎一樣的數據請求邏輯", 3),
        ("itemsDisplayHTML 邏輯", "商品數量 + 產品類型徽章顯示邏輯", 4),
        ("baristaHTML 邏輯", "咖啡師信息顯示邏輯", 3),
        ("combinedBadge 邏輯", "合併徽章顯示邏輯", 3),
        ("orderDiv 創建邏輯", "訂單卡片 div 創建和屬性設置", 4),
        ("取餐碼顯示邏輯", "badge-dark 取餐碼顯示", 4),
        ("客戶/電話顯示邏輯", "客戶名稱和電話格式化顯示", 4),
        ("訂單編號顯示邏輯", "訂單編號 # 顯示", 4),
        ("訂單時間顯示邏輯", "訂單時間格式化顯示", 4),
        ("總價顯示邏輯", "total_price toFixed 顯示", 4),
    ]

    print(f"\n  {'重複項目':35s} {'重複次數':10s}")
    print(f"  {'─' * 45}")
    for name, desc, count in sorted(duplicates, key=lambda x: -x[2]):
        bar = "█" * count + "░" * (4 - count)
        print(f"  {name:35s} {bar:10s} {count}/4")

    # 5. 結論
    print("\n\n📊 5. 結論與建議")
    print("-" * 60)
    print(
        """
  🔴 核心問題：
    1. 3 個基礎類互相競爭，沒有一個被具體渲染器繼承
    2. 4 個具體渲染器各自為政，大量重複程式碼
    3. OptimizedBaseRenderer 有 DocumentFragment、倒計時管理等好功能但無人使用
    4. EnhancedPreparingOrdersRenderer 1241 行過於龐大

  🟢 重構建議：
    1. 合併 3 個基礎類為統一的 BaseOrderRenderer (v2)
    2. 讓 4 個具體渲染器都繼承 BaseOrderRenderer (v2)
    3. 提取共用方法到基礎類
    4. 刪除 optimized-base-renderer.js（孤兒代碼）
    5. 標記 renderers/base-renderer.js 為 deprecated

  📈 預期效益：
    - 總行數: ~3,900 行 → ~2,500 行（-36%）
    - 基礎類: 3 個 → 1 個（-67%）
    - renderOrderItems 重複: 5 次 → 1 次（-80%）
    - 訂單類型徽章重複: 5 次 → 1 次（-80%）
    """
    )


if __name__ == "__main__":
    print_analysis()
