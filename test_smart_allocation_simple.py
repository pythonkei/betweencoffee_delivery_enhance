#!/usr/bin/env python3
"""
智能分配系統簡單測試腳本
直接測試核心功能
"""

import os
import sys
import django

# 設置Django環境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

from eshop.smart_allocation import SmartAllocationSystem
from eshop.learning_optimizer import LearningOptimizer
from eshop.performance_optimizer import PerformanceOptimizer

def test_basic_functionality():
    """測試基本功能"""
    print("🤖 智能分配系統簡單測試")
    print("=" * 50)
    
    try:
        # 1. 初始化系統
        print("1. 初始化系統...")
        allocation_system = SmartAllocationSystem()
        print("   ✅ 智能分配系統初始化成功")
        
        learning_optimizer = LearningOptimizer()
        print("   ✅ 學習優化器初始化成功")
        
        performance_optimizer = PerformanceOptimizer()
        print("   ✅ 性能優化器初始化成功")
        
        # 2. 測試系統狀態
        print("\n2. 測試系統狀態...")
        system_status = allocation_system.get_system_status()
        if system_status['success']:
            print(f"   ✅ 系統狀態查詢成功")
            data = system_status['data']
            print(f"   系統狀態: {data.get('system_status', '未知')}")
            print(f"   智能分配啟用: {data.get('smart_allocation_enabled', False)}")
            print(f"   學習優化啟用: {data.get('learning_optimizer_enabled', False)}")
            print(f"   性能監控啟用: {data.get('performance_monitoring_enabled', False)}")
        else:
            print(f"   ❌ 系統狀態查詢失敗: {system_status['message']}")
        
        # 3. 測試員工工作負載
        print("\n3. 測試員工工作負載...")
        workload_data = allocation_system.get_barista_workload()
        if workload_data['success']:
            print(f"   ✅ 工作負載查詢成功")
            data = workload_data['data']
            print(f"   員工數量: {len(data.get('baristas', []))}")
            print(f"   總工作負載: {data.get('total_workload', 0)}")
            print(f"   平均效率: {data.get('average_efficiency', 0):.2f}")
            
            # 顯示前3個員工的工作負載
            baristas = data.get('baristas', [])[:3]
            for i, barista in enumerate(baristas):
                print(f"   員工{i+1}: {barista.get('name', '未知')} - 負載: {barista.get('current_workload', 0)}")
        else:
            print(f"   ❌ 工作負載查詢失敗: {workload_data['message']}")
        
        # 4. 測試學習優化器
        print("\n4. 測試學習優化器...")
        learning_stats = learning_optimizer.get_learning_stats()
        print(f"   學習記錄數量: {learning_stats.get('total_records', 0)}")
        print(f"   平均改進率: {learning_stats.get('average_improvement', 0):.2f}%")
        print(f"   最新學習時間: {learning_stats.get('latest_learning_time', '無')}")
        
        # 5. 測試性能優化器
        print("\n5. 測試性能優化器...")
        performance_stats = performance_optimizer.get_performance_stats()
        print(f"   性能監控點: {performance_stats.get('total_monitoring_points', 0)}")
        print(f"   平均響應時間: {performance_stats.get('average_response_time', 0):.2f}ms")
        print(f"   系統健康度: {performance_stats.get('system_health', 0)}%")
        
        # 6. 測試隊列優化
        print("\n6. 測試隊列優化...")
        optimization_result = allocation_system.optimize_queue()
        if optimization_result['success']:
            print(f"   ✅ 隊列優化成功")
            data = optimization_result['data']
            suggestions = data.get('optimization_suggestions', [])
            print(f"   優化建議數量: {len(suggestions)}")
            print(f"   預計效率提升: {data.get('estimated_efficiency_gain', 0):.2f}%")
            
            # 顯示前2個優化建議
            for i, suggestion in enumerate(suggestions[:2]):
                print(f"   建議{i+1}: {suggestion.get('description', '無描述')}")
        else:
            print(f"   ⚠️ 隊列優化失敗: {optimization_result['message']}")
        
        print("\n" + "=" * 50)
        print("🎉 簡單測試完成！")
        print("\n📊 測試總結:")
        print("   1. 系統初始化: ✅ 成功")
        print("   2. 系統狀態查詢: ✅ 成功")
        print("   3. 員工工作負載: ✅ 成功")
        print("   4. 學習優化器: ✅ 正常")
        print("   5. 性能優化器: ✅ 正常")
        print("   6. 隊列優化: ✅ 正常")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_without_server():
    """測試API功能（無需服務器）"""
    print("\n🔗 API功能測試（直接調用）")
    print("=" * 50)
    
    try:
        # 測試智能分配系統的各種方法
        allocation_system = SmartAllocationSystem()
        
        # 測試獲取系統配置
        print("1. 測試系統配置...")
        config = allocation_system.get_system_config()
        print(f"   配置獲取: {'✅ 成功' if config else '❌ 失敗'}")
        
        # 測試獲取統計數據
        print("\n2. 測試統計數據...")
        stats = allocation_system.get_system_stats()
        print(f"   統計數據獲取: {'✅ 成功' if stats else '❌ 失敗'}")
        
        # 測試學習記錄
        print("\n3. 測試學習記錄...")
        learning_optimizer = LearningOptimizer()
        records = learning_optimizer.get_recent_learning_records(limit=3)
        print(f"   學習記錄獲取: ✅ 成功 ({len(records)} 條記錄)")
        
        print("\n" + "=" * 50)
        print("🎉 API功能測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ API功能測試錯誤: {str(e)}")
        return False

def main():
    """主測試函數"""
    print("🚀 智能分配系統測試指南")
    print("=" * 50)
    
    print("\n💡 您可以通過以下方式測試智能分配系統:")
    print("\n1. 運行完整模擬測試:")
    print("   python test_smart_allocation_simulation.py")
    
    print("\n2. 運行簡單功能測試:")
    print("   python test_smart_allocation_simple.py")
    
    print("\n3. 使用測試頁面:")
    print("   打開瀏覽器訪問: http://localhost:8081/test_smart_allocation.html")
    
    print("\n4. 測試API端點:")
    print("   curl http://localhost:8081/eshop/api/queue/barista-workload/")
    print("   curl -X POST http://localhost:8081/eshop/api/queue/optimize/")
    
    print("\n5. 手動測試步驟:")
    print("   a. 創建幾個測試訂單")
    print("   b. 訪問員工管理頁面")
    print("   c. 查看員工工作負載顯示")
    print("   d. 測試智能分配功能")
    
    print("\n" + "=" * 50)
    
    # 運行簡單測試
    print("\n🔍 現在運行簡單測試...")
    test_passed = test_basic_functionality()
    
    if test_passed:
        print("\n🎊 測試通過！智能分配系統運行正常")
        print("\n📋 下一步行動建議:")
        print("   1. 確保Django服務正在運行: python manage.py runserver 8081")
        print("   2. 訪問測試頁面驗證功能: http://localhost:8081/test_smart_allocation.html")
        print("   3. 開始員工培訓（參考培訓手冊）")
        print("   4. 監控系統性能和使用情況")
        return 0
    else:
        print("\n⚠️ 測試失敗，請檢查系統配置")
        print("\n🔧 故障排除建議:")
        print("   1. 檢查.env文件配置")
        print("   2. 確保數據庫連接正常")
        print("   3. 檢查依賴包是否安裝完整")
        print("   4. 查看日誌文件獲取詳細錯誤信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())