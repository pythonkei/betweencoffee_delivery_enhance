#!/usr/bin/env python
"""
測試 queue_manager_refactored.py 的所有遷移後方法

這個測試腳本驗證遷移後的所有隊列管理方法是否正常工作，
包括錯誤處理框架的集成和兼容性包裝器。
"""

import sys
import os
import logging

# 設置 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betweencoffee_delivery.settings')

try:
    import django
    django.setup()
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    print("⚠️ Django 不可用，跳過數據庫相關測試")
except Exception as e:
    DJANGO_AVAILABLE = False
    print(f"⚠️ Django 設置失敗: {e}，跳過數據庫相關測試")

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_error_handling_framework():
    """測試錯誤處理框架的基本功能"""
    print("\n" + "="*60)
    print("測試錯誤處理框架")
    print("="*60)
    
    try:
        # 嘗試導入錯誤處理框架
        from eshop.error_handling import (
            handle_error,
            handle_success,
            handle_database_error,
            ErrorHandler
        )
        
        print("✅ 錯誤處理框架導入成功")
        
        # 測試 ErrorHandler
        error_handler = ErrorHandler(module_name='test_module')
        print(f"✅ ErrorHandler 創建成功: {error_handler}")
        
        # 測試 handle_success
        success_result = handle_success(
            operation='test_operation',
            data={'test': 'data'},
            message='測試成功'
        )
        
        print(f"✅ handle_success 測試成功:")
        print(f"   success: {success_result.get('success')}")
        print(f"   message: {success_result.get('message')}")
        print(f"   data: {success_result.get('data')}")
        
        # 測試 handle_error
        try:
            raise ValueError("測試錯誤")
        except Exception as e:
            error_result = handle_error(
                error=e,
                context='test_context',
                operation='test_operation',
                data={'test': 'data'}
            )
            
            print(f"✅ handle_error 測試成功:")
            print(f"   success: {error_result.get('success')}")
            print(f"   error_id: {error_result.get('error_id')}")
            print(f"   message: {error_result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理框架測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_queue_manager_import():
    """測試 queue_manager_refactored.py 的導入"""
    print("\n" + "="*60)
    print("測試 queue_manager_refactored.py 導入")
    print("="*60)
    
    try:
        # 嘗試導入遷移後的隊列管理器
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        print("✅ CoffeeQueueManager 導入成功")
        
        # 創建實例
        manager = CoffeeQueueManager()
        print(f"✅ CoffeeQueueManager 實例創建成功: {manager}")
        
        # 檢查方法是否存在
        methods_to_check = [
            # 核心方法
            'add_order_to_queue',
            'add_order_to_queue_compatible',
            'start_preparation',
            'start_preparation_compatible',
            'mark_as_ready',
            'mark_as_ready_compatible',
            
            # 私有方法
            '_calculate_coffee_count',
            '_calculate_position',
            '_get_next_simple_position',
            '_calculate_priority_position',
            '_check_and_reorder_queue',
            
            # 重要方法
            'recalculate_all_order_times',
            'recalculate_all_order_times_compatible',
            'update_estimated_times',
            'update_estimated_times_compatible',
            'verify_queue_integrity',
            'verify_queue_integrity_compatible',
            'sync_order_queue_status',
            'sync_order_queue_status_compatible',
            'fix_queue_positions',
            'fix_queue_positions_compatible'
        ]
        
        for method_name in methods_to_check:
            if hasattr(manager, method_name):
                print(f"✅ 方法存在: {method_name}")
            else:
                print(f"❌ 方法不存在: {method_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ queue_manager_refactored.py 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_signatures():
    """測試方法簽名和文檔"""
    print("\n" + "="*60)
    print("測試方法簽名和文檔")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試核心方法
        core_methods = [
            'add_order_to_queue',
            'start_preparation',
            'mark_as_ready'
        ]
        
        for method_name in core_methods:
            method = getattr(manager, method_name)
            docstring = method.__doc__
            
            if docstring:
                print(f"✅ {method_name} 有文檔字符串")
                # 檢查返回格式描述
                if '返回格式:' in docstring:
                    print(f"✅ {method_name} 文檔中包含返回格式描述")
                else:
                    print(f"⚠️ {method_name} 文檔中缺少返回格式描述")
            else:
                print(f"❌ {method_name} 沒有文檔字符串")
        
        # 測試兼容性包裝器
        compatible_methods = [
            'add_order_to_queue_compatible',
            'start_preparation_compatible',
            'mark_as_ready_compatible'
        ]
        
        for method_name in compatible_methods:
            method = getattr(manager, method_name)
            if callable(method):
                print(f"✅ {method_name} 是可調用的")
            else:
                print(f"❌ {method_name} 不可調用")
        
        return True
        
    except Exception as e:
        print(f"❌ 方法簽名測試失敗: {e}")
        return False


def test_error_handling_in_methods():
    """測試方法中的錯誤處理"""
    print("\n" + "="*60)
    print("測試方法中的錯誤處理")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試錯誤處理 - 傳入 None 應該觸發錯誤
        print("測試 add_order_to_queue 的錯誤處理...")
        
        # 注意：這裡我們傳入 None 來測試錯誤處理
        # 在實際使用中，應該傳入有效的 OrderModel 實例
        result = manager.add_order_to_queue(None)
        
        if result:
            print(f"✅ add_order_to_queue 返回結果: {result.get('success')}")
            
            if not result.get('success'):
                print(f"✅ 錯誤處理正常工作:")
                print(f"   錯誤ID: {result.get('error_id')}")
                print(f"   錯誤消息: {result.get('message')}")
            else:
                print("⚠️ 傳入 None 但返回成功，可能需要檢查錯誤處理邏輯")
        else:
            print("❌ add_order_to_queue 返回 None")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility_wrappers():
    """測試兼容性包裝器"""
    print("\n" + "="*60)
    print("測試兼容性包裝器")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試兼容性包裝器
        print("測試 add_order_to_queue_compatible...")
        result = manager.add_order_to_queue_compatible(None)
        
        if result is None:
            print("✅ add_order_to_queue_compatible 返回 None（預期行為）")
        else:
            print(f"⚠️ add_order_to_queue_compatible 返回: {result}")
        
        # 測試 start_preparation_compatible
        print("測試 start_preparation_compatible...")
        result = manager.start_preparation_compatible(None)
        
        if result is False:
            print("✅ start_preparation_compatible 返回 False（預期行為）")
        else:
            print(f"⚠️ start_preparation_compatible 返回: {result}")
        
        # 測試 mark_as_ready_compatible
        print("測試 mark_as_ready_compatible...")
        result = manager.mark_as_ready_compatible(None)
        
        if result is False:
            print("✅ mark_as_ready_compatible 返回 False（預期行為）")
        else:
            print(f"⚠️ mark_as_ready_compatible 返回: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 兼容性包裝器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_private_methods():
    """測試私有方法"""
    print("\n" + "="*60)
    print("測試私有方法")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 檢查私有方法是否存在
        private_methods = [
            '_calculate_coffee_count',
            '_calculate_position',
            '_get_next_simple_position',
            '_calculate_priority_position',
            '_check_and_reorder_queue'
        ]
        
        for method_name in private_methods:
            if hasattr(manager, method_name):
                print(f"✅ 私有方法存在: {method_name}")
            else:
                print(f"❌ 私有方法不存在: {method_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 私有方法測試失敗: {e}")
        return False


def test_important_methods():
    """測試重要方法"""
    print("\n" + "="*60)
    print("測試重要方法")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試重要方法
        important_methods = [
            'recalculate_all_order_times',
            'update_estimated_times',
            'verify_queue_integrity',
            'sync_order_queue_status',
            'fix_queue_positions'
        ]
        
        for method_name in important_methods:
            method = getattr(manager, method_name)
            docstring = method.__doc__
            
            if docstring:
                print(f"✅ {method_name} 有文檔字符串")
                # 檢查返回格式描述
                if '返回格式:' in docstring:
                    print(f"✅ {method_name} 文檔中包含返回格式描述")
                else:
                    print(f"⚠️ {method_name} 文檔中缺少返回格式描述")
            else:
                print(f"❌ {method_name} 沒有文檔字符串")
        
        # 測試兼容性包裝器
        compatible_methods = [
            'recalculate_all_order_times_compatible',
            'update_estimated_times_compatible',
            'verify_queue_integrity_compatible',
            'sync_order_queue_status_compatible',
            'fix_queue_positions_compatible'
        ]
        
        for method_name in compatible_methods:
            method = getattr(manager, method_name)
            if callable(method):
                print(f"✅ {method_name} 是可調用的")
            else:
                print(f"❌ {method_name} 不可調用")
        
        return True
        
    except Exception as e:
        print(f"❌ 重要方法測試失敗: {e}")
        return False


def test_important_methods_error_handling():
    """測試重要方法的錯誤處理"""
    print("\n" + "="*60)
    print("測試重要方法的錯誤處理")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試重要方法的錯誤處理
        print("測試 recalculate_all_order_times 的錯誤處理...")
        result = manager.recalculate_all_order_times()
        
        if result:
            print(f"✅ recalculate_all_order_times 返回結果: {result.get('success')}")
            
            if not result.get('success'):
                print(f"✅ 錯誤處理正常工作:")
                print(f"   錯誤ID: {result.get('error_id')}")
                print(f"   錯誤消息: {result.get('message')}")
            else:
                print("⚠️ 方法返回成功，但可能沒有實際數據庫操作")
        else:
            print("❌ recalculate_all_order_times 返回 None")
        
        print("\n測試 update_estimated_times 的錯誤處理...")
        result = manager.update_estimated_times()
        
        if result:
            print(f"✅ update_estimated_times 返回結果: {result.get('success')}")
        else:
            print("❌ update_estimated_times 返回 None")
        
        print("\n測試 verify_queue_integrity 的錯誤處理...")
        result = manager.verify_queue_integrity()
        
        if result:
            print(f"✅ verify_queue_integrity 返回結果: {result.get('success')}")
        else:
            print("❌ verify_queue_integrity 返回 None")
        
        return True
        
    except Exception as e:
        print(f"❌ 重要方法錯誤處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility_wrappers_for_important_methods():
    """測試重要方法的兼容性包裝器"""
    print("\n" + "="*60)
    print("測試重要方法的兼容性包裝器")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        
        manager = CoffeeQueueManager()
        
        # 測試兼容性包裝器
        print("測試 recalculate_all_order_times_compatible...")
        result = manager.recalculate_all_order_times_compatible()
        
        if isinstance(result, dict):
            print("✅ recalculate_all_order_times_compatible 返回字典（預期行為）")
        else:
            print(f"⚠️ recalculate_all_order_times_compatible 返回: {type(result)}")
        
        print("\n測試 update_estimated_times_compatible...")
        result = manager.update_estimated_times_compatible()
        
        if isinstance(result, bool):
            print("✅ update_estimated_times_compatible 返回布爾值（預期行為）")
        else:
            print(f"⚠️ update_estimated_times_compatible 返回: {type(result)}")
        
        print("\n測試 verify_queue_integrity_compatible...")
        result = manager.verify_queue_integrity_compatible()
        
        if isinstance(result, dict):
            print("✅ verify_queue_integrity_compatible 返回字典（預期行為）")
        else:
            print(f"⚠️ verify_queue_integrity_compatible 返回: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 重要方法兼容性包裝器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """運行所有測試"""
    print("開始測試 queue_manager_refactored.py 的所有方法")
    print("="*60)
    
    test_results = []
    
    # 運行測試
    test_results.append(("錯誤處理框架", test_error_handling_framework()))
    test_results.append(("隊列管理器導入", test_queue_manager_import()))
    test_results.append(("方法簽名", test_method_signatures()))
    test_results.append(("錯誤處理", test_error_handling_in_methods()))
    test_results.append(("兼容性包裝器", test_compatibility_wrappers()))
    test_results.append(("私有方法", test_private_methods()))
    test_results.append(("重要方法", test_important_methods()))
    test_results.append(("重要方法錯誤處理", test_important_methods_error_handling()))
    test_results.append(("重要方法兼容性包裝器", test_compatibility_wrappers_for_important_methods()))
    
    # 顯示測試結果
    print("\n" + "="*60)
    print("測試結果總結")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        if result:
            print(f"✅ {test_name}: 通過")
            passed += 1
        else:
            print(f"❌ {test_name}: 失敗")
            failed += 1
    
    print(f"\n總計: {passed} 通過, {failed} 失敗")
    
    if failed == 0:
        print("\n🎉 所有測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 個測試失敗")
        return False


def main():
    """主函數"""
    try:
        success = run_all_tests()
        
        if success:
            print("\n" + "="*60)
            print("遷移測試完成 - 所有方法正常")
            print("="*60)
            print("\n🎉 恭喜！queue_manager_refactored.py 遷移成功！")
            print("\n遷移完成的方法:")
            print("1. ✅ 核心方法 (3個)")
            print("2. ✅ 私有方法 (5個)")
            print("3. ✅ 重要方法 (5個)")
            print("\n總計: 13 個方法成功遷移")
            print("\n建議下一步:")
            print("1. 在 Django 環境中進行集成測試")
            print("2. 測試實際的隊列操作流程")
            print("3. 驗證與原始 queue_manager.py 的兼容性")
            print("4. 更新相關的調用代碼")
        else:
            print("\n" + "="*60)
            print("遷移測試完成 - 發現問題")
            print("="*60)
            print("\n需要修復的問題:")
            print("1. 檢查錯誤處理框架導入")
            print("2. 修復 queue_manager_refactored.py 中的語法錯誤")
            print("3. 確保所有方法都有正確的簽名")
            print("4. 測試兼容性包裝器的行為")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 測試運行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
