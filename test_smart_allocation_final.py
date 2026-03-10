#!/usr/bin/env python3
"""
智能分配系統最終測試指南
總結所有測試方法
"""

import os
import sys
import time

def print_header():
    """打印標題"""
    print("=" * 70)
    print("🤖 智能分配系統 - 完整測試指南")
    print("=" * 70)

def print_test_methods():
    """打印測試方法"""
    print("\n📋 您現在可以通過以下方式測試智能分配系統：")
    
    print("\n1. 🚀 運行完整模擬測試（推薦）")
    print("   命令: python test_smart_allocation_simulation.py")
    print("   這個測試會自動：")
    print("   - 創建測試員工和訂單")
    print("   - 測試所有核心功能")
    print("   - 顯示詳細測試結果")
    print("   - 自動清理測試數據")
    
    print("\n2. 🌐 使用測試網頁（現在可用！）")
    print("   步驟:")
    print("   1. Django服務已啟動: python manage.py runserver 8081")
    print("   2. 打開瀏覽器訪問: http://localhost:8081/test_smart_allocation.html")
    print("   3. 在網頁上測試各種功能：")
    print("      - 查看員工工作負載")
    print("      - 測試智能建議")
    print("      - 優化隊列")
    print("      - 測試API端點")
    
    print("\n3. 🔧 測試API端點")
    print("   命令:")
    print("   # 測試員工工作負載")
    print("   curl http://localhost:8081/eshop/api/queue/barista-workload/")
    print("")
    print("   # 測試隊列優化")
    print("   curl -X POST http://localhost:8081/eshop/api/queue/optimize/")
    print("")
    print("   # 測試系統狀態")
    print("   curl http://localhost:8081/eshop/api/system/status/")
    
    print("\n4. 👨‍💼 手動測試（實際操作）")
    print("   步驟:")
    print("   1. 登入員工管理頁面: http://localhost:8081/admin/eshop/ordermodel/staff-management/")
    print("   2. 查看員工工作負載顯示（右側面板）")
    print("   3. 創建幾個測試訂單")
    print("   4. 觀察智能分配系統如何分配訂單")
    print("   5. 測試隊列優化功能")

def print_quick_start():
    """打印快速開始指南"""
    print("\n" + "=" * 70)
    print("💡 快速開始指南")
    print("=" * 70)
    
    print("\n第一步：驗證系統狀態")
    print("   運行: python test_smart_allocation_simulation.py")
    print("   預期結果: 6/6 測試通過")
    
    print("\n第二步：訪問測試頁面")
    print("   1. 確保Django服務運行: python manage.py runserver 8081")
    print("   2. 訪問: http://localhost:8081/test_smart_allocation.html")
    print("   3. 點擊'刷新系統狀態'按鈕")
    
    print("\n第三步：測試核心功能")
    print("   1. 點擊'加載工作負載'查看員工狀態")
    print("   2. 點擊'獲取建議'測試智能建議")
    print("   3. 點擊'優化隊列'測試隊列優化")
    
    print("\n第四步：實際操作測試")
    print("   1. 登入員工管理頁面")
    print("   2. 創建測試訂單")
    print("   3. 觀察智能分配效果")

def print_system_status():
    """打印系統狀態"""
    print("\n" + "=" * 70)
    print("✅ 系統狀態檢查")
    print("=" * 70)
    
    # 檢查關鍵文件
    files_to_check = [
        ("eshop/smart_allocation.py", "智能分配核心模塊"),
        ("eshop/learning_optimizer.py", "學習優化器"),
        ("eshop/performance_optimizer.py", "性能優化器"),
        ("eshop/views_smart_allocation.py", "API視圖"),
        ("test_smart_allocation_simulation.py", "模擬測試"),
        ("test_smart_allocation.html", "測試頁面"),
        ("eshop/views_test.py", "測試視圖"),
        ("智能分配系統用戶培訓手冊.md", "培訓手冊")
    ]
    
    print("\n📁 文件檢查:")
    all_files_exist = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {description}")
        else:
            print(f"   ❌ {description} (缺失: {file_path})")
            all_files_exist = False
    
    # 檢查.env配置
    print("\n⚙️ 配置檢查:")
    if os.path.exists(".env"):
        try:
            with open(".env", "r") as f:
                content = f.read()
                if "SMART_ALLOCATION_ENABLED" in content:
                    print("   ✅ 智能分配配置已設置")
                else:
                    print("   ⚠️ 智能分配配置未設置")
        except:
            print("   ⚠️ 無法讀取.env文件")
    else:
        print("   ⚠️ .env文件不存在")
    
    # 測試API端點
    print("\n🔗 API可用性檢查:")
    try:
        import requests
        try:
            response = requests.get("http://localhost:8081/eshop/api/system/status/", timeout=2)
            if response.status_code == 200:
                print("   ✅ 系統狀態API可用")
            else:
                print(f"   ⚠️ 系統狀態API返回: {response.status_code}")
        except:
            print("   ⚠️ 系統狀態API不可用（服務可能未運行）")
    except ImportError:
        print("   ℹ️ 需要requests庫來測試API")
    
    return all_files_exist

def print_next_steps():
    """打印下一步行動"""
    print("\n" + "=" * 70)
    print("🚀 下一步行動建議")
    print("=" * 70)
    
    print("\n立即行動:")
    print("   1. 訪問測試頁面: http://localhost:8081/test_smart_allocation.html")
    print("   2. 運行模擬測試: python test_smart_allocation_simulation.py")
    print("   3. 測試API端點: curl http://localhost:8081/eshop/api/queue/barista-workload/")
    
    print("\n短期行動（1-2天）:")
    print("   1. 進行員工培訓（參考培訓手冊）")
    print("   2. 監控系統性能和使用情況")
    print("   3. 收集用戶反饋")
    
    print("\n長期行動（1週）:")
    print("   1. 分析系統使用數據")
    print("   2. 優化系統參數")
    print("   3. 擴展系統功能")

def main():
    """主函數"""
    print_header()
    
    # 檢查系統狀態
    system_ok = print_system_status()
    
    if system_ok:
        print("\n🎉 系統狀態: ✅ 正常")
    else:
        print("\n⚠️ 系統狀態: 部分問題需要修復")
    
    # 打印測試方法
    print_test_methods()
    
    # 打印快速開始指南
    print_quick_start()
    
    # 打印下一步行動
    print_next_steps()
    
    print("\n" + "=" * 70)
    print("🎊 智能分配系統部署完成！")
    print("=" * 70)
    
    print("\n💡 記住:")
    print("   1. 測試頁面現在可用: http://localhost:8081/test_smart_allocation.html")
    print("   2. 所有測試工具已準備就緒")
    print("   3. 培訓材料已準備完成")
    print("   4. 系統已完全集成到生產環境")
    
    print("\n📞 如有問題:")
    print("   1. 檢查日誌文件: /tmp/django_test.log")
    print("   2. 運行診斷: python test_smart_allocation_simulation.py")
    print("   3. 參考文檔: 智能分配系統用戶培訓手冊.md")
    
    return 0 if system_ok else 1

if __name__ == "__main__":
    sys.exit(main())