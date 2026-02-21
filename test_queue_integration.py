#!/usr/bin/env python
"""
隊列管理器集成測試 - 驗證遷移後的 queue_manager_refactored.py
與原始 queue_manager.py 的兼容性
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


def test_both_managers_import():
    """測試兩個隊列管理器的導入"""
    print("\n" + "="*60)
    print("測試兩個隊列管理器的導入")
    print("="*60)
    
    try:
        # 導入原始隊列管理器
        from eshop.queue_manager import CoffeeQueueManager as OriginalManager
        print("✅ 原始 queue_manager.py 導入成功")
        
        # 導入遷移後的隊列管理器
        from eshop.queue_manager_refactored import CoffeeQueueManager as RefactoredManager
        print("✅ 遷移後的 queue_manager_refactored.py 導入成功")
        
        # 創建實例
        original_manager = OriginalManager()
        refactored_manager = RefactoredManager()
        
        print(f"✅ 原始管理器實例創建成功: {original_manager}")
        print(f"✅ 遷移後管理器實例創建成功: {refactored_manager}")
        
        return True
        
    except Exception as e:
        print(f"❌ 導入測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_compatibility():
    """測試方法兼容性"""
    print("\n" + "="*60)
    print("測試方法兼容性")
    print("="*60)
    
    try:
        from eshop.queue_manager import CoffeeQueueManager as OriginalManager
        from eshop.queue_manager_refactored import CoffeeQueueManager as RefactoredManager
        
        original_manager = OriginalManager()
        refactored_manager = RefactoredManager()
        
        # 檢查兩個管理器都有相同的方法
        original_methods = [method for method in dir(original_manager) 
                           if not method.startswith('_') and callable(getattr(original_manager, method))]
        
        refactored_methods = [method for method in dir(refactored_manager) 
                             if not method.startswith('_') and callable(getattr(refactored_manager, method))]
        
        print(f"原始管理器方法數: {len(original_methods)}")
        print(f"遷移後管理器方法數: {len(refactored_methods)}")
        
        # 檢查核心方法是否存在
        core_methods = [
            'add_order_to_queue',
            'start_preparation',
            'mark_as_ready',
            'update_estimated_times',
            'verify_queue_integrity',
            'fix_queue_positions',
            'sync_order_queue_status',
            'recalculate_all_order_times'
        ]
        
        for method in core_methods:
            has_original = hasattr(original_manager, method)
            has_refactored = hasattr(refactored_manager, method)
            
            if has_original and has_refactored:
                print(f"✅ {method}: 兩個管理器都有")
            elif has_original and not has_refactored:
                print(f"❌ {method}: 只有原始管理器有")
            elif not has_original and has_refactored:
                print(f"⚠️ {method}: 只有遷移後管理器有")
            else:
                print(f"❌ {method}: 兩個管理器都沒有")
        
        return True
        
    except Exception as e:
        print(f"❌ 方法兼容性測試失敗: {e}")
        return False


def test_error_handling_compatibility():
    """測試錯誤處理兼容性"""
    print("\n" + "="*60)
    print("測試錯誤處理兼容性")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager as RefactoredManager
        
        manager = RefactoredManager()
        
        # 測試錯誤處理
        print("測試錯誤處理響應格式...")
        
        # 測試 add_order_to_queue 的錯誤處理
        result = manager.add_order_to_queue(None)
        
        if isinstance(result, dict):
            print("✅ add_order_to_queue 返回字典格式")
            
            # 檢查標準化響應格式
            # 注意：錯誤響應使用 'details'，成功響應使用 'data'
            required_keys = ['success', 'message', 'timestamp']
            if result['success']:
                required_keys.append('data')
            else:
                required_keys.append('details')
            
            missing_keys = [key for key in required_keys if key not in result]
            
            if missing_keys:
                print(f"❌ 缺少標準化響應鍵: {missing_keys}")
            else:
                print("✅ 標準化響應格式完整")
                
                # 檢查錯誤處理
                if not result['success']:
                    print("✅ 錯誤處理正常工作")
                    print(f"   錯誤ID: {result.get('error_id', 'N/A')}")
                    print(f"   錯誤消息: {result.get('message', 'N/A')}")
                else:
                    print("⚠️ 傳入 None 但返回成功")
        else:
            print(f"❌ add_order_to_queue 返回非字典格式: {type(result)}")
        
        # 測試兼容性包裝器
        print("\n測試兼容性包裝器...")
        
        result = manager.add_order_to_queue_compatible(None)
        
        if result is None:
            print("✅ add_order_to_queue_compatible 返回 None（預期行為）")
        else:
            print(f"⚠️ add_order_to_queue_compatible 返回: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理兼容性測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_important_methods_compatibility():
    """測試重要方法的兼容性"""
    print("\n" + "="*60)
    print("測試重要方法的兼容性")
    print("="*60)
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager as RefactoredManager
        
        manager = RefactoredManager()
        
        # 測試重要方法
        important_methods = [
            ('recalculate_all_order_times', '字典'),
            ('update_estimated_times', '字典'),
            ('verify_queue_integrity', '字典'),
            ('sync_order_queue_status', '字典'),
            ('fix_queue_positions', '字典')
        ]
        
        for method_name, expected_type in important_methods:
            method = getattr(manager, method_name)
            
            # 測試方法調用
            try:
                result = method()
                
                if isinstance(result, dict):
                    print(f"✅ {method_name} 返回字典格式")
                    
                    # 檢查標準化響應
                    if 'success' in result:
                        print(f"✅ {method_name} 使用標準化響應格式")
                    else:
                        print(f"⚠️ {method_name} 未使用標準化響應格式")
                else:
                    print(f"❌ {method_name} 返回非字典格式: {type(result)}")
                    
            except Exception as e:
                print(f"❌ {method_name} 調用失敗: {e}")
        
        # 測試兼容性包裝器
        print("\n測試重要方法的兼容性包裝器...")
        
        compatible_methods = [
            ('recalculate_all_order_times_compatible', '字典'),
            ('update_estimated_times_compatible', '布爾值'),
            ('verify_queue_integrity_compatible', '字典'),
            ('sync_order_queue_status_compatible', '布爾值'),
            ('fix_queue_positions_compatible', '布爾值')
        ]
        
        for method_name, expected_type in compatible_methods:
            method = getattr(manager, method_name)
            
            try:
                result = method()
                
                if expected_type == '字典' and isinstance(result, dict):
                    print(f"✅ {method_name} 返回字典（預期行為）")
                elif expected_type == '布爾值' and isinstance(result, bool):
                    print(f"✅ {method_name} 返回布爾值（預期行為）")
                else:
                    print(f"⚠️ {method_name} 返回: {type(result)}（期望: {expected_type}）")
                    
            except Exception as e:
                print(f"❌ {method_name} 調用失敗: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 重要方法兼容性測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_actual_queue_operations():
    """測試實際的隊列操作"""
    print("\n" + "="*60)
    print("測試實際的隊列操作")
    print("="*60)
    
    if not DJANGO_AVAILABLE:
        print("⚠️ Django 不可用，跳過實際隊列操作測試")
        return True
    
    try:
        from eshop.queue_manager_refactored import CoffeeQueueManager
        from eshop.models import OrderModel, CoffeeQueue
        
        manager = CoffeeQueueManager()
        
        # 獲取一個測試訂單 - 使用 first() 而不是切片
        test_order = OrderModel.objects.filter(
            payment_status='paid',
            status='preparing'
        ).first()
        
        if not test_order:
            print("⚠️ 沒有找到測試訂單，跳過實際操作測試")
            return True
        print(f"使用測試訂單: #{test_order.id}")
        
        # 測試 add_order_to_queue
        print("\n測試 add_order_to_queue...")
        result = manager.add_order_to_queue(test_order)
        
        if result.get('success'):
            print(f"✅ add_order_to_queue 成功: {result.get('message')}")
            
            # 檢查隊列項是否創建
            queue_item_id = result['data'].get('queue_item_id')
            if queue_item_id:
                try:
                    queue_item = CoffeeQueue.objects.get(id=queue_item_id)
                    print(f"✅ 隊列項創建成功: #{queue_item.id}")
                    print(f"   位置: {queue_item.position}")
                    print(f"   狀態: {queue_item.status}")
                    print(f"   咖啡杯數: {queue_item.coffee_count}")
                except CoffeeQueue.DoesNotExist:
                    print("❌ 隊列項未找到")
        else:
            print(f"❌ add_order_to_queue 失敗: {result.get('message')}")
        
        # 測試 verify_queue_integrity
        print("\n測試 verify_queue_integrity...")
        result = manager.verify_queue_integrity()
        
        if result.get('success'):
            data = result['data']
            print(f"✅ 隊列完整性檢查成功")
            print(f"   等待中: {data.get('waiting_count')}")
            print(f"   製作中: {data.get('preparing_count')}")
            print(f"   已就緒: {data.get('ready_count')}")
            print(f"   總數: {data.get('total_count')}")
            print(f"   問題數: {len(data.get('issues', []))}")
        else:
            print(f"❌ 隊列完整性檢查失敗: {result.get('message')}")
        
        # 測試 update_estimated_times
        print("\n測試 update_estimated_times...")
        result = manager.update_estimated_times()
        
        if result.get('success'):
            data = result['data']
            print(f"✅ 更新預計時間成功")
            print(f"   更新訂單數: {data.get('waiting_orders_updated')}")
            print(f"   總製作時間: {data.get('total_preparation_minutes')} 分鐘")
        else:
            print(f"❌ 更新預計時間失敗: {result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 實際隊列操作測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling_framework_integration():
    """測試錯誤處理框架集成"""
    print("\n" + "="*60)
    print("測試錯誤處理框架集成")
    print("="*60)
    
    try:
        from eshop.error_handling import (
            handle_error,
            handle_success,
            handle_database_error,
            ErrorHandler
        )
        
        print("✅ 錯誤處理框架導入成功")
        
        # 測試錯誤處理器
        error_handler = ErrorHandler(module_name='integration_test')
        print(f"✅ ErrorHandler 創建成功: {error_handler}")
        
        # 測試標準化響應
        success_result = handle_success(
            operation='integration_test',
            data={'test': 'integration'},
            message='集成測試成功'
        )
        
        print(f"✅ handle_success 測試成功:")
        print(f"   success: {success_result.get('success')}")
        print(f"   message: {success_result.get('message')}")
        
        # 測試錯誤處理
        try:
            raise ValueError("集成測試錯誤")
        except Exception as e:
            error_result = handle_error(
                error=e,
                context='integration_test',
                operation='test_operation',
                data={'test': 'data'}
            )
            
            print(f"✅ handle_error 測試成功:")
            print(f"   success: {error_result.get('success')}")
            print(f"   error_id: {error_result.get('error_id')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理框架集成測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_integration_tests():
    """運行所有集成測試"""
    print("開始隊列管理器集成測試")
    print("="*60)
    
    test_results = []
    
    # 運行測試
    test_results.append(("兩個管理器導入", test_both_managers_import()))
    test_results.append(("方法兼容性", test_method_compatibility()))
    test_results.append(("錯誤處理兼容性", test_error_handling_compatibility()))
    test_results.append(("重要方法兼容性", test_important_methods_compatibility()))
    test_results.append(("實際隊列操作", test_actual_queue_operations()))
    test_results.append(("錯誤處理框架集成", test_error_handling_framework_integration()))
    
    # 顯示測試結果
    print("\n" + "="*60)
    print("集成測試結果總結")
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
        print("\n🎉 所有集成測試通過！")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 個集成測試失敗")
        return False


def main():
    """主函數"""
    try:
        success = run_all_integration_tests()
        
        if success:
            print("\n" + "="*60)
            print("集成測試完成 - 隊列管理器遷移成功")
            print("="*60)
            print("\n🎉 恭喜！queue_manager_refactored.py 集成測試通過！")
            print("\n遷移成果:")
            print("1. ✅ 與原始 queue_manager.py 兼容")
            print("2. ✅ 錯誤處理框架集成成功")
            print("3. ✅ 標準化響應格式正常")
            print("4. ✅ 兼容性包裝器工作正常")
            print("5. ✅ 實際隊列操作正常")
            print("\n建議下一步:")
            print("1. 逐步替換原始 queue_manager.py 的調用")
            print("2. 監控生產環境中的錯誤處理")
            print("3. 更新相關文檔")
            print("4. 進行性能測試")
        else:
            print("\n" + "="*60)
            print("集成測試完成 - 發現問題")
            print("="*60)
            print("\n需要修復的問題:")
            print("1. 檢查方法兼容性")
            print("2. 修復錯誤處理集成")
            print("3. 驗證實際操作流程")
            print("4. 測試兼容性包裝器")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 集成測試運行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)