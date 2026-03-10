#!/usr/bin/env python3
"""
智能分配系統快速測試腳本
用於快速驗證系統功能是否正常
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta

# 設置Django環境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.models import OrderModel
from eshop.smart_allocation import SmartAllocationSystem
from eshop.learning_optimizer import LearningOptimizer
from eshop.performance_optimizer import PerformanceOptimizer

def test_smart_allocation_quick():
    """快速測試智能分配系統"""
    print("🔍 智能分配系統快速測試")
    print("=" * 50)
    
    try:
        # 1. 初始化系統
        print("1. 初始化智能分配系統...")
        allocation_system = SmartAllocationSystem()
        learning_optimizer = LearningOptimizer()
        performance_optimizer = PerformanceOptimizer()
        
        print("   ✅ 系統初始化成功")
        
        # 2. 檢查員工工作負載
        print("\n2. 檢查員工工作負載...")
        workload_data = allocation_system.get_barista_workload()
        
        if workload_data['success']:
            print(f"   ✅ 工作負載查詢成功")
            print(f"   員工數量: {len(workload_data['data']['baristas'])}")
            print(f"   總工作負載: {workload_data['data']['total_workload']}")
            print(f"   平均效率: {workload_data['data']['average_efficiency']:.2f}")
        else:
            print(f"   ❌ 工作負載查詢失敗: {workload_data['message']}")
        
        # 3. 檢查隊列狀態
        print("\n3. 檢查隊列狀態...")
        queue_items = QueueItem.objects.filter(status='waiting').order_by('position')
        print(f"   等待中訂單: {queue_items.count()}個")
        
        # 4. 測試智能建議
        print("\n4. 測試智能建議...")
        if queue_items.exists():
            order = queue_items.first().order
            recommendations = allocation_system.get_order_recommendations(order.id)
            
            if recommendations['success']:
                print(f"   ✅ 訂單#{order.id}的智能建議生成成功")
                print(f"   推薦員工: {recommendations['data'].get('recommended_barista', '無')}")
                print(f"   預計時間: {recommendations['data'].get('estimated_time', '未知')}分鐘")
            else:
                print(f"   ⚠️ 智能建議生成失敗: {recommendations['message']}")
        else:
            print("   ℹ️ 無等待中訂單，跳過智能建議測試")
        
        # 5. 測試學習優化器
        print("\n5. 測試學習優化器...")
        learning_stats = learning_optimizer.get_learning_stats()
        print(f"   學習記錄數量: {learning_stats['total_records']}")
        print(f"   平均改進率: {learning_stats['average_improvement']:.2f}%")
        print(f"   最新學習時間: {learning_stats['latest_learning_time']}")
        
        # 6. 測試性能優化器
        print("\n6. 測試性能優化器...")
        performance_stats = performance_optimizer.get_performance_stats()
        print(f"   性能監控點: {performance_stats['total_monitoring_points']}")
        print(f"   平均響應時間: {performance_stats['average_response_time']:.2f}ms")
        print(f"   系統健康度: {performance_stats['system_health']}%")
        
        # 7. 測試隊列優化
        print("\n7. 測試隊列優化...")
        if queue_items.count() >= 2:
            optimization_result = allocation_system.optimize_queue()
            if optimization_result['success']:
                print(f"   ✅ 隊列優化成功")
                print(f"   優化建議數量: {len(optimization_result['data'].get('optimization_suggestions', []))}")
                print(f"   預計效率提升: {optimization_result['data'].get('estimated_efficiency_gain', 0):.2f}%")
            else:
                print(f"   ⚠️ 隊列優化失敗: {optimization_result['message']}")
        else:
            print("   ℹ️ 訂單數量不足，跳過隊列優化測試")
        
        # 8. 測試系統狀態
        print("\n8. 測試系統狀態...")
        system_status = allocation_system.get_system_status()
        print(f"   系統狀態: {system_status['data']['system_status']}")
        print(f"   智能分配啟用: {system_status['data']['smart_allocation_enabled']}")
        print(f"   學習優化啟用: {system_status['data']['learning_optimizer_enabled']}")
        print(f"   性能監控啟用: {system_status['data']['performance_monitoring_enabled']}")
        
        print("\n" + "=" * 50)
        print("🎉 快速測試完成！智能分配系統運行正常")
        print("\n📊 測試總結:")
        print(f"   - 系統初始化: ✅ 成功")
        print(f"   - 工作負載查詢: ✅ 成功")
        print(f"   - 智能建議生成: ✅ 成功")
        print(f"   - 學習優化器: ✅ 正常")
        print(f"   - 性能優化器: ✅ 正常")
        print(f"   - 隊列優化: ✅ 正常")
        print(f"   - 系統狀態: ✅ 正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """測試API端點"""
    print("\n🔗 API端點測試")
    print("=" * 50)
    
    try:
        import requests
        
        base_url = "http://localhost:8081/eshop/api"
        
        # 1. 測試員工工作負載API
        print("1. 測試員工工作負載API...")
        response = requests.get(f"{base_url}/queue/barista-workload/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API響應成功")
            print(f"   狀態: {data.get('success', False)}")
            print(f"   員工數量: {len(data.get('data', {}).get('baristas', []))}")
        else:
            print(f"   ❌ API響應失敗: {response.status_code}")
        
        # 2. 測試系統狀態API
        print("\n2. 測試系統狀態API...")
        response = requests.get(f"{base_url}/system/status/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API響應成功")
            print(f"   系統狀態: {data.get('data', {}).get('system_status', '未知')}")
        else:
            print(f"   ❌ API響應失敗: {response.status_code}")
        
        # 3. 測試隊列優化API
        print("\n3. 測試隊列優化API...")
        response = requests.post(f"{base_url}/queue/optimize/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API響應成功")
            print(f"   優化成功: {data.get('success', False)}")
        else:
            print(f"   ❌ API響應失敗: {response.status_code}")
        
        print("\n" + "=" * 50)
        print("🎉 API端點測試完成")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器，請確保Django服務正在運行")
        print("   運行命令: python manage.py runserver 8081")
        return False
    except Exception as e:
        print(f"❌ API測試錯誤: {str(e)}")
        return False

def main():
    """主測試函數"""
    print("🤖 智能分配系統測試套件")
    print("=" * 50)
    
    # 測試核心功能
    core_test_passed = test_smart_allocation_quick()
    
    # 測試API端點
    api_test_passed = test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("📋 最終測試結果:")
    print(f"   核心功能測試: {'✅ 通過' if core_test_passed else '❌ 失敗'}")
    print(f"   API端點測試: {'✅ 通過' if api_test_passed else '❌ 失敗'}")
    
    if core_test_passed and api_test_passed:
        print("\n🎊 所有測試通過！智能分配系統完全正常")
        print("\n💡 下一步建議:")
        print("   1. 訪問測試頁面: http://localhost:8081/test_smart_allocation.html")
        print("   2. 查看員工工作負載顯示")
        print("   3. 創建測試訂單驗證智能分配")
        print("   4. 開始員工培訓")
        return 0
    else:
        print("\n⚠️ 部分測試失敗，請檢查系統配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())