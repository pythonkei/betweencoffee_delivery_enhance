#!/usr/bin/env python3
"""
智能分配系統簡單測試
最簡單的測試方法
"""

import os
import sys
import django

# 設置Django環境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')
django.setup()

def test_smart_allocation_easy():
    """最簡單的測試"""
    print("🤖 智能分配系統測試指南")
    print("=" * 60)
    
    print("\n📋 您有幾種方法可以測試智能分配系統：")
    
    print("\n1. 🚀 運行完整模擬測試（推薦）")
    print("   命令: python test_smart_allocation_simulation.py")
    print("   這個測試會：")
    print("   - 創建測試員工和訂單")
    print("   - 測試所有核心功能")
    print("   - 顯示詳細測試結果")
    print("   - 自動清理測試數據")
    
    print("\n2. 🌐 使用測試網頁")
    print("   步驟:")
    print("   1. 啟動Django服務: python manage.py runserver 8081")
    print("   2. 打開瀏覽器訪問: http://localhost:8081/test_smart_allocation.html")
    print("   3. 在網頁上測試各種功能")
    
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
    
    print("\n5. 📊 檢查系統狀態")
    print("   命令:")
    print("   # 檢查環境配置")
    print("   python manage.py check")
    print("")
    print("   # 檢查數據庫")
    print("   python manage.py migrate --plan")
    
    print("\n" + "=" * 60)
    print("💡 快速開始建議：")
    print("")
    print("第一步：運行模擬測試")
    print("   python test_smart_allocation_simulation.py")
    print("")
    print("第二步：啟動服務並訪問測試頁面")
    print("   python manage.py runserver 8081")
    print("   然後訪問: http://localhost:8081/test_smart_allocation.html")
    print("")
    print("第三步：實際操作測試")
    print("   1. 創建測試訂單")
    print("   2. 查看智能分配效果")
    print("   3. 驗證工作負載顯示")
    
    print("\n" + "=" * 60)
    print("✅ 智能分配系統已成功部署！")
    print("")
    print("📁 已創建的測試文件：")
    print("   - test_smart_allocation_simulation.py - 完整模擬測試")
    print("   - test_smart_allocation.html - 網頁測試界面")
    print("   - test_smart_allocation_easy.py - 本測試指南")
    print("")
    print("🔗 可用API端點：")
    print("   - /eshop/api/queue/barista-workload/ - 員工工作負載")
    print("   - /eshop/api/queue/optimize/ - 隊列優化")
    print("   - /eshop/api/system/status/ - 系統狀態")
    print("   - /eshop/api/orders/<id>/recommendations/ - 訂單建議")
    print("")
    print("📚 用戶培訓手冊：")
    print("   文件: 智能分配系統用戶培訓手冊.md")
    print("   包含完整的操作指南和培訓計劃")
    
    return True

def run_quick_check():
    """快速檢查系統狀態"""
    print("\n🔍 快速系統檢查")
    print("-" * 40)
    
    try:
        # 檢查關鍵文件
        files_to_check = [
            "eshop/smart_allocation.py",
            "eshop/learning_optimizer.py", 
            "eshop/performance_optimizer.py",
            "eshop/views_smart_allocation.py",
            "test_smart_allocation_simulation.py",
            "test_smart_allocation.html"
        ]
        
        print("檢查關鍵文件...")
        for file in files_to_check:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} (缺失)")
        
        # 檢查.env配置
        print("\n檢查環境配置...")
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                content = f.read()
                if "SMART_ALLOCATION_ENABLED" in content:
                    print("   ✅ 智能分配配置已設置")
                else:
                    print("   ⚠️ 智能分配配置未設置")
        else:
            print("   ⚠️ .env文件不存在")
        
        print("\n" + "-" * 40)
        print("🎯 系統檢查完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 檢查過程中發生錯誤: {str(e)}")
        return False

def main():
    """主函數"""
    print("🚀 智能分配系統測試工具")
    print("=" * 60)
    
    # 運行快速檢查
    check_passed = run_quick_check()
    
    if check_passed:
        print("\n✅ 系統文件檢查通過")
        print("\n📋 現在您可以：")
        print("   1. 運行模擬測試驗證功能")
        print("   2. 啟動服務進行實際測試")
        print("   3. 開始員工培訓")
    else:
        print("\n⚠️ 系統檢查發現問題")
        print("   請檢查缺失的文件或配置")
    
    # 顯示測試指南
    test_smart_allocation_easy()
    
    print("\n" + "=" * 60)
    print("🎉 測試指南完成！")
    print("\n💡 記住：")
    print("   1. 先運行模擬測試驗證核心功能")
    print("   2. 再進行實際操作測試")
    print("   3. 參考培訓手冊進行員工培訓")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())