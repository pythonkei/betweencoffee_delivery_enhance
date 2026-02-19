#!/usr/bin/env python3
"""
支付工具模塊遷移測試腳本

這個腳本測試以下內容：
1. 新的錯誤處理框架在支付模塊中的應用
2. 支付工具模塊的遷移效果
3. 標準化響應格式
"""

import os
import sys
import logging
from datetime import datetime

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_error_handling_framework():
    """測試錯誤處理框架在支付模塊中的應用"""
    logger.info("🔍 測試錯誤處理框架在支付模塊中的應用...")
    
    try:
        # 導入遷移後的支付工具模塊
        from eshop.payment_utils_refactored import (
            get_payment_tools,
            generate_fps_reference,
            example_payment_function,
            get_payment_method_display,
            is_payment_method_available,
            get_available_payment_methods
        )
        
        # 測試1: 錯誤處理 - 無效支付方式
        logger.info("1. 測試錯誤處理 - 無效支付方式")
        error_result = get_payment_tools('invalid_method')
        
        if not error_result.get('success'):
            logger.info(f"✅ 錯誤處理測試通過: {error_result.get('error_id')}")
            logger.info(f"   錯誤類型: {error_result.get('error_type')}")
            logger.info(f"   錯誤消息: {error_result.get('message')}")
        else:
            logger.error("❌ 錯誤處理測試失敗: 應該返回錯誤但返回了成功")
            return False
        
        # 測試2: 成功處理 - FPS參考編號生成
        logger.info("\n2. 測試成功處理 - FPS參考編號生成")
        success_result = generate_fps_reference(123)
        
        if success_result.get('success'):
            logger.info(f"✅ 成功處理測試通過")
            logger.info(f"   參考編號: {success_result.get('data', {}).get('reference')}")
            logger.info(f"   消息: {success_result.get('message')}")
        else:
            logger.error(f"❌ 成功處理測試失敗: {success_result.get('error_id', 'N/A')}")
            return False
        
        # 測試3: 裝飾器測試
        logger.info("\n3. 測試裝飾器 - 示例支付函數")
        decorator_result = example_payment_function(456, 'alipay')
        
        # 裝飾器返回的是包裝後的結果，包含 success 和 data
        # 注意：裝飾器返回的是原始函數的結果，不是包裝後的格式
        # 所以我們需要檢查結果是否包含預期的字段
        if isinstance(decorator_result, dict):
            # 如果返回的是字典，檢查是否包含預期字段
            if 'order_id' in decorator_result and 'payment_method' in decorator_result:
                logger.info("✅ 裝飾器測試通過")
                logger.info(f"   訂單ID: {decorator_result.get('order_id', 'N/A')}")
                logger.info(f"   支付方式: {decorator_result.get('payment_method', 'N/A')}")
            else:
                # 可能是錯誤響應格式
                if decorator_result.get('success'):
                    data = decorator_result.get('data', {})
                    if 'order_id' in data and 'payment_method' in data:
                        logger.info("✅ 裝飾器測試通過（包裝格式）")
                        logger.info(f"   訂單ID: {data.get('order_id', 'N/A')}")
                        logger.info(f"   支付方式: {data.get('payment_method', 'N/A')}")
                    else:
                        logger.error("❌ 裝飾器測試失敗: 返回格式不正確")
                        return False
                else:
                    logger.error(f"❌ 裝飾器測試失敗: {decorator_result.get('error_id', 'N/A')}")
                    return False
        else:
            logger.error("❌ 裝飾器測試失敗: 返回類型不是字典")
            return False
        
        # 測試4: 支付方式顯示文本
        logger.info("\n4. 測試支付方式顯示文本")
        display_result = get_payment_method_display('alipay')
        
        if display_result.get('success'):
            logger.info(f"✅ 支付方式顯示測試通過")
            logger.info(f"   顯示文本: {display_result.get('data', {}).get('display_text')}")
        else:
            logger.error(f"❌ 支付方式顯示測試失敗")
            return False
        
        # 測試5: 支付方式可用性檢查
        logger.info("\n5. 測試支付方式可用性檢查")
        availability_result = is_payment_method_available('alipay')
        
        if availability_result.get('success'):
            logger.info(f"✅ 可用性檢查測試通過")
            logger.info(f"   可用性: {availability_result.get('data', {}).get('available')}")
        else:
            logger.error(f"❌ 可用性檢查測試失敗")
            return False
        
        # 測試6: 獲取可用支付方式
        logger.info("\n6. 測試獲取可用支付方式")
        methods_result = get_available_payment_methods()
        
        if methods_result.get('success'):
            methods = methods_result.get('data', {}).get('methods', [])
            logger.info(f"✅ 獲取支付方式測試通過")
            logger.info(f"   可用支付方式數量: {len(methods)}")
            for method in methods:
                logger.info(f"   - {method.get('id')}: {method.get('name')}")
        else:
            logger.error(f"❌ 獲取支付方式測試失敗")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理框架測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_response_format_consistency():
    """測試響應格式一致性"""
    logger.info("🔍 測試響應格式一致性...")
    
    try:
        from eshop.payment_utils_refactored import generate_fps_reference
        
        # 測試成功響應格式
        result = generate_fps_reference(789)
        
        required_keys = ['success', 'message', 'details', 'timestamp']
        if result.get('success'):
            required_keys.append('data')
        
        missing_keys = []
        for key in required_keys:
            if key not in result:
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"❌ 響應格式不一致，缺少鍵: {missing_keys}")
            logger.error(f"   實際響應鍵: {list(result.keys())}")
            return False
        
        logger.info("✅ 響應格式一致性測試通過")
        logger.info(f"   響應包含所有必要鍵: {required_keys}")
        
        # 檢查錯誤響應格式（如果有錯誤ID）
        if 'error_id' in result:
            error_keys = ['error_id', 'error_type']
            for key in error_keys:
                if key not in result:
                    logger.error(f"❌ 錯誤響應缺少鍵: {key}")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 響應格式測試失敗: {str(e)}")
        return False


def test_backward_compatibility():
    """測試向後兼容性"""
    logger.info("🔍 測試向後兼容性...")
    
    try:
        # 檢查原始模塊和新模塊的函數簽名
        import inspect
        
        # 原始模塊
        from eshop import payment_utils as original_module
        # 新模塊
        from eshop import payment_utils_refactored as new_module
        
        # 檢查關鍵函數是否存在
        key_functions = [
            'get_payment_tools',
            'generate_fps_reference',
            'validate_payment_amount',
            'update_order_payment_status',
            'get_payment_method_display',
            'is_payment_method_available',
            'get_available_payment_methods'
        ]
        
        missing_functions = []
        for func_name in key_functions:
            if not hasattr(new_module, func_name):
                missing_functions.append(func_name)
        
        if missing_functions:
            logger.error(f"❌ 新模塊缺少函數: {missing_functions}")
            return False
        
        logger.info("✅ 向後兼容性測試通過")
        logger.info(f"   所有 {len(key_functions)} 個關鍵函數都存在")
        
        # 檢查函數參數（示例）
        for func_name in ['generate_fps_reference', 'get_payment_method_display']:
            if hasattr(original_module, func_name) and hasattr(new_module, func_name):
                original_sig = inspect.signature(getattr(original_module, func_name))
                new_sig = inspect.signature(getattr(new_module, func_name))
                
                if str(original_sig) != str(new_sig):
                    logger.warning(f"⚠️ 函數 {func_name} 簽名不同:")
                    logger.warning(f"   原始: {original_sig}")
                    logger.warning(f"   新: {new_sig}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 向後兼容性測試失敗: {str(e)}")
        return False


def generate_migration_report():
    """生成遷移報告"""
    logger.info("📊 生成遷移報告...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'tests': {
            'error_handling_framework': test_error_handling_framework(),
            'response_format_consistency': test_response_format_consistency(),
            'backward_compatibility': test_backward_compatibility()
        },
        'summary': {
            'total_tests': 3,
            'passed_tests': 0,
            'failed_tests': 0
        }
    }
    
    # 計算統計
    passed = sum(1 for test in report['tests'].values() if test)
    failed = len(report['tests']) - passed
    
    report['summary']['passed_tests'] = passed
    report['summary']['failed_tests'] = failed
    
    # 輸出報告
    logger.info("=" * 60)
    logger.info("📋 支付工具模塊遷移測試報告")
    logger.info("=" * 60)
    
    for test_name, result in report['tests'].items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    logger.info("-" * 60)
    logger.info(f"總測試數: {report['summary']['total_tests']}")
    logger.info(f"通過測試: {report['summary']['passed_tests']}")
    logger.info(f"失敗測試: {report['summary']['failed_tests']}")
    
    if passed == len(report['tests']):
        logger.info("🎉 所有測試通過！支付工具模塊遷移成功。")
    else:
        logger.warning("⚠️ 部分測試失敗，需要進一步檢查。")
    
    logger.info("=" * 60)
    
    return report


def main():
    """主函數"""
    logger.info("🚀 開始支付工具模塊遷移測試")
    logger.info(f"測試時間: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    try:
        report = generate_migration_report()
        
        # 輸出建議
        logger.info("💡 遷移建議:")
        
        if report['summary']['passed_tests'] == report['summary']['total_tests']:
            logger.info("1. ✅ 支付工具模塊遷移成功，可以進行下一步")
            logger.info("2. ✅ 建議逐步替換原始模塊的導入")
            logger.info("3. ✅ 可以開始遷移其他核心模塊")
        else:
            logger.info("1. ⚠️ 需要檢查失敗的測試項目")
            logger.info("2. ⚠️ 可能需要修復遷移問題")
            logger.info("3. ⚠️ 建議重新測試確認遷移效果")
        
        # 遷移步驟
        logger.info("\n📋 遷移步驟:")
        logger.info("1. 備份原始 payment_utils.py")
        logger.info("2. 將 payment_utils_refactored.py 重命名為 payment_utils.py")
        logger.info("3. 更新所有導入 payment_utils 的模塊")
        logger.info("4. 運行全面測試")
        logger.info("5. 監控生產環境錯誤日誌")
        
        return report['summary']['passed_tests'] == report['summary']['total_tests']
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)