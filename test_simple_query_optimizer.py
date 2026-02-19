#!/usr/bin/env python3
"""
簡單的查詢優化器測試腳本
測試錯誤處理框架的基本功能
"""

import os
import sys
import logging

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_error_handling_basics():
    """測試錯誤處理框架基礎功能"""
    logger.info("🔍 測試錯誤處理框架基礎功能...")
    
    try:
        # 導入錯誤處理框架
        from eshop.error_handling import (
            handle_error,
            handle_success,
            error_handler_decorator
        )
        
        # 測試1: 錯誤處理
        logger.info("1. 測試錯誤處理")
        try:
            raise ValueError("測試錯誤")
        except Exception as e:
            error_result = handle_error(
                error=e,
                context='test_error',
                operation='test_error',
                data={'test': 'data'}
            )
            
            if not error_result.get('success'):
                logger.info(f"✅ 錯誤處理測試通過: {error_result.get('error_id')}")
                logger.info(f"   錯誤類型: {error_result.get('error_type')}")
            else:
                logger.error("❌ 錯誤處理測試失敗")
                return False
        
        # 測試2: 成功處理
        logger.info("\n2. 測試成功處理")
        success_result = handle_success(
            operation='test_success',
            data={'test': 'data'},
            message='測試成功'
        )
        
        if success_result.get('success'):
            logger.info(f"✅ 成功處理測試通過")
            logger.info(f"   消息: {success_result.get('message')}")
        else:
            logger.error("❌ 成功處理測試失敗")
            return False
        
        # 測試3: 裝飾器
        logger.info("\n3. 測試裝飾器")
        
        @error_handler_decorator(context='test_decorator')
        def test_function(x, y):
            """測試函數"""
            return {'result': x + y, 'x': x, 'y': y}
        
        # 測試正常情況
        decorator_result = test_function(10, 20)
        if isinstance(decorator_result, dict):
            if 'result' in decorator_result:
                logger.info("✅ 裝飾器測試通過")
                logger.info(f"   結果: {decorator_result.get('result')}")
            else:
                # 可能是包裝格式
                if decorator_result.get('success'):
                    data = decorator_result.get('data', {})
                    if 'result' in data:
                        logger.info("✅ 裝飾器測試通過（包裝格式）")
                        logger.info(f"   結果: {data.get('result')}")
                    else:
                        logger.error("❌ 裝飾器測試失敗: 返回格式不正確")
                        return False
                else:
                    logger.error(f"❌ 裝飾器測試失敗: {decorator_result.get('error_id', 'N/A')}")
                    return False
        else:
            logger.error("❌ 裝飾器測試失敗: 返回類型不是字典")
            return False
        
        # 測試錯誤情況
        @error_handler_decorator(context='test_error_decorator')
        def error_function():
            """會出錯的測試函數"""
            raise ValueError("裝飾器測試錯誤")
        
        error_decorator_result = error_function()
        if isinstance(error_decorator_result, dict) and not error_decorator_result.get('success'):
            logger.info("✅ 錯誤裝飾器測試通過")
            logger.info(f"   錯誤ID: {error_decorator_result.get('error_id', 'N/A')}")
        else:
            logger.error("❌ 錯誤裝飾器測試失敗")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理框架測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_query_optimizer_simple():
    """測試查詢優化器簡單功能"""
    logger.info("🔍 測試查詢優化器簡單功能...")
    
    try:
        # 導入查詢優化器
        from eshop.query_optimizer_refactored import (
            QueryOptimizer,
            example_query_function
        )
        
        # 測試1: 緩存統計
        logger.info("1. 測試緩存統計")
        cache_stats_result = QueryOptimizer.get_cache_stats()
        
        if cache_stats_result.get('success'):
            logger.info("✅ 緩存統計測試通過")
            data = cache_stats_result.get('data', {})
            logger.info(f"   總緩存鍵: {data.get('total_keys', 0)}")
        else:
            logger.error("❌ 緩存統計測試失敗")
            return False
        
        # 測試2: 緩存失效
        logger.info("\n2. 測試緩存失效")
        invalidate_result = QueryOptimizer.invalidate_cache('test_prefix')
        
        if invalidate_result.get('success'):
            logger.info("✅ 緩存失效測試通過")
            data = invalidate_result.get('data', {})
            logger.info(f"   刪除的鍵數量: {data.get('count', 0)}")
        else:
            logger.error("❌ 緩存失效測試失敗")
            return False
        
        # 測試3: 示例查詢函數
        logger.info("\n3. 測試示例查詢函數")
        example_result = example_query_function([1, 2, 3])
        
        if isinstance(example_result, dict):
            if 'order_ids' in example_result:
                logger.info("✅ 示例查詢函數測試通過")
                logger.info(f"   訂單ID: {example_result.get('order_ids')}")
            else:
                # 可能是包裝格式
                if example_result.get('success'):
                    data = example_result.get('data', {})
                    if 'order_ids' in data:
                        logger.info("✅ 示例查詢函數測試通過（包裝格式）")
                        logger.info(f"   訂單ID: {data.get('order_ids')}")
                    else:
                        logger.error("❌ 示例查詢函數測試失敗: 返回格式不正確")
                        return False
                else:
                    logger.error(f"❌ 示例查詢函數測試失敗: {example_result.get('error_id', 'N/A')}")
                    return False
        else:
            logger.error("❌ 示例查詢函數測試失敗: 返回類型不是字典")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 查詢優化器測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函數"""
    logger.info("🚀 開始簡單查詢優化器測試")
    logger.info("=" * 60)
    
    try:
        # 測試錯誤處理框架基礎
        error_handling_result = test_error_handling_basics()
        
        # 測試查詢優化器簡單功能
        query_optimizer_result = test_query_optimizer_simple()
        
        # 輸出結果
        logger.info("=" * 60)
        logger.info("📋 測試結果")
        logger.info("=" * 60)
        
        logger.info(f"錯誤處理框架測試: {'✅ 通過' if error_handling_result else '❌ 失敗'}")
        logger.info(f"查詢優化器測試: {'✅ 通過' if query_optimizer_result else '❌ 失敗'}")
        
        total_tests = 2
        passed_tests = sum([error_handling_result, query_optimizer_result])
        
        logger.info("-" * 60)
        logger.info(f"總測試數: {total_tests}")
        logger.info(f"通過測試: {passed_tests}")
        logger.info(f"失敗測試: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            logger.info("🎉 所有測試通過！")
        else:
            logger.warning("⚠️ 部分測試失敗，需要進一步檢查。")
        
        logger.info("=" * 60)
        
        return passed_tests == total_tests
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)