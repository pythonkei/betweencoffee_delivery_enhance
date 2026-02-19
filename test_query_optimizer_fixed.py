#!/usr/bin/env python3
"""
查詢優化器修復版本測試腳本
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


def test_fixed_version():
    """測試修復版本"""
    logger.info("🔍 測試查詢優化器修復版本...")
    
    try:
        # 導入修復版本的查詢優化器
        from eshop.query_optimizer_refactored_fixed import (
            QueryOptimizer,
            example_query_function,
            get_queue_summary_cached_compatible,
            get_active_orders_cached_compatible
        )
        
        logger.info("✅ 模塊導入成功")
        
        # 測試1: 緩存統計
        logger.info("\n1. 測試緩存統計")
        cache_stats_result = QueryOptimizer.get_cache_stats()
        
        if cache_stats_result.get('success'):
            logger.info("✅ 緩存統計測試通過")
            data = cache_stats_result.get('data', {})
            logger.info(f"   總緩存鍵: {data.get('total_keys', 0)}")
            logger.info(f"   查詢緩存鍵: {data.get('query_keys', 0)}")
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
        
        # 測試4: 兼容性包裝器
        logger.info("\n4. 測試兼容性包裝器")
        
        # 測試隊列摘要兼容性包裝器
        queue_summary = get_queue_summary_cached_compatible()
        if isinstance(queue_summary, dict):
            logger.info("✅ 隊列摘要兼容性包裝器測試通過")
            logger.info(f"   返回類型: {type(queue_summary).__name__}")
        else:
            logger.error("❌ 隊列摘要兼容性包裝器測試失敗")
            return False
        
        # 測試活動訂單兼容性包裝器
        active_orders = get_active_orders_cached_compatible()
        if isinstance(active_orders, list):
            logger.info("✅ 活動訂單兼容性包裝器測試通過")
            logger.info(f"   返回類型: {type(active_orders).__name__}")
        else:
            logger.error("❌ 活動訂單兼容性包裝器測試失敗")
            return False
        
        # 測試5: 響應格式一致性
        logger.info("\n5. 測試響應格式一致性")
        result = QueryOptimizer.get_cache_stats()
        
        required_keys = ['success', 'message', 'details', 'timestamp']
        if result.get('success'):
            required_keys.append('data')
        
        missing_keys = []
        for key in required_keys:
            if key not in result:
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"❌ 響應格式不一致，缺少鍵: {missing_keys}")
            return False
        
        logger.info("✅ 響應格式一致性測試通過")
        logger.info(f"   響應包含所有必要鍵: {required_keys}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 查詢優化器測試失敗: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函數"""
    logger.info("🚀 開始查詢優化器修復版本測試")
    logger.info("=" * 60)
    
    try:
        # 測試修復版本
        test_result = test_fixed_version()
        
        # 輸出結果
        logger.info("=" * 60)
        logger.info("📋 測試結果")
        logger.info("=" * 60)
        
        logger.info(f"查詢優化器修復版本測試: {'✅ 通過' if test_result else '❌ 失敗'}")
        
        if test_result:
            logger.info("🎉 修復版本測試通過！")
            logger.info("💡 建議: 可以將 query_optimizer_refactored_fixed.py 重命名為 query_optimizer.py")
        else:
            logger.warning("⚠️ 修復版本測試失敗，需要進一步檢查。")
        
        logger.info("=" * 60)
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)